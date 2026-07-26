#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM curriculum rules tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RULES="scripts/canvas_llm_phase22/curriculum_rules.py"
LIBRARY="config/curriculum/canvas/curriculum-rule-library-2026-2027-grade-4.json"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$RULES"
python3 "$RULES" self-test

python3 - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import curriculum_rules as cr
from scripts.canvas_llm_phase22 import homework_rules as hr
from scripts.canvas_llm_phase22 import pacing_parser as pacing

library = cr.load_library()
assert library.profile.profile_id == '2026-2027-grade-4-default'
assert len(library.active_rules()) == 9

payload = json.loads(Path('config/curriculum/canvas/curriculum-rule-library-2026-2027-grade-4.json').read_text())
assert payload['profile']['label'] == '2026-2027 Grade 4 Default Profile'

math_rules = [rule for rule in library.active_rules() if rule.subject == 'math']
assert len(math_rules) == 4
assert any('12-30 even' in rule.generation_pattern.lower() for rule in math_rules)

reading_rules = [rule for rule in library.active_rules() if rule.subject == 'reading']
assert len(reading_rules) == 4

spelling_rules = [rule for rule in library.active_rules() if rule.subject == 'spelling']
assert len(spelling_rules) == 1
assert spelling_rules[0].rule_type == 'assessment'

history = cr.validate_subject('history', library)
assert history.state == 'MANUAL_MODE'
science = cr.validate_subject('science', library)
assert science.state == 'MANUAL_MODE'
shurley = cr.validate_subject('shurley', library)
assert shurley.state == 'MANUAL_MODE'

week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14'}
rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
]
plan = pacing.parse_rows_to_plan(week_meta, rows)
apps = hr.apply_rules(plan, library)
assert any(a.rule_id == 'math-monday-homework' for a in apps)
assert any(a.rule_id == 'reading-tuesday-comprehension' for a in apps)
assert any(a.rule_id == 'spelling-test' for a in apps)

assert cr.rules_have_no_canvas_writes()

print('PASS rule creation')
print('PASS profile loading')
print('PASS Math rules from library')
print('PASS Reading rules from library')
print('PASS Spelling rules from library')
print('PASS missing rule detection for language-arts only')
PY

bin/chief-of-staff --curriculum-rules-status | grep -q 'Curriculum Rules'
bin/chief-of-staff --curriculum-rules-status | grep -q 'MANUAL MODE'

echo "PASS Canvas LLM curriculum rules tests complete"
