#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM grading optimizer tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OPTIMIZER="scripts/canvas_llm_phase22/grading_optimizer.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$OPTIMIZER"
python3 "$OPTIMIZER" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import grading_optimizer as opt
from scripts.canvas_llm_phase22 import pacing_parser as pacing

plan = opt.build_q1w2_grading_plan()
assert plan.week_code == 'Q1W2'
assert plan.instructional_days == 5
assert not plan.short_week

math_result = next(r for r in plan.subject_results if r.subject == 'math')
assert len(math_result.recommended_grade_items) == 3
assert any('Lesson 2 Homework' in item for item in math_result.recommended_grade_items)
assert any('Tuesday Classwork' in item for item in math_result.recommended_grade_items)
assert any('Lesson 4 Homework' in item for item in math_result.recommended_grade_items)
assert 'Thursday Classwork' in math_result.deferred_items
assert math_result.status == 'READY'

reading_result = next(r for r in plan.subject_results if r.subject == 'reading')
assert len(reading_result.recommended_grade_items) == 3
assert any('Lesson 3' in item for item in reading_result.recommended_grade_items)
assert any('Wednesday Workbook' in item for item in reading_result.recommended_grade_items)
assert any('Lesson 5' in item for item in reading_result.recommended_grade_items)

spelling_result = next(r for r in plan.subject_results if r.subject == 'spelling')
assert spelling_result.recommended_grade_items == ['Spelling Test 5']
assert any('Friday assessment' in w for w in spelling_result.warnings)

assert len(plan.teacher_decisions) == 2
assert all(d['automatic_selection'] is False for d in plan.teacher_decisions)

short_meta = {'code': 'Q1W3', 'startsOn': '2026-08-03', 'endsOn': '2026-08-05'}
short_rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-03', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-04', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-05', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-03', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
]
short_plan = pacing.parse_rows_to_plan(short_meta, short_rows)
short_result = opt.optimize_week(short_plan)
assert short_result.short_week is True
math_short = next(r for r in short_result.subject_results if r.subject == 'math')
assert math_short.status == 'TEACHER REVIEW REQUIRED'

summary = opt.grading_optimization_dashboard_summary(plan)
assert 'Math' in summary['ready']
assert 'Reading' in summary['ready']

assert opt.optimizer_performs_no_canvas_writes()

print('PASS normal week optimization')
print('PASS math recommendations')
print('PASS reading recommendations')
print('PASS assessment awareness')
print('PASS short week detection')
print('PASS teacher decision points')
print('PASS no Canvas writes')
PY

bin/chief-of-staff --grading-optimization-preview | grep -q 'Grading Optimization Preview'
bin/chief-of-staff --grading-optimization-preview | grep -q 'Q1W2'
bin/chief-of-staff --grading-optimization-preview | grep -q 'No Canvas writes performed'

echo "PASS Canvas LLM grading optimizer tests complete"
