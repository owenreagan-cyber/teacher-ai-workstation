#!/usr/bin/env python3
"""Build the Q1W9 (September 14-18, 2026) Canvas package drafts (local only).

Generates the exact FPK agenda-page HTML, assignment specs, assessment/agenda
announcements, and the Week 9 rolling Homeroom newsletter for the approved
Q1W9 production deployment. Preview-only: this module performs no Canvas
network I/O and no writes.

Verified inputs:
- live pacing (2026-2027 FPK Pacing Guides, tab ``4A - Reagan``), Sep 14-18 2026
- Q1W7/Q1W8 live agenda HTML (structure + established wording)
- Q1W8 live assignment settings (groups, 100 pts, percent, on_paper)
- live Homeroom Week 8 newsletter (rolling HTML base)

Authority:
- docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
- docs/programs/canvas-llm/canonical-context-pack/naming-conventions.md
- docs/programs/canvas-llm/canonical-context-pack/homework-rules-contract.md
- docs/programs/canvas-llm/canonical-context-pack/newsletter-homeroom-contract.md
- docs/programs/canvas-llm/canvas-weekly-workflow-guardrails.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import playground_picnic as picnic  # noqa: E402

AUDIT = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit"

# --------------------------------------------------------------------------- #
# Shared FPK shell (byte-identical to the live Q1W7/Q1W8 agenda pages)
# --------------------------------------------------------------------------- #
LINK = (
    '<link rel="stylesheet" href="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219636/canvas_global_app.css">'
)
SCRIPT = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

H3_BORDER = (
    "border-width: 0px !important; border-style: none !important; "
    "border-color: currentcolor !important;"
)
DAY_H3 = (
    "color: #ffffff; background-color: #0065a7; margin-top: 15px; margin-bottom: 2px; "
    + H3_BORDER
)
H4 = (
    "color: #ffffff; background-color: #333333; padding-left: 10px; margin: 0px; "
    + H3_BORDER
)
REM_H3 = "background-color: #c51062; color: #ffffff; " + H3_BORDER
BANNER = (
    '<p style="color: #ffffff; background-color: #0065a7; text-align: center; margin: 0;">'
    '<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
    '<span style="font-size: 10pt;">Quarter 1, Week 9 | September 14\u201318, 2026</span></p>'
)

WEEK_MARKER = "September 14\u201318, 2026"
PAGE_URL = "q1w9-september-14-18-2026"
PAGE_TITLE = "Q1W9 - September 14\u201318, 2026"

MATH_COURSE_ID = 26404
READING_COURSE_ID = 26442
LA_COURSE_ID = 28171
HISTORY_COURSE_ID = 28165
HOMEROOM_COURSE_ID = 26429

# Mon Sep 14 .. Thu Sep 17 2026 @ 11:59 PM America/New_York
DUE_MON = "2026-09-15T03:59:59Z"
DUE_TUE = "2026-09-16T03:59:59Z"
DUE_WED = "2026-09-17T03:59:59Z"
DUE_THU = "2026-09-18T03:59:59Z"

POWER_UP_A_FILE_ID = 6120835  # live Math course 26404 file: "Power Up A.pdf"
POWER_UP_A_PREVIEW = (
    "https://thalesacademy.instructure.com/courses/26404"
    f"/files/{POWER_UP_A_FILE_ID}/preview"
)

# Playground Picnic flyer (Homeroom course 26429 file "Final Flyer.pdf").
# Canvas serves the /preview endpoint with `Content-Disposition: attachment`,
# so the frame renders blank and leaves a large empty green box. Link instead.
HOMEROOM_COURSE_ID = 26429
PICNIC_FLYER_FILE_ID = 6185432
PICNIC_FLYER_LABEL = "View the Playground Picnic Flyer"
PICNIC_FLYER_LINK = (
    '<p style="margin: 14px 0 0;"><a href="'
    f"https://thalesacademy.instructure.com/courses/{HOMEROOM_COURSE_ID}"
    f'/files/{PICNIC_FLYER_FILE_ID}" target="_blank" '
    'style="display: inline-block; background: #15803d; color: #ffffff; '
    'padding: 10px 18px; border-radius: 8px; text-decoration: none;">'
    f"{PICNIC_FLYER_LABEL}</a></p>"
)

# Announcement schedule (established precedent: week announcements Friday 4:00 PM ET)
ANNOUNCE_AT = "2026-09-11T20:00:00Z"  # Fri Sep 11, 4:00 PM ET
HOMEROOM_RESEND_AT = "2026-09-17T20:00:00Z"  # Thu Sep 17, 4:00 PM ET
SPELLING_ANNOUNCE_AT = "2026-09-11T20:30:00Z"  # Fri Sep 11, 4:30 PM ET

# Live Q1W8 objects updated in place (avoids duplicate titles / stale resources).
MATH_ASSESSMENT_REMINDER_ID = 165340
HOMEROOM_WEEK8_ANNOUNCEMENT_ID = 165184

WEEKLY_UPDATE_IDS: dict[str, int] = {
    "math": 165048,
    "reading_spelling": 165049,
    "language_arts": 165050,
    "history": 165051,
}


def _items(lines: list[str]) -> str:
    return "".join(f"<li>{line}</li>" for line in lines)


def _day(
    block_id: str,
    day_label: str,
    in_class: list[str],
    *,
    at_home: list[str] | None = None,
    full_width: bool = False,
) -> str:
    """Render one day block in the established FPK agenda structure."""
    in_html = f"<ul>{_items(in_class)}</ul>"
    if at_home is None:
        width = "100%" if full_width or not at_home else "49%"
        return (
            f'<div id="{block_id}" class="">\n'
            f'<h3 style="{DAY_H3}">{day_label}</h3>\n'
            f'<div style="display: flex; width: 100%;">'
            f'<div style="width: {width}; padding-left: 15px;">'
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
        f'<h4 class="kl_solid_border" style="{H4}">At Home</h4>'
        f"<ul>{_items(at_home)}</ul></div></div>\n"
        f"</div>"
    )


def _page(reminders_html: str, days_html: str) -> str:
    return (
        f"{LINK}\n"
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        f'<div id="kl_banner" class="">\n{BANNER}\n'
        f'<h3 style="{REM_H3}">Reminders</h3>\n'
        f'<div style="width: 100%; padding-left: 15px;">{reminders_html}</div>\n'
        f"{days_html}\n"
        f"</div>\n</div>\n{SCRIPT}"
    )


# --------------------------------------------------------------------------- #
# Week 9 agenda pages
# --------------------------------------------------------------------------- #
def build_math_page() -> str:
    reminders = (
        "<p>Written Assessment 5 and Fact Assessment 5 are on Thursday, September 17.</p>"
    )
    days = (
        _day(
            "kl_activities2",
            "Monday",
            ["Lesson 28", "Problems 1-10"],
            at_home=["Lesson 28: Problems 12-30 Evens"],
        )
        + _day(
            "kl_custom_block_4",
            "Tuesday",
            ["Lesson 29", "Problems 1-10"],
            at_home=["If you do not finish Problems 1-10 in class, complete them at home. "
                     "These problems will be checked and graded."],
        )
        + _day(
            "kl_custom_block_3",
            "Wednesday",
            ["Lesson 30", "Problems 1-10"],
            at_home=["Lesson 30: Problems 11-29 Odds"],
        )
        + _day(
            "kl_custom_block_2",
            "Thursday",
            ["Written Assessment 5", "Fact Assessment 5"],
            full_width=True,
        )
        + _day("kl_custom_block_1", "Friday", ["Cleaning"], full_width=True)
    )
    return _page(reminders, days)


def build_reading_page() -> str:
    reminders = (
        "<p><strong>Spelling Test 30</strong> — Wednesday, September 16</p>"
    )
    days = (
        _day(
            "kl_activities2",
            "Monday",
            ["Spelling: Review", "Reading: Lesson 33"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_4",
            "Tuesday",
            ["Spelling: Practice Test", "Reading: Lesson 34"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_3",
            "Wednesday",
            ["Spelling Test 30", "Reading: Lesson 35"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_2",
            "Thursday",
            ["Spelling: Review", "Reading: Lesson 36"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_1",
            "Friday",
            ["Spelling: Rotations", "Reading: Rotations"],
            full_width=True,
        )
    )
    return _page(reminders, days)


def build_language_arts_page() -> str:
    reminders = "<p>We will continue our Personal Narrative writing unit this week.</p>"
    days = (
        _day("kl_activities2", "Monday", ["Personal Narrative Lesson 11"], full_width=True)
        + _day("kl_custom_block_4", "Tuesday", ["Personal Narrative Lesson 12"], full_width=True)
        + _day("kl_custom_block_3", "Wednesday", ["Personal Narrative Lesson 13"], full_width=True)
        + _day("kl_custom_block_2", "Thursday", ["Personal Narrative Lesson 14"], full_width=True)
        + _day("kl_custom_block_1", "Friday", ["Friday Folders"], full_width=True)
    )
    return _page(reminders, days)


def build_history_page() -> str:
    reminders = (
        "<p><strong>Early Islamic Civilizations Test</strong> \u2014 Thursday, September 17 "
        "(open notes)</p>"
    )
    days = (
        _day("kl_activities2", "Monday", ["Early Islamic Civilizations Chapter 5"], full_width=True)
        + _day(
            "kl_custom_block_4",
            "Tuesday",
            ["Early Islamic Civilizations Chapter 5"],
            full_width=True,
        )
        + _day("kl_custom_block_3", "Wednesday", ["Early Islamic Civilizations Review"], full_width=True)
        + _day(
            "kl_custom_block_2",
            "Thursday",
            ["Early Islamic Civilizations Test"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_1",
            "Friday",
            ["Parent Picnic / Cleaning Room"],
            full_width=True,
        )
    )
    return _page(reminders, days)


PAGE_BUILDERS: dict[str, dict[str, Any]] = {
    "Math": {"course_id": MATH_COURSE_ID, "builder": build_math_page},
    "Reading/Spelling": {"course_id": READING_COURSE_ID, "builder": build_reading_page},
    "Language Arts": {"course_id": LA_COURSE_ID, "builder": build_language_arts_page},
    "History": {"course_id": HISTORY_COURSE_ID, "builder": build_history_page},
}


# --------------------------------------------------------------------------- #
# Assignments (established Q1W7/Q1W8 settings: 100 pts, percent, on_paper)
# --------------------------------------------------------------------------- #
ASSIGNMENTS: list[dict[str, Any]] = [
    {
        "course": "Reading/Spelling",
        "course_id": READING_COURSE_ID,
        "resulting_title": "RM4: Lesson 33 Workbook",
        "assignment_group": "Homework",
        "due_at": DUE_MON,
        "timing": "Mon Sep 14, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Reading/Spelling",
        "course_id": READING_COURSE_ID,
        "resulting_title": "RM4: Lesson 34 Workbook and Comprehension",
        "assignment_group": "Homework",
        "due_at": DUE_TUE,
        "timing": "Tue Sep 15, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Reading/Spelling",
        "course_id": READING_COURSE_ID,
        "resulting_title": "RM4: Lesson 35 Workbook",
        "assignment_group": "Homework",
        "due_at": DUE_WED,
        "timing": "Wed Sep 16, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Reading/Spelling",
        "course_id": READING_COURSE_ID,
        "resulting_title": "RM4: Lesson 36 Workbook and Comprehension",
        "assignment_group": "Homework",
        "due_at": DUE_THU,
        "timing": "Thu Sep 17, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Math",
        "course_id": MATH_COURSE_ID,
        "resulting_title": "SM5: Lesson 28 Homework",
        "assignment_group": "Homework/Class Work",
        "due_at": DUE_MON,
        "timing": "Mon Sep 14, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Math",
        "course_id": MATH_COURSE_ID,
        "resulting_title": "SM5: Lesson 29 Homework",
        "assignment_group": "Homework/Class Work",
        "due_at": DUE_TUE,
        "timing": "Tue Sep 15, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Math",
        "course_id": MATH_COURSE_ID,
        "resulting_title": "SM5: Lesson 30 Homework",
        "assignment_group": "Homework/Class Work",
        "due_at": DUE_WED,
        "timing": "Wed Sep 16, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Math",
        "course_id": MATH_COURSE_ID,
        "resulting_title": "SM5: Fact Assessment 5",
        "assignment_group": "Fact Assessments",
        "due_at": DUE_THU,
        "timing": "Thu Sep 17, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "Math",
        "course_id": MATH_COURSE_ID,
        "resulting_title": "SM5: Written Assessment 5",
        "assignment_group": "Written Assessments",
        "due_at": DUE_THU,
        "timing": "Thu Sep 17, 11:59 PM America/New_York",
        "description": "",
    },
    {
        "course": "History",
        "course_id": HISTORY_COURSE_ID,
        "resulting_title": "HIST 4B: Early Islamic Civilizations Test",
        "assignment_group": "Assignments",
        "due_at": DUE_THU,
        "timing": "Thu Sep 17, 11:59 PM America/New_York",
        "description": (
            f"{LINK}"
            "<p>Early Islamic Civilizations Test</p>"
            "<p>We will take our Early Islamic Civilizations test on Thursday, "
            "September 17.</p>"
            "<p>This will be an open-notes test, so you may use your class notes "
            "during the assessment.</p>"
            "<p>Make sure your notes are organized and ready to use. Read each "
            "question carefully, use your notes when needed, and check your work "
            "before turning in your test.</p>"
            f"{SCRIPT}"
        ),
    },
]


# --------------------------------------------------------------------------- #
# Announcement drafts
# --------------------------------------------------------------------------- #
def _wrap_newsletter(intro: str, newsletter_body: str) -> str:
    """Compose the announcement without duplicating the newsletter's trailing JS."""
    tail = "" if SCRIPT in newsletter_body else SCRIPT
    return f"{LINK}{intro}\n{newsletter_body}\n{tail}" if tail else f"{LINK}{intro}\n{newsletter_body}"


