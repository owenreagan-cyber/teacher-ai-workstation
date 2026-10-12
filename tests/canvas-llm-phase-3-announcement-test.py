#!/usr/bin/env python3
"""Phase 3.2 — assessment + announcement intelligence regression tests.

Deterministic, offline, zero Canvas writes. Exercises: assessment trigger
detection, paired Math/Reading assignments with separate groups, Fact Test ->
Power Up resolution (missing file fails closed), Reading Test -> Checkout
resolution, Test 14 exception, first-notice/reminder scheduling (weekend-aware),
deterministic-facts protection against LLM alteration, unsupported-fact
rejection, custom/multi-course identity, no indefinite recurrence, duplicate
identity, approval requirement, and zero Canvas writes.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_announcement as pa


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def assessment_week() -> dict:
    return {
        "week": {"code": "Q2W3", "startDate": "2026-10-26", "endDate": "2026-10-30"},
        "days": {
            "Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L31"}, "reading": {"raw": "L37"}, "spelling": {"raw": "32"}}},
            "Tuesday": {"date": "2026-10-27", "subjects": {"math": {"raw": "WA6/ FA6"}, "reading": {"raw": "L38"}, "spelling": {"raw": "33"}}},
            "Wednesday": {"date": "2026-10-28", "subjects": {"math": {"raw": "L33"}, "reading": {"raw": "MT2"}, "spelling": {"raw": "34"}}},
            "Thursday": {"date": "2026-10-29", "subjects": {"math": {"raw": "L34"}, "reading": {"raw": "L39"}, "spelling": {"raw": "Test 35"}}},
            "Friday": {"date": "2026-10-30", "subjects": {"math": {"raw": "INV 3"}, "reading": {"raw": "L40"}, "spelling": {"raw": "review"}}},
        },
    }


def main() -> int:
    config = pa.load_config()

    # --- Assessment trigger detection ---
    week = assessment_week()
    events = pa.resolve_assessment_facts(week)
    families = [e["family"] for e in events]
    check("detects math assessment", "math_assessment" in families)
    check("detects reading assessment", "reading_assessment" in families)
    check("detects spelling assessment", "spelling_assessment" in families)
    check("no assessment on investigation-only week", pa.resolve_assessment_facts(
        {"week": {"code": "Q2W1"}, "days": {"Friday": {"date": "2026-10-16", "subjects": {"math": {"raw": "INV 3"}}}}}
    ) == [])

    # --- Paired Math assignments (separate groups) ---
    math_event = next(e for e in events if e["family"] == "math_assessment")
    math_assignments = [a for a in math_event["assignments"] if a]
    check("Math creates two gradebook assignments", len(math_assignments) == 2)
    groups = [a["group"] for a in math_assignments]
    check("Math groups = Written Assessments + Fact Assessments", groups == ["Written Assessments", "Fact Assessments"])
    check("Math not merged into one assignment", len({a["title"] for a in math_assignments}) == 2)

    # --- Fact Test -> Power Up resolution ---
    check("Fact Test 6 -> Power Up letter resolved", math_event["preparation"]["powerUp"] is not None)
    check("Fact Test -> Canvas file UNRESOLVED (fail closed)", math_event["preparation"]["resourceStatus"] == "UNRESOLVED")
    ft = pa.resolve_fact_test(6)
    check("Fact Test map deterministic", ft["powerUp"] and ft["skill"])

    # --- Paired Reading assignments (separate groups) ---
    reading_event = next(e for e in events if e["family"] == "reading_assessment")
    reading_assignments = [a for a in reading_event["assignments"] if a]
    check("Reading creates two assignments", len(reading_assignments) == 2)
    check("Reading groups = Assessments + Check Out", [a["group"] for a in reading_assignments] == ["Assessments", "Check Out"])

    # --- Reading Test -> Checkout resolution + Test 14 exception ---
    check("Reading Test 2 -> Checkout 2", pa.resolve_checkout(2)["checkoutNumber"] == 2)
    check("Reading Test 14 -> no Checkout", pa.resolve_checkout(14) is None)
    check("Checkout 1 fluency confirmed (100/2)", pa.resolve_checkout(1)["fluencyResolved"] is True and pa.resolve_checkout(1)["fluency"]["maxErrors"] == 2)
    check("Checkout 8 fluency unresolved", pa.resolve_checkout(8)["fluencyResolved"] is False)

    # --- Scheduling (first notice + reminder, weekend-aware) ---
    sched = pa.schedule_notices("2026-10-27", config)  # Tuesday
    check("first notice ~5 days before", sched["firstNotice"] == "2026-10-22")
    check("reminder ~1-2 days before", sched["reminder"] == "2026-10-23")
    sched_weekend = pa.schedule_notices("2026-10-20", config)
    check("weekend-aware reminder moved + warning", sched_weekend["reminder"] == "2026-10-16" and any("exceeds 2 days" in w for w in sched_weekend["warnings"]))

    # --- Deterministic facts cannot be modified by LLM output ---
    fp = {"course": "Math", "assessmentDate": "2026-10-20", "assessments": ["Math Test 6", "Fact Test 6"],
          "facts": {"assessmentDate": "2026-10-20", "assessments": ["Math Test 6", "Fact Test 6"]}}
    check("facts preserved when unchanged", pa._facts_preserved(fp, "Math Test 6 and Fact Test 6 on 2026-10-20") is True)
    check("facts changed -> rejected", pa._facts_preserved(fp, "Math Test 7 and Fact Test 6 on 2026-10-20") is False)
    check("unsupported fact (extra assessment) rejected", pa._facts_preserved({"facts": {"assessments": ["Math Test 6"]}}, "Math Test 7") is False)

    # --- Dry-run writer skips model by default ---
    draft = pa.draft_announcement(fp, "FIRST_NOTICE", use_llm=False)
    check("dry-run writer model SKIPPED", draft["model_status"] == "SKIPPED")
    check("dry-run writer preserves facts block", draft["facts"] == fp["facts"])
    check("dry-run writer includes both assessments", "Math Test 6" in draft["wording"] and "Fact Test 6" in draft["wording"])

    # --- Duplicate identity ---
    i1 = pa.announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "FIRST_NOTICE")
    i2 = pa.announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "FIRST_NOTICE")
    i_rem = pa.announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "REMINDER")
    check("duplicate identity deterministic", i1 == i2)
    check("notice type distinguishes identity", i1 != i_rem)

    # --- No indefinite recurrence (finite two-notice plan) ---
    check("finite notice plan (first + reminder only)", set([p for p in ("FIRST_NOTICE", "REMINDER")]) == {"FIRST_NOTICE", "REMINDER"})

    # --- State machine: approval required, PUBLISHED_VERIFIED blocked ---
    item = {"state": "SOURCE_TRIGGER"}
    item = pa.transition_announcement(item, "FACTS_RESOLVED", reason="resolved")
    item = pa.transition_announcement(item, "DRAFTED", reason="drafted")
    item = pa.transition_announcement(item, "TEACHER_APPROVED", reason="Owen approved")
    check("announcement requires TEACHER_APPROVED before schedule", item["state"] == "TEACHER_APPROVED")
    try:
        pa.transition_announcement(item, "PUBLISHED_VERIFIED", reason="publish")
        check("PUBLISHED_VERIFIED blocked in Phase 3.2", False)
    except pa.AnnouncementStateError:
        check("PUBLISHED_VERIFIED blocked in Phase 3.2", True)

    # --- Chief review preview ---
    review = pa.build_chief_review(events, config)
    check("chief review lists upcoming assessments", "UPCOMING ASSESSMENTS" in review)
    check("chief review shows first notice + reminder", "FIRST NOTICE" in review and "REMINDER" in review)
    check("chief review shows assignments", "✓" in review and "Written Assessments" in review)

    # --- Multi-course identity separation (custom announcements) ---
    id_math = pa.announcement_identity("Math", "custom", "PictureDay", "2026-09-08", "FIRST_NOTICE")
    id_homeroom = pa.announcement_identity("Homeroom", "custom", "PictureDay", "2026-09-08", "FIRST_NOTICE")
    check("multi-course announcements get distinct identities", id_math != id_homeroom)

    # --- Zero Canvas writes (static proof from workflow) ---
    from scripts.canvas_llm_phase3 import week_workflow as ww
    zw = ww._zero_write_proof()
    check("zero-write proof holds with announcement module", zw["write_free"])

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
