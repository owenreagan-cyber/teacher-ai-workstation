#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 18A canonical WeeklyPlan tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

PKG="scripts/canvas_llm_phase18a"
CLI="$PKG/cli.py"

echo "PASS compile check"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$PKG/__init__.py" "$PKG/models.py" "$PKG/validation.py" \
  "$PKG/source_precedence.py" "$PKG/precedent.py" "$PKG/examples.py" "$CLI"

echo "PASS no write-path token in Phase 18A package"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|http\.client|urllib\.request' \
  "$PKG"/*.py >/tmp/canvas_phase_18a_test_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18a_test_write_scan.txt
  echo "FAIL: write-path token found"
  exit 1
fi
rm -f /tmp/canvas_phase_18a_test_write_scan.txt

python3 - <<'PY'
import sys
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
from scripts.canvas_llm_phase18a.source_precedence import (
    precedence_rank,
    highest_precedence,
)
from scripts.canvas_llm_phase18a.precedent import is_anomaly, is_promotable
from scripts.canvas_llm_phase18a.examples import build_example_plan

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


def errors(plan):
    return "\n".join(validate_plan(plan).errors)


# 1. Fully populated five-day week validates.
plan = base_plan()
report = validate_plan(plan)
assert report.ok, report.errors
assert all(len(c.days) == 5 for c in plan.courses.values())
print("PASS fully populated five-day week validates")

# 2. Legitimate blank day validates and stays blank.
plan = base_plan()
plan.courses["Math"].days[4] = day("Friday", blank=True)
report = validate_plan(plan)
assert report.ok, report.errors
blank_day = plan.courses["Math"].days[4]
assert blank_day.blank and not blank_day.in_class and not blank_day.homework and not blank_day.raw
print("PASS legitimate blank day stays blank")

# 3. Unknown curriculum shorthand is preserved verbatim, not guessed.
plan = base_plan()
plan.courses["History"].days[2] = day(
    "Wednesday", in_class="", homework="", raw="S9 L3",
    decided="live_pacing", ambiguity="shorthand not in rule catalog",
)
report = validate_plan(plan)
assert report.ok, report.errors
entry = plan.courses["History"].days[2]
assert entry.raw == "S9 L3" and not entry.in_class and entry.ambiguity
print("PASS unknown curriculum shorthand preserved")

# 4. Teacher override takes precedence over pacing.
plan = base_plan()
plan.courses["Math"].days[3] = day(
    "Thursday", in_class="Review Lessons 12-13", homework="No Homework",
    raw="Lesson 14", decided="teacher_instruction",
    evidence=[PACING, TEACHER],
)
report = validate_plan(plan)
assert report.ok, report.errors
assert precedence_rank("teacher_instruction") < precedence_rank("live_pacing")
assert highest_precedence(["live_pacing", "teacher_instruction"]) == "teacher_instruction"
print("PASS teacher override takes precedence over pacing")

# 5. Canonical rule does not override teacher instruction.
plan = base_plan()
plan.courses["Math"].days[0] = day(
    "Monday", in_class="Teacher-chosen lesson", homework="",
    raw="Lesson 11", decided="teacher_instruction",
    evidence=[
        PACING,
        Evidence(source_class="canonical_rule", reference="canonical rule"),
        TEACHER,
    ],
)
report = validate_plan(plan)
assert report.ok, report.errors
print("PASS canonical rule does not override teacher instruction")

# 6. Precedent does not override pacing (must fail validation).
plan = base_plan()
plan.courses["Math"].days[0] = day(
    "Monday", in_class="Lesson 9", homework="", raw="Lesson 10",
    decided="precedent",
    evidence=[
        PACING,
        Evidence(source_class="precedent", reference="precedent", precedent_class="operational_behavior"),
    ],
)
errs = errors(plan)
assert errs, "expected validation to fail"
assert "lower precedence" in errs, errs
print("PASS precedent does not override pacing (validation fails)")

# 7. Anomaly cannot silently become a rule (must fail validation).
plan = base_plan()
plan.courses["Math"].days[0] = day(
    "Monday", in_class="Lesson 13", homework="", raw="Lesson 12",
    decided="precedent",
    evidence=[
        Evidence(source_class="precedent", reference="scout finding", precedent_class="anomaly"),
    ],
)
errs = errors(plan)
assert errs, "expected validation to fail"
assert "anomaly" in errs, errs
assert is_anomaly("anomaly") and not is_promotable("anomaly")
assert is_promotable("operational_behavior")
print("PASS anomaly cannot silently become a rule (validation fails)")

# 8. Protected Science and Homeroom remain protected.
plan = base_plan()
plan.courses["Science"] = CoursePlan(
    course="Science", protected=True,
    days=[day(w, blank=True) for w in WEEKDAYS],
)
plan.protected_courses = ["Science", "Homeroom"]
report = validate_plan(plan)
assert report.ok, report.errors
assert plan.courses["Science"].protected
assert "Science" in plan.protected_courses and "Homeroom" in plan.protected_courses
print("PASS protected Science and Homeroom remain protected")

# 9. Contradictory weekday/date fails validation.
plan = base_plan()
plan.courses["Math"].days[0] = DayEntry(
    weekday="Monday", date="2026-08-04", in_class="Lesson", homework="HW",
    raw="Lesson", decided_source="live_pacing", evidence=[PACING],
)
errs = errors(plan)
assert errs, "expected validation to fail"
assert "does not fall on Monday" in errs, errs
print("PASS contradictory weekday/date fails validation")

# 10. Serialization round trip.
plan = build_example_plan()
restored = WeeklyPlan.from_json(plan.to_json())
assert plan.to_dict() == restored.to_dict()
restored2 = WeeklyPlan.from_dict(plan.to_dict())
assert plan.to_dict() == restored2.to_dict()
print("PASS serialization round trip")

# 11. No write-path invocation: the model types expose no write/HTTP surface,
# and building + validating + serializing runs entirely in memory.
for cls in (WeeklyPlan, CoursePlan, DayEntry, Evidence):
    for name in dir(cls):
        assert not any(m in name for m in ("write", "post", "put", "patch", "delete")), (cls.__name__, name)
example = build_example_plan()
assert validate_plan(example).ok
_ = example.to_json()
print("PASS no write-path invocation during Phase 18A model path")
PY

echo "PASS Canvas LLM Phase 18A canonical WeeklyPlan tests complete"
