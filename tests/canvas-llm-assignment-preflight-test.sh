#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM assignment preflight tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PREVIEW="scripts/canvas_llm_phase22/assignment_deployment_preview.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$PREVIEW" "$WRITER"
python3 "$PREVIEW" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import assignment_deployment_preview as preview
from scripts.canvas_llm_phase22 import canvas_writer as writer

ready = preview.preflight_assignment(
    preview.AssignmentDeploymentPreview(
        assignment_id='a1',
        title='Math Practice',
        description='Complete exercises 1-10.',
        points=10,
        due_date='2026-08-20',
        category='homework',
        submission_type='online_text_entry',
    )
)
assert ready.readiness == 'READY'

blocked = preview.preflight_assignment(
    preview.AssignmentDeploymentPreview(
        assignment_id='a2',
        title='',
        description='',
        points=-5,
        due_date='',
        category='bad',
        submission_type='invalid',
    )
)
assert blocked.readiness == 'BLOCKED'

try:
    writer.create_assignment()
    raise AssertionError('create_assignment should be blocked')
except RuntimeError:
    pass

try:
    preview.create_assignment_blocked()
except RuntimeError:
    pass

assert preview.assignment_writes_disabled()
assert writer.writer_has_no_assignment_writes()

source = Path('scripts/canvas_llm_phase22/assignment_deployment_preview.py').read_text().lower()
assert 'requests.post' not in source
assert 'canvas.instructure' not in source

print('PASS assignment validation returns READY for complete fields')
print('PASS missing fields blocked')
print('PASS create_assignment unavailable')
print('PASS no assignment write paths')
PY

echo "PASS Canvas LLM assignment preflight tests complete"
