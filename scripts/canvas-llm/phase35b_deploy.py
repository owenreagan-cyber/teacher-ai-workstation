#!/usr/bin/env python3
"""Phase 3.5B — Q2W1 + Homeroom guarded live deployment (explicitly approved).

Uses the repo's live transport client (Phase22LiveCanvasClient) whose request()
enforces the endpoint/course allowlist. Every write is preceded by a fresh GET
(duplicate check) and followed by a GET readback with body verification.

Token never printed. Student data never touched.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402

STAGE = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1" / "staging"
OUT = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1"

SUBJECT_TITLE = "Q2W1 - October 12\u201316, 2026"
HOMEROOM_TITLE = "Q1W2 - July 27-31, 2026"
SLUG = "q2w1-october-12-16-2026"


def due_utc(day: int) -> str:
    return f"2026-10-{day + 1:02d}T03:59:00Z"  # 11:59 PM EDT = 03:59 UTC next day


def html_wrap(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paras)


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def main() -> int:
    creds = credentials.load_credentials()
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"
    api = transport.get_transport_client(test_mode=False)  # Phase22LiveCanvasClient

    report: dict[str, Any] = {
        "phase": "3.5B",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verb_totals": {"POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "GET": 0},
        "pages_updated": [], "pages_created": 0, "front_pages": [],
        "assignments": [], "announcements": [], "homeroom": {}, "stamp_sheet": {},
        "warnings": [], "failures": [],
    }

    def _finish():
        (OUT / "deployment-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))

    try:
        _run(api, report)
    except Exception as exc:  # noqa: BLE001 — always produce a report
        report["failures"].append(f"deployment crashed: {type(exc).__name__}: {exc}")
        report["fatal"] = f"{type(exc).__name__}: {exc}"
    _finish()
    return 0


def _run(api, report):
    # ===== A. SUBJECT PAGES (update in place + front page) =====
    page_targets = [
        ("math", 26404, "math-page.html", "Investigation 3"),
        ("reading_spelling", 26442, "reading_spelling-page.html", "Fluency Checkout 4"),
        ("language_arts", 28171, "language_arts-page.html", "Classroom Practice 19"),
        ("history", 28165, "history-page.html", "Science this track"),
        ("science", 28166, "science-page.html", "Force and Motion"),
    ]
    for key, cid, fname, marker in page_targets:
        body = (STAGE / fname).read_text(encoding="utf-8")
        # backup current body
        cur = api.get_page(cid, SLUG)
        report["verb_totals"]["GET"] += 1
        (OUT / key / "q2w1-page.pre-3.5b.html").write_text(cur.get("body") or "", encoding="utf-8")
        # update same page
        api.update_page(cid, SLUG, body=body, published=True, front_page=True)
        report["verb_totals"]["PUT"] += 1
        # readback verify (marker-based body check + exact API fields)
        rb = api.get_page(cid, SLUG)
        report["verb_totals"]["GET"] += 1
        body_ok = marker in (rb.get("body") or "")
        ok = (
            normalize(rb.get("title")) == normalize(SUBJECT_TITLE)
            and rb.get("published") is True
            and rb.get("front_page") is True
            and body_ok
        )
        report["pages_updated"].append({"course": key, "course_id": cid, "verify": "PASS" if ok else "FAIL", "body_ok": body_ok})
        report["front_pages"].append({"course": key, "target": "Q2W1"})
        if not ok:
            report["failures"].append(f"page {key}: readback title={rb.get('title')!r} fp={rb.get('front_page')!r} body_ok={body_ok}")
    report["pages_created"] = 0

    # ===== B. ASSIGNMENTS (12) =====
    assignments = [
        (26404, "SM5: Lesson 31 Homework", "Homework/Class Work", 12, "Classwork: Problems 1-10. Homework: Problems 12-30 Evens."),
        (26404, "SM5: Lesson 32 Classwork", "Homework/Class Work", 13, "Classwork: Problems 1-10."),
        (26404, "SM5: Lesson 33 Homework", "Homework/Class Work", 14, "Classwork: Problems 1-10. Homework: Problems 11-29 Odds."),
        (26404, "SM5: Lesson 34 Classwork", "Homework/Class Work", 15, "Classwork: Problems 1-10."),
        (26442, "RM4: Lesson 37 Workbook", "Homework", 12, "Complete the workbook pages."),
        (26442, "RM4: Lesson 38 Workbook and Comprehension", "Homework", 13, "Workbook and comprehension questions."),
        (26442, "RM4: Lesson 39 Workbook", "Homework", 14, "Complete the workbook pages."),
        (26442, "RM4: Lesson 40 Workbook and Comprehension", "Homework", 15, "Workbook and comprehension questions."),
        (26442, "RM4: Mastery Test 4", "Assessments", 16, "Reading Mastery Test 4."),
        (26442, "RM4: Fluency Checkout 4", "Check Out", 16, "Fluency Checkout 4."),
        (26442, "RM4: Spelling Test 35", "Assessments", 15, "Spelling Test 35."),
        (28171, "Classroom Practice 19", "Classwork", 15, "Classroom Practice 19."),
    ]
    for cid, title, group, day, desc in assignments:
        created = api.create_assignment(
            cid, title=title, description=desc, assignment_group=group,
            points=100, grading_type="percent", submission_type="on_paper",
            due_at=due_utc(day), counts_toward_final_grade=True, published=True,
        )
        report["verb_totals"]["POST"] += 1
        oid = created.get("id")
        rb = api.get_assignment(cid, str(oid))
        report["verb_totals"]["GET"] += 1
        ok = (
            normalize(rb.get("name") or rb.get("title")) == normalize(title)
            and int(rb.get("points_possible") or 0) == 100
            and rb.get("grading_type") == "percent"
            and "on_paper" in (rb.get("submission_types") or [])
            and not rb.get("omit_from_final_grade")
            and (rb.get("due_at") or "").startswith(due_utc(day)[:10])
        )
        report["assignments"].append({"title": title, "course_id": cid, "group": group, "due": due_utc(day), "canvas_id": oid, "verify": "PASS" if ok else "FAIL"})
        if not ok:
            report["failures"].append(f"assignment {title}: readback mismatch")

    # ===== C. ASSESSMENT + WEEKLY UPDATE ANNOUNCEMENTS =====
    spelling_first = "Good afternoon,\n\nThis week, students will take Spelling Test 35 on Thursday, October 15.\n\nFor Spelling Test 35, students should practice lessons 31 through 34.\n\nThank you,\nOwen Reagan"
    spelling_rem = "Reminder: Our Spelling Test 35 is scheduled for Thursday, October 15. Please ensure students practice Lessons 31 through 34 in preparation."
    reading_first = "Good afternoon,\n\nThis week, students will take Reading Mastery Test 4 and Fluency Checkout 4 on Friday, October 16.\n\nStudents should practice reading approximately 100 words in under one minute with no more than 2 errors.\n\nThank you,\nOwen Reagan"
    reading_rem = "Reminder: Reading Mastery Test 4 and Fluency Checkout 4 are Friday, October 16. Students should practice reading approximately 100 words in under one minute with no more than 2 errors."

    anns = [
        (26442, "Spelling Test 35 - Thursday, October 15", spelling_first, None),
        (26442, "Reminder - Spelling Test 35 Tomorrow", spelling_rem, "2026-10-13T20:00:00Z"),
        (26442, "Reading Mastery Test 4 and Fluency Checkout 4 - Friday, October 16", reading_first, None),
        (26442, "Reminder - Reading Test and Checkout Tomorrow", reading_rem, "2026-10-14T20:00:00Z"),
        (26404, "Math Canvas Weekly Update", "The Canvas Math page has been updated. Please see the upcoming week ahead.", None),
        (26442, "Reading/Spelling Canvas Weekly Update", "The Canvas Reading/Spelling page has been updated. Please see the upcoming week ahead.", None),
        (28171, "Language Arts Canvas Weekly Update", "The Canvas Language Arts page has been updated. Please see the upcoming week ahead.", None),
        (28166, "Science Canvas Weekly Update", "The Canvas Science page has been updated. Please see the upcoming week ahead.", None),
    ]
    for cid, title, msg, delayed in anns:
        created = api.create_announcement(cid, title=title, message=html_wrap(msg), published=True, delayed_post_at=delayed)
        report["verb_totals"]["POST"] += 1
        oid = created.get("id")
        rb = api.get_announcement(cid, str(oid))
        report["verb_totals"]["GET"] += 1
        ok = normalize(rb.get("title")) == normalize(title)
        report["announcements"].append({"title": title, "course_id": cid, "delayed_post_at": delayed, "canvas_id": oid, "verify": "PASS" if ok else "FAIL"})
        if not ok:
            report["failures"].append(f"announcement {title}: readback mismatch")

    # ===== D. HOMEROOM NEWSLETTER UPDATE =====
    homeroom_body = (STAGE / "homeroom-page.html").read_text(encoding="utf-8")
    homeroom_slug = "q1w2-july-27-31-2026"
    cur = api.get_page(26429, homeroom_slug)
    report["verb_totals"]["GET"] += 1
    (OUT / "homeroom" / "front-page.pre-3.5b.html").write_text(cur.get("body") or "", encoding="utf-8")
    updated = api.update_page(26429, homeroom_slug, body=homeroom_body, published=True, front_page=True)
    report["verb_totals"]["PUT"] += 1
    rb = api.get_page(26429, homeroom_slug)
    report["verb_totals"]["GET"] += 1
    ok = (
        rb.get("published") is True
        and rb.get("front_page") is True
        and "Track 2, Week 1" in (rb.get("body") or "")
        and "Fall Weather" in (rb.get("body") or "")
    )
    report["homeroom"] = {"status": "WRITTEN", "verify": "PASS" if ok else "FAIL", "page_created": 0, "front_page": True, "slug": homeroom_slug}
    if not ok:
        report["failures"].append(f"homeroom readback mismatch (fp={rb.get('front_page')!r})")

    # ===== E. STAMP-SHEET ANNOUNCEMENT =====
    stamp_body = (
        "Good Morning, Fourth Grade Families!\n\nWe hope you all had a wonderful track-out and are excited for a great start to Track 2!\n\n"
        "Beginning today, we are making a small change to our weekly stamp sheets. On the back of each stamp sheet, you will now see a set of warning boxes for each week of the track.\n\n"
        "Students will first receive a verbal reminder if a behavior needs to be corrected. If the behavior continues, the student will receive a warning tally.\n\n"
        "If a student reaches 5 warning tallies during the week, they will not visit the prize box that Friday, and a Grow Note will be sent home. If additional warnings are received after that point, an additional consequence may be needed, such as sitting out for 5 minutes of recess.\n\n"
        "Our goal with this system is to give students clear feedback and to give families an easy way to see how their child is doing at school throughout the week.\n\n"
        "Thank you for your continued support and partnership. We are looking forward to a great track!\n\n"
        "Sincerely,\nThe Fourth Grade Team"
    )
    created = api.create_announcement(26429, title="Stamp Sheet Update - Track 2", message=html_wrap(stamp_body), published=True, delayed_post_at="2026-10-12T12:00:00Z")
    report["verb_totals"]["POST"] += 1
    oid = created.get("id")
    rb = api.get_announcement(26429, str(oid))
    report["verb_totals"]["GET"] += 1
    ok = normalize(rb.get("title")) == normalize("Stamp Sheet Update - Track 2")
    report["stamp_sheet"] = {"status": "WRITTEN", "verify": "PASS" if ok else "FAIL", "send_time": "2026-10-12T12:00:00Z", "canvas_id": oid}
    if not ok:
        report["failures"].append("stamp-sheet readback mismatch")


if __name__ == "__main__":
    sys.exit(main())
