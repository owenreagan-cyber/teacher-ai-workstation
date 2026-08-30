#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM rule validation tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RULES="scripts/canvas_llm_phase22/curriculum_rules.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$RULES"

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import curriculum_rules as cr

library = cr.load_library()

math = cr.validate_subject('math', library)
assert math.state == 'PASS'
assert math.rule_count == 4

reading = cr.validate_subject('reading', library)
assert reading.state == 'PASS'

spelling = cr.validate_subject('spelling', library)
assert spelling.state == 'PASS'

history = cr.validate_subject('history', library)
assert history.state == 'MANUAL_MODE'
assert history.generation_mode == 'MANUAL'

science = cr.validate_subject('science', library)
assert science.state == 'MANUAL_MODE'

shurley = cr.validate_subject('shurley', library)
assert shurley.state == 'MANUAL_MODE'

language_arts = cr.validate_subject('language-arts', library)
assert language_arts.state == 'NEEDS_TEACHER_RULE'
assert language_arts.message == 'Teacher rule required.'

empty_library = cr.CurriculumRuleLibrary(
    profile=library.profile,
    rules=[],
    subjects_needing_teacher_rules=list(cr.SUBJECTS_NEEDING_TEACHER_RULES),
)
invalid = cr.validate_subject('math', empty_library)
assert invalid.state == 'INVALID'

validations = cr.validate_all_subjects(library)
assert any(v.state == 'PASS' for v in validations)
assert any(v.state == 'NEEDS_TEACHER_RULE' for v in validations)

print('PASS validation PASS state')
print('PASS validation MANUAL_MODE state')
print('PASS validation NEEDS_TEACHER_RULE state')
print('PASS validation INVALID state')
PY

echo "PASS Canvas LLM rule validation tests complete"
