"""The one parser for the instructional-weeks config.

``config/curriculum/canvas/instructional-weeks-2026-2027.json`` gives each week's
dates only as text, in its ``pageTitle`` ("Q2W7 - November 30–December 4, 2026")
and ``displaySubtitle`` ("Quarter 2, Week 7 | November 30–December 4, 2026").
Every reader of that file (phase 22, the intake week resolver, the phase-3
pacing extractor, and grade-check quarters and school days) turns that text
into dates here, so they all agree.

Handles:

- same-month ranges: "July 20-24, 2026"
- cross-month ranges: "August 31–September 4, 2026"
- cross-year ranges: "December 28 – January 1, 2027" (the year belongs to the
  end date; the start falls in the year before)
- en dash, em dash, or hyphen, with or without spaces
- full or abbreviated month names, with or without a period ("Nov 30 – Dec 4")
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WEEKS_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "instructional-weeks-2026-2027.json"

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
_MONTHS.update({name[:3]: n for name, n in list(_MONTHS.items())})
_MONTHS["sept"] = 9

_RANGE_RE = re.compile(
    r"(?P<sm>[A-Za-z]{3,9})\.?\s+(?P<sd>\d{1,2})\s*[-–—]\s*"
    r"(?:(?P<em>[A-Za-z]{3,9})\.?\s+)?(?P<ed>\d{1,2}),?\s*(?P<yr>\d{4})"
)


def _month(name: str | None) -> int | None:
    return _MONTHS.get((name or "").lower())


def parse_week_range(text: str | None) -> tuple[dt.date, dt.date] | None:
    """Return (first day, last day) of the range in ``text``, or None."""
    clean = " ".join(str(text or "").replace("&nbsp;", " ").replace("\xa0", " ").split())
    for match in _RANGE_RE.finditer(clean):
        start_month = _month(match.group("sm"))
        if start_month is None:
            continue
        end_month = _month(match.group("em")) if match.group("em") else start_month
        if end_month is None:
            continue
        end_year = int(match.group("yr"))
        start_year = end_year - 1 if start_month > end_month else end_year
        try:
            start = dt.date(start_year, start_month, int(match.group("sd")))
            end = dt.date(end_year, end_month, int(match.group("ed")))
        except ValueError:
            continue
        if start <= end:
            return start, end
    return None


def week_range(week: dict[str, Any]) -> tuple[dt.date, dt.date] | None:
    """Dates for one config week: ``displaySubtitle`` first, then ``pageTitle``."""
    return parse_week_range(week.get("displaySubtitle")) or parse_week_range(week.get("pageTitle"))


def load_weeks(path: Path | None = None) -> list[dict[str, Any]]:
    """The config's weeks, each with ISO ``startsOn``/``endsOn`` (None if unparsable)."""
    raw = json.loads((path or WEEKS_PATH).read_text(encoding="utf-8"))
    weeks = []
    for week in raw.get("weeks", []):
        bounds = week_range(week)
        weeks.append({
            **week,
            "startsOn": bounds[0].isoformat() if bounds else None,
            "endsOn": bounds[1].isoformat() if bounds else None,
        })
    return weeks