def build_homeroom_newsletter_announcement(newsletter_body: str) -> str:
    """Short family intro + the full current Week 9 newsletter HTML."""
    intro = (
        '<p style="margin: 0 0 12px;"><strong>Hound Families,</strong></p>'
        '<p style="margin: 0 0 12px;">Please see this week\u2019s classroom newsletter '
        'below for important dates, reminders, birthdays, and classroom updates. This is '
        'the last week of the track, so please note the Friday details and the track out '
        'dates below.</p>'
        '<p style="margin: 0 0 12px;">Have a great week!</p>'
        '<p style="margin: 0 0 12px;">Mr. Reagan</p>'
    )
    return _wrap_newsletter(intro, newsletter_body)


def build_homeroom_reminder_announcement(newsletter_body: str) -> str:
    """Thursday track-out reminder carrying the same Week 9 newsletter HTML."""
    intro = (
        '<p style="margin: 0 0 12px;"><strong>Hound Families,</strong></p>'
        '<p style="margin: 0 0 12px;">A quick reminder that this is our final week of the '
        'track. Spirit shirts with uniform bottoms and Friday Folders are Friday, '
        '\U0001F526 Flashlight Friday is Friday (please send a blanket), and our '
        'Playground Picnic is Friday at 12:15 PM.</p>'
        '<p style="margin: 0 0 12px;"><strong>Track Out begins after Friday, '
        'September 18</strong> and runs <strong>September 21 \u2013 October 9</strong>. '
        'School resumes Monday, October 12.</p>'
        '<p style="margin: 0 0 12px;">Please see the full newsletter below.</p>'
        '<p style="margin: 0 0 12px;">Have a wonderful track out!</p>'
        '<p style="margin: 0 0 12px;">Mr. Reagan</p>'
    )
    return _wrap_newsletter(intro, newsletter_body)


