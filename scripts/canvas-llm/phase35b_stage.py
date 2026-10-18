#!/usr/bin/env python3
"""Phase 3.5B — Q2W1 + Homeroom deployment STAGING (build bodies locally, no writes).

Builds the exact production HTML for the 5 subject Q2W1 pages and performs the
Homeroom newsletter surgery, writing everything to a staging dir for inspection.
This script performs NO Canvas writes.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1" / "staging"
STAGE.mkdir(parents=True, exist_ok=True)

H3_BORDER = "border-width: 0px !important; border-style: none !important; border-color: currentcolor !important;"
DAY_H3 = f"color: #ffffff; background-color: #0065a7; margin-top: 15px; margin-bottom: 2px; {H3_BORDER}"
H4 = f"color: #ffffff; background-color: #333333; padding-left: 10px; margin: 0px; {H3_BORDER}"
REM_H3 = f"background-color: #c51062; color: #ffffff; {H3_BORDER}"
DAY_BLOCK_IDS = ["kl_activities2", "kl_custom_block_4", "kl_custom_block_3", "kl_custom_block_2", "kl_custom_block_1"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def esc(s: str) -> str:
    import html
    return html.escape(s)


def _items(lines: list[str]) -> str:
    return "".join(f"<li>{esc(l)}</li>" for l in lines)


def _banner(subtitle: str) -> str:
    return (
        '<p style="color: #ffffff; background-color: #0065a7; text-align: center; margin: 0;">'
        '<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
        f'<span style="font-size: 10pt;">{esc(subtitle)}</span></p>'
    )


def build_agenda(subtitle: str, reminders: list[str], days: dict[str, dict[str, Any]]) -> str:
    rem = "".join(f"<p>{esc(r)}</p>" for r in reminders)
    day_html = ""
    for block_id, wd in zip(DAY_BLOCK_IDS, WEEKDAYS):
        spec = days[wd]
        in_class = spec["in_class"]
        at_home = spec.get("at_home")
        if at_home:
            day_html += (
                f'<div id="{block_id}" class="">\n<h3 style="{DAY_H3}">{wd}</h3>\n'
                f'<div style="display: flex; width: 100%;">'
                f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="{H4}">In Class</h4><ul>{_items(in_class)}</ul></div>'
                f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="{H4}">At Home</h4><ul>{_items(at_home)}</ul></div>'
                f"</div>\n</div>"
            )
        else:
            day_html += (
                f'<div id="{block_id}" class="">\n<h3 style="{DAY_H3}">{wd}</h3>\n'
                f'<div style="display: flex; width: 100%;">'
                f'<div style="width: 100%; padding-left: 15px;"><h4 class="kl_solid_border" style="{H4}">In Class</h4><ul>{_items(in_class)}</ul></div>'
                f"</div>\n</div>"
            )
    return (
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{_banner(subtitle)}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n<div style="width: 100%; padding-left: 15px;">{rem}</div>\n'
        f"{day_html}\n</div>\n</div>"
    )


def build_flat_list(subtitle: str, reminders: list[str], days: dict[str, list[str]]) -> str:
    rem = "".join(f"<p>{esc(r)}</p>" for r in reminders)
    day_html = ""
    for block_id, wd in zip(DAY_BLOCK_IDS, WEEKDAYS):
        lines = days[wd]
        day_html += (
            f'<div id="{block_id}" class="">\n<h3 style="{DAY_H3}">{wd}</h3>\n'
            f'<div style="display: flex; width: 100%;">'
            f'<div style="width: 100%; padding-left: 15px;"><h4 class="kl_solid_border" style="{H4}">In Class</h4><ul>{_items(lines)}</ul></div>'
            f"</div>\n</div>"
        )
    return (
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{_banner(subtitle)}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n<div style="width: 100%; padding-left: 15px;">{rem}</div>\n'
        f"{day_html}\n</div>\n</div>"
    )


SUBTITLE = "Quarter 2, Week 1 | October 12\u201316, 2026"


def main() -> int:
    # --- MATH ---
    math_days = {
        "Monday": {"in_class": ["Lesson 31", "Problems 1-10"], "at_home": ["Lesson 31: Problems 12-30 Evens"]},
        "Tuesday": {"in_class": ["Lesson 32", "Problems 1-10"], "at_home": ["If you do not finish Problems 1-10 in class, complete them at home. These problems will be checked and graded."]},
        "Wednesday": {"in_class": ["Lesson 33", "Problems 1-10"], "at_home": ["Lesson 33: Problems 11-29 Odds"]},
        "Thursday": {"in_class": ["Lesson 34", "Problems 1-10"], "at_home": ["If you do not finish Problems 1-10 in class, complete them at home. These problems will be checked and graded."]},
        "Friday": {"in_class": ["Investigation 3"], "at_home": None},
    }
    math_reminders = [
        "This week we are working through Lessons 31\u201334 and Investigation 3.",
        "We will be having our first Math Test and Fact Assessment of Track 2 (Quarter 2) on Tuesday, October 20!",
    ]
    (STAGE / "math-page.html").write_text(build_agenda(SUBTITLE, math_reminders, math_days), encoding="utf-8")

    # --- READING/SPELLING (flat list) ---
    rs_days = {
        "Monday": ["Spelling: Lesson 32", "Reading: Lesson 37", "Workbook"],
        "Tuesday": ["Spelling: Lesson 33", "Reading: Lesson 38"],
        "Wednesday": ["Spelling: Lesson 34", "Reading: Lesson 39", "Workbook"],
        "Thursday": ["Spelling Test 35", "Reading: Lesson 40"],
        "Friday": ["Spelling: Review", "Reading Mastery Test 4", "Fluency Checkout 4"],
    }
    rs_reminders = [
        "Spelling Test 35 is Thursday, October 15.",
        "Reading Mastery Test 4 and Fluency Checkout 4 are Friday, October 16.",
    ]
    (STAGE / "reading_spelling-page.html").write_text(build_flat_list(SUBTITLE, rs_reminders, rs_days), encoding="utf-8")

    # --- LANGUAGE ARTS ---
    la_days = {
        "Monday": {"in_class": ["Chapter 5, Lesson 1"], "at_home": None},
        "Tuesday": {"in_class": ["Chapter 5, Lesson 1"], "at_home": None},
        "Wednesday": {"in_class": ["Chapter 5, Lesson 2"], "at_home": None},
        "Thursday": {"in_class": ["Chapter 5, Lesson 2", "Classroom Practice 19"], "at_home": None},
        "Friday": {"in_class": ["Chapter 5, Lesson 3"], "at_home": None},
    }
    la_reminders = ["We are beginning Chapter 5 in Shurley this week."]
    (STAGE / "language_arts-page.html").write_text(build_agenda(SUBTITLE, la_reminders, la_days), encoding="utf-8")

    # --- SCIENCE ---
    science_days = {
        "Monday": {"in_class": ["Force and Motion Chapter 1"], "at_home": None},
        "Tuesday": {"in_class": ["Force and Motion Chapter 1"], "at_home": None},
        "Wednesday": {"in_class": ["Force and Motion Chapter 2"], "at_home": None},
        "Thursday": {"in_class": ["Force and Motion Chapter 2 Check"], "at_home": None},
        "Friday": {"in_class": ["Force and Motion Chapters 1\u20132 Review"], "at_home": None},
    }
    science_reminders = ["We are learning about Force and Motion in Science."]
    (STAGE / "science-page.html").write_text(build_agenda(SUBTITLE, science_reminders, science_days), encoding="utf-8")

    # --- HISTORY (redirect-only, no day blocks) ---
    hist_reminders = [
        "We are learning Science this track! Please check the Science Canvas page for this week's agenda, assignments, and updates.",
    ]
    hist_body = (
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{_banner(SUBTITLE)}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n'
        f'<div style="width: 100%; padding-left: 15px;">{"".join(f"<p>{esc(r)}</p>" for r in hist_reminders)}</div>\n'
        f"</div>\n</div>"
    )
    (STAGE / "history-page.html").write_text(hist_body, encoding="utf-8")

    print("Staged subject pages:")
    for f in sorted(STAGE.glob("*-page.html")):
        print(f"  {f.name} ({f.stat().st_size} bytes)")

    # --- HOMEROOM surgery ---
    homeroom = stage_homeroom()
    print(f"Homeroom staged: {homeroom}")
    return 0


def stage_homeroom() -> str:
    """Apply the surgical Homeroom edits to the live body and stage the result."""
    live = (REPO_ROOT / ".local/canvas-llm/deployment-backups/Q2W1").parent  # not used; read live from snapshot
    # Read the live body captured earlier.
    live_body = Path("/tmp/homeroom-front-body.html").read_text(encoding="utf-8")

    # 1. Header week label
    live_body = live_body.replace("Week 9 · September 14–18, 2026", "Track 2, Week 1 · October 12–16, 2026")

    # 2. Welcome message
    old_welcome = (
        '<p style="font-size: 16px; margin: 10px 0 0;">We are heading into the final week of our first track! '
        'This week includes our Fourth Grade Playground Picnic on Friday, September 18. '
        'Please take a moment to review the important reminders and updates below.</p>'
    )
    new_welcome = (
        '<p style="font-size: 16px; margin: 10px 0 0;">Welcome back! I hope everyone had a wonderful, relaxing track out and was able to enjoy some time together.</p>'
        '<p style="font-size: 16px; margin: 10px 0 0;">We are excited to begin a wonderful second track together! This is a great opportunity for students to reset, refocus, and build on everything they learned during our first track. We have a lot to look forward to, and I am excited to see everyone back in the classroom refreshed and ready for another great stretch of learning, growth, and fun.</p>'
        '<p style="font-size: 16px; margin: 10px 0 0;">Thank you, as always, for your continued support and partnership!</p>'
    )
    if old_welcome in live_body:
        live_body = live_body.replace(old_welcome, new_welcome)
    else:
        return "WELCOME_MATCH_FAILED"

    # 3. Important Dates: remove expired tiles, keep Oct 20, add Nov 11.
    # Remove Sept 18 tile
    live_body = re.sub(r'\s*<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: #9a3412; ">SEPTEMBER 18</div><div style="font-size: 16px; ">Spirit Shirt Day</div><div style="font-size: 13px;">Spirit shirts with uniform bottoms</div></div>', "", live_body)
    # Remove Sept 22 tile
    live_body = re.sub(r'\s*<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: #9a3412; ">SEPTEMBER 22</div><div style="font-size: 16px; ">Report Cards</div></div>', "", live_body)
    # Remove Track Out tile
    live_body = re.sub(r'\s*<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: #9a3412; ">SEPT\. 21 – OCT\. 9</div><div style="font-size: 16px; ">Track Out</div></div>', "", live_body)
    # Add Nov 11 Veterans Day after Oct 20 tile
    old_oct20 = '<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: #9a3412; ">OCTOBER 20</div><div style="font-size: 16px; ">Make-Up Picture Day</div></div>'
    new_dates = old_oct20 + '<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: #9a3412; ">NOVEMBER 11</div><div style="font-size: 16px; ">Veterans Day Performance</div><div style="font-size: 13px;">9:00 AM\u201310:00 AM</div></div>'
    live_body = live_body.replace(old_oct20, new_dates)

    # 4. Remove Playground Picnic section
    live_body = re.sub(r'\s*<div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 16px; padding: 22px; margin-bottom: 22px;">.*?View the Playground Picnic Flyer</a></p>\s*</div>', "", live_body, flags=re.DOTALL)

    # 5. September Birthdays -> October Birthdays (Liam, October 13)
    old_birthdays = re.search(r'<h2 style="margin: 0 0 16px; color: #a21caf; font-size: 23px;">🎂 September Birthdays 🎉</h2>', live_body)
    if old_birthdays:
        live_body = live_body.replace(old_birthdays.group(0), '<h2 style="margin: 0 0 16px; color: #a21caf; font-size: 23px;">🎂 October Birthdays 🎉</h2>')
        # Replace the birthday tiles div content
        old_tiles = re.search(r'<div style="display: flex; gap: 18px; flex-wrap: wrap;">.*?</div></div>\s*</div>', live_body, flags=re.DOTALL)
        if old_tiles:
            new_tiles = (
                '<div style="display: flex; gap: 18px; flex-wrap: wrap;"><div style="flex: 1 1 30%; min-width: 220px; background-color: #fff0f5; border: 1px solid #f4b6cf; border-radius: 18px; padding: 24px; text-align: center;"><div style="font-size: 32px; margin-bottom: 8px;">🎂🎉</div><div style="font-size: 22px;  color: #c51062;">Liam</div><div style="font-size: 18px; color: #333333; margin-top: 6px;">October 13</div></div></div>'
            )
            live_body = live_body.replace(old_tiles.group(0), new_tiles)
        else:
            return "BIRTHDAY_TILES_MATCH_FAILED"
    else:
        return "BIRTHDAY_HEADER_MATCH_FAILED"

    # 6. Routines -> Starting Track 2 Strong
    old_routines = re.search(r'<div style="background: #eef2ff; border-left: 6px solid #4f46e5; border-radius: 14px; padding: 22px; margin-bottom: 22px;">\s*<h2[^>]*>⭐ Routines, Responsibility &amp; Finishing Strong</h2>.*?</div>', live_body, flags=re.DOTALL)
    if old_routines:
        new_routines = (
            '<div style="background: #eef2ff; border-left: 6px solid #4f46e5; border-radius: 14px; padding: 22px; margin-bottom: 22px;">'
            '<h2 style="margin: 0 0 10px; color: #4338ca; font-size: 22px;">⭐ Starting Track 2 Strong</h2>'
            '<p style="margin: 0;">A new track gives us a fresh opportunity to reset and start strong. As we begin Track 2, students will be held to high expectations for their choices, effort, responsibility, and treatment of others.</p>'
            '<p style="margin: 10px 0 0;">We will continue focusing on following directions the first time, transitioning appropriately, staying organized, coming to class prepared, and making smart choices throughout the school day.</p>'
            '<p style="margin: 10px 0 0;">We will also be emphasizing good sportsmanship, respectful communication, handling wins and losses appropriately, and being a positive teammate and classmate. Our goal is for every student to take increasing ownership of their choices and help make our classroom a place where everyone can learn and be successful.</p>'
            '</div>'
        )
        live_body = live_body.replace(old_routines.group(0), new_routines)
    else:
        return "ROUTINES_MATCH_FAILED"

    # 7. Summer Heat & Hydration tile -> Fall Weather & Recess
    old_weather = re.search(r'<div style="flex: 1 1 250px; background: #ecfeff; border-radius: 14px; padding: 20px; border-top: 5px solid #0891b2;"><div style="font-size: 28px;">☀️💧</div><h3 style="color: #0e7490; margin: 7px 0; font-size: 19px;">Summer Heat &amp; Hydration</h3>.*?</div>', live_body, flags=re.DOTALL)
    if old_weather:
        new_weather = (
            '<div style="flex: 1 1 250px; background: #ecfeff; border-radius: 14px; padding: 20px; border-top: 5px solid #0891b2;"><div style="font-size: 28px;">🍂🌧️</div><h3 style="color: #0e7490; margin: 7px 0; font-size: 19px;">Fall Weather &amp; Recess</h3><p style="margin: 0; font-size: 14px;">As we move into fall, the weather will be getting cooler and wetter. We go outside for recess unless weather conditions, such as lightning, make it unsafe to do so.</p><p style="margin: 8px 0 0; font-size: 14px;">Please check the weather each morning and make sure your child is dressed appropriately for outdoor recess. Keeping an extra sweater or light jacket in your child\'s locker is also a great idea for cooler days.</p></div>'
        )
        live_body = live_body.replace(old_weather.group(0), new_weather)
    else:
        return "WEATHER_MATCH_FAILED"

    # 8. Remove Flashlight Friday section
    live_body = re.sub(r'\s*<div style="background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 16px; padding: 22px; margin-bottom: 22px;">\s*<h2[^>]*>🔦 Flashlight Friday.*?</div>', "", live_body, flags=re.DOTALL)

    # 9. Remove Friday Folders & Track Out section
    live_body = re.sub(r'\s*<div style="background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 16px; padding: 22px; margin-bottom: 22px;">\s*<h2[^>]*>📁 Friday Folders.*?</div>', "", live_body, flags=re.DOTALL)

    # 10. A Note from Mr. Reagan -> new closing note
    old_note = re.search(r'<div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px; padding: 22px; margin-bottom: 22px;">\s*<h2[^>]*>⭐ A Note from Mr\. Reagan</h2>.*?</div>', live_body, flags=re.DOTALL)
    if old_note:
        new_note = (
            '<div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px; padding: 22px; margin-bottom: 22px;">'
            '<h2 style="margin: 0 0 12px; color: #c2410c; font-size: 23px;">⭐ A Note from Mr. Reagan</h2>'
            '<p style="margin: 0;">I hope everyone had a wonderful track out and is feeling refreshed and ready to begin Track 2!</p>'
            '<p style="margin: 10px 0 0;">I am very proud of everything our students accomplished during the first part of the year, and I am excited to see how much more they will grow over the weeks ahead. A new track is a great chance to reset, strengthen good habits, and challenge ourselves to do even better.</p>'
            '<p style="margin: 10px 0 0;">I am looking forward to another wonderful track together!</p>'
            '</div>'
        )
        live_body = live_body.replace(old_note.group(0), new_note)
    else:
        return "NOTE_MATCH_FAILED"

    (STAGE / "homeroom-page.html").write_text(live_body, encoding="utf-8")
    return "OK"


if __name__ == "__main__":
    sys.exit(main())
