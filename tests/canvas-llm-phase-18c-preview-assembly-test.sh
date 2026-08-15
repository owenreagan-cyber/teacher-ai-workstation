#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

echo "Running Canvas LLM Phase 18C preview assembly tests..."

python3 -m py_compile \
  scripts/canvas_llm_phase18c/__init__.py \
  scripts/canvas_llm_phase18c/contracts.py \
  scripts/canvas_llm_phase18c/preview.py \
  scripts/canvas_llm_phase18c/drift.py \
  scripts/canvas_llm_phase18c/cli.py \
  scripts/canvas_llm_phase22/contracts.py \
  scripts/canvas_llm_phase24/contracts.py \
  scripts/canvas_llm_phase26/contracts.py
echo "PASS compile check"

PYTHON_BIN="python3"
RUN_PY() { "$PYTHON_BIN" - "$@"; }

# ---------------------------------------------------------------------------
# Helper context shared by most tests.
# ---------------------------------------------------------------------------
CONFIG_CTX='RuntimeContext(canvas_config={
  "math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"},
  "reading-spelling": {"course_id": "R", "module_id": "RM", "assignment_group_id": "RA"},
  "language-arts": {"course_id": "L", "module_id": "LM", "assignment_group_id": "LA"},
  "history": {"course_id": "H", "module_id": "HM", "assignment_group_id": "HA"},
})'

# ---------------------------------------------------------------------------
# Test 1: end-to-end happy path — items present exactly once.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

ctx = RuntimeContext(canvas_config={
  "math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"},
  "reading-spelling": {"course_id": "R", "module_id": "RM", "assignment_group_id": "RA"},
  "language-arts": {"course_id": "L", "module_id": "LM", "assignment_group_id": "LA"},
  "history": {"course_id": "H", "module_id": "HM", "assignment_group_id": "HA"},
})
p = assemble_teacher_preview(build_example_plan(), ctx)
assert len(p.courses) == 5
assert all(len(c.days) == 5 for c in p.courses)
# prediction events: non-blank, non-ambiguous, non-protected canonical days, each exactly once
events = p.prediction["predictions"]
counts = {}
for e in events:
    counts[(e["subject"], e["weekday"])] = counts.get((e["subject"], e["weekday"]), 0) + 1
assert all(v == 1 for v in counts.values()), counts
assert len(p.workstation["subjects"]) == 5
print("PASS test 1: end-to-end happy path items present exactly once")
PY

# ---------------------------------------------------------------------------
# Test 2: blank remains blank through the entire pipeline.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys, json
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
# Science is blank-protected: no science events, no agenda content, no content invented.
assert not any(e["subject"] == "science" for e in p.prediction["predictions"])
science = next(c for c in p.courses if c.course == "Science")
assert all(d.status == "protected" for d in science.days)
# No agenda surface may inject content into a blank day.
for day in p.agenda["days"]:
    assert not (day.get("subjects") or {}).get("Science"), day
    assert not any(h.startswith("Science:") for h in day.get("homework", [])), day
# The blank invariant must be machine-checked by the drift detector too.
assert p.drift["invalid_drift"] == [], p.drift["invalid_drift"]
print("PASS test 2: blank stays blank on every downstream surface (no default)")
PY

# ---------------------------------------------------------------------------
# Test 3: unresolved remains unresolved; prediction does not fill it.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
hist = next(c for c in p.courses if c.course == "History")
wed = next(d for d in hist.days if d.weekday == "Wednesday")
assert wed.status == "unresolved"
ev = [e for e in p.prediction["predictions"] if e["subject"] == "history" and e["weekday"] == "Wednesday"][0]
assert ev["decision_layer"] == "unresolved"
assert ev["in_class_title"] == "" and ev["at_home_title"] == ""
print("PASS test 3: unresolved remains unresolved (prediction is advisory)")
PY

