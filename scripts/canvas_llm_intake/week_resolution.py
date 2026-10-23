"""Week resolution helpers for the intake workspace.

Resolves current/next quarter+week from the canonical instructional-weeks
export using America/New_York, with explicit ``--quarter N --week N`` override
for deterministic testing.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any
from zoneinfo import ZoneInfo

from scripts.canvas_llm_phase3 import constants as P3

_TZ = ZoneInfo("America/New_York")


def _now_local() -> dt.datetime:
    now = dt.datetime.now(_TZ)
    # TAW_TODAY=YYYY-MM-DD pins the date (time of day stays real) for tests
    # only; unset in real use.
    pinned = os.environ.get("TAW_TODAY")
    if pinned:
        d = dt.date.fromisoformat(pinned)
        return now.replace(year=d.year, month=d.month, day=d.day)
    return now


def load_weeks() -> list[dict[str, Any]]:
    return json.loads(P3.WEEKS_PATH.read_text(encoding="utf-8")).get("weeks", [])


def _week_bounds(week: dict[str, Any]) -> tuple[dt.date, dt.date] | None:
    from scripts.instructional_weeks import week_range

    return week_range(week)


def _week_start(week: dict[str, Any]) -> dt.date | None:
    bounds = _week_bounds(week)
    return bounds[0] if bounds else None


def week_code_for(quarter: int, week: int) -> str:
    return f"Q{quarter}W{week}"


def find_week(quarter: int, week: int) -> dict[str, Any] | None:
    code = week_code_for(quarter, week)
    for w in load_weeks():
        if w.get("code") == code:
            return w
    return None


def current_week(today: dt.date | None = None) -> tuple[int, int]:
    """Return (quarter, week) for the week containing today (Monday-Friday)."""
    today = today or _now_local().date()
    best: dict[str, Any] | None = None
    for w in load_weeks():
        bounds = _week_bounds(w)
        if bounds is None:
            continue
        start, end = bounds
        if start <= today <= end:
            best = w
            break
    if best is None:
        raise RuntimeError(f"no instructional week contains {today}")
    return int(best["quarter"]), int(best["week"])


def next_week(today: dt.date | None = None) -> tuple[int, int]:
    """Return (quarter, week) for the first instructional week after today."""
    today = today or _now_local().date()
    ordered = sorted(
        (w for w in load_weeks() if _week_start(w) is not None),
        key=lambda w: _week_start(w),  # type: ignore[arg-type]
    )
    for w in ordered:
        start = _week_start(w)
        if start is not None and start > today:
            return int(w["quarter"]), int(w["week"])
    raise RuntimeError(f"no instructional week after {today}")


def resolve(
    mode: str,
    *,
    quarter: int | None = None,
    week: int | None = None,
    today: dt.date | None = None,
) -> tuple[int, int]:
    """Resolve the target (quarter, week).

    ``mode`` is one of ``current`` / ``next``, or ``explicit`` when
    ``--quarter``/``--week`` are provided.
    """
    if quarter is not None and week is not None:
        return quarter, week
    if mode == "current":
        return current_week(today=today)
    if mode == "next":
        return next_week(today=today)
    raise ValueError(f"unknown resolution mode {mode!r}")


def command_self_test() -> int:
    # Explicit override wins.
    assert resolve("current", quarter=2, week=2) == (2, 2)
    # Deterministic date-based resolution (fixed "today").
    assert current_week(today=dt.date(2026, 10, 12)) == (2, 1)  # Monday of Q2W1
    assert current_week(today=dt.date(2026, 10, 16)) == (2, 1)  # Friday of Q2W1
    assert next_week(today=dt.date(2026, 10, 16)) == (2, 2)  # -> Q2W2
    assert week_code_for(2, 2) == "Q2W2"
    assert find_week(2, 2) is not None and find_week(2, 2)["code"] == "Q2W2"
    print("PASS intake week-resolution self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
