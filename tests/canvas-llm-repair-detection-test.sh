#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM repair detection tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REPAIR="scripts/canvas_llm_phase22/canvas_repair.py"
VERIFY="scripts/canvas_llm_phase22/canvas_verification.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$REPAIR" "$VERIFY" "$WRITER"
python3 "$REPAIR" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_repair as repair
from scripts.canvas_llm_phase22 import canvas_writer as writer
from scripts.canvas_llm_phase22 import canvas_connector as connector

writer.FAKE_CANVAS_STORE['pages'].clear()
expected = 'August Newsletter'
actual = 'July Newsletter'
body = '<p>Monthly update</p>'
writer.FAKE_CANVAS_STORE['pages']['newsletter-aug'] = {
    'course_id': connector.SANDBOX_COURSE_ID,
    'title': actual,
    'body': body,
    'body_hash': writer.body_hash(actual, body),
}

rec = repair.detect_page_drift(
    'artifact-001',
    connector.SANDBOX_COURSE_ID,
    'newsletter-aug',
    expected_title=expected,
    expected_body_hash=writer.body_hash(expected, body),
)
assert rec is not None
assert 'DRIFT DETECTED' in rec.issue
assert rec.requires_teacher_approval is True
assert rec.recommended_action in repair.REPAIR_ACTIONS

recs = repair.scan_for_drift([
    {
        'target_type': 'page',
        'artifact_id': 'artifact-001',
        'course_id': connector.SANDBOX_COURSE_ID,
        'target_id': 'newsletter-aug',
        'expected_title': expected,
        'expected_body_hash': writer.body_hash(expected, body),
    },
])
assert len(recs) == 1
assert repair.repair_has_no_auto_fix()

source = Path('scripts/canvas_llm_phase22/canvas_repair.py').read_text().lower()
for transport in ('requests.post', 'canvas.instructure', 'auto_repair(', 'self_heal('):
    assert transport not in source, f'forbidden pattern found: {transport}'
assert 'requires_teacher_approval' in source

print('PASS drift detection identifies title mismatch')
print('PASS recommendation created with teacher approval required')
print('PASS no automatic repair paths')
PY

bin/chief-of-staff --canvas-repair-status | grep -q 'No automatic repairs'

echo "PASS Canvas LLM repair detection tests complete"
