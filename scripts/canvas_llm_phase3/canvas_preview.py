"""Part H — Canvas dry-run preview (no Canvas mutation).

After teacher approval, generate a dry-run Canvas package using canonical config
and Phase 2A live precedent. Renders agenda HTML with the canonical "At Home"
right-column rule and the kl_wrapper_3 shell. Produces local preview artifacts
only; zero Canvas writes by construction.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from . import pacing_extractor as pe

H3_BORDER = (
    "border-width: 0px !important; border-style: none !important; "
    "border-color: currentcolor !important;"
)
DAY_H3 = (
    "color: #ffffff; background-color: #0065a7; margin-top: 15px; margin-bottom: 2px; "
    + H3_BORDER
)
H4 = (
    "color: #ffffff; background-color: #333333; padding-left: 10px; margin: 0px; " + H3_BORDER
)
REM_H3 = "background-color: #c51062; color: #ffffff; " + H3_BORDER

DAY_BLOCK_IDS = [
    "kl_activities2",
    "kl_custom_block_4",
    "kl_custom_block_3",
    "kl_custom_block_2",
    "kl_custom_block_1",
]


def _items(lines: list[str]) -> str:
    return "".join(f"<li>{line}</li>" for line in lines)


def _day(block_id: str, day_label: str, in_class: list[str], at_home: list[str] | None) -> str:
    in_html = f"<ul>{_items(in_class)}</ul>"
    if at_home is None or not at_home:
        # No supported At Home content: single 100% In Class column, no empty At Home.
        return (
            f'<div id="{block_id}" class="">\n'
            f'<h3 style="{DAY_H3}">{day_label}</h3>\n'
            f'<div style="display: flex; width: 100%;">'
            f'<div style="width: 100%; padding-left: 15px;">'
            f'<h4 class="kl_solid_border" style="{H4}">In Class</h4>{in_html}</div></div>\n'
            f"</div>"
        )
    return (
        f'<div id="{block_id}" class="">\n'
        f'<h3 style="{DAY_H3}">{day_label}</h3>\n'
        f'<div style="display: flex; width: 100%;">'
        f'<div style="width: 49%; padding-left: 15px;">'
        f'<h4 class="kl_solid_border" style="{H4}">In Class</h4>{in_html}</div>'
        f'<div style="width: 49%; padding-left: 15px;">'
        f'<h4 class="kl_solid_border" style="{H4}">At Home</h4><ul>{_items(at_home)}</ul></div>'
        f"</div>\n</div>"
    )


def _banner(week_code: str, start: datetime, end: datetime) -> str:
    quarter = int(week_code[1])
    week = int(week_code[3:])
    if start.strftime("%B") == end.strftime("%B"):
        rng = f"{start.strftime('%B %-d')}\u2013{end.strftime('%-d')}, {start.year}"
    else:
        rng = f"{start.strftime('%B %-d')}\u2013{end.strftime('%B %-d')}, {end.year}"
    subtitle = f"Quarter {quarter}, Week {week} | {rng}"
    return (
        '<p style="color: #ffffff; background-color: #0065a7; text-align: center; margin: 0;">'
        '<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
        f'<span style="font-size: 10pt;">{subtitle}</span></p>'
    )


def build_agenda_html(
    week_code: str,
    days: dict[str, dict[str, Any]],
    reminders: list[str] | None = None,
) -> str:
    """Render a canonical agenda page for one subject's week.

    ``days`` maps weekday -> {"in_class": [lines], "at_home": [lines] | None}.
    """
    bounds = pe.week_bounds(week_code)
    banner = _banner(week_code, bounds[0], bounds[1]) if bounds else ""
    rem_html = "".join(f"<p>{r}</p>" for r in (reminders or []))
    day_html = ""
    for block_id, wd in zip(DAY_BLOCK_IDS, C.WEEKDAYS):
        spec = days.get(wd, {"in_class": [], "at_home": None})
        day_html += _day(block_id, wd, spec.get("in_class", []), spec.get("at_home"))
    return (
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{banner}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n'
        f'<div style="width: 100%; padding-left: 15px;">{rem_html}</div>\n'
        f"{day_html}\n</div>\n</div>"
    )


def build_dry_run_package(week: dict[str, Any], subject_days: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Assemble a dry-run preview bundle and write it under .local/phase3-preview/.

    Returns a summary. Zero Canvas writes by construction: only local files.
    """
    C.PHASE3_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    week_code = week["week"]["code"]
    pages: dict[str, Any] = {}
    for subject, days in subject_days.items():
        html = build_agenda_html(week_code, days)
        out = C.PHASE3_PREVIEW_DIR / f"{week_code}-{subject}-page.html"
        out.write_text(html, encoding="utf-8")
        pages[subject] = {"file": str(out), "body_chars": len(html)}

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "week_code": week_code,
        "mode": "dry-run-preview",
        "canvas_writes": 0,
        "canvas_post": 0,
        "canvas_put": 0,
        "canvas_patch": 0,
        "canvas_delete": 0,
        "pages": pages,
    }
    (C.PHASE3_PREVIEW_DIR / f"{week_code}-preview-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def build_combined_reading_spelling_html(
    week_code: str,
    reading_days: dict[str, dict[str, Any]],
    spelling_days: dict[str, dict[str, Any]],
    reminders: list[str] | None = None,
) -> str:
    """Render ONE combined Reading + Spelling weekly agenda page.

    Reading and Spelling share Canvas course 26442 and therefore one weekly
    page. Each day renders a distinct Reading section and Spelling section,
    with At Home shown only where supported. Uses the canonical kl_wrapper_3
    shell and color tokens.
    """
    bounds = pe.week_bounds(week_code)
    banner = _banner(week_code, bounds[0], bounds[1]) if bounds else ""
    rem_html = "".join(f"<p>{r}</p>" for r in (reminders or []))

    day_html = ""
    for block_id, wd in zip(DAY_BLOCK_IDS, C.WEEKDAYS):
        rspec = reading_days.get(wd, {"in_class": [], "at_home": None})
        sspec = spelling_days.get(wd, {"in_class": [], "at_home": None})
        r_in = rspec.get("in_class") or []
        s_in = sspec.get("in_class") or []
        r_at_home = rspec.get("at_home")
        s_at_home = sspec.get("at_home")
        at_home = list(r_at_home or []) + list(s_at_home or [])

        reading_html = f'<h4 class="kl_solid_border" style="{H4}">Reading</h4><ul>{_items(r_in)}</ul>' if r_in else ""
        spelling_html = f'<h4 class="kl_solid_border" style="{H4}">Spelling</h4><ul>{_items(s_in)}</ul>' if s_in else ""

        if at_home:
            # Two-column: combined In Class + At Home.
            in_html = f"{reading_html}{spelling_html}"
            day_html += (
                f'<div id="{block_id}" class="">\n'
                f'<h3 style="{DAY_H3}">{wd}</h3>\n'
                f'<div style="display: flex; width: 100%;">'
                f'<div style="width: 49%; padding-left: 15px;">{in_html}</div>'
                f'<div style="width: 49%; padding-left: 15px;">'
                f'<h4 class="kl_solid_border" style="{H4}">At Home</h4><ul>{_items(at_home)}</ul></div>'
                f"</div>\n</div>"
            )
        else:
            day_html += (
                f'<div id="{block_id}" class="">\n'
                f'<h3 style="{DAY_H3}">{wd}</h3>\n'
                f'<div style="display: flex; width: 100%;">'
                f'<div style="width: 100%; padding-left: 15px;">{reading_html}{spelling_html}</div>'
                f"</div>\n</div>"
            )

    return (
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{banner}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n'
        f'<div style="width: 100%; padding-left: 15px;">{rem_html}</div>\n'
        f"{day_html}\n</div>\n</div>"
    )


