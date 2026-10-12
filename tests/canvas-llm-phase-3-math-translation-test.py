#!/usr/bin/env python3
"""Phase 3.1 — canonical Math rules + Q2W1 end-to-end translation tests.

Deterministic, offline, zero Canvas writes. Exercises: Math token translation
(L/INV/WA/FA), raw pacing preservation, normal lesson-day work (In Class / At
Home), weekday homework schedule, unfinished-classwork non-promotion, no
invented homework, Investigation isolation from lesson homework, assessment
isolation, owner-policy-over-precedent precedence, assignment-group resolution,
same-day 11:59 PM due calculation, 100 points / percent / on_paper, and the
dry-run-only guarantee.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import week_workflow as ww


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def q2w1_week() -> dict:
    return {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"math": {"raw": "L31"}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"math": {"raw": "L32"}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {"math": {"raw": "L33"}}},
            "Thursday": {"date": "2026-10-15", "subjects": {"math": {"raw": "L34"}}},
            "Friday": {"date": "2026-10-16", "subjects": {"math": {"raw": "INV 3"}}},
        },
    }


def main() -> int:
    config = pm.load_config()

    # --- Token translation ---
    check("L31 -> Lesson 31", pm.parse_math_tokens("L31")["tokens"][0]["translation"] == "Lesson 31")
    check("L34 -> Lesson 34", pm.parse_math_tokens("L34")["tokens"][0]["translation"] == "Lesson 34")
    check("INV 3 -> Investigation 3", pm.parse_math_tokens("INV 3")["tokens"][0]["translation"] == "Investigation 3")
    check("L 31 -> Lesson 31 (variant)", pm.parse_math_tokens("L 31")["tokens"][0]["translation"] == "Lesson 31")
    check("Lesson 31 -> Lesson 31 (variant)", pm.parse_math_tokens("Lesson 31")["tokens"][0]["translation"] == "Lesson 31")
    check("Inv 3 -> Investigation 3 (variant)", pm.parse_math_tokens("Inv 3")["tokens"][0]["translation"] == "Investigation 3")
    check("raw pacing preserved", pm.parse_math_tokens("L31")["source"] == "L31")

    # --- Normal lesson-day work ---
    mon = pm.math_day_plan("L31", "Monday", "2026-10-12", False, config)
    check("Monday In Class = Lesson 31 + #1-10", mon["in_class"] == ["Lesson 31", "#1-10"])
    check("Monday At Home = #12-30 evens", mon["at_home"] == "#12-30 evens" and mon["at_home_status"] == "homework")
    check("Monday homework accuracy grade created", len(mon["assignments"]) == 1 and mon["assignments"][0]["kind"] == "homework_accuracy_grade")
    check("homework title SM5: Lesson 31 Homework", mon["assignments"][0]["title"] == "SM5: Lesson 31 Homework")
    check("homework group Homework/Class Work", mon["assignments"][0]["assignment_group"] == "Homework/Class Work")

    wed = pm.math_day_plan("L33", "Wednesday", "2026-10-14", False, config)
    check("Wednesday At Home = #11-29 odds", wed["at_home"] == "#11-29 odds")

    tue = pm.math_day_plan("L32", "Tuesday", "2026-10-13", False, config)
    check("Tuesday no homework", tue["at_home_status"] == "no_homework" and tue["at_home"] is None)
    check("Tuesday classwork accuracy grade (title resolved)", tue["assignments"][0]["kind"] == "classwork_accuracy_grade" and tue["assignments"][0]["title"] == "SM5: Lesson 32 Classwork" and tue["assignments"][0]["title_authority"] == "OWNER_POLICY")

    thu = pm.math_day_plan("L34", "Thursday", "2026-10-15", False, config)
    check("Thursday no assignment (no Tuesday assessment)", thu["assignments"] == [])

    # --- Assignment base fields ---
    a = mon["assignments"][0]
    check("100 points", a["points_possible"] == 100)
    check("percent grading", a["grading_type"] == "percent")
    check("on_paper submission", a["submission_types"] == "on_paper")
    check("same-day due 11:59 PM America/New_York", a["due_date"] == "2026-10-12" and a["due_time"] == "11:59 PM" and a["timezone"] == "America/New_York")
    check("dry-run only", a["preview_only"] is True)

    # --- Investigation isolation ---
    fri = pm.math_day_plan("INV 3", "Friday", "2026-10-16", False, config)
    check("Friday Investigation In Class only", fri["in_class"] == ["Investigation 3"])
    check("Friday Investigation no At Home", fri["at_home_status"] == "no_homework" and fri["at_home"] is None)
    check("Friday Investigation no assignment", fri["assignments"] == [])
    check("Investigation does not inherit Monday lesson homework", pm.math_day_plan("INV 3", "Monday", "2026-10-12", False, config)["at_home"] is None)

    # --- Assessment isolation ---
    assess = pm.math_day_plan("WA6/ FA6", "Tuesday", "2026-10-13", False, config)
    check("assessment tokens do not inherit lesson homework", assess["at_home_status"] == "no_homework")
    check("assessment tokens produce Written + Fact", [x["kind"] for x in assess["assignments"]] == ["written_assessment", "fact_assessment"])
    check("Written Assessment title", assess["assignments"][0]["title"] == "SM5: Written Assessment 6")
    check("Fact Assessment title", assess["assignments"][1]["title"] == "SM5: Fact Assessment 6")
    check("Written group = Written Assessments", assess["assignments"][0]["assignment_group"] == "Written Assessments")
    check("Fact group = Fact Assessments", assess["assignments"][1]["assignment_group"] == "Fact Assessments")

    # --- WA6/ FA6* future token: '*' surfaced unresolved, not invented ---
    combined = pm.parse_math_tokens("WA6/ FA6*")
    check("WA6/ FA6* parses both assessment tokens", [t["kind"] for t in combined["tokens"]] == ["written_assessment", "fact_assessment"])
    check("WA6/ FA6* trailing '*' unresolved", any("*" in u for u in combined["unresolved"]))

    # --- Unknown token fails closed ---
    unknown = pm.parse_math_tokens("XYZ9")
    check("unknown token fails closed", unknown["resolved"] is False and unknown["unresolved"] == ["XYZ9"])

    # --- Tuesday assessment displaces classwork grade to Thursday ---
    check("Tuesday assessment -> no Tuesday classwork grade", all(a["kind"] != "classwork_accuracy_grade" for a in pm.math_day_plan("WA6/ FA6", "Tuesday", "2026-10-13", True, config)["assignments"]))
    check("Tuesday assessment -> Thursday classwork grade", any(a["kind"] == "classwork_accuracy_grade" for a in pm.math_day_plan("L34", "Thursday", "2026-10-15", True, config)["assignments"]))

    # --- Unfinished-classwork is NOT promoted to OWNER_POLICY ---
    not_promoted = {r["rule"] for r in config["notPromoted"]}
    check("unfinished-classwork wording not owner policy", "unfinished-classwork wording" in not_promoted)
    npr = next(r for r in config["notPromoted"] if r["rule"] == "unfinished-classwork wording")
    check("unfinished-classwork marked LIVE_CANVAS_PRECEDENT + requires approval", npr["authority"] == "LIVE_CANVAS_PRECEDENT" and npr["requiresTeacherApproval"] is True)

    # --- Owner policy outranks live precedent / model ---
    report = pm.translate_math_week(q2w1_week(), config)
    check("Math translation deterministic OWNER_POLICY", report["deterministic"] is True and report["authority"] == "OWNER_POLICY")
    check("Math local model skipped", report["local_model"]["status"] == "SKIPPED")
    check("3 weekly accuracy grades for Q2W1", len(report["assignments"]) == 3)
    check("classwork grade day = Tuesday", report["classwork_grade_day"] == "Tuesday")
    check("no needs-Owen decision (classwork title resolved)", report["needs_owen_decision"] == [])
    check("classwork title uses approved Classwork suffix", "SM5: Lesson 32 Classwork" in [a.get("title") for a in report["assignments"]])
    check("no bare 'SM5: Lesson N' anomaly title produced", all((a.get("title") or "").endswith("Homework") or (a.get("title") or "").endswith("Classwork") for a in report["assignments"]))

    # --- Workflow integration: propose is deterministic, preview builds dry-run ---
    week = q2w1_week()
    proposal = ww._propose_subject(week, "math")
    check("workflow: math proposal OWNER_POLICY", proposal["authority"] == "OWNER_POLICY")
    check("workflow: math proposal has human preview", isinstance(proposal.get("human_preview"), str) and "Investigation 3" in proposal["human_preview"])
    days = ww._translated_preview_days(week, "math")
    check("workflow: Friday preview omits At Home (Investigation)", days["Friday"]["at_home"] is None)
    check("workflow: Monday preview carries homework", days["Monday"]["at_home"] == ["#12-30 evens"])

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