def build_math_assessment_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>This is a reminder that students will complete "
        "<strong>Written Assessment 5 and Fact Assessment 5 on Thursday, "
        "September 17</strong>.</p>"
        "<p>Fact Assessment 5 will include <strong>40 addition problems</strong>.</p>"
        "<p>Students can practice their facts using <strong>Power Up A</strong>. "
        "I have included the practice resource below.</p>"
        '<p style="margin: 14px 0 0;">'
        '<iframe style="width: 100%; height: 700px; border: 0;" '
        f'src="{POWER_UP_A_PREVIEW}" title="Power Up A practice"></iframe></p>'
        "<p>Best,</p><p>Owen Reagan</p>"
        f"{SCRIPT}"
    )


def build_reading_spelling_agenda_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>The Week 9 Reading &amp; Spelling agenda for <strong>September 14\u201318</strong> "
        "has been updated.</p>"
        "<p>Students will complete Reading Lessons 33\u201336. In Spelling, we will review, "
        "take a practice test, complete <strong>Spelling Test 30 on Wednesday, "
        "September 16</strong>, and review to finish the track.</p>"
        "<p>Please review the Week 9 page for the full week ahead.</p>"
        "<p>Have a great weekend!</p><p>Mr. Reagan</p>"
        f"{SCRIPT}"
    )