# ---------------------------------------------------------------------------
# Test 4: protected stays blocked; no write-eligible object.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
science = next(s for s in p.workstation["subjects"] if s["subject"] == "science")
assert science["assignmentPolicy"] == "disabled"
assert science["readinessState"] == "Blocked"
assert not any(e["subject"] == "science" for e in p.prediction["predictions"])
print("PASS test 4: protected course stays blocked (no write-eligible object)")
PY

# ---------------------------------------------------------------------------
# Test 5: duplicate downstream-key collision fails closed.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
from dataclasses import replace
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18b.translation import translate_weekly_plan
from scripts.canvas_llm_phase18c.drift import detect_drift

plan = build_example_plan()
result = translate_weekly_plan(plan)
# Duplicate one downstream event to simulate a key collision.
dup = result.prediction["predictions"][0]
modified = dict(result.prediction)
modified["predictions"] = list(result.prediction["predictions"]) + [dup]
result2 = replace(result, prediction=modified)
report = detect_drift(plan, result2)
assert report.invalid_drift, "duplicate downstream event was not detected"
print("PASS test 5: duplicate downstream-key collision detected (fail closed)")
PY

# ---------------------------------------------------------------------------
# Test 6: contract schema drift — translated shape matches shared contracts.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18b.translation import translate_weekly_plan
from scripts.canvas_llm_phase22.contracts import WeeklyAgendaPage
from scripts.canvas_llm_phase24.contracts import WeekPrediction
from scripts.canvas_llm_phase26.contracts import SubjectSnapshot

result = translate_weekly_plan(build_example_plan())
assert set(result.agenda.keys()) == set(WeeklyAgendaPage(week_code="", title="").to_dict().keys())
assert set(result.prediction.keys()) == set(WeekPrediction(
    week_code="", source_hierarchy=[], predictions=[], unresolved_decisions=[],
    teacher_overrides=[], teacher_corrections=[], pattern_records=[], warnings=[],
    review_state="", provenance=[],
).to_dict().keys())
assert set(result.subjects[0].keys()) == set(SubjectSnapshot(
    subject="", title="", readiness_state="", approval_state="", confidence=0.0,
    source_hierarchy=[], predicted_instruction=[], resolved_resources=[],
    unresolved_resources=[], blocked_resources=[], teacher_edits=[],
    production_preview_status="",
).to_dict().keys())
print("PASS test 6: translated shapes match shared contracts (no schema drift)")
PY

# ---------------------------------------------------------------------------
# Test 7: missing Canvas config blocks preview (no guessed IDs).
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
assert p.readiness == "BLOCKED_MISSING_CONFIG"
assert p.missing_config
# No guessed Canvas ID anywhere in the preview.
blob = str(p.to_dict())
assert "course_id=guess" not in blob
print("PASS test 7: missing Canvas config blocks preview with no guessed IDs")
PY

# ---------------------------------------------------------------------------
# Test 8: due-time unresolved — no due time manufactured.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys, json
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

ctx = RuntimeContext(canvas_config={
  "math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"},
  "reading-spelling": {"course_id": "R", "module_id": "RM", "assignment_group_id": "RA"},
  "language-arts": {"course_id": "L", "module_id": "LM", "assignment_group_id": "LA"},
  "history": {"course_id": "H", "module_id": "HM", "assignment_group_id": "HA"},
})  # due_time_policy defaults to "unresolved"
p = assemble_teacher_preview(build_example_plan(), ctx)
assert p.readiness == "BLOCKED_POLICY"
assert any("due-time" in r.lower() for r in p.unresolved_policy)
# 18C must not manufacture a concrete due time.
assert "11:59" not in json.dumps(p.to_dict())
assert "12:00" not in json.dumps(p.to_dict())
print("PASS test 8: due-time unresolved propagated with no manufactured due time")
PY

# ---------------------------------------------------------------------------
# Test 9: idempotent preview assembly (deterministic).
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys, json
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

a = json.dumps(assemble_teacher_preview(build_example_plan(), RuntimeContext()).to_dict(), sort_keys=True)
b = json.dumps(assemble_teacher_preview(build_example_plan(), RuntimeContext()).to_dict(), sort_keys=True)
assert a == b
print("PASS test 9: preview assembly is deterministic/idempotent")
PY

