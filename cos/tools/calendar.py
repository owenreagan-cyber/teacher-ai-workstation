"""calendar.today: today's events via the EventKit reader helper (read-only).

The helper (cos/helpers/eventkit-reader) prints JSON. Only title, times,
all-day flag, and calendar name are kept; notes, attendees, and locations
are never requested from the helper's output.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cos.config import REPO_ROOT
from cos.registry import Tool

HELPER_DIR = REPO_ROOT / "cos" / "helpers" / "eventkit-reader"
DEFAULT_HELPER = HELPER_DIR / ".build" / "release" / "eventkit-reader"
KEYWORDS = ("calendar", "meeting", "meetings", "schedule", "event", "events", "appointment",
            "busy", "free", "today", "tomorrow", "conference", "agenda")
TITLE_CAP = 120


class HelperError(Exception):
    pass


def helper_path(ctx) -> Path:
    return Path(ctx.eventkit_helper) if ctx.eventkit_helper else DEFAULT_HELPER


def call_helper(ctx, argv: list[str], timeout: float = 15) -> dict:
    path = helper_path(ctx)
    if not path.exists():
        raise HelperError(f"EventKit helper not built; see docs/cos-m1-live-checks.md ({path})")
    res = ctx.run([str(path), *argv], timeout=timeout)
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        raise HelperError(f"EventKit helper returned non-JSON output (exit {res.returncode})")
    if not isinstance(data, dict):
        raise HelperError("EventKit helper returned an unexpected shape")
    status = data.get("status")
    if status != "ok":
        raise HelperError(f"EventKit access {status or 'unknown'}: grant access on the first "
                          "live run (docs/cos-m1-live-checks.md)")
    return data


def _time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None
    return dt.strftime("%I:%M %p").lstrip("0")


def normalize_event(ev: dict) -> dict:
    title = str(ev.get("title") or "(no title)")[:TITLE_CAP]
    all_day = bool(ev.get("all_day"))
    return {"title": title, "all_day": all_day,
            "start": None if all_day else _time(ev.get("start")),
            "end": None if all_day else _time(ev.get("end")),
            "start_iso": ev.get("start"),
            "calendar": str(ev.get("calendar") or "")[:60]}


def today(ctx, args: dict) -> dict:
    try:
        data = call_helper(ctx, ["events", "--days", "1"])
    except HelperError as e:
        return {"error": str(e)}
    events = [normalize_event(e) for e in data.get("events", []) if isinstance(e, dict)]
    events.sort(key=lambda e: (not e["all_day"], e["start_iso"] or ""))
    return {"date": ctx.clock().date().isoformat(), "count": len(events), "events": events}


def tools(ctx):
    return [Tool(
        name="calendar.today",
        description="Owen's calendar events for today (read-only): title, start/end time, calendar.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        side_effect="none", data_class="P1", timeout_s=20,
        func=lambda args: today(ctx, args), keywords=KEYWORDS,
    )]
