#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM homework rules tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RULES="scripts/canvas_llm_phase22/homework_rules.py"
PACING="scripts/canvas_llm_phase22/pacing_parser.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$RULES" "$PACING"
python3 "$RULES" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import pacing_parser as pacing
from scripts.canvas_llm_phase22 import homework_rules as rules

week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14'}
rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'math', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
]
plan = pacing.parse_rows_to_plan(week_meta, rows)
apps = rules.apply_rules(plan)

assert any(a.rule_id == 'math-monday-homework' for a in apps)
assert any(a.rule_id == 'math-wednesday-homework' for a in apps)
assert sum(1 for a in apps if 'Practice Check' in a.title) == 2
assert sum(1 for a in apps if 'Comprehension' in a.title) == 2
assert sum(1 for a in apps if a.rule_id.startswith('reading-') and 'Workbook' in a.title and 'Comprehension' not in a.title) == 2
assert any(a.rule_id == 'spelling-test' and a.title == 'Spelling Test 5' for a in apps)
assert rules.rules_have_no_canvas_writes()

print('PASS Math Monday rule')
print('PASS Math Wednesday rule')
print('PASS Math practice checks')
print('PASS Reading comprehension rule')
print('PASS Reading workbook rule')
print('PASS Spelling assessment rule')
PY

bin/chief-of-staff --homework-rules-status | grep -q 'Homework Rules'

echo "PASS Canvas LLM homework rules tests complete"
