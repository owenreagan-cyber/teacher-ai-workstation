#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 18B WeeklyPlan integration tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

PKG="scripts/canvas_llm_phase18b"
CLI="$PKG/cli.py"

echo "PASS compile check"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$PKG/__init__.py" "$PKG/translation.py" "$PKG/precedent_loader.py" "$CLI"

echo "PASS no write-path token in Phase 18B package"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|http\.client|urllib\.request|CANVAS_TOKEN' \
  "$PKG"/*.py >/tmp/canvas_phase_18b_test_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18b_test_write_scan.txt
  echo "FAIL: write-path token found"
  exit 1
fi
rm -f /tmp/canvas_phase_18b_test_write_scan.txt

python3 - <<'PY'
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))

from scripts.canvas_llm_phase18a.models import (
    CoursePlan,
    DayEntry,
    Evidence,
    WeeklyPlan,
    WEEKDAYS,
    KNOWN_COURSES,
)
from scripts.canvas_llm_phase18a.validation import validate_plan
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18b.translation import (
    SUBJECT_KEYS,
    TranslationResult,
    translate_weekly_plan,
)
from scripts.canvas_llm_phase18b.precedent_loader import (
    load_precedent_bundle,
    static_catalog,
)

DATES = {
    "Monday": "2026-08-03",
    "Tuesday": "2026-08-04",
    "Wednesday": "2026-08-05",
    "Thursday": "2026-08-06",
    "Friday": "2026-08-07",
}

PACING = Evidence(source_class="live_pacing", reference='pacing tab "4B - Reagan"')
TEACHER = Evidence(source_class="teacher_instruction", reference="teacher instruction")


def day(weekday, in_class="Lesson", homework="HW", raw="Lesson",
        decided="live_pacing", evidence=None, blank=False, ambiguity=""):
    if blank:
        in_class, homework, raw, decided = "", "", "", ""
        evidence = []
    return DayEntry(
        weekday=weekday, date=DATES[weekday], in_class=in_class, homework=homework,
        raw=raw, blank=blank, decided_source=decided,
        evidence=evidence if evidence is not None else [PACING], ambiguity=ambiguity,
    )


def course(name, days=None, artifacts=None, protected=False):
    return CoursePlan(
        course=name,
        days=days if days is not None else [day(w) for w in WEEKDAYS],
        requested_artifacts=artifacts or ["page"],
        protected=protected,
    )


def base_plan():
    return WeeklyPlan(
        school_year="2026-2027", quarter=1, week_number=3, week_code="Q1W3",
        monday_date="2026-08-03", friday_date="2026-08-07",
        courses={c: course(c) for c in KNOWN_COURSES},
    )


# Test 1 — Happy-path translation.
result = translate_weekly_plan(build_example_plan())
assert isinstance(result, TranslationResult)
assert result.plan_id.startswith("wp-")
assert result.agenda["week_code"] == result.week_code
assert result.prediction["weekCode"] == result.week_code
print("PASS test 1: happy-path WeeklyPlan translation")

# Test 2 — Course/day fidelity (5 courses x Mon-Fri).
plan = base_plan()
result = translate_weekly_plan(plan)
by_course_day = {(e["subject"], e["weekday"]) for e in result.prediction["predictions"]}
expected_pairs = {(SUBJECT_KEYS[c], wd) for c in KNOWN_COURSES for wd in WEEKDAYS}
assert by_course_day == expected_pairs, (by_course_day, expected_pairs)
assert {s["subject"] for s in result.subjects} == set(SUBJECT_KEYS.values())
print("PASS test 2: course/day fidelity (5 courses x Mon-Fri)")

# Test 3 — Stronger source wins: teacher instruction not replaced by prediction.
plan = base_plan()
plan.courses["Math"].days[3] = day(
    "Thursday", in_class="Review Lessons 12-13", homework="No Homework",
    raw="Lesson 14", decided="teacher_instruction", evidence=[PACING, TEACHER],
)
result = translate_weekly_plan(plan)
math_thu = next(
    e for e in result.prediction["predictions"]
    if e["subject"] == "math" and e["weekday"] == "Thursday"
)
assert math_thu["decision_layer"] == "teacher_instruction"
assert math_thu["in_class_title"] == "Review Lessons 12-13"
assert math_thu["at_home_title"] == "No Homework"
assert math_thu["teacher_override"] and math_thu["teacher_override"]["value"] == "Review Lessons 12-13"
assert math_thu["review_state"] == "teacher_decided"
print("PASS test 3: stronger source wins (teacher instruction beats prediction)")

