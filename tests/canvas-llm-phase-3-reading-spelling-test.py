#!/usr/bin/env python3
"""Phase 3.3 — Reading + Spelling deterministic rules + Q2W1 preview tests.

Deterministic, offline, zero Canvas writes. Exercises: Reading lesson
translation, raw-source preservation, RMT+FCO parsing, exact Reading Test /
Checkout resolution, Test 14 no-Checkout, unresolved Checkout 8-13 thresholds,
two separate assignments with distinct groups, Spelling lesson/test/review
translation, exact Spelling Test number resolution, practice range, Test 25
gating, assignment-course conflict fail-closed, announcement fact packets,
LLM-facts protection, weekly-page CREATE forbidden / missing / duplicate
fail-closed, front-page activation targeting existing page only, and zero
Canvas writes.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_announcement as pa
from scripts.canvas_llm_phase3 import pacing_pages as pp
from scripts.canvas_llm_phase3 import week_workflow as ww


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def q2w1_week() -> dict:
    return {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"reading": {"raw": "L37"}, "spelling": {"raw": "32"}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"reading": {"raw": "L38"}, "spelling": {"raw": "33"}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {"reading": {"raw": "L39"}, "spelling": {"raw": "34"}}},
            "Thursday": {"date": "2026-10-15", "subjects": {"reading": {"raw": "L40"}, "spelling": {"raw": "Test"}}},
            "Friday": {"date": "2026-10-16", "subjects": {"reading": {"raw": "RMT+FCO"}, "spelling": {"raw": "review"}}},
        },
    }


def main() -> int:
    config = prd.load_config()

    # --- Reading lesson translation ---
    check("L37 -> Lesson 37", prd.parse_reading_token("L37")["translation"] == "Lesson 37")
    check("L40 -> Lesson 40", prd.parse_reading_token("L40")["translation"] == "Lesson 40")
    check("raw source preserved", prd.parse_reading_token("L37")["source"] == "L37")
    check("RMT+FCO parsed as rmt_fco", prd.parse_reading_token("RMT+FCO")["kind"] == "rmt_fco")

    # --- RMT+FCO exact resolution ---
    r = prd.resolve_reading_test_checkout(40)
    check("RMT+FCO -> Reading Mastery Test 4", r["readingTestNumber"] == 4)
    check("RMT+FCO -> Fluency Checkout 4", r["checkoutNumber"] == 4 and r["checkoutExists"] is True)
    check("Checkout 4 fluency 100/2 confirmed", r["fluency"]["wpm"] == 100 and r["fluency"]["maxErrors"] == 2 and r["fluencyResolved"] is True)

    # --- Test 14 no-Checkout ---
    r14 = prd.resolve_reading_test_checkout(140)
    check("Test 14 has no Checkout", r14["readingTestNumber"] == 14 and r14["checkoutExists"] is False)

    # --- Checkout thresholds independence ---
    check("Checkout 8 fluency unresolved", prd.resolve_checkout(8)["fluencyResolved"] is False)
    check("Checkout 14 -> None", prd.resolve_checkout(14) is None)
    check("Checkout 4 exists + fluency resolved", prd.resolve_checkout(4)["checkoutNumber"] == 4 and prd.resolve_checkout(4)["fluencyResolved"] is True)

    # --- Spelling translation ---
    check("32 -> Spelling Lesson 32", prd.parse_spelling_token("32")["translation"] == "Spelling Lesson 32")
    check("Test -> test token (number None)", prd.parse_spelling_token("Test")["kind"] == "test" and prd.parse_spelling_token("Test")["number"] is None)
    check("Test 40 -> Spelling Test 40 explicit", prd.parse_spelling_token("Test 40")["number"] == 40)
    check("review -> Spelling Review", prd.parse_spelling_token("review")["translation"] == "Spelling Review")

    # --- Exact Spelling Test number resolution ---
    week = q2w1_week()
    check("Q2W1 Spelling Test = 35 (ceil(34/5)*5)", prd.resolve_spelling_test_number(week) == 35)
    check("practice range 35 -> 31-34", prd.spelling_practice_range(35) == (31, 34))

    # --- Whole-week translation ---
    report = prd.translate_reading_spelling_week(week, config)
    check("Reading/Spelling deterministic", report["deterministic"] is True and report["authority"] == "OWNER_POLICY")
    check("Friday in_class = Test 4 + Checkout 4", report["reading"]["days"]["Friday"]["in_class"] == ["Reading Mastery Test 4", "Fluency Checkout 4"])
    check("Thursday Spelling Test 35", report["spelling"]["days"]["Thursday"]["translation"] == "Spelling Test 35")
    check("Thursday practice range 31-34", report["spelling"]["days"]["Thursday"]["practiceRange"] == {"start": 31, "end": 34, "wording": "practice Lessons 31 through 34"})

    # --- Two separate Reading assignments, distinct groups ---
    reading_assess = report["reading"]["days"]["Friday"]["assignments"]
    check("Reading produces two assignments", len(reading_assess) == 2)
    check("Reading groups distinct", [a["assignment_group"] for a in reading_assess] == ["Assessments", "Check Out"])
    check("Reading never merges gradebook items", len({a["title"] for a in reading_assess}) == 2)

    # --- Spelling assignment course conflict fails closed ---
    spelling_assign = report["spelling"]["assignments"]
    check("one Spelling assignment", len(spelling_assign) == 1)
    check("Spelling assignment course = 26442", spelling_assign[0]["course"] == 26442)
    check("Spelling cannot route to 28171", spelling_assign[0]["course"] != 28171)
    check("no spelling-course decision remains open", not any(d["field"] == "spelling_assignment_course" for d in report["needs_owen_decision"]))

    # --- Spelling test gating ---
    check("Test 25 gated", config["spelling"]["testNumbering"]["test25Gated"] is True)

    # --- Reading announcement fact packet ---
    events = pa.resolve_assessment_facts(week)
    reading_events = [e for e in events if e["family"] == "reading_assessment"]
    check("Reading assessment detected from RMT+FCO", len(reading_events) == 1)
    re_ = reading_events[0]
    check("Reading fact packet has test + checkout numbers", re_["facts"]["assessments"] == ["Reading Mastery Test 4", "Fluency Checkout 4"])
    check("Reading fact packet checkoutExists true", re_["facts"]["checkoutExists"] is True)

    # --- LLM cannot alter deterministic facts ---
    fp = {"course": "Reading/Spelling", "assessmentDate": "2026-10-16", "assessments": ["Reading Mastery Test 4", "Fluency Checkout 4"],
          "facts": {"assessmentDate": "2026-10-16", "assessments": ["Reading Mastery Test 4", "Fluency Checkout 4"]}}
    check("facts preserved when unchanged", pa._facts_preserved(fp, "Reading Mastery Test 4 and Fluency Checkout 4 on 2026-10-16") is True)
    check("facts changed -> rejected", pa._facts_preserved(fp, "Reading Mastery Test 5 and Fluency Checkout 4 on 2026-10-16") is False)
    draft = pa.draft_announcement(fp, "FIRST_NOTICE", use_llm=False)
    check("announcement draft model SKIPPED", draft["model_status"] == "SKIPPED")
    check("announcement draft preserves facts", draft["facts"] == fp["facts"])

    # --- Weekly-page policy ---
    check("weekly-page CREATE forbidden", pp.expected_page_identity("Q2W1", "math")["createForbidden"] is True)
    check("expected page slug exists", bool(pp.expected_page_identity("Q2W1", "math")["expectedPageSlug"]))
    bad = pp.validate_page_policy({"operation": "CREATE", "expectedPageSlug": "x", "createForbidden": True})
    check("CREATE page -> FAIL", bad["status"] == "FAIL")
    missing = pp.validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True, "missing": True})
    check("missing page -> FAIL", missing["status"] == "FAIL")
    dup = pp.validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True, "duplicated": True})
    check("duplicate page -> FAIL", dup["status"] == "FAIL")
    ok = pp.validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True})
    check("existing-page UPDATE -> PASS", ok["status"] == "PASS")

    # --- Front-page activation targets existing page only ---
    act = pp.front_page_activation_target("Q2W1", "math")
    check("front-page activation createForbidden", act["createForbidden"] is True and act["idempotent"] is True)
    check("front-page activation targets existing page", act["operation"] == "set_front_page" and act["target"]["mustExist"] is True)

    # --- Workflow integration ---
    prop = ww._propose_subject(week, "reading")
    check("workflow: reading proposal OWNER_POLICY", prop["authority"] == "OWNER_POLICY")
    check("workflow: reading local model skipped", prop["local_model"]["status"] == "SKIPPED")
    days = ww._translated_preview_days(week, "reading")
    check("workflow: Friday preview has Test + Checkout", days["Friday"]["in_class"] == ["Reading Mastery Test 4", "Fluency Checkout 4"])

    # --- Zero Canvas writes ---
    zw = ww._zero_write_proof()
    check("zero-write proof holds", zw["write_free"])

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