def build_math_agenda_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>The Week 9 Math agenda for <strong>September 14\u201318</strong> has been "
        "updated.</p>"
        "<p>Students will complete Lessons 28\u201330 and finish the track with "
        "<strong>Written Assessment 5 and Fact Assessment 5 on Thursday, "
        "September 17</strong>.</p>"
        "<p>Please review the Week 9 page for the full week ahead.</p>"
        "<p>Have a great weekend!</p><p>Mr. Reagan</p>"
        f"{SCRIPT}"
    )


def build_history_agenda_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>The Week 9 History agenda for <strong>September 14\u201318</strong> has been "
        "updated.</p>"
        "<p>Students will finish our Early Islamic Civilizations unit and take the "
        "<strong>Early Islamic Civilizations Test on Thursday, September 17</strong>. "
        "This will be an open-notes test.</p>"
        "<p>Please review the Week 9 page for the full week ahead.</p>"
        "<p>Have a great weekend!</p><p>Mr. Reagan</p>"
        f"{SCRIPT}"
    )


def build_spelling_test_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>Students will take <strong>Spelling Test 30 on Wednesday, "
        "September 16</strong>.</p>"
        "<p>The spelling test is cumulative, so students should review word lists "
        "1-30. Reading the words aloud, spelling them aloud, and writing them from "
        "memory are excellent ways to prepare.</p>"
        "<p>Thank you,</p>"
        "<p>Owen Reagan</p>"
        f"{SCRIPT}"
    )


def build_history_assessment_announcement() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>Students will take our <strong>Early Islamic Civilizations Test on "
        "Thursday, September 17</strong>.</p>"
        "<p>This will be an open-notes test, so students may use their class notes "
        "during the assessment.</p>"
        "<p>Please make sure your child's class notes are organized and ready to "
        "use.</p>"
        "<p>Thank you,</p>"
        "<p>Owen Reagan</p>"
        f"{SCRIPT}"
    )


# --------------------------------------------------------------------------- #
# Q1W9 subject Weekly Update drafts (existing announcements updated in place)
# --------------------------------------------------------------------------- #
WEEKLY_UPDATE_DRAFTS: dict[str, dict[str, str]] = {
    "math": {
        "week_in_review": (
            "We had another great week in Math! Students completed Lessons 26\u201327 and "
            "finished Written Assessment 4 and Fact Assessment 4."
        ),
        "week_ahead": (
            "Next week, students will complete <strong>Lessons 28\u201330</strong> and finish "
            "the track with <strong>Written Assessment 5 and Fact Assessment 5 on "
            "Thursday, September 17</strong>. Fact Assessment 5 includes "
            "<strong>40 addition problems</strong>. Students can practice their facts "
            "using Power Up A."
        ),
    },
    "reading_spelling": {
        "week_in_review": (
            "In Reading, students completed Lessons 30\u201332 and finished the Reading "
            "Test and Fluency Checkout. In Spelling, students completed Lessons "
            "26\u201329."
        ),
        "week_ahead": (
            "Next week, students will complete <strong>Reading Lessons 33\u201336</strong>. "
            "In Spelling, we will review, take a practice test, and complete the final "
            "test of the track, <strong>Spelling Test 30, on Wednesday, "
            "September 16</strong>."
        ),
    },
    "language_arts": {
        "week_in_review": (
            "We had a productive week in Language Arts! Students continued our "
            "Personal Narrative writing unit with Lessons 7\u201310."
        ),
        "week_ahead": (
            "Next week, we will continue our Personal Narrative writing unit with "
            "<strong>Lessons 11\u201314</strong>."
        ),
    },
    "history": {
        "week_in_review": (
            "We had a great week in History! Students continued their study of "
            "Medieval Islamic Kingdoms with Chapters 2\u20134."
        ),
        "week_ahead": (
            "Next week, students will finish the Early Islamic Civilizations unit and "
            "take the <strong>Early Islamic Civilizations Test on Thursday, "
            "September 17</strong>. This will be an open-notes test."
        ),
    },
}


# --------------------------------------------------------------------------- #
# Homeroom Week 9 newsletter (rolling HTML base, updated in place)
# --------------------------------------------------------------------------- #
NEWSLETTER_SOURCE = AUDIT / "q1w9-newsletter-source.html"

BADGE_OLD = "Week 8 \u00b7 September 7\u201311, 2026"
BADGE_NEW = "Week 9 \u00b7 September 14\u201318, 2026"

INTRO_OLD = (
    "We hope everyone enjoys the Labor Day weekend! We have a short but exciting "
    "week ahead, with students returning on Tuesday for Fall Picture Day and class "
    "pictures. Please take a moment to review the important reminders and updates below."
)
INTRO_NEW = (
    "We are heading into the final week of our first track! This week includes our "
    "Fourth Grade Playground Picnic on Friday, September 18. Please take a moment to "
    "review the important reminders and updates below."
)

