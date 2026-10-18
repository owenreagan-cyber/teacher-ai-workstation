#!/usr/bin/env python3
"""Phase 3.5A — assemble the Q2W1 final approval packet (read-only).

Reads the fresh live-readiness report, the deterministic translation reports,
and the announcement facts, then emits the complete Q2W1 approval packet with
unique approval IDs, LATE_WINDOW-aware scheduling, and the front-page plan.

Zero Canvas writes. No mutation.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_phase3 import pacing_announcement as pa

BACKUP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1"
PREVIEW_DIR = C.PHASE3_PREVIEW_DIR

TODAY = date(2026, 10, 11)  # Q2W1 begins Monday Oct 12; today is Sunday Oct 11.


def late_window(assessment_iso: str, lead_days: int) -> dict[str, Any]:
    """Compute a notice date; flag LATE_WINDOW if it has already passed."""
    a = date.fromisoformat(assessment_iso)
    target = a - timedelta(days=lead_days)
    while target.weekday() >= 5:
        target -= timedelta(days=1)
    late = target < TODAY
    return {
        "assessment_date": assessment_iso,
        "lead_days": lead_days,
        "computed_date": target.isoformat(),
        "status": "LATE_WINDOW" if late else "ON_SCHEDULE",
        "proposed_post_approval": "send ASAP after deployment (Monday Oct 12)" if late else target.isoformat(),
    }


def main() -> int:
    week = pe.extract_week_json("Q2W1", fresh=False)
    readiness = json.loads((BACKUP_DIR / "readiness-report.json").read_text(encoding="utf-8"))

    # Translation reports.
    math = pm.translate_math_week(week)
    rs = prd.translate_reading_spelling_week(week)
    la = pt.translate_subject_week(week, "language_arts")
    sci = pt.translate_subject_week(week, "science")
    hist = pt.translate_subject_week(week, "history")

    # Announcement facts (deterministic).
    events = pa.resolve_assessment_facts(week)

    # Announcement schedule with LATE_WINDOW.
    announcements: list[dict[str, Any]] = []
    for e in events:
        for notice_type, lead in (("FIRST_NOTICE", 5), ("REMINDER", 2)):
            sched = late_window(e["assessmentDate"], lead)
            announcements.append({
                "approval_id": pa.announcement_identity(
                    e["course"], e["family"], pa.source_event_label(e), e["assessmentDate"], notice_type,
                ),
                "family": e["family"],
                "course": e["course"],
                "notice_type": notice_type,
                "assessment_date": e["assessmentDate"],
                "assessments": [a for a in (e.get("assessments") or []) if a],
                **sched,
            })

    # Assignment inventory (from translation engines).
    assignments: list[dict[str, Any]] = []
    assignments.extend(math["assignments"])
    assignments.extend(rs["reading"]["assignments"])
    assignments.extend(rs["spelling"]["assignments"])
    assignments.extend(la["assignments"])
    # Science + History: 0 assignments (per policy).

    assignment_rows = []
    for a in assignments:
        assignment_rows.append({
            "title": a.get("title"),
            "group": a.get("assignment_group"),
            "kind": a.get("kind"),
            "due_date": a.get("due_date"),
            "points": a.get("points_possible"),
            "grading": a.get("grading_type"),
            "submission": a.get("submission_types"),
            "authority": a.get("authority"),
            "course": a.get("course") or a.get("courseName"),
        })

    # Front-page plan from readiness report.
    course_map = {r["key"]: r for r in readiness["targets"]}
    front_plan = []
    for key, name in (("math", "Math"), ("reading_spelling", "Reading/Spelling"),
                      ("language_arts", "Language Arts"), ("history", "History"), ("science", "Science")):
        r = course_map[key]
        front_plan.append({
            "course": name,
            "existing_q2w1_page": r["page_title"],
            "current_front_page": r["front_page_title"],
            "target_front_page": "Q2W1 - October 12\u201316, 2026",
            "action": "set front page after body update + verify",
        })

    packet = {
        "packet_id": "Q2W1-FINAL-APPROVAL-PACKET",
        "title": "Q2W1 \u2014 FINAL CANVAS APPROVAL PACKET",
        "subtitle": "OCTOBER 12\u201316, 2026",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "3.5A",
        "deployment_status": "READY_FOR_OWEN_APPROVAL",
        "A_pages_to_update": [
            {"approval_id": "PAGE-MATH-Q2W1", "course": "Math", "course_id": 26404, "page": "q2w1-october-12-16-2026"},
            {"approval_id": "PAGE-READING-Q2W1", "course": "Reading/Spelling", "course_id": 26442, "page": "q2w1-october-12-16-2026"},
            {"approval_id": "PAGE-LA-Q2W1", "course": "Language Arts", "course_id": 28171, "page": "q2w1-october-12-16-2026"},
            {"approval_id": "PAGE-SCIENCE-Q2W1", "course": "Science", "course_id": 28166, "page": "q2w1-october-12-16-2026"},
            {"approval_id": "PAGE-HISTORY-Q2W1", "course": "History", "course_id": 28165, "page": "q2w1-october-12-16-2026", "mode": "redirect-only"},
        ],
        "B_front_page_changes": front_plan,
        "C_assignments_to_create": assignment_rows,
        "D_assignments_already_present": [
            c for c in readiness["assignment_classification"] if c["classification"] == "EXACT_MATCH_EXISTS"
        ],
        "E_announcements": announcements,
        "F_final_announcement_wording": _announcement_wording(events),
        "G_weekly_updates": [
            {"course": "Math", "action": "send ASAP after page + front-page verification", "weekly_update": "Math Canvas Weekly Update"},
            {"course": "Reading/Spelling", "action": "send ASAP after page + front-page verification", "weekly_update": "Reading/Spelling Canvas Weekly Update"},
            {"course": "Language Arts", "action": "send ASAP after page + front-page verification", "weekly_update": "Language Arts Canvas Weekly Update"},
            {"course": "Science", "action": "send ASAP after page + front-page verification", "weekly_update": "Science Canvas Weekly Update"},
            {"course": "History", "action": "none (inactive Q2; redirect-only)"},
        ],
        "H_warnings": _warnings(readiness, sci),
        "I_blockers": [],
        "J_pages_to_create": 0,
        "weekly_pages_to_create": 0,
        "mastery_tracker": "handoff preserved in config/curriculum/canvas/mastery-tracker-policy-2026-2027.json (NOT built)",
    }

    out = BACKUP_DIR / "approval-packet.json"
    out.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


def _announcement_wording(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for e in events:
        for notice_type in ("FIRST_NOTICE", "REMINDER"):
            fp = {
                "course": e["course"], "assessmentDate": e["assessmentDate"],
                "assessments": [a for a in (e.get("assessments") or []) if a],
                "preparation": e.get("preparation"), "facts": e.get("facts"),
            }
            draft = pa.draft_announcement(fp, notice_type, use_llm=False)
            out.append({"family": e["family"], "notice_type": notice_type, "wording": draft["wording"], "facts": draft["facts"]})
    return out


def _warnings(readiness: dict[str, Any], sci: dict[str, Any]) -> list[str]:
    warnings = []
    for r in readiness["targets"]:
        if not r["page_exists"]:
            warnings.append(f"{r['course']}: Q2W1 page not found")
        if not r["unique"]:
            warnings.append(f"{r['course']}: Q2W1 page duplicated ({r['duplicate_count']})")
        if not r["in_agenda_module"]:
            warnings.append(f"{r['course']}: Q2W1 page not in '2026-2027 Agenda Pages' module")
    if sci.get("unresolved"):
        warnings.append(f"Science unresolved tokens: {sci['unresolved']}")
    warnings.append("First notices for both assessments are LATE_WINDOW (window passed); propose ASAP post-approval send.")
    warnings.append("Q2W1 pages currently contain a blank/seed placeholder body; must be updated in Phase 3.5B.")
    return warnings


if __name__ == "__main__":
    raise SystemExit(main())
