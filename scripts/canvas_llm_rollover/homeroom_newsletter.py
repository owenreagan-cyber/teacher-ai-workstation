"""Deterministic monthly Homeroom newsletter update (pure; no Canvas I/O).

The rolling Homeroom newsletter is an approved, Canvas-safe HTML document. A
monthly update must preserve the existing theme/layout and evergreen content,
remove expired event tiles/sections, and never invent student birthdays.

This module performs a small, auditable set of exact-string / top-level-section
operations on an existing source HTML body:

* replace the week badge and welcome paragraph;
* rebuild the Important Dates tile grid from an explicit, source-backed list;
* remove expired named sections;
* apply exact text replacements (e.g. a corrected weekday);
* optionally insert a birthdays section (only when an authorized source exists).

Birthday data is never accepted from a caller without an explicit owner
override; the canonical ``noBirthdays`` privacy setting is the default.
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path
from typing import Any

from . import birthdays as bday

_DIV_RE = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
BIRTHDAY_SHOUTOUT_START = "<!-- BIRTHDAY_SHOUTOUT_START -->"
BIRTHDAY_SHOUTOUT_END = "<!-- BIRTHDAY_SHOUTOUT_END -->"
BIRTHDAY_SECTION_START = "<!-- BIRTHDAY_SECTION_START -->"
BIRTHDAY_SECTION_END = "<!-- BIRTHDAY_SECTION_END -->"


def _element_bounds(html: str, marker: str) -> tuple[int, int] | None:
    """Return the (start, end) of the top-level <div> containing ``marker``."""
    idx = html.find(marker)
    if idx == -1:
        return None
    start = html.rfind("<div", 0, idx)
    if start == -1:
        return None
    depth = 0
    for match in _DIV_RE.finditer(html[start:]):
        if match.group(1):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return start, start + match.end()
    return None


def replace_section(html: str, marker: str, replacement: str) -> str:
    bounds = _element_bounds(html, marker)
    if bounds is None:
        raise ValueError(f"section marker not found: {marker!r}")
    return html[: bounds[0]] + replacement + html[bounds[1]:]


def remove_section(
    html: str, marker: str, *, consume_trailing_line: bool = True,
    ignore_missing: bool = False,
) -> str:
    bounds = _element_bounds(html, marker)
    if bounds is None:
        if ignore_missing:
            return html
        raise ValueError(f"section marker not found: {marker!r}")
    end = bounds[1]
    if consume_trailing_line:
        line_end = html.find("\n", end)
        if line_end != -1:
            end = line_end
    return html[: bounds[0]] + html[end:]


def _tile(item: dict[str, Any]) -> str:
    highlight = bool(item.get("highlight"))
    if highlight:
        tile_style = "flex: 1 1 180px; background: #FBEFEF; border-radius: 12px; padding: 14px; border: 2px solid #8F3D46;"
        label_style = "font-size: 13px; color: #8F3D46; "
        event_style = "font-size: 16px; color: #24324A; "
    else:
        tile_style = "flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #F3E3BC;"
        label_style = "font-size: 13px; color: #8F3D46;"
        event_style = "font-size: 16px; color: #24324A;"
    time_html = (
        f'<div style="font-size: 13px; color: #5A4A3A;">{item["time"]}</div>'
        if item.get("time") else ""
    )
    date_label = item.get("date_label", "")
    if highlight:
        date_label = f"📌 {date_label}"
    return (
        f'<div style="{tile_style}">'
        f'<div style="{label_style}">{date_label}</div>'
        f'<div style="{event_style}">{item["event"]}</div>'
        f"{time_html}</div>"
    )


def build_important_dates_section(dates: list[dict[str, Any]]) -> str:
    tiles = "".join(_tile(item) for item in dates)
    return (
        '<div style="background: #FDF6E7; border: 1px solid #F3E3BC; border-radius: 16px; '
        'padding: 22px; margin-bottom: 22px;"><h2 style="margin: 0 0 16px; color: #8a6a1f; '
        'font-size: 23px;">📅 Important Dates</h2>'
        '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        f"{tiles}</div></div>"
    )


def build_birthday_section(month_label: str, entries: list[dict[str, str]]) -> str:
    """Build a birthdays section ONLY when an authorized entry list is supplied."""
    if not entries:
        raise ValueError("refusing to build an empty/fabricated birthday section")
    cards = "".join(
        '<div style="flex: 1 1 30%; min-width: 220px; background-color: #FBEFEF; '
        'border: 1px solid #E5B9BC; border-radius: 18px; padding: 24px; text-align: center;">'
        f'<div style="font-size: 32px; margin-bottom: 8px;">🎂</div>'
        f'<div style="font-size: 22px; color: #8F3D46;">{bday.escape_name(entry["name"])}</div>'
        f'<div style="font-size: 18px; color: #333333; margin-top: 6px;">{_html.escape(entry["date"])}</div></div>'
        for entry in entries
    )
    return (
        '<div style="margin-bottom: 22px;">'
        f'<h2 style="margin: 0 0 16px; color: #a21caf; font-size: 23px;">🍂 {_html.escape(month_label)} Birthdays 🎉</h2>'
        f'<div style="display: flex; gap: 18px; flex-wrap: wrap;">{cards}</div></div>'
    )


def build_monthly_birthday_section(
    month_groups: list[tuple[int, list[bday.Birthday]]],
) -> str:
    """Monthly birthday list for the month(s) covered by the weekly page."""
    cards: list[str] = []
    for month, entries in month_groups:
        for birthday in entries:
            cards.append(
                '<div style="flex: 1 1 30%; min-width: 220px; background-color: #FBEFEF; '
                'border: 1px solid #E5B9BC; border-radius: 18px; padding: 24px; text-align: center;">'
                '<div style="font-size: 32px; margin-bottom: 8px;">🎂</div>'
                f'<div style="font-size: 22px; color: #8F3D46;">{bday.escape_name(birthday.name)}</div>'
                f'<div style="font-size: 18px; color: #333333; margin-top: 6px;">'
                f'{bday.month_label(month)} {birthday.day}</div></div>'
            )
    if not cards:
        empty = "<p><em>No birthdays this month.</em></p>"
        heading = "🍂 Birthdays 🎉"
    else:
        empty = ""
        months = ", ".join(bday.month_label(month) for month, _ in month_groups)
        heading = f"🍂 {months} Birthdays 🎉"
    return (
        f"{BIRTHDAY_SECTION_START}\n"
        '<div style="margin-bottom: 22px;">'
        f'<h2 style="margin: 0 0 16px; color: #a21caf; font-size: 23px;">{heading}</h2>'
        f'<div style="display: flex; gap: 18px; flex-wrap: wrap;">{"".join(cards)}</div>{empty}</div>\n'
        f"{BIRTHDAY_SECTION_END}"
    )


def build_birthday_shoutout(text: str) -> str:
    if not text:
        return ""
    return (
        f"{BIRTHDAY_SHOUTOUT_START}\n"
        '<div style="background-color: #FDF6E7; border-left: 4px solid #E4A94F; '
        'padding: 14px 18px; margin: 0 0 22px; border-radius: 10px;">'
        f'<p style="margin: 0; font-size: 17px;"><strong>🎂 {_html.escape(text)}</strong></p></div>\n'
        f"{BIRTHDAY_SHOUTOUT_END}"
    )


def _upsert_marked_block(
    html: str,
    *,
    start_marker: str,
    end_marker: str,
    content: str,
    anchor_marker: str,
    after: bool,
) -> str:
    """Replace a marked block in place, or insert it at the anchor.

    Idempotent: regenerating a newsletter never appends a duplicate birthday
    section or shoutout.
    """
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL
    )
    if pattern.search(html):
        return pattern.sub(content, html, count=1)
    if not content:
        return html
    bounds = _element_bounds(html, anchor_marker)
    if bounds is None:
        raise ValueError(f"anchor marker not found: {anchor_marker!r}")
    insert_at = bounds[1] if after else bounds[0]
    prefix = "\n\n  " if after else "  "
    suffix = "" if after else "\n\n  "
    return html[:insert_at] + prefix + content + suffix + html[insert_at:]


def build_monthly_update(
    source_html: str,
    *,
    week_badge: str,
    intro_paragraph: str,
    important_dates: list[dict[str, Any]],
    remove_markers: list[str] | None = None,
    replacements: dict[str, str] | None = None,
    birthday_section: str | None = None,
    birthday_shoutout: str | None = None,
) -> str:
    """Apply the monthly update to an existing newsletter body."""
    html = source_html

    # Week badge: "Track 2, Week 3 · October 26–30, 2026" -> upcoming week.
    html, badge_count = re.subn(
        r"Track\s*2,\s*Week\s*\d+\s*·\s*[^<]+",
        week_badge,
        html,
        count=1,
    )
    if badge_count != 1:
        raise ValueError("week badge marker not found exactly once")

    # Welcome paragraph: exact canonical sentence, replaced only once.
    intro_pattern = re.compile(
        r'<p style="font-size: 16px; margin: 10px 0 0;">We are looking forward.*?</p>',
        re.DOTALL,
    )
    html, intro_count = intro_pattern.subn(
        f'<p style="font-size: 16px; margin: 10px 0 0;">{intro_paragraph}</p>',
        html,
        count=1,
    )
    if intro_count != 1:
        raise ValueError("welcome paragraph marker not found exactly once")

    html = replace_section(html, "📅 Important Dates", build_important_dates_section(important_dates))

    for marker in remove_markers or []:
        html = remove_section(html, marker, ignore_missing=True)

    for old, new in (replacements or {}).items():
        if old in html:
            html = html.replace(old, new, 1)
        elif new in html:
            continue
        else:
            raise ValueError(f"replacement source text not found: {old!r}")

    # Birthday shoutout (weekly window) and monthly birthday list. Both are
    # marker-upserted so regeneration can never duplicate them.
    html = _upsert_marked_block(
        html,
        start_marker=BIRTHDAY_SHOUTOUT_START,
        end_marker=BIRTHDAY_SHOUTOUT_END,
        content=birthday_shoutout or "",
        anchor_marker="📅 Important Dates",
        after=False,
    )
    html = _upsert_marked_block(
        html,
        start_marker=BIRTHDAY_SECTION_START,
        end_marker=BIRTHDAY_SECTION_END,
        content=birthday_section or "",
        anchor_marker="📅 Important Dates",
        after=True,
    )

    return html


def stale_markers_present(html: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker in html]


NOVEMBER_PLAN_PATH = (
    Path(__file__).resolve().parents[2]
    / "config" / "curriculum" / "canvas" / "homeroom-newsletter-november-2026-plan.json"
)


def load_plan(path=None) -> dict[str, Any]:
    import json

    p = Path(path) if path is not None else NOVEMBER_PLAN_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def build_from_plan(
    source_html: str,
    plan: dict[str, Any],
    *,
    roster: list[bday.Birthday] | None = None,
    week_start=None,
    week_end=None,
) -> str:
    """Render a weekly Homeroom newsletter from the committed planning record.

    Birthday values come only from the owner-authorized private roster. Tests
    inject a synthetic roster; production loads the private `.local/` roster.
    """
    from datetime import date

    birthday_shoutout = ""
    birthday_section = ""
    birthday_meta = plan.get("monthlyBirthdays") or {}
    authorized = birthday_meta.get("status") in ("OWNER_APPROVED", "OWNER_APPROVED_PRIVATE_ROSTER")
    if authorized:
        if roster is None:
            roster = bday.load_roster()
        start = week_start or date.fromisoformat(plan["week"]["startDate"])
        end = week_end or date.fromisoformat(plan["week"]["endDate"])
        month_groups = bday.monthly_birthdays(start, end, roster=roster)
        birthday_section = build_monthly_birthday_section(month_groups)
        shoutout_text = bday.weekly_shoutout(start, end, roster=roster)
        birthday_shoutout = build_birthday_shoutout(shoutout_text)
    return build_monthly_update(
        source_html,
        week_badge=plan["week"]["badge"],
        intro_paragraph=plan["week"]["intro"],
        important_dates=plan["importantDates"],
        remove_markers=plan.get("removeSections") or [],
        replacements=plan.get("replacements") or {},
        birthday_section=birthday_section or None,
        birthday_shoutout=birthday_shoutout or None,
    )


def command_self_test() -> int:
    source = (
        '<div style="max-width: 900px;">\n'
        '  <div><span>Track 2, Week 3 · October 26–30, 2026</span></div>\n\n'
        '  <div><p style="font-size: 16px; margin: 10px 0 0;">We are looking forward to a great week.</p></div>\n\n'
        '  <div style="background: #FDF6E7;"><h2>📅 Important Dates</h2>'
        '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        '<div style="flex: 1 1 180px;"><div>📚 FRIDAY, OCTOBER 30</div><div>Book Character Day</div></div>'
        "</div></div>\n\n"
        '  <div style="background: #FBEFEF;"><h2>📚 Book Character Day — Friday, October 30</h2>'
        "<p>Expired.</p></div></div>\n\n"
        '  <div><h2>⭐ Behavior Tracker</h2><p>Beginning Monday, October 12, we are adding a new behavior tracker.</p></div>\n'
        '  <div><h2>Family Movie Night</h2><p>Thursday, November 6</p></div>\n'
        "</div>"
    )
    out = build_monthly_update(
        source,
        week_badge="Track 2, Week 4 · November 2–6, 2026",
        intro_paragraph="We are looking forward to a great week in November.",
        important_dates=[
            {"date_label": "NOVEMBER 6", "event": "Progress Reports", "highlight": True},
            {"date_label": "NOVEMBER 11", "event": "Veterans Day Performance", "time": "9:00–10:00 AM", "highlight": True},
        ],
        remove_markers=["📚 Book Character Day"],
        replacements={
            "Beginning Monday, October 12, we are adding a new behavior tracker.":
                "Earlier this quarter, we added a new behavior tracker."
        },
    )
    assert "Week 4 · November 2–6, 2026" in out
    assert "Progress Reports" in out and "Veterans Day Performance" in out
    assert "Book Character Day" not in out
    assert "October" not in out, out
    assert "Earlier this quarter" in out
    assert out.count("📅 Important Dates") == 1

    # Empty birthdays are refused (never fabricated).
    try:
        build_birthday_section("November", [])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    section = build_birthday_section("November", [{"name": "[REDACTED]", "date": "November 4"}])
    assert "November Birthdays" in section and "November 4" in section

    # Authorized synthetic birthday list + duplicate prevention + escaping.
    plan = load_plan()
    roster = [bday.Birthday("Test & Kid", 11, 20)]
    out1 = build_from_plan(source, plan, roster=roster)
    assert "November 20" in out1
    assert "Test &amp; Kid" in out1
    assert out1.count(BIRTHDAY_SECTION_START) == 1
    out2 = build_from_plan(out1, plan, roster=roster)
    assert out2.count(BIRTHDAY_SECTION_START) == 1
    assert out2.count("November 20") == 1
    # No weekly shoutout for Nov 2-6 when the birthday is later in the month.
    assert BIRTHDAY_SHOUTOUT_START not in out1

    # A birthday inside the week produces one deterministic shoutout block.
    roster_week = [bday.Birthday("Test Kid", 11, 4)]
    out_week = build_from_plan(source, plan, roster=roster_week)
    assert out_week.count(BIRTHDAY_SHOUTOUT_START) == 1
    assert "Happy birthday to Test Kid on November 4!" in out_week
    out_week2 = build_from_plan(out_week, plan, roster=roster_week)
    assert out_week2.count(BIRTHDAY_SHOUTOUT_START) == 1

    print("PASS homeroom monthly-newsletter self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