def command_self_test() -> int:
    days = {
        "Monday": {"in_class": ["Lesson 31", "Problems 1-10"], "at_home": ["Lesson 31: Problems 12-30 Evens"]},
        "Tuesday": {"in_class": ["Lesson 32"], "at_home": None},
        "Wednesday": {"in_class": ["Lesson 33"], "at_home": ["Lesson 33: Problems 11-29 Odds"]},
        "Thursday": {"in_class": ["Written Assessment 6"], "at_home": None},
        "Friday": {"in_class": ["Investigation 3"], "at_home": None},
    }
    html = build_agenda_html("Q2W1", days)
    assert 'id="kl_wrapper_3"' in html
    assert "kl_circle_left kl_wrapper" in html
    assert "#0065a7" in html and "#c51062" in html and "#333333" in html
    assert "Weekly Agenda" in html
    assert ">Reminders</h3>" in html
    assert ">At Home</h4>" in html
    assert ">In Class</h4>" in html
    # Monday and Wednesday use two columns.
    assert html.count('width: 49%') >= 4  # 2 per two-column day * 2 days
    # Tuesday/Thursday/Friday omit At Home (100% In Class).
    assert html.count('width: 100%') >= 3
    # Never render an empty At Home box: Tuesday's At Home must be absent.
    assert ">Homework</h4>" not in html

    print("PASS canvas dry-run preview self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
