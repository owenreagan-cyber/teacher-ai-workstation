"""CLI commands for guarded Canvas deployment (preflight / deploy / verify).

Wired into ``bin/canvas-intake``. Production writes require an explicit
``--production`` flag and owner confirmation; dry-run and preflight are GET-only
(or fully local for dry-run).
"""
from __future__ import annotations

import json
from typing import Any

from . import coordinator
from . import ledger
from . import plan as plan_mod
from . import preflight as preflight_mod
from .client import LiveDeployClient, DeployClientError


def _resolve(args: Any) -> tuple[int, int]:
    # quarter/week are required for deployment commands.
    return int(args.quarter), int(args.week)


def _make_client(production: bool):
    if not production:
        return None
    return LiveDeployClient()


def cmd_preflight(args: Any) -> int:
    quarter, week = _resolve(args)
    client = _make_client(args.production)
    rec = preflight_mod.run_preflight(quarter, week, client)
    print(json.dumps(rec, indent=2, ensure_ascii=False))
    return 0


def cmd_deploy(args: Any) -> int:
    quarter, week = _resolve(args)

    # Dry run: deterministic plan only (no Canvas GET, no writes).
    if args.dry_run:
        plan = plan_mod.build_plan(quarter, week)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    if not args.production:
        print("BLOCKED: production Canvas writes require --production (use --dry-run to preview the plan)")
        return 2

    try:
        client = LiveDeployClient()
    except Exception as exc:  # noqa: BLE001
        print(f"BLOCKED: Canvas transport unavailable: {type(exc).__name__}")
        return 2

    # A deploy requires a fresh preflight + confirmation.
    preflight_id = args.preflight_id
    if not preflight_id:
        rec = preflight_mod.run_preflight(quarter, week, client)
        if not rec.get("ready"):
            print("BLOCKED: preflight not ready")
            for b in rec.get("blockers", []):
                print(f"  - {b}")
            return 2
        preflight_id = rec["preflight_id"]
        expected_source = rec["source_hash"]
        expected_approval = rec["approval_snapshot_hash"]
        print(f"Preflight {preflight_id} ready.")
    else:
        rec = ledger.load_preflight(quarter, week, preflight_id)
        if rec is None:
            print(f"BLOCKED: preflight {preflight_id} not found")
            return 2
        expected_source = rec.get("source_hash", "")
        expected_approval = rec.get("approval_snapshot_hash", "")

    if not args.confirm:
        print("BLOCKED: deploy requires --confirm with explicit owner confirmation (e.g. 'DEPLOY Q2W3')")
        return 2

    try:
        report = coordinator.deploy(
            quarter, week, preflight_id=preflight_id,
            expected_source_hash=expected_source,
            expected_approval_snapshot_hash=expected_approval,
            owner_confirmation=args.confirm, client=client, source="OWNER_CLI",
        )
    except coordinator.DeploymentBlocked as exc:
        print(f"BLOCKED: {exc}")
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"BLOCKED: deployment failed: {type(exc).__name__}")
        return 2

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report.get("deployment_state") == "PUBLISHED_VERIFIED":
        print("DEPLOYED AND VERIFIED")
        return 0
    print(f"DEPLOYMENT {report.get('deployment_state')} — ATTENTION REQUIRED")
    return 1


def cmd_verify(args: Any) -> int:
    quarter, week = _resolve(args)
    client = _make_client(args.production)
    if client is None:
        print("BLOCKED: verify requires --production (readback against live Canvas)")
        return 2
    result = coordinator.verify(quarter, week, client=client)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def build_parser(sub) -> None:
    """Attach deployment subcommands to an existing argparse subparsers object."""
    sp = sub.add_parser("preflight", help="GET-only deployment preflight (plan + live object resolution)")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--production", action="store_true",
                    help="resolve live Canvas objects (GET-only); without it, dry-run plan only")
    sp.set_defaults(func=cmd_preflight)

    sp = sub.add_parser("deploy", help="guarded Canvas deployment (requires --production + confirmation)")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--dry-run", action="store_true", help="print the exact write plan (no Canvas)")
    sp.add_argument("--production", action="store_true", help="perform real Canvas writes")
    sp.add_argument("--preflight-id", type=str, default=None)
    sp.add_argument("--confirm", type=str, default=None,
                    help="explicit owner confirmation, e.g. 'DEPLOY Q2W3'")
    sp.set_defaults(func=cmd_deploy)

    sp = sub.add_parser("verify", help="post-write readback verification (requires --production)")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--production", action="store_true")
    sp.set_defaults(func=cmd_verify)


def command_self_test() -> int:
    # Dry-run plan build is local + deterministic (no Canvas).
    plan = plan_mod.build_plan(2, 3)
    assert "counts" in plan and "week_code" in plan and "source_hash" in plan
    print("PASS canvas-deploy cli self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
