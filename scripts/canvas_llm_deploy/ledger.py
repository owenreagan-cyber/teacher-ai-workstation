"""Local deployment ledger + preflight records + backups (untracked, no secrets)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_planner.state_root import deployment_root

DEPLOY_ROOT = deployment_root()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def deploy_dir(quarter: int, week: int) -> Path:
    return DEPLOY_ROOT / "2026-2027" / f"q{quarter}" / f"w{week}"


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_preflight(quarter: int, week: int, preflight: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / f"preflight-{preflight['preflight_id']}.json", preflight)


def load_preflight(quarter: int, week: int, preflight_id: str) -> dict[str, Any] | None:
    return read_json(deploy_dir(quarter, week) / f"preflight-{preflight_id}.json")


def write_ledger(quarter: int, week: int, ledger: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / "deployment-ledger.json", ledger)


def load_ledger(quarter: int, week: int) -> dict[str, Any] | None:
    return read_json(deploy_dir(quarter, week) / "deployment-ledger.json")


def write_backup(quarter: int, week: int, name: str, data: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / "backups" / f"{name}.json", data)


def finalize_published_verified(quarter: int, week: int, report: dict[str, Any]) -> Path:
    """Write the canonical published-verified-ledger.json and advance the manifest.

    The manifest moves READY_TO_PUBLISH -> PUBLISHED_VERIFIED (forward, monotonic).
    """
    path = write_json(deploy_dir(quarter, week) / "published-verified-ledger.json", report)
    m = imf.load_manifest(quarter, week)
    if m is not None:
        if m.get("status") != "PUBLISHED_VERIFIED":
            imf.advance_status(m, "PUBLISHED_VERIFIED")
        m["ready_to_publish"] = True
        m["published_at"] = _now()
        imf.save_manifest(quarter, week, m)
    return path


def command_self_test() -> int:
    import tempfile

    orig = imf.staging_dir
    global DEPLOY_ROOT
    orig_root = DEPLOY_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        # Point both staging + deploy roots at the temp dir.
        DEPLOY_ROOT = Path(tmp) / "deployments"
        # manifest staging_dir affects finalize; use a separate temp for manifest.
        imf.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            pre = {"preflight_id": "pf123", "plan": {}}
            assert write_preflight(2, 3, pre).exists()
            assert load_preflight(2, 3, "pf123")["preflight_id"] == "pf123"
            write_ledger(2, 3, {"deployment_state": "DEPLOYING"})
            assert load_ledger(2, 3)["deployment_state"] == "DEPLOYING"
            write_backup(2, 3, "math-page-before", {"body": "x"})
            assert (deploy_dir(2, 3) / "backups" / "math-page-before.json").exists()
            # finalize advances manifest
            m = imf.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                 date_range={"start": "2026-10-26", "end": "2026-10-30"})
            m["status"] = "READY_TO_PUBLISH"
            imf.save_manifest(2, 3, m)
            finalize_published_verified(2, 3, {"status": "PUBLISHED_VERIFIED"})
            assert imf.load_manifest(2, 3)["status"] == "PUBLISHED_VERIFIED"
        finally:
            imf.staging_dir = orig
            DEPLOY_ROOT = orig_root
    print("PASS canvas-deploy ledger self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