WARM_DIV_OPEN = (
    '  <div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px; '
    'padding: 22px; margin-bottom: 22px;">'
)
PICTURE_H2 = (
    '    <h2 style="margin: 0 0 12px; color: #c2410c; font-size: 23px;">'
    '\U0001F4F8 Picture Day \u2014 Tuesday, September 8</h2>'
)
PICNIC_DIV_OPEN = (
    '  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 16px; '
    'padding: 22px; margin-bottom: 22px;">'
)
PICNIC_HEADING = (
    '    <h2 style="margin: 0 0 12px; color: #15803d; font-size: 23px;">'
    '\U0001F9FA Fourth Grade Playground Picnic'
)
BIRTHDAY_BLOCK_START = (
    '  <div style="margin-bottom: 22px;">\n'
    '    <h2 style="margin: 0 0 16px; color: #a21caf; font-size: 23px;">'
    '\U0001F382 September Birthdays'
)
LABOR_DAY_TILE = (
    '<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; '
    'padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: '
    '#9a3412; ">SEPTEMBER 7</div><div style="font-size: 16px; ">Labor Day</div>'
    '<div style="font-size: 13px;">No School</div></div>'
)
PICTURE_DAY_TILE = (
    '<div style="flex: 1 1 180px; background: #ffffff; border-radius: 12px; '
    'padding: 14px; border: 1px solid #fed7aa;"><div style="font-size: 13px; color: '
    '#9a3412; ">SEPTEMBER 8</div><div style="font-size: 16px; ">Picture Day</div>'
    '<div style="font-size: 13px;">Fall &amp; class pictures</div></div>'
)
ROUTINES_H2 = (
    '<h2 style="margin: 0 0 10px; color: #4338ca; font-size: 22px;">'
    '\u2B50 Routines, Responsibility &amp; the Second Half of Track</h2>'
)
ROUTINES_H2_NEW = (
    '<h2 style="margin: 0 0 10px; color: #4338ca; font-size: 22px;">'
    '\u2B50 Routines, Responsibility &amp; Finishing Strong</h2>'
)
ROUTINES_P = (
    "Students have now had several weeks to practice our classroom routines and "
    "procedures. As we prepare for the <strong>second half of the track</strong>, "
    "students will be held more consistently accountable for following those "
    "expectations independently."
)
ROUTINES_P_NEW = (
    "Students have had several weeks to practice our classroom routines and "
    "procedures. As we finish the track, students will be held more consistently "
    "accountable for following those expectations independently."
)
CLOSING_ANCHOR = '  <div style="text-align: center; padding: 24px 12px 8px;">'

FLASHLIGHT_SECTION = (
    '  <div style="background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 16px; '
    'padding: 22px; margin-bottom: 22px;">\n'
    '    <h2 style="margin: 0 0 12px; color: #4338ca; font-size: 23px;">'
    '\U0001F526 Flashlight Friday \u2014 Friday, September 18</h2>\n'
    '    <p style="margin: 0;">On Friday, we will celebrate the end of the track with '
    '<strong>Flashlight Friday / Reading in the Dark</strong>. Students should bring a '
    '<strong>blanket</strong> to school that day.</p>\n'
    '    <p style="margin: 10px 0 0;">Blankets may also be used during the Parent Picnic '
    'on Friday, so one blanket is all your child needs.</p>\n'
    '  </div>'
)

FRIDAY_FOLDERS_SECTION = (
    '  <div style="background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 16px; '
    'padding: 22px; margin-bottom: 22px;">\n'
    '    <h2 style="margin: 0 0 12px; color: #0f766e; font-size: 23px;">'
    '\U0001F4C1 Friday Folders &amp; Track Out</h2>\n'
    '    <p style="margin: 0;">Friday Folders will come home on Friday, September 18. '
    'Please review your child\u2019s work with them, celebrate their growth, and return '
    'the folder after track out.</p>\n'
    '    <p style="margin: 10px 0 0;"><strong>Track Out begins after Friday, '
    'September 18</strong> and runs <strong>September 21 \u2013 October 9</strong>. '
    'School resumes on Monday, October 12.</p>\n'
    '  </div>'
)

Q1_MESSAGE_SECTION = (
    '  <div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px; '
    'padding: 22px; margin-bottom: 22px;">\n'
    '    <h2 style="margin: 0 0 12px; color: #c2410c; font-size: 23px;">'
    '\u2B50 A Note from Mr. Reagan</h2>\n'
    '    <p style="margin: 0;">It has been a tremendous first quarter of the school '
    'year! We are off to an amazing start, and your children have already shown '
    'tremendous growth. I am incredibly proud of the hard work, progress, and '
    'enthusiasm they have shown throughout these first nine weeks.</p>\n'
    '    <p style="margin: 10px 0 0;">I hope the children enjoy their clicker fidgets '
    '\u2014 and that they don\u2019t drive y\u2019all too crazy with the sounds!</p>\n'
    '    <p style="margin: 10px 0 0;">Please enjoy a well-deserved track out as we '
    'recharge and get ready for an exciting second quarter! I look forward to seeing '
    'everyone back refreshed and ready for all that is ahead.</p>\n'
    '  </div>'
)

END_OF_QUARTER_SECTION = (
    FLASHLIGHT_SECTION + "\n\n" + FRIDAY_FOLDERS_SECTION + "\n\n" + Q1_MESSAGE_SECTION
)


def _require_once(text: str, needle: str, label: str) -> None:
    count = text.count(needle)
    if count != 1:
        raise RuntimeError(f"anchor count {count} (expected 1) for {label}: {needle[:70]!r}")


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    _require_once(text, old, label)
    return text.replace(old, new, 1)


def _find_block(text: str, start: str, label: str) -> tuple[int, int]:
    """Return (start, end) of a balanced top-level ``<div>`` block beginning at ``start``."""
    _require_once(text, start, label)
    s = text.index(start)
    depth = 0
    i = s
    n = len(text)
    while i < n:
        nxt_open = text.find("<div", i)
        nxt_close = text.find("</div>", i)
        if nxt_open == -1:
            nxt_open = n
        if nxt_close == -1:
            nxt_close = n
        if nxt_open < nxt_close:
            depth += 1
            i = nxt_open + len("<div")
        else:
            depth -= 1
            i = nxt_close + len("</div>")
            if depth == 0:
                end = i
                if text[end : end + 2] == "\n\n":
                    end += 2
                elif text[end : end + 1] == "\n":
                    end += 1
                return s, end
    raise RuntimeError(f"{label}: unbalanced <div>")


