"""Chief of Staff FRIDAY ROLLOVER status (read-only, PASS/WARN/FAIL).

Answers (§40): current week, upcoming week, scheduled time, readiness,
blockers, front-page targets, Homeroom readiness, weekly-update readiness,
whether execution is due, and whether the rollover is already verified.

Uses the deterministic rollover engine (no Canvas I/O; fast local state).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import week_resolution as wr
from scripts.canvas_llm_rollover import rollover, schedule


def resolve_weeks() -> tuple[tuple[int, int], tuple[int, int]]:
    """Resolve (from, to) using the canonical calendar, weekends included."""
    today = wr._now_local().date()
    try:
        from_week = wr.current_week(today=today)
    except RuntimeError:
        from_week = None
    try:
        to_week = wr.next_week(today=today)
    except RuntimeError:
        to_week = None
    if to_week is None:
        raise RuntimeError("no upcoming instructional week")
    if from_week is None:
        # Weekend fallback: the week immediately before ``to_week``.
        weeks = sorted(
            (w for w in wr.load_weeks() if wr._week_start(w) is not None),
            key=lambda w: wr._week_start(w),
        )
        code = wr.week_code_for(*to_week)
        idx = next(i for i, w in enumerate(weeks) if w.get("code") == code)
        prev = weeks[idx - 1]
        from_week = (int(prev["quarter"]), int(prev["week"]))
    return from_week, to_week


def _overall(state: str) -> str:
    if state in (schedule.READY, schedule.PUBLISHED_VERIFIED, schedule.HELD_UNTIL_4PM):
        return "PASS"
    if state in (schedule.NEEDS_OWEN, schedule.PREPARING, schedule.NOT_DUE):
        return "WARN"
    return "FAIL"


def render_status() -> dict[str, Any]:
    from_week, to_week = resolve_weeks()
    s = rollover.status(*from_week, *to_week)
    overall = _overall(s["status"])
    return {"status": s, "overall": overall, "text": _text(s)}


def _text(s: dict[str, Any]) -> str:
    if s.get("status") == schedule.PUBLISHED_VERIFIED:
        schedule_label = "Completed rollover window"
    elif s.get("publication_time_required"):
        schedule_label = "Canonical window"
    else:
        schedule_label = "Scheduled"
    lines = [
        "Friday Rollover",
        f"{s['from_week']} → {s['to_week']}",
        f"{schedule_label}: {_friendly_schedule(s['scheduled_at'])}",
        f"Status: {s['status']}",
    ]
    if s.get("publication_time_required"):
        lines.append(
            "Publication time: OWNER SELECTION REQUIRED "
            f"(canonical window {_friendly_schedule(s.get('canonical_scheduled_at') or '')} has passed)"
        )
    if s["needs_owen"]:
        lines.append("Reason: owner input required")
    for b in s["blockers"]:
        lines.append(f"Blocker: {b}")
    lines.append(f"Academic courses: {len(s['academic_courses'])}")
    lines.append(f"Homeroom course: {s['homeroom_course_id']}")
    lines.append(f"Weekly updates: {s['weekly_announcement_count']}")
    lines.append(f"Summary: {_overall(s['status'])}")
    return "\n".join(lines)


def _friendly_schedule(scheduled_at: str) -> str:
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
        return dt.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).strftime(
            "%A, %B %-d at %-I:%M %p")
    except (ValueError, KeyError):
        return scheduled_at


def command_self_test() -> int:
    s = render_status()
    assert s["overall"] in ("PASS", "WARN", "FAIL")
    assert "Friday Rollover" in s["text"]
    print("PASS canvas-rollover status self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    s = render_status()
    print(s["text"])
    if "--json" in (argv or []):
        print(json.dumps(s["status"], indent=2, ensure_ascii=False))
    return 0 if s["overall"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
