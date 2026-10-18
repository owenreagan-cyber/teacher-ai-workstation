#!/usr/bin/env python3
"""Q1W5 corrective deployment preflight — READ-ONLY preview (zero Canvas writes).

Fresh GET-only Canvas preflight + final proposed action list. Does NOT
POST/PUT/PATCH/DELETE, publish, unpublish, create, update, or schedule.

Environment (for a FRESH live GET): CANVAS_TOKEN and CANVAS_BASE_URL must be
exported in the terminal session. Without them, the run is OFFLINE and uses
the most recent read-only audit snapshot (still zero writes).

Usage:
    cd /Users/owen/Projects/teacher-ai-workstation
    python3 scripts/canvas-llm/q1w5_corrective_preflight.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AUDIT_SNAPSHOT = REPO_ROOT / ".local" / "canvas-llm" / "q1w5-audit" / "q1w5-live-audit.json"
AUDIT_MODULE = REPO_ROOT / "scripts" / "canvas-llm" / "q1w5_live_audit.py"

# ---- Corrected action list (single source of truth) ----
MANIFEST: list[dict[str, Any]] = [
    # ----- Math (26404) -----
    {"course": "Math", "course_id": 26404, "object_type": "page",
     "existing": "q1w5-august-17-21-2026", "existing_id": None,
     "action": "LEAVE", "resulting_title": "Q1W5 - August 17–21, 2026", "timing": "",
     "reason": "KL HTML + no-homework-day layout already correct"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Math Test 2", "existing_id": 1027216,
     "action": "UPDATE", "resulting_title": "SM5: Written Assessment 2",
     "timing": "Thu Aug 20, 11:59 PM America/New_York",
     "reason": "Non-canonical title; must use SM5: Written Assessment {n}"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Fact Assessment 2", "existing_id": 1027217,
     "action": "LEAVE", "resulting_title": "SM5: Fact Assessment 2",
     "timing": "Thu Aug 20, 11:59 PM America/New_York",
     "reason": "Canonical title + date already correct"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Lesson 14", "existing_id": 1027212,
     "action": "UPDATE", "resulting_title": "SM5: Lesson 14 Homework",
     "timing": "Mon Aug 17, 11:59 PM America/New_York",
     "reason": "Monday homework = accuracy grade #1; canonical SM5: Lesson N Homework"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Lesson 15", "existing_id": 1027213,
     "action": "UPDATE", "resulting_title": "SM5: Lesson 15",
     "timing": "Tue Aug 18, 11:59 PM America/New_York",
     "reason": "Tuesday classwork accuracy grade; set omit_from_final_grade=false (title and due date unchanged)"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Lesson 16", "existing_id": 1027214,
     "action": "UPDATE", "resulting_title": "SM5: Lesson 16 Homework",
     "timing": "Wed Aug 19, 11:59 PM America/New_York",
     "reason": "Wednesday homework = accuracy grade #2; canonical SM5: Lesson N Homework"},
    {"course": "Math", "course_id": 26404, "object_type": "assignment",
     "existing": "SM5: Lesson 17", "existing_id": 1027215,
     "action": "REMOVE", "resulting_title": "(removed)", "timing": "",
     "reason": "Friday has no homework and is not this week's selected classwork accuracy grade"},
    {"course": "Math", "course_id": 26404, "object_type": "announcement",
     "existing": "Reminder - Math Test 2 and Fact Assessment 2 Tomorrow", "existing_id": 164186,
     "action": "UPDATE", "resulting_title": "Reminder - Math Test 2 and Fact Assessment 2 Tomorrow",
     "timing": "scheduled Wed Aug 19, 4:00 PM America/New_York (1 day before)",
     "reason": "Say 40 addition facts in 2 minutes; remove any in-class review mention; professional parent-email style"},
    {"course": "Math", "course_id": 26404, "object_type": "announcement",
     "existing": "Math Test 2 and Fact Assessment 2 - Thursday, August 20", "existing_id": 164175,
     "action": "REMOVE", "resulting_title": "(removed)", "timing": "",
     "reason": "Claims an in-class review on Wednesday; no in-class review exists in pacing"},
    {"course": "Math", "course_id": 26404, "object_type": "announcement",
     "existing": "Math - Week of August 17-21", "existing_id": 164181,
     "action": "LEAVE", "resulting_title": "Math - Week of August 17-21", "timing": "",
     "reason": "Weekly recap correct"},
    # ----- Reading / Spelling (26442) -----
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "page",
     "existing": "q1w5-august-17-21-2026", "existing_id": None,
     "action": "LEAVE", "resulting_title": "Q1W5 - August 17–21, 2026", "timing": "",
     "reason": "Content matches approved pacing (Tue/Thu comprehension; Wed spelling test)"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "assignment",
     "existing": "RM4: Lesson 16 Workbook", "existing_id": 1027218,
     "action": "LEAVE", "resulting_title": "RM4: Lesson 16 Workbook",
     "timing": "Mon Aug 17, 11:59 PM America/New_York",
     "reason": "Monday workbook classwork = Reading accuracy grade #3"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "assignment",
     "existing": "RM4: Lesson 17 Workbook", "existing_id": 1027219,
     "action": "LEAVE", "resulting_title": "RM4: Lesson 17 Workbook",
     "timing": "Tue Aug 18, 11:59 PM America/New_York",
     "reason": "Tuesday comprehension homework = Reading accuracy grade #1"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "assignment",
     "existing": "RM4: Lesson 18 Workbook", "existing_id": 1027220,
     "action": "REMOVE", "resulting_title": "(removed)", "timing": "",
     "reason": "Wednesday is not one of this week's selected Reading accuracy grades"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "assignment",
     "existing": "RM4: Lesson 19 Workbook", "existing_id": 1027221,
     "action": "LEAVE", "resulting_title": "RM4: Lesson 19 Workbook",
     "timing": "Thu Aug 20, 11:59 PM America/New_York",
     "reason": "Thursday comprehension homework = Reading accuracy grade #2"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "assignment",
     "existing": None, "existing_id": None,
     "action": "CREATE", "resulting_title": "RM4: Spelling Test 15",
     "timing": "Wed Aug 19, 11:59 PM America/New_York",
     "reason": "Missing; canonical requires RM4: Spelling Test 15 for Wed Aug 19"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "announcement",
     "existing": "Reminder - Spelling Test 15 Tomorrow", "existing_id": 164187,
     "action": "LEAVE", "resulting_title": "Reminder - Spelling Test 15 Tomorrow",
     "timing": "scheduled Tue Aug 18, 4:00 PM America/New_York",
     "reason": "Scheduled 'Tomorrow' reminder correct and non-duplicated"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "announcement",
     "existing": "Spelling Test 15 - Wednesday, August 19", "existing_id": 164177,
     "action": "REMOVE", "resulting_title": "(removed)", "timing": "",
     "reason": "Redundant with weekly announcement + scheduled Tomorrow reminder"},
    {"course": "Reading/Spelling", "course_id": 26442, "object_type": "announcement",
     "existing": "Reading and Spelling - Week of August 17-21", "existing_id": 164182,
     "action": "LEAVE", "resulting_title": "Reading and Spelling - Week of August 17-21", "timing": "",
     "reason": "Weekly course announcement retained"},
    # ----- Language Arts (26495) -----
    {"course": "Language Arts", "course_id": 26495, "object_type": "page",
     "existing": "q1w5-august-17-21-2026", "existing_id": None,
     "action": "UPDATE", "resulting_title": "q1w5-august-17-21-2026",
     "timing": "(publish deferred to final write phase)",
     "reason": "Update-in-place only; preserve KL HTML + exact Shurley shorthand; no At Home on no-homework days",
     "content": ["Monday: CP8 / 2.7", "Tuesday: 2.7/CP 10", "Wednesday: Ch2 L 8",
                 "Thursday: Ch2 L9", "Friday: Ch.2 Test"]},
    {"course": "Language Arts", "course_id": 26495, "object_type": "assignment",
     "existing": None, "existing_id": None,
     "action": "CREATE", "resulting_title": "ELA4: Chapter 2 Test",
     "timing": "Fri Aug 21, 11:59 PM America/New_York",
     "reason": "Chapter 2 Test missing; canonical ELA4 prefix"},
    {"course": "Language Arts", "course_id": 26495, "object_type": "announcement",
     "existing": None, "existing_id": None,
     "action": "CREATE", "resulting_title": "Reminder - Chapter 2 Test Tomorrow",
     "timing": "scheduled Thu Aug 20, 4:00 PM America/New_York (1 day before)",
     "reason": "Supported Chapter 2 Test reminder; professional parent-email style"},
    # ----- History (26493) -----
    {"course": "History", "course_id": 26493, "object_type": "page",
     "existing": "q1w5-august-17-21-2026", "existing_id": None,
     "action": "UPDATE", "resulting_title": "q1w5-august-17-21-2026",
     "timing": "(publish deferred to final write phase)",
     "reason": "Update-in-place only; exact MTS shorthand; omit At Home when blank; remove unverified Aug 28 test reminder; preserve KL HTML",
     "content": ["Monday: MTS Ch1", "Tuesday: MTS Ch1", "Wednesday: MTS Ch2",
                 "Thursday: MTS Ch2", "Friday: MTS Ch 3"]},
    # ----- Science (26496) -----
    {"course": "Science", "course_id": 26496, "object_type": "course",
     "existing": "Science - 4th Grade", "existing_id": None,
     "action": "LEAVE", "resulting_title": "(untouched)", "timing": "",
     "reason": "Inactive quarter; leave completely untouched"},
    # ----- Homeroom (26427) -----
    {"course": "Homeroom", "course_id": 26427, "object_type": "course",
     "existing": "Homeroom - 4th Grade", "existing_id": None,
     "action": "LEAVE", "resulting_title": "(reported, not modified)", "timing": "",
     "reason": "Report only; do not modify yet"},
]


def _items(snapshot: dict[str, Any], course_id: int, object_type: str) -> list[dict[str, Any]]:
    entry = snapshot.get("courses", {}).get(str(course_id), {})
    if object_type == "assignment":
        return entry.get("assignments", [])
    if object_type == "announcement":
        return entry.get("announcements", [])
    return entry.get("pages", [])


def _match_key(obj: dict[str, Any], object_type: str) -> str:
    if object_type == "assignment":
        return obj.get("name") or ""
    if object_type == "announcement":
        return obj.get("title") or ""
    return (obj.get("url") or obj.get("title") or "")


def _find_existing(snapshot: dict[str, Any], action: dict[str, Any]) -> list[dict[str, Any]]:
    items = _items(snapshot, action["course_id"], action["object_type"])
    eid = action.get("existing_id")
    existing = action.get("existing")
    out: list[dict[str, Any]] = []
    for obj in items:
        if eid is not None and obj.get("id") == eid:
            out.append(obj)
        elif eid is None and existing and _match_key(obj, action["object_type"]) == existing:
            out.append(obj)
    return out


def _duplicate_check(snapshot: dict[str, Any], action: dict[str, Any]) -> str:
    """Duplicate-safety verdict for CREATE actions against the (fresh) snapshot."""
    items = _items(snapshot, action["course_id"], action["object_type"])
    title = action["resulting_title"]
    matches = [o for o in items if _match_key(o, action["object_type"]) == title]
    if not matches:
        return "CREATE (0 matches)"
    if len(matches) == 1:
        return f"REUSE/UPDATE (1 match: id={matches[0].get('id')})"
    return "BLOCK (multiple matches)"


def _load_fresh() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("q1w5_live_audit", str(AUDIT_MODULE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    report: dict[str, Any] = {"courses": {}}
    for subject, cid in mod.COURSES.items():
        report["courses"][str(cid)] = mod.audit_course(subject, cid)
    return report


def load_snapshot() -> tuple[dict[str, Any], bool]:
    token = os.environ.get("CANVAS_TOKEN", "").strip()
    base = os.environ.get("CANVAS_BASE_URL", "").strip()
    if token and base:
        return _load_fresh(), True
    return json.loads(AUDIT_SNAPSHOT.read_text()), False


def main() -> int:
    snapshot: dict[str, Any]
    fresh: bool
    try:
        snapshot, fresh = load_snapshot()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: preflight could not load Canvas state: {exc}")
        return 1

    print("Q1W5 CORRECTIVE DEPLOYMENT PREVIEW")
    print()
    if fresh:
        print("Mode: FRESH LIVE GET (read-only; zero writes)")
    else:
        print("Mode: OFFLINE (using existing read-only audit snapshot; no fresh GET —")
        print("CANVAS_TOKEN/CANVAS_BASE_URL not set in this shell)")
    gen = snapshot.get("generated_at_utc", "unknown")
    print(f"Snapshot generated_at_utc: {gen}")
    print()

    for a in MANIFEST:
        line = (
            f"{a['course']} | {a['object_type']} | "
            f"existing={a['existing'] or a['existing_id'] or '-'} | "
            f"action={a['action']} | -> {a['resulting_title']} | "
            f"{a['timing'] or '-'}"
        )
        print(line)
        print(f"    reason: {a['reason']}")
        if a.get("content"):
            print("    page content:")
            for row in a["content"]:
                print(f"      - {row}")

    print()
    print("Duplicate safety (CREATE candidates searched against live/snapshot state):")
    for a in MANIFEST:
        if a["action"] != "CREATE":
            continue
        print(f"  {a['course']} | {a['object_type']} | {a['resulting_title']} "
              f"=> {_duplicate_check(snapshot, a)}")
        if a["object_type"] == "assignment" and a["timing"]:
            print(f"      due: {a['timing']}")

    print()
    print("WRITES PERFORMED: 0")
    print()
    print("Preview only. No POST/PUT/PATCH/DELETE, publish, unpublish, create,")
    print("update, or schedule action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
