"""Friday reminder and automatic-rollover orchestration.

The LaunchAgent calls this local module twice on Friday. At 1 PM it records a
local reminder result only. At 4 PM it invokes the canonical rollover engine;
there is no second publisher.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from scripts.canvas_llm_intake import week_resolution
from scripts.canvas_planner.state_root import planner_root

EASTERN = ZoneInfo("America/New_York")


def settings_path(root: Path | None = None) -> Path:
    return (Path(root) if root is not None else planner_root()) / "settings.json"


def load_settings(root: Path | None = None) -> dict[str, Any]:
    try:
        value = json.loads(settings_path(root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    return {"automatic_rollover": bool(value.get("automatic_rollover", True))}


def set_automatic_rollover(enabled: bool, root: Path | None = None) -> dict[str, Any]:
    value = {"schemaVersion": 1, "automatic_rollover": bool(enabled)}
    path = settings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
    return value


def _weeks(today) -> tuple[int, int, int, int]:
    tq, tw = week_resolution.next_week(today=today)
    weeks = sorted(
        (w for w in week_resolution.load_weeks() if week_resolution._week_start(w) is not None),
        key=week_resolution._week_start,
    )
    code = week_resolution.week_code_for(tq, tw)
    index = next(i for i, value in enumerate(weeks) if value.get("code") == code)
    if index == 0:
        raise RuntimeError(f"no prior instructional week for {code}")
    prior = weeks[index - 1]
    return int(prior["quarter"]), int(prior["week"]), tq, tw


def scheduled_run(
    *, now: datetime | None = None,
    client_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Run the 1 PM reminder or 4 PM all-or-nothing rollover action."""
    local = (now or datetime.now(EASTERN)).astimezone(EASTERN)
    fq, fw, tq, tw = _weeks(local.date())
    code = week_resolution.week_code_for(tq, tw)
    if local.weekday() != 4:
        return {"action": "NOOP", "reason": "scheduled Friday action ran outside Friday", "week": code}
    if local.hour < 16:
        from .service import CanvasPlannerService
        status = CanvasPlannerService().weekly_status(tq, tw, now=local)
        reminder = next((item for item in status["action_items"]
                         if item["id"] == f"friday-readiness:{code.lower()}"), None)
        return {
            "action": "REMINDER", "week": code,
            "open": reminder is not None,
            "action_item": reminder,
            "canvas_writes": 0,
        }
    if not load_settings()["automatic_rollover"]:
        return {"action": "ROLLOVER_DISABLED", "week": code, "canvas_writes": 0}
    from scripts.canvas_llm_rollover import rollover
    readiness = rollover.build_readiness(fq, fw, tq, tw, today=local.date())
    if not readiness["ready"]:
        return {
            "action": "ROLLOVER_BLOCKED", "week": code,
            "blockers": readiness["blockers"], "canvas_writes": 0,
        }
    if client_factory is None:
        from scripts.canvas_llm_deploy.client import LiveDeployClient
        client_factory = LiveDeployClient
    report = rollover.publish_weekly_package(
        fq, fw, tq, tw, client=client_factory(),
        owner_confirmation=f"ROLLOVER {code}", today=local.date(),
    )
    return {"action": "ROLLOVER", "week": code, "report": report}