def _remove_block(text: str, start: str, label: str) -> str:
    s, e = _find_block(text, start, label)
    return text[:s] + text[e:]


def _remove_card_containing(text: str, marker: str, label: str) -> str:
    """Remove the card ``<div>`` that contains ``marker`` (a heading string)."""
    _require_once(text, marker, label)
    m = text.index(marker)
    openers = [x for x in (text.rfind(WARM_DIV_OPEN, 0, m), text.rfind(PICNIC_DIV_OPEN, 0, m)) if x >= 0]
    if not openers:
        raise RuntimeError(f"{label}: no card opener found before marker")
    start = max(openers)
    depth = 0
    i = start
    n = len(text)
    while i < n:
        nxt_open = text.find("<div", i)
        nxt_close = text.find("</div>", i)
        if nxt_open == -1:
            nxt_open = n
        if nxt_close == -1:
            nxt_close = n
        if nxt_open < nxt_close:
            depth += 1
            i = nxt_open + len("<div")
        else:
            depth -= 1
            i = nxt_close + len("</div>")
            if depth == 0:
                e = i
                if text[e : e + 2] == "\n\n":
                    e += 2
                elif text[e : e + 1] == "\n":
                    e += 1
                return text[:start] + text[e:]
    raise RuntimeError(f"{label}: unbalanced <div>")


def build_newsletter() -> str:
    """Week 9 rolling newsletter from the live Week 8 HTML base."""
    body = NEWSLETTER_SOURCE.read_text(encoding="utf-8")
    body = _replace_once(body, BADGE_OLD, BADGE_NEW, "week badge")
    body = _replace_once(body, INTRO_OLD, INTRO_NEW, "intro paragraph")

    # Remove the expired Picture Day callout (Sept 8) and re-render the picnic block
    # from the canonical helper in its established position (before Birthdays).
    body = _remove_card_containing(body, PICTURE_H2, "Picture Day callout")
    body = _remove_card_containing(body, PICNIC_HEADING, "stale picnic section")

    # Prune genuinely-expired Important Dates tiles (Labor Day, Picture Day).
    # All future tiles (Spirit Shirt Day, Report Cards, Track Out, Make-Up
    # Picture Day) are preserved.
    removed: list[str] = []
    for tile, label in ((LABOR_DAY_TILE, "Labor Day"), (PICTURE_DAY_TILE, "Picture Day")):
        if tile not in body:
            raise RuntimeError(f"expired date tile anchor not found: {label}")
        body = body.replace(tile, "", 1)
        removed.append(label)

    body = _replace_once(
        body,
        BIRTHDAY_BLOCK_START,
        picnic.render_picnic_section() + "\n\n" + BIRTHDAY_BLOCK_START,
        "birthdays block",
    )
    # Q1W9 spacing fix: Canvas serves the flyer preview as an attachment, so the
    # iframe renders blank and leaves ~700px of empty green. Swap the embed for a
    # link to the same file, preserving surrounding markup exactly.
    body = _replace_once(
        body,
        picnic.render_flyer_embed(),
        PICNIC_FLYER_LINK,
        "picnic flyer embed",
    )

    # Refresh the mid-track routines copy for the final week of the track.
    body = _replace_once(body, ROUTINES_H2, ROUTINES_H2_NEW, "routines heading")
    body = _replace_once(body, ROUTINES_P, ROUTINES_P_NEW, "routines paragraph")

    # Warm callout carrying the family end-of-quarter message + Friday details.
    body = _replace_once(
        body,
        CLOSING_ANCHOR,
        END_OF_QUARTER_SECTION + "\n\n" + CLOSING_ANCHOR,
        "closing sign-off",
    )
    return body


def newsletter_checks(body: str) -> dict[str, bool]:
    return {
        "week9_badge": BADGE_NEW in body,
        "week8_badge_removed": BADGE_OLD not in body,
        "picnic_section": picnic.has_picnic_section(body),
        "picnic_flyer": str(picnic.FLYER_FILE_ID) in body,
        "picture_day_removed": "September 8" not in body and "Picture Day" in body,
        "labor_day_removed": "Labor Day" not in body,
        "flashlight_friday": "Flashlight Friday" in body and "Reading in the Dark" in body,
        "spirit_shirt": "Spirit Shirt Day" in body,
        "blanket_requirement": (
            "Students should bring a <strong>blanket</strong> to school that day." in body
        ),
        "friday_folders": "Friday Folders will come home on Friday, September 18" in body,
        "track_out_date": "SEPT. 21 \u2013 OCT. 9" in body,
        "q1_message": "tremendous first quarter" in body and "clicker fidgets" in body,
        "no_subject_reminders": all(
            token not in body
            for token in (
                "Spelling Test 30",
                "Written Assessment 5",
                "Fact Assessment 5",
                "Early Islamic Civilizations Test",
                "Reading Lessons 33",
            )
        ),
        "single_flyer": body.count(str(picnic.FLYER_FILE_ID)) == 1,
    }


