#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM curriculum rule lockdown tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RULES="scripts/canvas_llm_phase22/curriculum_rules.py"
HOMEWORK="scripts/canvas_llm_phase22/homework_rules.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$RULES" "$HOMEWORK"
python3 "$RULES" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import curriculum_rules as cr
from scripts.canvas_llm_phase22 import homework_rules as hr
from scripts.canvas_llm_phase22 import pacing_parser as pacing

library = cr.load_library()

for subject in cr.AUTO_SUBJECTS:
    validation = cr.validate_subject(subject, library)
    assert validation.state == 'PASS', subject
    assert validation.generation_mode == 'AUTO', subject
    behavior = library.behavior_for_subject(subject)
    assert behavior is not None and behavior.is_auto, subject

for subject in cr.MANUAL_SUBJECTS:
    validation = cr.validate_subject(subject, library)
    assert validation.state == 'MANUAL_MODE', subject
    behavior = library.behavior_for_subject(subject)
    assert behavior is not None and behavior.is_manual, subject
    assert behavior.homework_generation_enabled is False, subject
    assert behavior.canvas_enabled is False, subject

math = library.behavior_for_subject('math')
assert math.homework_generation_enabled is True

week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14'}
rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
    {'subject': 'history', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '8', 'tests': '', 'title': 'Chapter 8', 'notes': '', 'unit': 'The American Revolution', 'chapter': '8'},
    {'subject': 'science', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '4', 'tests': '', 'title': 'Chapter 4', 'notes': '', 'unit': 'Energy and Matter', 'chapter': '4'},
    {'subject': 'shurley', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '1.3', 'tests': '', 'title': 'Chapter 1 Lesson 3', 'notes': ''},
]
plan = pacing.parse_rows_to_plan(week_meta, rows)
apps = hr.apply_rules(plan, library)

assert any(a.rule_id == 'math-monday-homework' for a in apps)
assert any(a.rule_id == 'reading-tuesday-comprehension' for a in apps)
assert any(a.rule_id == 'spelling-test' for a in apps)

history = next(a for a in apps if a.subject == 'history')
assert history.entry_type == 'in_class'
assert 'The American Revolution' in history.description
assert 'Manual Teacher Rule' in history.description
assert history.homework_enabled is False
assert history.canvas_assignment_enabled is False

science = next(a for a in apps if a.subject == 'science')
assert science.entry_type == 'in_class'
assert 'Energy and Matter' in science.description

shurley = next(a for a in apps if a.subject == 'shurley')
assert shurley.entry_type == 'in_class'
assert 'Chapter 1, Lesson 3' in shurley.description

assert not any(a.category == 'homework' and a.subject in cr.MANUAL_SUBJECTS for a in apps)
assert not any(a.canvas_assignment_enabled for a in apps if a.subject in cr.MANUAL_SUBJECTS)

incomplete_rows = [
    {'subject': 'history', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '8', 'tests': '', 'title': 'Chapter 8', 'notes': ''},
    {'subject': 'science', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '', 'tests': '', 'title': 'Energy unit study', 'notes': '', 'unit': 'Energy and Matter'},
    {'subject': 'shurley', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
]
incomplete_plan = pacing.parse_rows_to_plan(week_meta, incomplete_rows)
incomplete_apps = hr.apply_manual_subject_rules(incomplete_plan, library)
assert not any(a.subject == 'history' for a in incomplete_apps)
assert not any(a.subject == 'science' for a in incomplete_apps)
assert not any(a.subject == 'shurley' for a in incomplete_apps)

shurley_ref = cr.parse_shurley_reference('1.3')
assert shurley_ref.chapter == '1' and shurley_ref.lesson == '3'
try:
    cr.parse_shurley_reference('3')
    raise AssertionError('expected shurley rejection')
except ValueError:
    pass

sections = cr.filter_nonempty_sections({'Homework': [], 'Assessment': ['Quiz'], 'Materials': [], 'Notes': []})
assert 'Homework' not in sections
assert 'Materials' not in sections
assert 'Notes' not in sections
rendered = cr.render_labeled_sections({'Homework': [], 'Assessment': [], 'Materials': [], 'Notes': []})
assert rendered == ''
assert 'None' not in cr.render_labeled_sections({'Homework': ['Worksheet']})

summary = cr.curriculum_rules_status_summary(library)
assert summary['math'] == 'AUTO PASS'
assert summary['reading'] == 'AUTO PASS'
assert summary['spelling'] == 'AUTO PASS'
assert summary['history'] == 'MANUAL MODE'
assert summary['science'] == 'MANUAL MODE'
assert summary['shurley'] == 'MANUAL MODE'

preview = cr.behavior_preview_for_subject('history', library)
assert preview['generation'] == 'In Class Only'
assert preview['homework'] == 'Disabled'
assert preview['canvas_assignment'] == 'Disabled'

assert cr.rules_have_no_canvas_writes()
assert hr.rules_have_no_canvas_writes()

print('PASS AUTO subject behavior')
print('PASS MANUAL subject behavior')
print('PASS History unit_chapter lockdown')
print('PASS Science unit_chapter lockdown')
print('PASS Shurley chapter_lesson lockdown')
print('PASS incomplete reference rejection')
print('PASS empty section omission')
print('PASS no homework for MANUAL subjects')
print('PASS no Canvas assignment generation for MANUAL subjects')
PY

bin/chief-of-staff --curriculum-rules-status | grep -q 'AUTO PASS'
bin/chief-of-staff --curriculum-rules-status | grep -q 'MANUAL MODE'
bin/chief-of-staff --curriculum-behavior-preview History | grep -q 'In Class Only'
bin/chief-of-staff --curriculum-behavior-preview History | grep -q 'Disabled'

echo "PASS Canvas LLM curriculum rule lockdown tests complete"
