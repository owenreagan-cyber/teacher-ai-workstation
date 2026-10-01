"""time.now: local time, date, weekday, and days until a date."""
from __future__ import annotations

from datetime import date

from cos.registry import Tool

KEYWORDS = ("time", "date", "day", "today", "tomorrow", "week", "weekday", "until",
            "clock", "month", "year", "days", "how long")


def fmt_time(dt) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def now_info(ctx, args: dict) -> dict:
    now = ctx.clock()
    info = {
        "date": now.date().isoformat(),
        "weekday": now.strftime("%A"),
        "time": fmt_time(now),
        "timezone": now.tzname() or "local",
        "display": now.strftime("%A, %B ") + str(now.day) + now.strftime(", %Y"),
    }
    target = args.get("days_until")
    if target:
        try:
            when = date.fromisoformat(target)
        except ValueError:
            return {**info, "error": "days_until must be a date like 2026-12-18"}
        delta = (when - now.date()).days
        info["days_until"] = {"date": target, "days": delta,
                              "weekday": when.strftime("%A"),
                              "school_days": school_days_between(now.date(), when)}
    return info


def school_days_between(start: date, end: date) -> int:
    """Weekdays after start up to and including end (holidays not known in M1)."""
    if end <= start:
        return 0
    days, step = 0, start.toordinal() + 1
    for ordinal in range(step, end.toordinal() + 1):
        if date.fromordinal(ordinal).weekday() < 5:
            days += 1
    return days


def tools(ctx):
    return [Tool(
        name="time.now",
        description=("Current local date, time, and weekday. Optionally days and weekdays "
                     "(Mon–Fri, holidays not counted) until a date given as YYYY-MM-DD."),
        parameters={"type": "object", "properties": {
            "days_until": {"type": "string", "description": "Target date, YYYY-MM-DD", "maxLength": 10},
        }, "additionalProperties": False},
        side_effect="none", data_class="P2", timeout_s=2,
        func=lambda args: now_info(ctx, args), keywords=KEYWORDS,
    )]