# Test 4 — Precedence violation rejected before translation.
plan = base_plan()
plan.courses["Math"].days[0] = day(
    "Monday", in_class="Lesson 9", homework="", raw="Lesson 10",
    decided="precedent",
    evidence=[
        PACING,
        Evidence(source_class="precedent", reference="precedent", precedent_class="operational_behavior"),
    ],
)
try:
    translate_weekly_plan(plan)
    raise AssertionError("expected translation to reject lower-precedence decision")
except ValueError as exc:
    assert "invalid WeeklyPlan" in str(exc)
print("PASS test 4: precedence violation rejected before translation")

# Test 5 — Blank preservation downstream.
plan = base_plan()
plan.courses["Math"].days[4] = day("Friday", blank=True)
result = translate_weekly_plan(plan)
assert ("Math", "Friday") in {(b["course"], b["weekday"]) for b in result.blanks}
fri_agenda = result.agenda["days"][4]
assert "Math" not in fri_agenda["subjects"]
assert not any(hw.startswith("Math:") for hw in fri_agenda["homework"])
math_fri = [e for e in result.prediction["predictions"] if e["subject"] == "math" and e["weekday"] == "Friday"]
assert math_fri == []
print("PASS test 5: blank remains blank downstream")

# Test 6 — Ambiguity preservation (not guessed).
plan = base_plan()
plan.courses["History"].days[2] = day(
    "Wednesday", in_class="", homework="", raw="S9 L3",
    decided="live_pacing", ambiguity="shorthand not in rule catalog",
)
result = translate_weekly_plan(plan)
assert any(u["course"] == "History" and u["weekday"] == "Wednesday" for u in result.unresolved)
hist_wed = [e for e in result.prediction["predictions"] if e["subject"] == "history" and e["weekday"] == "Wednesday"]
assert hist_wed and hist_wed[0]["in_class_title"] == "" and hist_wed[0]["at_home_title"] == ""
assert hist_wed[0]["decision_layer"] == "unresolved" and hist_wed[0]["review_state"] == "needs_review"
assert "S9 L3" not in json.dumps(result.agenda)
print("PASS test 6: ambiguity remains unresolved (not guessed)")

# Test 7 — Protected course produces no write-eligible action.
plan = base_plan()
plan.courses["Science"] = CoursePlan(
    course="Science", protected=True, days=[day(w) for w in WEEKDAYS],
)
plan.protected_courses = ["Science"]
result = translate_weekly_plan(plan)
assert "Science" in result.protected
assert not any(e["subject"] == "science" for e in result.prediction["predictions"])
science = next(s for s in result.subjects if s["subject"] == "science")
assert science["readinessState"] == "Blocked"
assert science["assignmentPolicy"] == "disabled"
print("PASS test 7: protected course produces no write-eligible action")

# Test 8 — Anomaly blocking: anomaly cannot become canonical/downstream source.
plan = base_plan()
plan.courses["Math"].days[0] = day(
    "Monday", in_class="Lesson 13", homework="", raw="Lesson 12",
    decided="precedent",
    evidence=[Evidence(source_class="precedent", reference="scout finding", precedent_class="anomaly")],
)
try:
    translate_weekly_plan(plan)
    raise AssertionError("expected anomaly-based decision to be rejected")
except ValueError as exc:
    assert "invalid WeeklyPlan" in str(exc)
print("PASS test 8: anomaly cannot become canonical/downstream source")

# Test 9 — Provenance trace.
result = translate_weekly_plan(build_example_plan())
assert result.trace
sample = result.trace[0]
for key in ("canonical_plan_id", "canonical_week_code", "canonical_course", "canonical_day", "canonical_source", "downstream_kind"):
    assert key in sample, key
assert sample["canonical_plan_id"] == result.plan_id
print("PASS test 9: provenance trace survives translation")