# ---------------------------------------------------------------------------
# Test 10: publisher-derived label safety — labels derived, content intact.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
# Title is a derived display label, not canonical instructional content.
assert p.agenda["title"].startswith("Quarter 1, Week 3")
# Canonical in-class text is not rewritten.
math = next(c for c in p.courses if c.course == "Math")
mon = next(d for d in math.days if d.weekday == "Monday")
assert mon.in_class == "Lesson 11"
# Agenda page_url is a derived label, not a fabricated Canvas ID.
assert p.agenda["page_url"] == "weekly-agenda-q1w3"
print("PASS test 10: display labels are derived; canonical content not rewritten")
PY

# ---------------------------------------------------------------------------
# Test 11: legacy fixture conflict — canonical wins.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

ctx = RuntimeContext(legacy_fixtures={
    "math": {"Monday": {"in_class": "STALE FIXTURE VALUE"}},
    "canvas_config": {"math": {"course_id": "STALE_ID"}},
})
p = assemble_teacher_preview(build_example_plan(), ctx)
math = next(c for c in p.courses if c.course == "Math")
mon = next(d for d in math.days if d.weekday == "Monday")
assert mon.in_class == "Lesson 11"  # canonical wins, not fixture
assert "STALE FIXTURE VALUE" not in str(p.to_dict())
print("PASS test 11: legacy fixture cannot override canonical data")
PY

# ---------------------------------------------------------------------------
# Test 12: evidence survives the full path.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

plan = build_example_plan()
p = assemble_teacher_preview(plan, RuntimeContext())
math = next(c for c in p.courses if c.course == "Math")
thu = next(d for d in math.days if d.weekday == "Thursday")
assert any(e.get("sourceClass") == "teacher_instruction" for e in thu.evidence)
# Prediction events carry source evidence too.
ev = [e for e in p.prediction["predictions"] if e["subject"] == "math" and e["weekday"] == "Thursday"][0]
assert any(item.get("source_type") == "teacher_instruction" for item in ev["source_evidence"])
print("PASS test 12: evidence survives the full path")
PY

# ---------------------------------------------------------------------------
# Test 13: teacher instruction beats prediction (advisory only).
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
ev = [e for e in p.prediction["predictions"] if e["subject"] == "math" and e["weekday"] == "Thursday"][0]
assert ev["decision_layer"] == "teacher_instruction"
assert ev["manual_override_state"] == "teacher"
assert ev["in_class_title"] == "Review Lessons 12-13"
print("PASS test 13: teacher instruction outranks prediction (advisory only)")
PY

# ---------------------------------------------------------------------------
# Test 14: empty vs missing vs unresolved distinct states.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
hist = next(c for c in p.courses if c.course == "History")
mon = next(d for d in hist.days if d.weekday == "Monday")
wed = next(d for d in hist.days if d.weekday == "Wednesday")
# Empty homework (omitted) is distinct from unresolved and blank.
assert mon.status == "content" and mon.homework == ""
assert wed.status == "unresolved"
science = next(c for c in p.courses if c.course == "Science")
assert all(d.status == "protected" for d in science.days)
print("PASS test 14: empty/missing/unresolved/blank states are distinct")
PY

# ---------------------------------------------------------------------------
# Test 15: partial translation failure reports blocked (fail closed).
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

# A bad day in one course must fail closed rather than yield a partial preview.
plan = build_example_plan()
plan.courses["Math"].days[2].weekday = "Notaday"
try:
    assemble_teacher_preview(plan, RuntimeContext())
    raise SystemExit("FAIL test 15: invalid plan did not fail closed")
except ValueError:
    pass
print("PASS test 15: partial/failed translation fails closed (no false completeness)")
PY

# ---------------------------------------------------------------------------
# Test 16: date/week integrity — no downstream drift.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

