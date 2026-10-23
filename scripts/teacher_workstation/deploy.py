"""Teacher Workstation — guarded deployment route handlers (server-side only).

The Friday rollover engine is the only publisher of a weekly package. Legacy
deploy preflight remains available for read-only inspection, but direct deploy
is permanently rejected so the UI cannot create a second publishing path.

Safety:
- The Canvas token never leaves this process (it is loaded backend-only).
- Production writes require an explicit ``production=true`` flag + a valid,
  unexpired preflight + owner confirmation.
- No generic Canvas proxy: the server derives all Canvas targets/payloads
  canonically from the staged plan.
"""
from __future__ import annotations

from typing import Any


def run_preflight(quarter: int, week: int, production: bool) -> dict[str, Any]:
    from scripts.canvas_llm_deploy import preflight as pf

    if production:
        from scripts.canvas_llm_deploy.client import LiveDeployClient
        client = LiveDeployClient()
        return pf.run_preflight(quarter, week, client)
    return pf.run_preflight(quarter, week, None)


def run_deploy(
    quarter: int,
    week: int,
    *,
    preflight_id: str,
    expected_source_hash: str,
    expected_approval_snapshot_hash: str,
    owner_confirmation: str,
    production: bool,
) -> dict[str, Any]:
    raise ValueError("weekly publishing is owned exclusively by Friday rollover")


def run_rollover_dry_run(quarter: int, week: int, production: bool = False) -> dict[str, Any]:
    from scripts.canvas_llm_rollover import cli, rollover

    fq, fw, tq, tw = cli._resolve(None, None, f"q{quarter}w{week}")
    client = None
    if production:
        from scripts.canvas_llm_deploy.client import LiveDeployClient
        client = LiveDeployClient()
    result = rollover.run_preflight(fq, fw, tq, tw, client=client)
    return {
        "summary": "Dry run finished. Nothing was changed.",
        "ready": result["ready"], "blockers": result["blockers"],
        "warnings": result["warnings"], "canvas_writes": 0,
        "plan": cli._dry_run_view(result["manifest"]),
    }


def run_rollover_partial(
    quarter: int, week: int, *, owner_confirmation: str, production: bool,
) -> dict[str, Any]:
    if not production:
        raise ValueError("partial publish requires production=true after the explicit warning")
    from scripts.canvas_llm_deploy.client import LiveDeployClient
    from scripts.canvas_llm_rollover import cli, rollover

    fq, fw, tq, tw = cli._resolve(None, None, f"q{quarter}w{week}")
    return rollover.publish_approved_courses_only(
        fq, fw, tq, tw, client=LiveDeployClient(),
        owner_confirmation=owner_confirmation,
    )


def run_publish_now(
    quarter: int, week: int, *, courses: list[str], owner_confirmation: str,
    production: bool,
) -> dict[str, Any]:
    if not production:
        raise ValueError("Publish now requires the explicit production confirmation")
    from scripts.canvas_llm_deploy.client import LiveDeployClient
    from scripts.canvas_llm_rollover import cli, rollover

    fq, fw, tq, tw = cli._resolve(None, None, f"q{quarter}w{week}")
    return rollover.publish_now(
        fq, fw, tq, tw, client=LiveDeployClient(), courses=courses,
        owner_confirmation=owner_confirmation,
    )