# Test 10 — Legacy downstream compatibility (contract shapes).
result = translate_weekly_plan(build_example_plan())
agenda_keys = {"week_code", "title", "days", "assignments", "assessments", "reminders", "schedule_summary", "content_hash", "approval_state", "deployment_status", "page_url"}
assert agenda_keys <= set(result.agenda.keys())
pred_keys = {"weekCode", "sourceHierarchy", "predictions", "unresolvedDecisions", "teacherOverrides", "teacherCorrections", "patternRecords", "warnings", "reviewState", "provenance"}
assert pred_keys <= set(result.prediction.keys())
subject_keys = {"subject", "title", "readinessState", "approvalState", "confidence", "sourceHierarchy", "predictedInstruction", "resolvedResources", "unresolvedResources", "blockedResources", "teacherEdits", "productionPreviewStatus", "assignmentPolicy", "why"}
for s in result.subjects:
    assert subject_keys <= set(s.keys())
assert result.prediction["sourceHierarchy"] == ["teacher_instruction", "live_pacing", "canonical_rule", "live_canvas_config", "precedent", "historical_fallback"]
print("PASS test 10: downstream contract shapes remain consumable")

# Test 11 — Optional precedent bundle absent: no failure.
with tempfile.TemporaryDirectory() as tmp:
    res = load_precedent_bundle(Path(tmp) / "does-not-exist")
    assert res.status == "absent" and res.ok and res.records == []
    assert res.warnings
print("PASS test 11: absent precedent bundle handled safely")

# Test 12 — Optional valid precedent bundle: classified, usable only at proper precedence.
with tempfile.TemporaryDirectory() as tmp:
    bundle = Path(tmp)
    (bundle / "precedent.json").write_text(json.dumps({
        "precedents": [
            {"classification": "operational_behavior", "description": "Teachers post math homework on grade days"},
            {"classification": "anomaly", "description": "One week a duplicate page was created"},
            {"classification": "canvas_configuration", "description": "Math course id 12345 in sandbox"},
        ]
    }), encoding="utf-8")
    res = load_precedent_bundle(bundle)
    assert res.status == "ok" and res.ok
    assert len(res.records) == 1 and res.records[0]["classification"] == "operational_behavior"
    assert len(res.anomalies) == 1
    assert len(res.config_entries) == 1
    # anomaly is never promoted to a usable record
    assert all(r["classification"] == "operational_behavior" for r in res.records)
print("PASS test 12: valid precedent bundle classified; anomaly not promoted")

# Test 13 — Malformed precedent bundle: controlled WARN, not silent promotion.
with tempfile.TemporaryDirectory() as tmp:
    bundle = Path(tmp)
    (bundle / "precedent.json").write_text("{not valid json", encoding="utf-8")
    res = load_precedent_bundle(bundle)
    assert res.status == "malformed" and not res.ok
    assert res.records == [] and res.errors
with tempfile.TemporaryDirectory() as tmp:
    bundle = Path(tmp)
    (bundle / "precedent.json").write_text(json.dumps({
        "precedents": [{"classification": "bogus", "description": "x"}]
    }), encoding="utf-8")
    res = load_precedent_bundle(bundle)
    assert res.status == "malformed" and res.records == []
print("PASS test 13: malformed precedent bundle yields controlled WARN, no promotion")

# Test 14 — Canvas configuration remains registry-driven (not hardcoded from precedent).
result = translate_weekly_plan(build_example_plan())
blob = json.dumps(result.to_dict())
# No hardcoded numeric course/assignment-group/module/page IDs may appear in output.
for forbidden in ('"course_id"', '"courseId"', '"assignmentGroupId"', '"moduleId"', '"targetCanvasId"'):
    assert forbidden not in blob, forbidden
assert static_catalog()  # fallback catalog remains available
print("PASS test 14: Canvas configuration not hardcoded from precedent")

# Test 15 — No write path: runtime verification (no writer/connector modules loaded).
import importlib
for mod in ("canvas_writer", "canvas_connector", "weekly_agenda_publisher"):
    assert mod not in sys.modules, mod
print("PASS test 15: no Canvas writer/connector/publisher module loaded during translation")

# Test 16 — Round-trip compatibility: deterministic serialization.
r1 = translate_weekly_plan(build_example_plan())
r2 = translate_weekly_plan(build_example_plan())
assert r1.to_dict() == r2.to_dict()
assert json.loads(json.dumps(r1.to_dict(), sort_keys=True)) == r1.to_dict()
print("PASS test 16: canonical -> downstream serialization is deterministic")
PY

echo "PASS Canvas LLM Phase 18B WeeklyPlan integration tests complete"
