#!/usr/bin/env python3
"""Phase 3.4 — Shurley completion + History/Science shared engine + Q2W1 tests.

Deterministic, offline, zero Canvas writes. Exercises the resolved owner
decisions (Spelling course 26442, Math classwork title, shared Reading/Spelling
page), the completed Shurley token vocabulary, the shared History/Science
unit-chapter-activity engine, Q2 History redirect, and the fail-closed Science
assignment/announcement policy.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_announcement as pa
from scripts.canvas_llm_phase3 import pacing_pages as pp
from scripts.canvas_llm_phase3 import canvas_preview as cp
from scripts.canvas_llm_phase3 import week_workflow as ww


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def q2w1_week() -> dict:
    return {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "unitContext": {"science": "Force and Motion"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {
                "math": {"raw": "L31"}, "reading": {"raw": "L37"}, "spelling": {"raw": "32"},
                "language_arts": {"raw": "5.1"}, "science": {"raw": "Ch. 1"}, "history": {"raw": ""}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {
                "math": {"raw": "L32"}, "reading": {"raw": "L38"}, "spelling": {"raw": "33"},
                "language_arts": {"raw": "5.1"}, "science": {"raw": "Ch. 1"}, "history": {"raw": ""}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {
                "math": {"raw": "L33"}, "reading": {"raw": "L39"}, "spelling": {"raw": "34"},
                "language_arts": {"raw": "5.2"}, "science": {"raw": "Ch. 2"}, "history": {"raw": ""}}},
            "Thursday": {"date": "2026-10-15", "subjects": {
                "math": {"raw": "L34"}, "reading": {"raw": "L40"}, "spelling": {"raw": "Test"},
                "language_arts": {"raw": "5.2, CP19"}, "science": {"raw": "Ch. 2 Check"}, "history": {"raw": ""}}},
            "Friday": {"date": "2026-10-16", "subjects": {
                "math": {"raw": "INV 3"}, "reading": {"raw": "RMT+FCO"}, "spelling": {"raw": "review"},
                "language_arts": {"raw": "5.3"}, "science": {"raw": "Ch. 1-2 Review"}, "history": {"raw": ""}}},
        },
    }


def main() -> int:
    config = pt.load_config()

    # --- Resolved owner decisions ---
    # Spelling assignment course = 26442 (not 28171).
    sp = prd.spelling_assignment(35, "2026-10-15")
    check("Spelling assignment course = 26442", sp["course"] == 26442)
    check("Spelling may not route to 28171", sp["course"] != 28171)

    # Math classwork title.
    math_report = pm.translate_math_week(q2w1_week())
    titles = [a["title"] for a in math_report["assignments"]]
    check("Math classwork title SM5: Lesson 32 Classwork", "SM5: Lesson 32 Classwork" in titles)
    check("Math classwork title no longer NEEDS_OWEN_DECISION", math_report["needs_owen_decision"] == [])

    # --- Shurley token vocabulary ---
    check("Shurley 5.1 -> Chapter 5, Lesson 1", pt.translate_shurley_cell("5.1")["lines"] == ["Chapter 5, Lesson 1"])
    check("Shurley CP20 -> Classroom Practice 20", pt.translate_shurley_cell("CP20")["lines"] == ["Classroom Practice 20"])
    check("Shurley CH5 Checkup", pt.translate_shurley_cell("CH5 Checkup")["lines"] == ["Chapter 5 Checkup"])
    check("Shurley Ch. 5 Checkup", pt.translate_shurley_cell("Ch. 5 Checkup")["lines"] == ["Chapter 5 Checkup"])
    check("Shurley Chapter 5 Test", pt.translate_shurley_cell("Chapter 5 Test")["lines"] == ["Chapter 5 Test"])
    check("Shurley CH5 Review", pt.translate_shurley_cell("CH5 Review")["lines"] == ["Chapter 5 Review"])
    check("Shurley Ch.1 L6 -> Chapter 1, Lesson 6", pt.translate_shurley_cell("Ch.1 L6")["lines"] == ["Chapter 1, Lesson 6"])
    unk = pt.translate_shurley_cell("HG3")
    check("unknown Shurley token fails closed", unk["resolved"] is False and unk["unresolved"] == ["HG3"])

    # Shurley assignment policy: only Chapter Test + Classroom Practice.
    check("Checkup creates no assignment", "checkup" not in [x for x in config["subjects"]["language_arts"]["assignmentPolicy"]["autoCreateOnlyFor"]])
    check("Review creates no assignment", "review" in config["subjects"]["language_arts"]["assignmentPolicy"]["neverAutoCreate"])
    ct = pt.chapter_test_assignment(5, "2026-10-20", config)
    check("Chapter Test assignment title ELA4: Chapter 5 Test", ct["title"] == "ELA4: Chapter 5 Test")
    check("Chapter Test group Assessments", ct["assignment_group"] == "Assessments")

    # --- Science shared engine ---
    unit = pt.resolve_science_unit_name(config, None)
    check("Science unit = Force and Motion", unit == "Force and Motion")
    check("Science Ch.1 expansion", pt.translate_science_cell("Ch. 1", unit)["lines"] == ["Force and Motion Chapter 1"])
    check("Science Ch.2 Check", pt.translate_science_cell("Ch. 2 Check", unit)["lines"] == ["Force and Motion Chapter 2 Check"])
    check("Science Ch.1-2 Review", pt.translate_science_cell("Ch. 1-2 Review", unit)["lines"] == ["Force and Motion Chapters 1-2 Review"])
    check("Science Ramp Lab", pt.translate_science_cell("Ramp Lab", unit)["lines"] == ["Force and Motion Ramp Lab"])
    s30 = pt.translate_science_cell("Ch. 3 / 30cm", unit)
    check("Science Ch.3 / 30cm resolves chapter", "Force and Motion Chapter 3" in s30["lines"])
    check("Science 30cm component unresolved", s30["unresolved"] == ["30cm"] and s30["resolved"] is False)
    check("Science unknown unit fails closed", pt.translate_science_cell("Ch. 1", None)["resolved"] is False)

    # --- History shared engine + Q2 redirect ---
    check("History Ch 3 -> <Unit> Chapter 3", pt.translate_history_cell("Ch 3", "Maps")["lines"] == ["Maps Chapter 3"])
    check("History unknown unit fails closed", pt.translate_history_cell("Ch 3", None)["resolved"] is False)
    hist = pt.translate_subject_week(q2w1_week(), "history", config)
    check("History Q2 redirect-only", hist["mode"] == "inactive-redirect")
    check("inactive History generates no assignments", hist["assignments"] == [])
    check("History redirect message mentions Science", "Science" in hist["redirectMessage"])

    # --- Q2W1 Science: agenda yes, assignments 0, announcements 0 ---
    sci = pt.translate_subject_week(q2w1_week(), "science", config)
    check("Q2W1 Science agenda present", sci["days"]["Monday"]["lines"] == ["Force and Motion Chapter 1"])
    check("Q2W1 Science assignments = 0", sci["assignments"] == [])
    check("Q2W1 Science unresolved = 0", sci["unresolved"] == [])

    events = pa.resolve_assessment_facts(q2w1_week())
    families = [e["family"] for e in events]
    check("no speculative Science assignment/announcement", "science_assessment" not in families)
    check("no speculative Science Check announcement", not any(e.get("assessments") == ["Force and Motion Chapter 2 Check"] for e in events))
    check("Q2W1 detects Reading + Spelling assessments only (Math/LA/Science none)", sorted(families) == ["reading_assessment", "spelling_assessment"])

    # --- Combined Reading/Spelling page ---
    reading_days = ww._translated_preview_days(q2w1_week(), "reading")
    spelling_days = ww._translated_preview_days(q2w1_week(), "spelling")
    combined = cp.build_combined_reading_spelling_html("Q2W1", reading_days, spelling_days)
    check("combined page has kl_wrapper_3 shell", 'id="kl_wrapper_3"' in combined)
    check("combined page has Reading sections", combined.count(">Reading</h4>") == 5)
    check("combined page has Spelling sections", combined.count(">Spelling</h4>") == 5)
    check("combined page has At Home only where supported", combined.count(">At Home</h4>") == 2)
    check("combined page contains Comprehension Questions (Tue/Thu)", combined.count("Comprehension Questions") == 2)
    check("combined page contains Reading Mastery Test 4", "Reading Mastery Test 4" in combined)

    # --- Existing-page-only contract ---
    check("weekly page CREATE forbidden", pp.expected_page_identity("Q2W1", "math")["createForbidden"] is True)
    check("no weekly page CREATE path", pp.validate_page_policy({"operation": "CREATE", "expectedPageSlug": "x", "createForbidden": True})["status"] == "FAIL")

    # --- Zero Canvas writes ---
    zw = ww._zero_write_proof()
    check("zero-write proof holds", zw["write_free"])

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
