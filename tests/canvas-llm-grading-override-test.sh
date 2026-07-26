#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM grading override tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OPTIMIZER="scripts/canvas_llm_phase22/grading_optimizer.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$OPTIMIZER"

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import grading_optimizer as opt

opt._OVERRIDE_STORE.clear()

override = opt.create_grading_override(
    subject='math',
    week_code='Q1W2',
    assignment_id='artifact-math-classwork-tuesday',
    recommended_choice='Tuesday Classwork',
    teacher_choice='Thursday Classwork',
    reason='More representative of mastery',
)
assert override.override_id
assert override.recommended_choice == 'Tuesday Classwork'
assert override.teacher_choice == 'Thursday Classwork'

stored = opt.get_grading_override(override.override_id)
assert stored is not None
assert stored.teacher_choice == 'Thursday Classwork'

listed = opt.list_grading_overrides(week_code='Q1W2', subject='math')
assert len(listed) == 1

reverted = opt.revert_grading_override(override.override_id)
assert reverted is not None
assert reverted.reverted_at

assert opt.get_grading_override(override.override_id) is None
assert opt.list_grading_overrides(week_code='Q1W2') == []

assert opt.optimizer_performs_no_canvas_writes()

print('PASS override creation')
print('PASS override storage')
print('PASS override reversibility')
print('PASS no automatic teacher overrides')
PY

echo "PASS Canvas LLM grading override tests complete"
