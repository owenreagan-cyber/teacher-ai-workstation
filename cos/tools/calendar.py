"""calendar.today: today's events via the EventKit reader helper app (read-only).

The helper is ChiefOfStaffEventKitReader.app (built and signed by
scripts/cos-build-eventkit-helper.sh). It is launched only through
LaunchServices (`open`), never as a child process, so macOS attributes the
Calendar/Reminders grant to the helper's own bundle identity rather than to
Terminal or Raycast. The helper also refuses EventKit commands unless it is
its own responsible process.

macOS has no read-only EventKit tier for reading events: the grant is "full
access". Read-only behavior is enforced in code: the helper has no command
that creates, edits, or deletes anything, and only title, times, all-day
flag, and calendar name are kept.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from cos.config import REPO_ROOT, ensure_private_subdir, open_private
from cos.registry import Tool

HELPER_DIR = REPO_ROOT / "cos" / "helpers" / "eventkit-reader"
DEFAULT_APP = HELPER_DIR / "build" / "ChiefOfStaffEventKitReader.app"
OPEN = "/usr/bin/open"
KEYWORDS = ("calendar", "meeting", "meetings", "schedule", "event", "events", "appointment",
            "busy", "free", "today", "tomorrow", "conference", "agenda", "trip", "field trip", "assembly",
            "when is", "when are")
TITLE_CAP = 120
POLL_S = 0.05


class HelperError(Exception):
    pass


def helper_app(ctx) -> Path:
    return Path(ctx.eventkit_app) if ctx.eventkit_app else DEFAULT_APP


def launch_argv(app: Path, out: Path, err: Path, argv: list[str]) -> list[str]:
    """LaunchServices launch: new instance (-n), wait (-W), background (-g), hidden (-j).

    cos never asks for permission: COS_EVENTKIT_NO_PROMPT=1 makes the helper report
    not_determined instead of prompting. The one-time grant is a separate, explicit
    command in docs/cos-m1-live-checks.md."""
    return [OPEN, "-W", "-n", "-g", "-j", "--env", "COS_EVENTKIT_NO_PROMPT=1",
            "--stdout", str(out), "--stderr", str(err), str(app), "--args", *argv]


def _read_complete(out: Path, deadline: float) -> str:
    """open -W can return before a very short-lived app has written; wait for one full line."""
    while True:
        try:
            text = out.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if text.endswith("\n"):
            return text
        if time.monotonic() >= deadline:
            return text
        time.sleep(POLL_S)


def call_helper(ctx, argv: list[str], timeout: float = 15) -> dict:
    app = helper_app(ctx)
    if not (app / "Contents" / "MacOS" / "eventkit-reader").exists():
        raise HelperError("EventKit helper app not built; run scripts/cos-build-eventkit-helper.sh "
                          "(see docs/cos-m1-live-checks.md)")
    out_dir = ensure_private_subdir("eventkit", ctx.config.state_dir)
    tag = f"{os.getpid()}-{uuid.uuid4().hex}"
    out, err = out_dir / f"{tag}.out", out_dir / f"{tag}.err"
    for f in (out, err):
        open_private(f, "w").close()
    deadline = time.monotonic() + timeout
    try:
        res = ctx.run(launch_argv(app, out, err, argv), timeout=timeout)
        text = _read_complete(out, deadline)
    finally:
        for f in (out, err):
            f.unlink(missing_ok=True)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HelperError(f"EventKit helper returned no JSON (open exit {res.returncode})")
    if not isinstance(data, dict):
        raise HelperError("EventKit helper returned an unexpected shape")
    status = data.get("status")
    if status == "wrong_launch":
        raise HelperError(f"EventKit helper refused: {data.get('message', 'wrong launch')}")
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
    return events_result(ctx, data)


def events_result(ctx, data: dict) -> dict:
    """The tool result for helper output (also used by fixture mode)."""
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
