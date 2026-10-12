#!/usr/bin/env python3
"""Phase 3 — end-to-end validation for the pacing + local AI teacher review loop.

Deterministic, offline, zero Canvas writes. Exercises: pacing extraction, blank
preservation, date alignment, pacing diff, authority precedence, anomaly
exclusion, precedent retrieval, structured local-model response parsing, model
failure fallback, teacher-correction persistence, no automatic rule promotion,
lifecycle transitions (with PUBLISHED_VERIFIED blocked), Canvas preview-only,
and the quarter-activation redirect rule.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase3 import constants as C
from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import pacing_change as pc
from scripts.canvas_llm_phase3 import precedent_retrieval as pr
from scripts.canvas_llm_phase3 import local_llm as llm
from scripts.canvas_llm_phase3 import learning as learn
from scripts.canvas_llm_phase3 import state_machine as sm
from scripts.canvas_llm_phase3 import canvas_preview as cp
from scripts.canvas_llm_phase3 import week_workflow as ww


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def main() -> int:
    # --- Pacing extraction (synthetic, deterministic) ---
    rows = [
        ["Subject:", "", "", "10/12/26", "10/13/26", "10/14/26", "10/15/26", "10/16/26"],
        ["", "", "", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        ["Saxon Math", "5", "", "L31", "L32", "L33", "L34", "INV 3"],
        ["Reading Mastery", "4", "", "L37", "L38", "L39", "L40", "RMT+FCO"],
        ["Spelling", "4", "", "32", "33", "34", "Test", "review"],
        ["Shurley English", "4", "", "5.1", "", "", "", ""],
        ["History", "4", "", "", "", "", "", ""],
        ["Science", "4", "", "F&M: CH1", "F&M: CH1", "", "", ""],
    ]
    src = {"workbook": "test", "sheet": "4A - Reagan", "freshRead": False, "status": "SYNTHETIC"}
    week = pe.extract_week(rows, "Q2W1", src)
    check("pacing: Q2W1 start/end dates", week["week"]["startDate"] == "2026-10-12" and week["week"]["endDate"] == "2026-10-16")
    check("pacing: raw value preserved verbatim", week["days"]["Friday"]["subjects"]["math"]["raw"] == "INV 3")
    check("pacing: blank preserved as blank", week["days"]["Monday"]["subjects"]["history"]["raw"] == "" and week["days"]["Monday"]["subjects"]["history"]["blank"] is True)
    check("pacing: weekday/date mapping", week["days"]["Wednesday"]["date"] == "2026-10-14")

    # --- Pacing diff ---
    prev = {"week": {"code": "Q2W1"}, "days": {"Monday": {"subjects": {"math": {"raw": "L30"}}}}}
    curr = {"week": {"code": "Q2W1"}, "days": {"Monday": {"subjects": {"math": {"raw": "L31"}}}}}
    diff = pc.diff_weeks(prev, curr)
    check("diff: CHANGED detected", any(d["from"] == "L30" and d["to"] == "L31" for d in diff["changed"]))

    # --- Authority precedence + anomaly exclusion ---
    bundle = pr.retrieve(subject="math")
    check("precedent: authority order starts OWNER_POLICY", bundle["authority_order"][0] == "OWNER_POLICY")
    exclusions = pr.load_anomaly_exclusions()
    check("anomaly: duplicated HIST prefix excluded", pr.is_anomalous("HIST 4B: HIST 4B: Maps", exclusions))
    check("anomaly: normal RM4 title not excluded", not pr.is_anomalous("RM4: Lesson 22 Workbook", exclusions))

    # --- Local model structured response parsing (no model needed) ---
    check("llm: parse plain JSON object", llm._parse_json('{"a":1}') == {"a": 1})
    check("llm: parse object with surrounding prose", llm._parse_json('x {"b":[1]} y') == {"b": [1]})
    fallback = llm.propose_subject(week, bundle, "math") if not llm.model_available() else None
    if fallback is not None:
        check("llm: failure fallback preserves unresolved", fallback["status"] == "WARN")

    # --- Teacher correction + no automatic promotion ---
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        C.LEARNING_FILES = {k: Path(tmp) / Path(v).name for k, v in C.LEARNING_FILES.items()}
        for _ in range(5):
            learn.record_correction(
                week="Q2W1", subject="math", weekday="Monday", raw_pacing="L31",
                artifact_type="agenda-in-class", model_proposal="Lesson 30",
                teacher_final="Lesson 31", authority="OWNER_POLICY",
                source_refs=["pacing:math:Monday"], status="approved",
            )
        check("learning: 5 approvals -> promotion suggestion", len(learn.suggest_promotions(5)) == 1)
        check("learning: no automatic promotion", learn.load_promoted_rules() == [])

    # --- Lifecycle (PUBLISHED_VERIFIED blocked) ---
    item = sm.new_item("Q2W1", "math", "Monday", "L31")
    item = sm.transition(item, "PROPOSED", reason="proposal", actor="local-model")
    item = sm.transition(item, "TEACHER_APPROVED", reason="approve", actor="Owen Reagan")
    try:
        sm.transition(item, "PUBLISHED_VERIFIED", reason="publish")
        check("lifecycle: PUBLISHED_VERIFIED blocked in Phase 3", False)
    except sm.LifecycleError:
        check("lifecycle: PUBLISHED_VERIFIED blocked in Phase 3", True)
    check("lifecycle: provenance preserved", [h["to"] for h in item["history"]] == ["PROPOSED", "TEACHER_APPROVED"])

    # --- Canvas preview only (no writes) ---
    days = {
        "Monday": {"in_class": ["Lesson 31"], "at_home": ["Lesson 31: Problems 12-30 Evens"]},
        "Tuesday": {"in_class": ["Lesson 32"], "at_home": None},
        "Wednesday": {"in_class": ["Lesson 33"], "at_home": ["Lesson 33: Problems 11-29 Odds"]},
        "Thursday": {"in_class": ["Written Assessment 6"], "at_home": None},
        "Friday": {"in_class": ["Investigation 3"], "at_home": None},
    }
    html = cp.build_agenda_html("Q2W1", days)
    check("preview: kl_wrapper_3 shell", 'id="kl_wrapper_3"' in html and "kl_circle_left kl_wrapper" in html)
    check("preview: At Home label (not Homework)", ">At Home</h4>" in html and ">Homework</h4>" not in html)
    check("preview: no empty At Home box on no-homework day", html.count('width: 100%') >= 3)

    # --- Zero Canvas writes ---
    zw = ww._zero_write_proof()
    check("zero-write: no Canvas write verbs in phase3 package", zw["write_free"])

    # --- Quarter activation redirect rule ---
    activation = json.loads(C.QUARTER_ACTIVATION_PATH.read_text(encoding="utf-8"))
    check("activation: Q2 active=Science, inactive=History", activation["quarters"]["Q2"]["activeSubject"] == "science" and activation["quarters"]["Q2"]["inactiveSubject"] == "history")
    redirect = ww.inactive_subject_redirect("Q2W1")
    check("activation: Q2 History redirect present", redirect is not None and "Science" in redirect["canonicalMessage"])
    check("activation: Q1 no redirect (Science silent)", ww.inactive_subject_redirect("Q1W1") is None)

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
