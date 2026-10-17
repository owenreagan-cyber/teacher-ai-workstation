"""Teacher Workstation — guarded deployment route handlers (server-side only).

These are the ONLY routes in the local UI server that can reach Canvas mutation
code. They delegate to ``scripts.canvas_llm_deploy`` (the deployment
coordinator), which in turn delegates to the canonical Canvas write helpers.

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
    if not production:
        raise ValueError("deploy requires production=true")
    from scripts.canvas_llm_deploy import coordinator
    from scripts.canvas_llm_deploy.client import LiveDeployClient

    client = LiveDeployClient()
    return coordinator.deploy(
        quarter, week, preflight_id=preflight_id,
        expected_source_hash=expected_source_hash,
        expected_approval_snapshot_hash=expected_approval_snapshot_hash,
        owner_confirmation=owner_confirmation, client=client, source="OWNER_UI",
    )
