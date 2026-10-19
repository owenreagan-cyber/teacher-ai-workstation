"""Homeroom newsletter copy-forward (pure, deterministic, no Canvas I/O).

At the Friday 4 PM rollover, the already-existing upcoming-week Homeroom page
receives the *current* approved newsletter content, adjusted only for
week/date identity and expired events. This module implements the deterministic
content transform:

- preserve still-future important dates, Behavior Tracker, Carpool, Family
  Quick Links, Contact Guidance, class motto, and other evergreen sections;
- remove expired event dates;
- update week/date identity to the upcoming week;
- never invent new content and never resurrect expired events.

The approved content source is
``config/curriculum/canvas/homeroom-newsletter-content-2026-2027.json``
(OWNER_APPROVED). ISO dates reuse ``newsletter_guard.prune_expired_dates``;
human-friendly dates ("Tuesday, October 20", "November 6") are parsed here.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.canvas_llm_weekly_guardrails import prune_expired_dates

REPO_ROOT = Path(__file__).resolve().parents[2]
HOMEROOM_CONTENT_PATH = (
    REPO_ROOT / "config" / "curriculum" / "canvas"
    / "homeroom-newsletter-content-2026-2027.json"
)

# Sections that must survive copy-forward verbatim (evergreen).
EVERGREEN_SECTIONS = (
    "behaviorTracker",
    "waterBottlesAndDrinks",
    "scienceAndHistoryNotes",
    "classMotto",
    "carpool",
    "familyQuickLinks",
    "contactGuidance",
    "progressReportsAndReportCards",
)

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
_WEEKDAY_RE = re.compile(
    r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday),?\s*",
    re.IGNORECASE,
)


def _parse_month_day(s: str, today: date) -> date | None:
    """Parse a human date like 'October 20' or 'Picture Retakes — Tuesday, October 20'."""
    s = _WEEKDAY_RE.sub("", (s or "").strip())
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2})", s)
    if not m:
        return None
    month = _MONTHS.get(m.group(1).lower())
    if month is None:
        return None
    day = int(m.group(2))
    year = today.year
    d = date(year, month, day)
    # If more than ~6 months in the past, the date belongs to next year.
    if d < today - timedelta(days=180):
        d = date(year + 1, month, day)
    return d


def _as_date(value: Any, today: date) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, dict):
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        pass
    return _parse_month_day(s, today)


def load_approved_content() -> dict[str, Any]:
    return json.loads(HOMEROOM_CONTENT_PATH.read_text(encoding="utf-8"))


def _sections(content: dict[str, Any]) -> dict[str, Any]:
    return content.get("sections", content)


def _prune_important_dates(
    dates: list[dict[str, Any]], today: date
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split ``importantDates`` into kept / removed / ambiguous.

    A date strictly before ``today`` is removed. ISO dates go through the shared
    ``prune_expired_dates`` helper; human-friendly dates are parsed here.
    """
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    for item in dates:
        if not isinstance(item, dict):
            ambiguous.append(item)
            kept.append(item)
            continue
        value = str(item.get("date") or "").strip()
        if not value:
            ambiguous.append(item)
            kept.append(item)
            continue
        try:
            date.fromisoformat(value)
            is_iso = True
        except ValueError:
            is_iso = False
        if is_iso:
            k, r, a = prune_expired_dates([item], today.isoformat())
            kept.extend(k)
            removed.extend(r)
            ambiguous.extend(a)
            continue
        d = _as_date(value, today)
        if d is None:
            ambiguous.append(item)
            kept.append(item)
        elif d < today:
            removed.append(item)
        else:
            kept.append(item)
    return kept, removed, ambiguous


def copy_forward(
    current_content: dict[str, Any],
    *,
    today: date,
    to_date_range: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return the proposed upcoming-week newsletter content."""
    sections = dict(_sections(current_content))
    out: dict[str, Any] = dict(sections)

    # 1. Important Dates: prune expired, preserve future + ambiguous.
    important = sections.get("importantDates") or {}
    dates = important.get("dates", [])
    if dates:
        kept, _removed, ambiguous = _prune_important_dates(dates, today)
        out["importantDates"] = dict(important)
        out["importantDates"]["dates"] = kept
        out["importantDates"]["pruned_at"] = today.isoformat()
        if ambiguous:
            out["importantDates"]["ambiguous_dates"] = ambiguous

    # 2. Drop fully-expired single-event sections (date already in the past).
    for key in ("pictureRetakes", "movieNight", "bookCharacterDay", "afterSchoolClubs"):
        entry = out.get(key)
        if not isinstance(entry, dict):
            continue
        d = _as_date(entry.get("date") or entry.get("title"), today)
        if d is not None and d < today:
            out.pop(key, None)

    # 3. Evergreen sections preserved verbatim (already copied above).

    # 4. Week/date identity marker (adjustable without touching section content).
    if to_date_range:
        out["_week_identity"] = dict(to_date_range)

    return out


def content_hash(content: dict[str, Any]) -> str:
    """Stable hash of the newsletter content (for the rollover manifest)."""
    norm = json.dumps(_sections(content), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def render_proposed(proposed: dict[str, Any]) -> str:
    """Deterministic serialized body for the proposed newsletter content."""
    return json.dumps(_sections(proposed), indent=2, ensure_ascii=False, sort_keys=True)


def _body_hash(body: str) -> str:
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def command_self_test() -> int:
    # Rollover occurs Friday, October 23: Picture Retakes (Tue Oct 20) is past.
    today = date(2026, 10, 23)
    content = load_approved_content()
    sections = _sections(content)
    for s in EVERGREEN_SECTIONS:
        assert s in sections, s

    proposed = copy_forward(content, today=today, to_date_range={"start": "2026-10-26", "end": "2026-10-30"})
    psec = _sections(proposed)
    # Evergreen preserved verbatim.
    assert psec["classMotto"]["motto"] == sections["classMotto"]["motto"]
    assert psec["familyQuickLinks"]["links"] == sections["familyQuickLinks"]["links"]
    assert psec["behaviorTracker"]["title"] == "Behavior Tracker"

    # Expired dates removed, future dates preserved.
    kept_dates = [d.get("date") for d in psec["importantDates"]["dates"]]
    assert "Tuesday, October 20" not in kept_dates  # picture retakes already past
    assert "October 30" in kept_dates  # future preserved
    assert "November 6" in kept_dates
    assert "December 22" in kept_dates

    # Expired single-event section dropped, future one preserved.
    assert "pictureRetakes" not in psec  # Tuesday, October 20 is before Friday Oct 23
    assert "movieNight" in psec  # November 6 is future
    assert "bookCharacterDay" in psec  # October 30 is future

    # Hash deterministic.
    assert content_hash(proposed) == content_hash(copy_forward(
        content, today=today, to_date_range={"start": "2026-10-26", "end": "2026-10-30"}))

    print("PASS canvas-rollover homeroom self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
