"""Configured Friday schedule and notification-delivery gates.

Values only — no business logic here. Friday timing is a *configured* schedule
(not hard-coded), and email delivery is gated off by default. These settings
live under ``.local/canvas-planner/agent/schedule.json`` (gitignored).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.canvas_planner.state_root import planner_root

DEFAULT_SCHEDULE = {
    "timezone": "America/New_York",
    # Local times (24h HH:MM) for the canonical Friday flow.
    "source_sync_before_review": "12:00",
    "final_refresh": "15:00",       # 3:00 PM Friday
    "approval_ready_email": "15:30",  # 3:30 PM Friday
    "publish": "16:00",             # 4:00 PM Friday
}

# Notification delivery gate. ``mode`` is one of preview/local/email. Email is
# disabled by default; nothing in this package enables it automatically.
DEFAULT_DELIVERY = {
    "mode": "preview",
    "email_enabled": False,
    "email_recipient": "",
    "email_from": "",
}


def _config_path() -> Path:
    return planner_root() / "agent" / "schedule.json"


def _read() -> dict[str, Any]:
    try:
        data = json.loads(_config_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def schedule() -> dict[str, Any]:
    """Return the configured Friday schedule (defaults overlaid by local config)."""
    merged = dict(DEFAULT_SCHEDULE)
    merged.update(_read().get("schedule") or {})
    return merged


def delivery_config() -> dict[str, Any]:
    """Return the notification delivery gate config."""
    merged = dict(DEFAULT_DELIVERY)
    merged.update(_read().get("delivery") or {})
    merged["email_enabled"] = bool(merged.get("email_enabled"))
    return merged


def write_config(schedule: dict[str, Any] | None = None, delivery: dict[str, Any] | None = None) -> dict[str, Any]:
    """Persist explicit config overrides (local only). Never auto-enables email."""
    path = _config_path()
    data = _read()
    if schedule is not None:
        data["schedule"] = {**data.get("schedule", {}), **schedule}
    if delivery is not None:
        existing = data.get("delivery", {})
        data["delivery"] = {**existing, **delivery}
        # Fail-closed: writing config can only DISABLE email unless explicitly
        # and deliberately requested.
        data["delivery"]["email_enabled"] = bool(data["delivery"].get("email_enabled", False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def command_self_test() -> int:
    import tempfile
    from pathlib import Path
    import scripts.weekly_planner_agent.schedule_config as sc
    orig = sc.planner_root
    sc.planner_root = lambda: Path(tempfile.mkdtemp())
    try:
        s = schedule()
        assert s["publish"] == "16:00" and s["timezone"] == "America/New_York"
        d = delivery_config()
        assert d["mode"] == "preview" and d["email_enabled"] is False
    finally:
        sc.planner_root = orig
    print("PASS weekly-planner-agent schedule-config self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