plan = build_example_plan()
p = assemble_teacher_preview(plan, RuntimeContext())
assert p.week_code == plan.week_code == "Q1W3"
assert p.monday_date == "2026-08-03" and p.friday_date == "2026-08-07"
assert [d["weekday"] for d in p.days] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
print("PASS test 16: date/week identity preserved")
PY

# ---------------------------------------------------------------------------
# Test 17: cross-course isolation — no subject leakage.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

p = assemble_teacher_preview(build_example_plan(), RuntimeContext())
for e in p.prediction["predictions"]:
    if e["subject"] != "math":
        assert "Odd problems" not in e["in_class_title"] and "Odd problems" not in e["at_home_title"]
    if e["subject"] != "reading-spelling":
        assert "Read 20 min" not in e["in_class_title"] and "Read 20 min" not in e["at_home_title"]
# Math homework must never appear under History or Science.
for e in p.prediction["predictions"]:
    if e["subject"] in ("history", "science"):
        assert e["at_home_title"] in ("", "No Homework"), e
print("PASS test 17: cross-course isolation preserved")
PY

# ---------------------------------------------------------------------------
# Test 18: canonical immutability — downstream mutation cannot mutate canonical.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys, json, copy
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

plan = build_example_plan()
before = plan.to_dict()
p = assemble_teacher_preview(plan, RuntimeContext())
mut = json.loads(json.dumps(p.to_dict()))
mut["courses"][0]["days"][0]["in_class"] = "MUTATED"
mut["prediction"]["predictions"] = []
assert plan.to_dict() == before
print("PASS test 18: canonical WeeklyPlan is not mutated by downstream output")
PY

# ---------------------------------------------------------------------------
# Test 19: safe package imports — no execution modules loaded.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
import scripts.canvas_llm_phase22.contracts
import scripts.canvas_llm_phase24.contracts
import scripts.canvas_llm_phase26.contracts
import scripts.canvas_llm_phase18c.contracts
for mod in ("canvas_connector", "canvas_writer", "canvas_verification",
            "scripts.canvas_llm_phase22.phase22_workstation",
            "scripts.canvas_llm_phase22.weekly_agenda_publisher",
            "scripts.canvas_llm_phase24.rule_engine",
            "scripts.canvas_llm_phase26.pipeline"):
    assert mod not in sys.modules, mod
print("PASS test 19: safe package imports (no connector/writer/publisher/token loaded)")
PY

# ---------------------------------------------------------------------------
# Test 20: zero-write runtime — write modules not invoked.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

assemble_teacher_preview(build_example_plan(), RuntimeContext())
for mod in ("canvas_writer", "canvas_connector", "weekly_agenda_publisher"):
    assert mod not in sys.modules, mod
print("PASS test 20: zero-write runtime (no write module invoked)")
PY

# ---------------------------------------------------------------------------
# Test 21: protected course with non-blank content stays blocked end-to-end.
# ---------------------------------------------------------------------------
RUN_PY <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.models import DayEntry
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

plan = build_example_plan()
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
dates = ["2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07"]
plan.courses["Science"].days = [
    DayEntry(weekday=wd, date=d, in_class="Science Lesson", raw="Science Lesson",
             decided_source="live_pacing")
    for wd, d in zip(weekdays, dates)
]
p = assemble_teacher_preview(plan, RuntimeContext())
# Protected course content must never become a write-eligible downstream event.
assert not any(e["subject"] == "science" for e in p.prediction["predictions"])
snap = next(s for s in p.workstation["subjects"] if s["subject"] == "science")
assert snap["assignmentPolicy"] == "disabled"
assert snap["readinessState"] == "Blocked"
# The drift detector must remain clean and still classify each Science day as protected.
assert p.drift["invalid_drift"] == [], p.drift["invalid_drift"]
science = next(c for c in p.courses if c.course == "Science")
assert all(d.status == "protected" and d.derivation == "protected" for d in science.days)
print("PASS test 21: protected non-blank course produces no write-eligible object")
PY

echo "PASS: Canvas LLM Phase 18C preview assembly tests complete"
