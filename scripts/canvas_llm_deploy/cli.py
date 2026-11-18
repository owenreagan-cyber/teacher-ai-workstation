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
from . import scope as scope_mod
from .client import LiveDeployClient


def _resolve(args: Any) -> tuple[int, int]:
    # quarter/week are required for deployment commands.
    return int(args.quarter), int(args.week)


def _make_read_client():
    """GET-only Canvas client. Never constructs a write transport."""
    from scripts.canvas_llm_intake.canvas_readonly import CanvasReadOnly
    return CanvasReadOnly.from_env()


def _make_client(production: bool, quarter: int, week: int):
    if not production:
        return None
    return LiveDeployClient(quarter=quarter, week=week)


def cmd_reconcile(args: Any) -> int:
    quarter, week = _resolve(args)
    if not args.live:
        print("BLOCKED: --live is required; reconciliation is never fabricated locally")
        return 2
    from scripts.canvas_llm_intake import assignment_reconciliation as ar
    try:
        report = ar.run_live_reconciliation(
            quarter, week, client=_make_read_client(),
        )
    except Exception as exc:  # noqa: BLE001 - fail closed
        print(f"BLOCKED: live reconciliation failed: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps({
        "report_path": report.get("report_path"),
        "week_code": report.get("week_code"),
        "source_hash": report.get("source_hash"),
        "proposal_count": report.get("proposal_count"),
        "counts": report.get("counts"),
        "bundle_status": report.get("bundle_status"),
        "blockers": report.get("blockers"),
        "pending_actions": report.get("pending_actions"),
        "canvas_writes": report.get("canvas_writes"),
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_scope_authorize(args: Any) -> int:
    quarter, week = _resolve(args)
    plan = plan_mod.build_plan(quarter, week)
    subjects = [s.strip() for s in (args.subjects or "").split(",") if s.strip()]
    artifacts = [a.strip() for a in (args.artifacts or "").split(",") if a.strip()]
    protected: list[dict[str, Any]] = []
    for token in args.protect or []:
        left, _, title = token.partition("=")
        course_id, _, assignment_id = left.partition(":")
        if not course_id.isdigit() or not assignment_id:
            print(f"BLOCKED: --protect expects COURSE_ID:ASSIGNMENT_ID[=TITLE], got {token!r}")
            return 2
        protected.append({
            "course_id": int(course_id),
            "assignment_id": assignment_id,
            "title": title or None,
        })
    try:
        record = scope_mod.authorize_scope(
            quarter, week, plan=plan, subjects=subjects, artifacts=artifacts,
            protected_assignments=protected, confirmation=args.confirm or "",
            reason=args.reason or "restricted owner-authorized deployment scope",
        )
    except scope_mod.ScopeError as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


def cmd_preflight(args: Any) -> int:
    quarter, week = _resolve(args)
    client = _make_read_client() if args.production else None
    rec = preflight_mod.run_preflight(quarter, week, client, scoped=args.scoped)
    print(json.dumps(rec, indent=2, ensure_ascii=False))
    return 0 if rec.get("ready") else 2


def cmd_deploy(args: Any) -> int:
    quarter, week = _resolve(args)

    # Dry run: deterministic plan only (no Canvas GET, no writes).
    if args.dry_run:
        plan = plan_mod.build_plan(quarter, week)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    print(
        "BLOCKED: weekly publishing is owned exclusively by the Friday rollover "
        "engine (D-028). Use `bin/canvas-intake restricted-release` for an "
        "owner-scoped restricted release."
    )
    return 2


def cmd_restricted_release(args: Any) -> int:
    """Run an owner-scoped restricted release through the rollover publisher."""
    quarter, week = _resolve(args)
    if not args.production:
        print("BLOCKED: restricted release requires --production")
        return 2
    if not args.preflight_id:
        print("BLOCKED: restricted release requires --preflight-id")
        return 2
    from . import restricted_release

    try:
        report = restricted_release.release(
            quarter, week,
            preflight_id=args.preflight_id,
            confirmation=args.confirm or "",
            authorize_live=args.authorize_live,
        )
    except restricted_release.RestrictedReleaseBlocked as exc:
        print(f"BLOCKED: {exc}")
        return 2
    except Exception as exc:  # noqa: BLE001 - never mask an unexpected write-path error
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("lifecycle") in (
        "EARLY_CONTENT_PUBLISHED_VERIFIED", "PARTIAL_PUBLISHED_VERIFIED",
    ) else 1


def cmd_verify(args: Any) -> int:
    quarter, week = _resolve(args)
    client = _make_client(args.production, quarter, week)
    if client is None:
        print("BLOCKED: verify requires --production (readback against live Canvas)")
        return 2
    result = coordinator.verify(quarter, week, client=client)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def build_parser(sub) -> None:
    """Attach deployment subcommands to an existing argparse subparsers object."""
    sp = sub.add_parser("reconcile", help="GET-only live assignment reconciliation (writes a local report)")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--live", action="store_true", help="perform live Canvas GETs (required)")
    sp.set_defaults(func=cmd_reconcile)

    sp = sub.add_parser("scope-authorize", help="record an explicit restricted deployment scope")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--subjects", required=True, help="comma-separated, e.g. math,reading_spelling")
    sp.add_argument("--artifacts", required=True, help="comma-separated: page,assignments")
    sp.add_argument("--protect", action="append", default=[],
                    help="COURSE_ID:ASSIGNMENT_ID[=TITLE] preserved with readback")
    sp.add_argument("--confirm", type=str, default=None, help="exact phrase: SCOPE QxWy")
    sp.add_argument("--reason", type=str, default=None)
    sp.set_defaults(func=cmd_scope_authorize)

    sp = sub.add_parser("preflight", help="GET-only deployment preflight (plan + live object resolution)")
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--production", action="store_true",
                    help="resolve live Canvas objects (GET-only); without it, dry-run plan only")
    sp.add_argument("--scoped", action="store_true",
                    help="evaluate the recorded restricted scope instead of full-week readiness")
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

    sp = sub.add_parser(
        "restricted-release",
        help="owner-scoped restricted release through the Friday rollover publisher",
    )
    sp.add_argument("--quarter", type=int, required=True)
    sp.add_argument("--week", type=int, required=True)
    sp.add_argument("--production", action="store_true", help="perform real Canvas writes")
    sp.add_argument("--preflight-id", type=str, required=True)
    sp.add_argument("--confirm", type=str, default=None,
                    help="exact owner confirmation: ROLLOVER QxWy")
    sp.add_argument("--authorize-live", action="store_true",
                    help="mint a 15-minute live-transport authorization for this exact plan")
    sp.set_defaults(func=cmd_restricted_release)

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
