"""Friday rollover deployment ledger (untracked local state).

Reuses the existing deploy ledger directory + JSON helpers. The rollover ledger
lives beside the weekly deployment ledger under
``.local/canvas-llm/deployments/2026-2027/q<q>/w<w>/rollover-ledger.json``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.canvas_llm_deploy import ledger as deploy_ledger


def rollover_ledger_path(quarter: int, week: int) -> Path:
    return deploy_ledger.deploy_dir(quarter, week) / "rollover-ledger.json"


def write_rollover_ledger(quarter: int, week: int, data: dict[str, Any]) -> Path:
    return deploy_ledger.write_json(rollover_ledger_path(quarter, week), data)


def load_rollover_ledger(quarter: int, week: int) -> dict[str, Any] | None:
    return deploy_ledger.read_json(rollover_ledger_path(quarter, week))


def command_self_test() -> int:
    import tempfile
    orig = deploy_ledger.DEPLOY_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = __import__("pathlib").Path(tmp) / "deployments"
        try:
            write_rollover_ledger(2, 3, {"lifecycle": "EXECUTING"})
            rec = load_rollover_ledger(2, 3)
            assert rec is not None and rec["lifecycle"] == "EXECUTING"
            assert rollover_ledger_path(2, 3).name == "rollover-ledger.json"
        finally:
            deploy_ledger.DEPLOY_ROOT = orig
    print("PASS canvas-rollover ledger self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
