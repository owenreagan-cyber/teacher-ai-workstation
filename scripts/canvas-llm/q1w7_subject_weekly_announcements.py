#!/usr/bin/env python3
"""Q1W7 subject Weekly Update Announcements — draft-only, read-only.

Builds the four subject weekly update announcements for Week 7
(Aug 31 - Sep 4, 2026) using the canonical builder, then runs a fresh GET-only
duplicate check against live announcements. No Canvas writes.

Week in Review prose is based on the Q1W6 live/approved agendas. Week Ahead
prose is based on the Q1W7 final agenda. The embedded agenda is the EXACT
``kl_wrapper_3`` block from the Q1W7 manifest page body (byte-identical to the
live front page). Outputs:

- .local/canvas-llm/q1w7-audit/q1w7-subject-weekly-update-{subject}.html
- .local/canvas-llm/q1w7-audit/q1w7-subject-weekly-update-report.json

The token is never printed.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import subject_weekly_update as swu  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w7-audit"
MANIFEST_PATH = OUT_DIR / "q1w7-manifest.json"

WEEK_MARKER = "August 31\u2013September 4, 2026"

# subject_key -> (manifest course name, prose)
# Week in Review is grounded in the Q1W6 agendas; Week Ahead in Q1W7.
DRAFTS: dict[str, dict[str, Any]] = {
    "math": {
        "course": "Math",
        "week_in_review": (
            "We had another great week in Math! Students completed Lessons 18-20 and "
            "worked hard on Math Test 3 and Fact Assessment 3 on Thursday, then wrapped "
            "up the week with Investigation 2."
        ),
        "week_ahead": "Next week, we will continue with Lessons 21\u201325.",
        "schedule_change": None,
        "curriculum": {
            "verified": ["Saxon Math 5"],
            "source": [
                "config/curriculum/canvas-course-mappings.json (canonicalName)",
                "config/curriculum/math/saxon-math-5/lesson-power-up-map.json (curriculum)",
            ],
            "lesson_numbers_only": True,
            "note": "No per-lesson topic titles are verified in the canonical maps; "
                    "lesson numbers are kept.",
        },
    },
    "reading_spelling": {
        "course": "Reading/Spelling",
        "week_in_review": (
            "In Reading, students completed Lessons 21-24 and worked hard on Reading "
            "Mastery Test 2 on Wednesday while continuing to follow the adventures in "
            "<strong>The Wonderful Wizard of Oz</strong>. In Spelling, students completed "
            "Lessons 18-20 and worked hard on Spelling Test 20 on Friday."
        ),
        "week_ahead": (
            "Next week, we will continue with Reading Lessons 25\u201329 and Spelling "
            "Lessons 21\u201325."
        ),
        "schedule_change": None,
        "curriculum": {
            "verified": ["Reading Mastery 4", "The Wonderful Wizard of Oz", "Spelling 4"],
            "source": [
                "config/curriculum/canvas-course-mappings.json (canonicalName)",
                "config/curriculum/reading/reading-mastery-4/checkout-passage-map.json (Book A passages)",
                "Live 'Reading and Spelling - Week of August 17-21' announcement (The Wonderful Wizard of Oz)",
            ],
            "lesson_numbers_only": True,
            "note": "No per-lesson topic titles are verified; lesson numbers are kept.",
        },
    },
    "language_arts": {
        "course": "Language Arts",
        "week_in_review": (
            "We had a productive week in Language Arts! Students continued working "
            "through Shurley English Chapter 3, completing Lessons 1-3 and Classroom "
            "Practices 13 and 14, and practiced their introduction writing."
        ),
        "week_ahead": (
            "Next week, we will review Chapter 3 and take the <strong>Chapter 3 Shurley "
            "English Test on Tuesday, September 1</strong>. We will then begin our "
            "Personal Narrative writing unit."
        ),
        "schedule_change": None,
        "curriculum": {
            "verified": ["Shurley English 4", "Chapter 3", "Personal Narrative (Unit 1)"],
            "source": [
                "config/curriculum/canvas-course-mappings.json (canonicalName)",
                "Owen's HG translation: Writing, Unit 1: Personal Narrative, Week 1",
                "Live Q1W6 Language Arts agenda (Chapter 3, Classroom Practices 13-14)",
            ],
            "lesson_numbers_only": False,
            "note": "Writing lessons are named (Introductions / Focus on One Event / "
                    "Analyze the Prompt / Brainstorming) per Owen's HG translation.",
        },
    },
    "history": {
        "course": "History",
        "week_in_review": (
            "We had a great week in History! Students continued our World Mountains "
            "unit, completing Mountains Chapters 3 and 4 and reviewing for the test."
        ),
        "week_ahead": (
            "Next week, we will wrap up our World Mountains unit with Mountains Chapter "
            "4 and a review, then take the <strong>World Mountains Test on Wednesday, "
            "September 2</strong>. Students will then begin their Map Project."
        ),
        "schedule_change": (
            "One schedule change to note: our World Mountains Test, originally scheduled "
            "for Friday, August 28, was moved to Wednesday, September 2."
        ),
        "curriculum": {
            "verified": ["History 4", "World Mountains unit", "Mountains Chapters 3\u20134"],
            "source": [
                "config/curriculum/canvas-course-mappings.json (canonicalName)",
                "Canvas History module 'Exploring Maps and World Mountains: World Mountains'",
                "Live Q1W6 History agenda (Mountains Chapters 3-4, World Mountains Test)",
            ],
            "lesson_numbers_only": False,
            "note": "Unit/chapter names are verified from the Canvas module and agendas.",
        },
    },
}


def _get(base_url: str, token: str, path: str) -> Any:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:200]
        except Exception:  # noqa: BLE001
            detail = ""
        return {"__error__": f"HTTP {exc.code}: {detail or exc.reason}"}
    except urllib.error.URLError as exc:
        return {"__error__": f"network: {exc.reason}"}


def _paginate(base_url: str, token: str, path: str) -> list[Any]:
    url = f"{base_url}{path}?only_announcements=true&per_page=100"
    items: list[Any] = []
    for _ in range(20):
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
        data = json.loads(text) if text else []
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
            break
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                s = part.find("<")
                e = part.find(">")
                if 0 <= s < e:
                    nxt = part[s + 1 : e]
        if not nxt:
            break
        url = nxt
    return items


def _page_bodies() -> dict[str, str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    bodies: dict[str, str] = {}
    for action in manifest.get("actions", []):
        if action.get("object_type") == "page" and action.get("course") in {
            "Math", "Reading/Spelling", "Language Arts", "History",
        }:
            bodies[action["course"]] = action.get("body") or ""
    return bodies


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bodies = _page_bodies()
    missing = [c for c in ("Math", "Reading/Spelling", "Language Arts", "History") if c not in bodies]
    if missing:
        print(f"BLOCKED: missing Q1W7 page bodies in manifest for: {missing}")
        return 1

    # Live GET for duplicate detection (read-only).
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    report: dict[str, Any] = {
        "week": "Q1W7",
        "date_range": "August 31\u2013September 4, 2026",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "subjects": {},
    }

    for subject_key, draft in DRAFTS.items():
        course = draft["course"]
        cid = swu.SUBJECTS[subject_key]["course_id"]
        title = swu.SUBJECTS[subject_key]["title"]
        agenda = bodies[course]
        message = swu.build_message(
            subject_key,
            draft["week_in_review"],
            draft["week_ahead"],
            agenda,
            schedule_change=draft["schedule_change"],
        )
        expected_core = swu.agenda_core(agenda)

        slug = subject_key.replace("_", "-")
        html_path = OUT_DIR / f"q1w7-subject-weekly-update-{slug}.html"
        html_path.write_text(message, encoding="utf-8")

        announcements = _paginate(base_url, token, f"/api/v1/courses/{cid}/discussion_topics")
        status, match_id = swu.classify_duplicate(
            announcements, title=title, week_marker=WEEK_MARKER, expected_core=expected_core
        )

        report["subjects"][subject_key] = {
            "course": course,
            "course_id": cid,
            "announcement_title": title,
            "week_in_review": draft["week_in_review"],
            "week_ahead": draft["week_ahead"],
            "schedule_change": draft["schedule_change"],
            "curriculum": draft["curriculum"],
            "duplicate_status": status,
            "existing_announcement_id": match_id,
            "agenda_embedded_bytes": len(expected_core),
            "draft_html": str(html_path),
        }

        print(f"{course}: title={title!r} duplicate={status} "
              f"(match_id={match_id}) agenda_core={len(expected_core)} chars -> {html_path.name}")

    report_path = OUT_DIR / "q1w7-subject-weekly-update-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nreport written: {report_path}")
    print("WRITES PERFORMED: 0 (GET only; drafts are local files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
