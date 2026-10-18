#!/usr/bin/env python3
"""Build Q1W8 subject package drafts (local only — no Canvas writes).

Generates FPK agenda HTML, manifest actions, assessment-reminder drafts, and
subject Weekly Update drafts for Week 8 (September 7–11, 2026).

Outputs under .local/canvas-llm/q1w8-audit/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit"

if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import subject_weekly_update as swu  # noqa: E402

LINK = (
    '<link rel="stylesheet" href="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219636/canvas_global_app.css">'
)
SCRIPT = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

H3_BORDER = "border-width: 0px !important; border-style: none !important; border-color: currentcolor !important;"
DAY_H3 = (
    "color: #ffffff; background-color: #0065a7; margin-top: 15px; margin-bottom: 2px; "
    + H3_BORDER
)
H4 = (
    "color: #ffffff; background-color: #333333; padding-left: 10px; margin: 0px; "
    + H3_BORDER
)
REM_H3 = (
    "background-color: #c51062; color: #ffffff; "
    + H3_BORDER
)
BANNER = (
    '<p style="color: #ffffff; background-color: #0065a7; text-align: center; margin: 0;">'
    '<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
    '<span style="font-size: 10pt;">Quarter 1, Week 8 | September 7–11, 2026</span></p>'
)

PAGE_URL = "q1w8-september-7-11-2026"
PAGE_TITLE = "Q1W8 - September 7–11, 2026"

POWER_UP_C_FILE_ID = 6120836
POWER_UP_C_PREVIEW = (
    "https://thalesacademy.instructure.com/courses/26404"
    f"/files/{POWER_UP_C_FILE_ID}/preview"
)

DUE_TUE = "2026-09-09T03:59:59Z"  # Tue Sep 8, 11:59 PM ET
DUE_THU = "2026-09-11T03:59:59Z"  # Thu Sep 10, 11:59 PM ET

WEEKLY_UPDATE_IDS = {
    "math": "165048",
    "reading_spelling": "165049",
    "language_arts": "165050",
    "history": "165051",
}

WEEKLY_UPDATE_DRAFTS: dict[str, dict[str, str]] = {
    "math": {
        "week_in_review": (
            "We had another great week in Math! Students completed Lessons 21\u201325 "
            "and worked hard throughout the week."
        ),
        "week_ahead": (
            "Next week, students will complete <strong>Written Assessment 4 and Fact "
            "Assessment 4 on Thursday, September 10</strong>. Fact Assessment 4 includes "
            "<strong>40 multiplication facts</strong>. We will review together in class on "
            "Wednesday before completing Lessons 26 and 27."
        ),
    },
    "reading_spelling": {
        "week_in_review": (
            "In Reading, students completed Lessons 25\u201329. In Spelling, students "
            "completed Lessons 21\u201325."
        ),
        "week_ahead": (
            "Next week, students will complete a <strong>Reading Test and Fluency Checkout "
            "on Wednesday, September 9</strong>. The Reading Test will cover vocabulary "
            "and story concepts from Lessons 21\u201330. "
            "Looking ahead, the final Spelling Test of Track 1 will be on "
            "<strong>Wednesday, September 16</strong>."
        ),
    },
    "language_arts": {
        "week_in_review": (
            "We had a productive week in Language Arts! Students completed the "
            "<strong>Chapter 3 Shurley English Test</strong> and began our Personal "
            "Narrative writing unit."
        ),
        "week_ahead": (
            "Next week, we will continue our Personal Narrative writing unit with "
            "Lessons 7\u201310."
        ),
    },
    "history": {
        "week_in_review": (
            "We had a great week in History! Students completed our World Mountains unit, "
            "including the World Mountains Test, and began their Map Project."
        ),
        "week_ahead": (
            "Next week, we will continue with "
            "<strong>Medieval Islamic Kingdoms Chapters 2\u20134</strong>."
        ),
    },
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


def build_math_page() -> str:
    reminders = "<p>Written Assessment 4 and Fact Assessment 4 are on Thursday, September 10.</p>"
    days = (
        _day("kl_activities2", "Monday", ["Labor Day — No School"], full_width=True)
        + _day(
            "kl_custom_block_4",
            "Tuesday",
            ["Lesson 26", "Problems 1-10"],
            at_home=["Lesson 26: Problems 12-30 EVENS"],
        )
        + _day("kl_custom_block_3", "Wednesday", ["Review Sheet"], full_width=True)
        + _day(
            "kl_custom_block_2",
            "Thursday",
            ["Written Assessment 4", "Fact Assessment 4"],
            full_width=True,
        )
        + _day("kl_custom_block_1", "Friday", ["Lesson 27", "Problems 1-10"], full_width=True)
    )
    return _page(reminders, days)


def build_reading_page() -> str:
    reminders = (
        "<p><strong>Reading Test &amp; Fluency Checkout</strong> — Wednesday, September 9</p>"
        "<p>Review vocabulary and story concepts from Lessons 21-30.</p>"
        "<p><strong>Final Track 1 Spelling Test</strong> — Wednesday, September 16</p>"
    )
    days = (
        _day("kl_activities2", "Monday", ["Labor Day — No School"], full_width=True)
        + _day(
            "kl_custom_block_4",
            "Tuesday",
            ["Spelling: Lesson 26", "Reading: Lesson 30", "Workbook"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_3",
            "Wednesday",
            ["Spelling: Lesson 27", "Reading Test", "Fluency Checkout"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_2",
            "Thursday",
            ["Spelling: Lesson 28", "Reading: Lesson 31", "Workbook and Comprehension"],
            full_width=True,
        )
        + _day(
            "kl_custom_block_1",
            "Friday",
            ["Spelling: Lesson 29", "Reading: Lesson 32"],
            full_width=True,
        )
    )
    return _page(reminders, days)


def build_language_arts_page() -> str:
    reminders = "<p>We will continue our Personal Narrative writing unit this week.</p>"
    days = (
        _day("kl_activities2", "Monday", ["Labor Day — No School"], full_width=True)
        + _day("kl_custom_block_4", "Tuesday", ["Personal Narrative Lesson 7"], full_width=True)
        + _day("kl_custom_block_3", "Wednesday", ["Personal Narrative Lesson 8"], full_width=True)
        + _day("kl_custom_block_2", "Thursday", ["Personal Narrative Lesson 9"], full_width=True)
        + _day("kl_custom_block_1", "Friday", ["Personal Narrative Lesson 10"], full_width=True)
    )
    return _page(reminders, days)


def build_history_page() -> str:
    reminders = (
        "<p>We will continue working through Medieval Islamic Kingdoms Chapters 2–4 this week.</p>"
    )
    days = (
        _day("kl_activities2", "Monday", ["Labor Day — No School"], full_width=True)
        + _day("kl_custom_block_4", "Tuesday", ["Medieval Islamic Kingdoms Chapter 2"], full_width=True)
        + _day("kl_custom_block_3", "Wednesday", ["Medieval Islamic Kingdoms Chapter 3"], full_width=True)
        + _day("kl_custom_block_2", "Thursday", ["Medieval Islamic Kingdoms Chapter 4"], full_width=True)
        + _day("kl_custom_block_1", "Friday", ["Medieval Islamic Kingdoms Chapter 4"], full_width=True)
    )
    return _page(reminders, days)


def build_math_assessment_reminder() -> str:
    embed = (
        f'<p style="margin: 14px 0 0;">'
        f'<iframe style="width: 100%; height: 700px; border: 0;" '
        f'src="{POWER_UP_C_PREVIEW}" title="Power Up C practice"></iframe></p>'
    )
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>This is a reminder that students will complete "
        "<strong>Written Assessment 4 and Fact Assessment 4 on Thursday, September 10</strong>.</p>"
        "<p>Fact Assessment 4 will include <strong>40 multiplication facts</strong>.</p>"
        "<p>Students can practice their facts using <strong>Power Up C</strong>. "
        "I have included the practice resource below.</p>"
        f"{embed}"
        "<p>We will also review together in class on Wednesday.</p>"
        "<p>Best,</p><p>Owen Reagan</p>"
        f"{SCRIPT}"
    )


def build_reading_test_reminder() -> str:
    return (
        f"{LINK}"
        "<p>Good afternoon,</p>"
        "<p>This is a reminder that students will complete a "
        "<strong>Reading Test and Fluency Checkout on Wednesday, September 9</strong>.</p>"
        "<p>The Reading Test will cover <strong>vocabulary and story concepts from Lessons 21-30</strong>.</p>"
        "<p><strong>Vocabulary to review:</strong></p>"
        "<ul>"
        "<li>Admitted</li><li>Advance</li><li>Spectacles</li><li>Meek</li>"
        "<li>Seize</li><li>Ventriloquists</li><li>Confidence</li><li>Enormous</li>"
        "</ul>"
        "<p><strong>Students should also know the difference between first-hand and second-hand accounts:</strong></p>"
        "<p><strong>First-Hand Account:</strong> Uses words like “I” and “we.” "
        "It is told by someone who experienced the events.</p>"
        "<p><strong>Second-Hand Account:</strong> Does not use “I” or “we.” "
        "It is told by someone who has information about an event but was not actually there.</p>"
        "<p>Please have your child review these words and concepts before Wednesday.</p>"
        "<p>Best,</p><p>Owen Reagan</p>"
        f"{SCRIPT}"
    )


def build_manifest() -> dict[str, Any]:
    pages = {
        "Math": build_math_page(),
        "Reading/Spelling": build_reading_page(),
        "Language Arts": build_language_arts_page(),
        "History": build_history_page(),
    }
    actions: list[dict[str, Any]] = []
    for course, body in pages.items():
        cid = {
            "Math": 26404,
            "Reading/Spelling": 26442,
            "Language Arts": 28171,
            "History": 28165,
        }[course]
        actions.append(
            {
                "course": course,
                "course_id": cid,
                "object_type": "page",
                "existing": PAGE_URL,
                "action": "UPDATE",
                "resulting_title": PAGE_TITLE,
                "published": True,
                "front_page": "SET_AND_VERIFY",
                "body": body,
            }
        )

    actions.extend(
        [
            {
                "course": "Math",
                "course_id": 26404,
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": "SM5: Lesson 26 Homework",
                "assignment_group": "Homework/Class Work",
                "due_at": DUE_TUE,
                "timing": "Tue Sep 8, 11:59 PM America/New_York",
            },
            {
                "course": "Math",
                "course_id": 26404,
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": "SM5: Written Assessment 4",
                "assignment_group": "Written Assessments",
                "due_at": DUE_THU,
                "timing": "Thu Sep 10, 11:59 PM America/New_York",
            },
            {
                "course": "Math",
                "course_id": 26404,
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": "SM5: Fact Assessment 4",
                "assignment_group": "Fact Assessments",
                "due_at": DUE_THU,
                "timing": "Thu Sep 10, 11:59 PM America/New_York",
            },
            {
                "course": "Reading/Spelling",
                "course_id": 26442,
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": "RM4: Lesson 30 Workbook",
                "assignment_group": "Homework",
                "due_at": DUE_TUE,
                "timing": "Tue Sep 8, 11:59 PM America/New_York",
            },
            {
                "course": "Reading/Spelling",
                "course_id": 26442,
                "object_type": "assignment",
                "action": "CREATE",
                "resulting_title": "RM4: Lesson 31 Workbook and Comprehension",
                "assignment_group": "Homework",
                "due_at": DUE_THU,
                "timing": "Thu Sep 10, 11:59 PM America/New_York",
            },
            {
                "course": "Math",
                "course_id": 26404,
                "object_type": "announcement",
                "action": "CREATE",
                "resulting_title": "Math Assessment Reminder - Thursday",
                "message": build_math_assessment_reminder(),
            },
            {
                "course": "Reading/Spelling",
                "course_id": 26442,
                "object_type": "announcement",
                "action": "CREATE",
                "resulting_title": "Reading Test & Fluency Checkout Reminder - Wednesday",
                "message": build_reading_test_reminder(),
            },
        ]
    )

    course_by_key = {
        "math": "Math",
        "reading_spelling": "Reading/Spelling",
        "language_arts": "Language Arts",
        "history": "History",
    }
    for subject_key, draft in WEEKLY_UPDATE_DRAFTS.items():
        course = course_by_key[subject_key]
        title = swu.SUBJECTS[subject_key]["title"]
        message = swu.build_message(
            subject_key,
            draft["week_in_review"],
            draft["week_ahead"],
            pages[course],
        )
        actions.append(
            {
                "course": course,
                "course_id": swu.SUBJECTS[subject_key]["course_id"],
                "object_type": "announcement",
                "action": "UPDATE",
                "existing": title,
                "existing_id": WEEKLY_UPDATE_IDS[subject_key],
                "resulting_title": title,
                "message": message,
                "published": True,
            }
        )

    return {
        "title": "Q1W8 WEEKLY PACKAGE MANIFEST",
        "weekCode": "Q1W8",
        "weekRange": "September 7 - September 11, 2026",
        "mode": "preview-only",
        "writes_performed": 0,
        "read_only": True,
        "approval": {"teacherApproved": False, "approvedBy": None, "approvedAt": None},
        "actions": actions,
    }


def write_local_artifacts() -> dict[str, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    manifest_path = OUT_DIR / "q1w8-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    paths: dict[str, Path] = {"manifest": manifest_path}
    for action in manifest["actions"]:
        if action.get("object_type") != "page":
            continue
        slug = action["course"].lower().replace("/", "-").replace(" ", "-")
        p = OUT_DIR / f"q1w8-{slug}-page.html"
        p.write_text(action["body"], encoding="utf-8")
        paths[action["course"]] = p

    (OUT_DIR / "q1w8-math-assessment-reminder.html").write_text(
        build_math_assessment_reminder(), encoding="utf-8"
    )
    (OUT_DIR / "q1w8-reading-test-reminder.html").write_text(
        build_reading_test_reminder(), encoding="utf-8"
    )
    return paths


if __name__ == "__main__":
    paths = write_local_artifacts()
    print("Wrote Q1W8 local drafts:")
    for k, v in paths.items():
        print(f"  {k}: {v}")