ASSIGNMENT_REQUIRED_FIELDS = (
    "course_id",
    "resulting_title",
    "assignment_group",
    "due_at",
    "timing",
    "description",
    "points_possible",
    "grading_type",
    "submission_type",
    "published",
)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Structural validation of the manifest before any live write."""
    problems: list[str] = []
    actions = manifest.get("actions") or []

    for action in actions:
        otype = action.get("object_type")
        if otype == "assignment":
            for field in ASSIGNMENT_REQUIRED_FIELDS:
                if field not in action:
                    problems.append(f"assignment {action.get('resulting_title')!r} missing {field}")
            if action.get("due_at") and not action["due_at"].endswith("Z"):
                problems.append(f"assignment {action['resulting_title']!r} due_at not UTC ISO")
            if action.get("submission_type") != "on_paper":
                problems.append(f"assignment {action['resulting_title']!r} not on_paper")
            if action.get("points_possible") != 100 or action.get("grading_type") != "percent":
                problems.append(f"assignment {action['resulting_title']!r} points/grading drift")
        elif otype == "announcement":
            if action.get("action") == "CREATE" and not action.get("message"):
                problems.append(f"announcement {action.get('resulting_title')!r} missing message")
            if action.get("action") == "UPDATE" and not action.get("existing_id"):
                problems.append(f"announcement {action.get('resulting_title')!r} UPDATE lacks existing_id")
        elif otype == "page":
            body = action.get("body") or ""
            if action.get("course") == "Homeroom":
                # Rolling family newsletter: not an agenda/kl_wrapper_3 page.
                if "Fourth Grade Playground Picnic" not in body:
                    problems.append("Homeroom newsletter missing picnic section")
                if action.get("front_page") != "SET_AND_VERIFY":
                    problems.append("Homeroom newsletter front page not verified")
                continue
            if "kl_wrapper_3" not in body:
                problems.append(f"page {action.get('course')!r} missing kl_wrapper_3")
            if WEEK_MARKER not in body:
                problems.append(f"page {action.get('course')!r} missing week marker")
            if "#0065a7" not in body or "#c51062" not in body:
                problems.append(f"page {action.get('course')!r} missing approved colors")
            if action.get("front_page") != "SET_AND_VERIFY":
                problems.append(f"page {action.get('course')!r} front page not verified")
        else:
            problems.append(f"unknown object_type {otype!r}")

    # Forbidden objects must never appear.
    titles = {(a.get("resulting_title") or "") for a in actions}
    for forbidden in (
        "Spelling Test 30",
        "RM4: Spelling Test 30",
        "SM5: Cleaning",
        "Cleaning",
    ):
        if forbidden in titles and not forbidden.startswith("Week 9"):
            problems.append(f"forbidden assignment/announcement title present: {forbidden!r}")

    # Homeroom must not carry subject reminder text in its page.
    for action in actions:
        if action.get("course") == "Homeroom" and action.get("object_type") == "page":
            body = action.get("body") or ""
            for token in (
                "Spelling Test 30",
                "Written Assessment 5",
                "Fact Assessment 5",
                "Early Islamic Civilizations Test",
            ):
                if token in body:
                    problems.append(f"Homeroom newsletter contains subject reminder {token!r}")

    # Science must not be touched.
    if any(a.get("course") == "Science" for a in actions):
        problems.append("Science appears in the manifest (must be untouched)")

    return problems


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
def _weekly_update_action(subject_key: str) -> dict[str, Any]:
    from scripts.canvas_llm_phase22 import subject_weekly_update as swu

    course = {
        "math": "Math",
        "reading_spelling": "Reading/Spelling",
        "language_arts": "Language Arts",
        "history": "History",
    }[subject_key]
    draft = WEEKLY_UPDATE_DRAFTS[subject_key]
    page_body = PAGE_BUILDERS[course]["builder"]()
    message = swu.build_message(
        subject_key,
        draft["week_in_review"],
        draft["week_ahead"],
        page_body,
    )
    title = swu.SUBJECTS[subject_key]["title"]
    action = {
        "course": course,
        "course_id": swu.SUBJECTS[subject_key]["course_id"],
        "object_type": "announcement",
        "existing": title,
        "existing_id": WEEKLY_UPDATE_IDS[subject_key],
        "action": "UPDATE",
        "resulting_title": title,
        "message": message,
        "published": True,
    }
    return action


def build_manifest() -> dict[str, Any]:
    newsletter = build_newsletter()
    actions: list[dict[str, Any]] = []

    # 1. Agenda pages (update in place + set front page)
    for course, spec in PAGE_BUILDERS.items():
        actions.append(
            {
                "course": course,
                "course_id": spec["course_id"],
                "object_type": "page",
                "existing": PAGE_URL,
                "action": "UPDATE",
                "resulting_title": PAGE_TITLE,
                "published": True,
                "front_page": "SET_AND_VERIFY",
                "body": spec["builder"](),
            }
        )

    # 2. Homeroom newsletter (rolling page, update in place + keep front page)
    actions.append(
        {
            "course": "Homeroom",
            "course_id": HOMEROOM_COURSE_ID,
            "object_type": "page",
            "existing": "q1w2-july-27-31-2026",
            "action": "UPDATE",
            "resulting_title": "Q1W2 - July 27-31, 2026",
            "published": True,
            "front_page": "SET_AND_VERIFY",
            "body": newsletter,
        }
    )

    # 3. Assignments
    for spec in ASSIGNMENTS:
        actions.append(
            {
                "course": spec["course"],
                "course_id": spec["course_id"],
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": spec["resulting_title"],
                "assignment_group": spec["assignment_group"],
                "due_at": spec["due_at"],
                "timing": spec["timing"],
                "description": spec["description"],
                "points_possible": 100,
                "grading_type": "percent",
                "submission_type": "on_paper",
                "counts_toward_final_grade": True,
                "published": True,
            }
        )

    # 4. Announcements (published/scheduled at the established 4:00 PM ET slots)
    actions.append(
        {
            "course": "Reading/Spelling",
            "course_id": READING_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Week 9 Reading & Spelling Agenda Updated",
            "message": build_reading_spelling_agenda_announcement(),
            "published": True,
            "delayed_post_at": ANNOUNCE_AT,
        }
    )
    actions.append(
        {
            "course": "Math",
            "course_id": MATH_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Week 9 Math Agenda Updated",
            "message": build_math_agenda_announcement(),
            "published": True,
            "delayed_post_at": ANNOUNCE_AT,
        }
    )
    actions.append(
        {
            "course": "History",
            "course_id": HISTORY_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Week 9 History Agenda Updated",
            "message": build_history_agenda_announcement(),
            "published": True,
            "delayed_post_at": ANNOUNCE_AT,
        }
    )
    actions.append(
        {
            "course": "Reading/Spelling",
            "course_id": READING_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Spelling Test 30 - Wednesday, September 16",
            "message": build_spelling_test_announcement(),
            "published": True,
            "delayed_post_at": SPELLING_ANNOUNCE_AT,
        }
    )
    # Stale Q1W8 "Math Assessment Reminder - Thursday" is updated in place (its
    # embedded Power Up C resource is expired); no duplicate is created. Canvas
    # announcement updates cannot be scheduled, so it publishes immediately.
    actions.append(
        {
            "course": "Math",
            "course_id": MATH_COURSE_ID,
            "object_type": "announcement",
            "existing": "Math Assessment Reminder - Thursday",
            "existing_id": MATH_ASSESSMENT_REMINDER_ID,
            "action": "UPDATE",
            "resulting_title": "Math Assessment Reminder - Thursday",
            "message": build_math_assessment_announcement(),
            "published": True,
            "timing": "publish immediately (update-in-place)",
        }
    )
    actions.append(
        {
            "course": "History",
            "course_id": HISTORY_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Early Islamic Civilizations Test - Thursday, September 17",
            "message": build_history_assessment_announcement(),
            "published": True,
            "delayed_post_at": ANNOUNCE_AT,
        }
    )
    # Homeroom rolling family announcement (Q1W8 edition updated in place).
    actions.append(
        {
            "course": "Homeroom",
            "course_id": HOMEROOM_COURSE_ID,
            "object_type": "announcement",
            "existing": "4th Grade Happenings - Week 8",
            "existing_id": HOMEROOM_WEEK8_ANNOUNCEMENT_ID,
            "action": "UPDATE",
            "resulting_title": "Week 9 Newsletter | September 14\u201318",
            "message": build_homeroom_newsletter_announcement(newsletter),
            "published": True,
        }
    )
    actions.append(
        {
            "course": "Homeroom",
            "course_id": HOMEROOM_COURSE_ID,
            "object_type": "announcement",
            "action": "CREATE",
            "resulting_title": "Week 9 Newsletter Reminder - Track Out",
            "message": build_homeroom_reminder_announcement(newsletter),
            "published": True,
            "delayed_post_at": HOMEROOM_RESEND_AT,
        }
    )

    # 5. Existing subject Weekly Updates updated in place
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        actions.append(_weekly_update_action(subject_key))

    return {
        "title": "Q1W9 WEEKLY PACKAGE MANIFEST",
        "weekCode": "Q1W9",
        "weekRange": "September 14 - September 18, 2026",
        "mode": "approved-production",
        "writes_performed": 0,
        "read_only": False,
        "approval": {"teacherApproved": False, "approvedBy": None, "approvedAt": None},
        "actions": actions,
    }


def write_local_artifacts() -> dict[str, Path]:
    AUDIT.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    manifest = build_manifest()
    manifest_path = AUDIT / "q1w9-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["manifest"] = manifest_path

    pages_dir = AUDIT / "pages"
    pages_dir.mkdir(exist_ok=True)
    for course, spec in PAGE_BUILDERS.items():
        slug = course.lower().replace("/", "-").replace(" ", "-")
        p = pages_dir / f"q1w9-{slug}-page.html"
        p.write_text(spec["builder"](), encoding="utf-8")
        paths[course] = p

    newsletter = build_newsletter()
    newsletter_path = AUDIT / "q1w9-newsletter-week9.html"
    newsletter_path.write_text(newsletter, encoding="utf-8")
    paths["newsletter"] = newsletter_path

    (AUDIT / "q1w9-math-assessment-announcement.html").write_text(
        build_math_assessment_announcement(), encoding="utf-8"
    )
    (AUDIT / "q1w9-history-assessment-announcement.html").write_text(
        build_history_assessment_announcement(), encoding="utf-8"
    )
    (AUDIT / "q1w9-spelling-test-announcement.html").write_text(
        build_spelling_test_announcement(), encoding="utf-8"
    )

    checks = newsletter_checks(newsletter)
    problems = validate_manifest(manifest)
    (AUDIT / "q1w9-newsletter-checks.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    body_sha = hashlib.sha256(" ".join(newsletter.split()).encode("utf-8")).hexdigest()
    (AUDIT / "q1w9-package-checks.json").write_text(
        json.dumps(
            {
                "newsletter_checks": checks,
                "manifest_problems": problems,
                "newsletter_body_sha256": body_sha,
                "newsletter_length": len(newsletter),
                "assignment_count": sum(
                    1 for a in manifest["actions"] if a["object_type"] == "assignment"
                ),
                "announcement_count": sum(
                    1 for a in manifest["actions"] if a["object_type"] == "announcement"
                ),
                "page_count": sum(
                    1 for a in manifest["actions"] if a["object_type"] == "page"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if problems:
        raise SystemExit(
            "MANIFEST VALIDATION FAILED:\n  - " + "\n  - ".join(problems)
        )
    return paths


if __name__ == "__main__":
    out = write_local_artifacts()
    print("Wrote Q1W9 local drafts (preview-only, zero Canvas writes):")
    for key, path in out.items():
        print(f"  {key}: {path}")
