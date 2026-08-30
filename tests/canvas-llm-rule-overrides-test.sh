#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM rule overrides tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RULES="scripts/canvas_llm_phase22/curriculum_rules.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$RULES"

python3 - <<'PY'
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import curriculum_rules as cr

library = cr.load_library()
baseline = copy.deepcopy(library)

override = cr.create_override(
    library,
    rule_id='math-wednesday-homework',
    field_changed='grading_policy.points',
    new_value=80,
    reason='Adjusted points for short week',
)
assert override.old_value == 100
assert override.new_value == 80
assert override.reason

effective = cr.effective_rules(library)
wed = next(rule for rule in effective if rule.rule_id == 'math-wednesday-homework')
assert wed.grading_policy['points'] == 80

assert any(event['event'] == 'override_created' for event in library.audit_history)

reverted = cr.revert_override(library, override.override_id)
assert reverted.reverted_at
assert not reverted.active
assert any(event['event'] == 'override_reverted' for event in library.audit_history)

restored = cr.effective_rules(library)
wed_restored = next(rule for rule in restored if rule.rule_id == 'math-wednesday-homework')
assert wed_restored.grading_policy['points'] == 100

loaded_overrides = cr.load_library().active_overrides()
assert len(loaded_overrides) == 2

print('PASS override creation')
print('PASS override application')
print('PASS audit history')
print('PASS reversible changes')
PY

bin/chief-of-staff --curriculum-profile-status | grep -q 'Overrides:'

echo "PASS Canvas LLM rule overrides tests complete"
