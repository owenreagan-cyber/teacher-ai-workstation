#!/usr/bin/env python3
"""Phase 3.0.2 — pacing parser fix + canonical translation regression tests.

Deterministic, offline, zero Canvas writes. Exercises: the authoritative Q2W1
pacing table (full Monday-Friday Language Arts and Science, blank History,
Science unit context), sparse-row alignment, and every promoted OWNER_POLICY
translation rule (Shurley N.M, CP<n>, Science unit/chapter, History fail-closed,
Classroom Practice assignment preview, and owner-policy-over-model precedence).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_phase3 import week_workflow as ww


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def q2w1_rows() -> list[list[str]]:
    # Mirrors the authoritative October 2026 "4A - Reagan" block for Q2W1.
    return [
        ["Subject:", "", "", "10/12/26", "10/13/26", "10/14/26", "10/15/26", "10/16/26", "", "10/19/26", "10/20/26"],
        ["", "", "", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "", "Monday", "Tuesday"],
        ["Saxon Math", "5", "", "L31", "L32", "L33", "L34", "INV 3", "", "L35", "L36"],
        ["Reading Mastery", "4", "", "L37", "L38", "L39", "L40", "RMT+FCO", "", "41", "42"],
        ["Spelling", "4", "", "32", "33", "34", "Test", "review", "", "36", "37"],
        ["Shurley English", "4", "", "5.1", "5.1", "5.2", "5.2, CP19", "5.3", "", "", ""],
        ["History", "4", "", "", "", "", "", "", "", "", ""],
        ["Science", "4", "", "Ch. 1", "Ch. 1", "Ch. 2", "Ch. 2 Check", "Ch. 1-2 Review", "", "", ""],
        ["", "", "", "Science: Force and Motion", "", "", "", "", "", "", ""],
    ]


def main() -> int:
    config = pt.load_config()
    source = {"workbook": "test", "sheet": "4A - Reagan", "freshRead": False, "status": "SYNTHETIC"}
    week = pe.extract_week(q2w1_rows(), "Q2W1", source)
    days = week["days"]

    # --- Parser: full five-day Language Arts and Science (not Monday-only) ---
    la_expected = ["5.1", "5.1", "5.2", "5.2, CP19", "5.3"]
    for wd, expected in zip(C.WEEKDAYS, la_expected):
        check(f"parser: Language Arts {wd} = {expected!r}", days[wd]["subjects"]["language_arts"]["raw"] == expected)
    sci_expected = ["Ch. 1", "Ch. 1", "Ch. 2", "Ch. 2 Check", "Ch. 1-2 Review"]
    for wd, expected in zip(C.WEEKDAYS, sci_expected):
        check(f"parser: Science {wd} = {expected!r}", days[wd]["subjects"]["science"]["raw"] == expected)
    for wd in C.WEEKDAYS:
        check(f"parser: History {wd} blank at SOURCE", days[wd]["subjects"]["history"]["raw"] == "" and days[wd]["subjects"]["history"]["blank"] is True)
    check("parser: Science unit context stored separately", week["unitContext"]["science"] == "Force and Motion")
    check("parser: History unit context unresolved", week["unitContext"]["history"] is None)
    check("parser: sparse row Math Monday aligned", days["Monday"]["subjects"]["math"]["raw"] == "L31")
    check("parser: trailing week-2 cells do not leak", days["Friday"]["subjects"]["math"]["raw"] == "INV 3")

    # --- Shurley / Language Arts translation ---
    la = pt.translate_subject_week(week, "language_arts", config)
    check("translation: Language Arts deterministic", la["deterministic"] is True and la["authority"] == "OWNER_POLICY")
    check("translation: 5.1 -> Chapter 5, Lesson 1", la["days"]["Monday"]["lines"] == ["Chapter 5, Lesson 1"])
    check("translation: 5.2 -> Chapter 5, Lesson 2", la["days"]["Wednesday"]["lines"] == ["Chapter 5, Lesson 2"])
    check("translation: 5.3 -> Chapter 5, Lesson 3", la["days"]["Friday"]["lines"] == ["Chapter 5, Lesson 3"])
    check("translation: 5.2, CP19 -> both tokens", la["days"]["Thursday"]["lines"] == ["Chapter 5, Lesson 2", "Classroom Practice 19"])

    # --- Classroom Practice assignment preview ---
    check("cp: exactly one Classroom Practice assignment", len(la["assignments"]) == 1, )
    a = la["assignments"][0]
    check("cp: title = Classroom Practice 19", a["title"] == "Classroom Practice 19")
    check("cp: points = 100", a["points_possible"] == 100)
    check("cp: grading type = percent", a["grading_type"] == "percent")
    check("cp: submission on_paper", a["submission_types"] == "on_paper")
    check("cp: counts toward final grade", a["counts_toward_final_grade"] is True)
    check("cp: due date same calendar day", a["due_date"] == "2026-10-15")
    check("cp: due time 11:59 PM America/New_York", a["due_time"] == "11:59 PM" and a["timezone"] == "America/New_York")
    check("cp: assignment group Classwork", a["assignment_group"] == "Classwork")
    check("cp: preview-only (no Canvas write)", a["preview_only"] is True)

    # CP absence creates no assignment.
    week_no_cp = pe.extract_week(
        [r[:] for r in q2w1_rows()], "Q2W1", source
    )
    week_no_cp["days"]["Thursday"]["subjects"]["language_arts"]["raw"] = "5.2"
    la_no_cp = pt.translate_subject_week(week_no_cp, "language_arts", config)
    check("cp: no CP token -> no assignment", la_no_cp["assignments"] == [])

    # --- Science translation ---
    sci = pt.translate_subject_week(week, "science", config)
    check("translation: Science deterministic", sci["deterministic"] is True and sci["authority"] == "OWNER_POLICY")
    check("translation: Ch. 1 -> Force and Motion Chapter 1", sci["days"]["Monday"]["lines"] == ["Force and Motion Chapter 1"])
    check("translation: Ch. 2 -> Force and Motion Chapter 2", sci["days"]["Wednesday"]["lines"] == ["Force and Motion Chapter 2"])
    check("translation: Ch. 2 Check -> Force and Motion Chapter 2 Check", sci["days"]["Thursday"]["lines"] == ["Force and Motion Chapter 2 Check"])
    check("translation: Ch. 1-2 Review -> Force and Motion Chapters 1-2 Review", sci["days"]["Friday"]["lines"] == ["Force and Motion Chapters 1-2 Review"])
    check("translation: Ramp Lab -> Force and Motion Ramp Lab", pt.translate_science_cell("Ramp Lab", "Force and Motion")["lines"] == ["Force and Motion Ramp Lab"])
    check("translation: F&M: CH1 -> Force and Motion Chapter 1", pt.translate_science_cell("F&M: CH1", "Force and Motion")["lines"] == ["Force and Motion Chapter 1"])

    # Unknown unit name fails closed.
    sci_unknown = pt.translate_science_cell("Ch. 1", None)
    check("translation: unknown Science unit fails closed", sci_unknown["resolved"] is False and sci_unknown["unresolved"] == ["Ch. 1"])

    # --- History translation + Q2 redirect-only ---
    check("translation: History Ch 3 -> <Unit> Chapter 3", pt.translate_history_cell("Ch 3", "Maps")["lines"] == ["Maps Chapter 3"])
    check("translation: History Ch 4 Worksheet -> <Unit> Chapter 4 Worksheet", pt.translate_history_cell("Ch 4 Worksheet", "Maps")["lines"] == ["Maps Chapter 4 Worksheet"])
    check("translation: History Review -> <Unit> Review", pt.translate_history_cell("Review", "Maps")["lines"] == ["Maps Review"])
    check("translation: History Test -> <Unit> Test", pt.translate_history_cell("Test", "Maps")["lines"] == ["Maps Test"])
    check("translation: unknown History unit fails closed", pt.translate_history_cell("Ch 3", None)["resolved"] is False)

    hist = pt.translate_subject_week(week, "history", config)
    check("translation: Q2 History redirect-only", hist["mode"] == "inactive-redirect" and hist["days"] == {} and hist["assignments"] == [])

    # --- Owner policy outranks model output ---
    proposal = ww._propose_subject(week, "language_arts")
    check("precedence: Language Arts proposal is OWNER_POLICY", proposal["authority"] == "OWNER_POLICY")
    check("precedence: local model skipped (deterministic)", proposal["local_model"]["status"] == "SKIPPED")
    check("precedence: deterministic result not model-inferred", "Chapter 5, Lesson 2" in proposal["days"]["Thursday"]["lines"])

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
