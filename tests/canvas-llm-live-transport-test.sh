#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM live transport read verification tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TRANSPORT="scripts/canvas_llm_phase22/canvas_connection_manager.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$TRANSPORT"
python3 "$TRANSPORT" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport

HOMEROOM = transport.HOMEROOM_COURSE_ID
MATH = transport.MATH_COURSE_ID
READING = transport.READING_COURSE_ID

allowed = [
    ('GET', f'/api/v1/courses/{HOMEROOM}'),
    ('GET', f'/api/v1/courses/{HOMEROOM}/pages/q1w2-weekly-agenda'),
    ('GET', f'/api/v1/courses/{MATH}/assignments/987654'),
    ('GET', f'/api/v1/courses/{READING}/assignment_groups'),
]
for method, path in allowed:
    transport.validate_live_transport_path(method, path)

blocked = [
    ('GET', f'/api/v1/courses/{HOMEROOM}/students'),
    ('GET', f'/api/v1/courses/{HOMEROOM}/users/123'),
    ('GET', f'/api/v1/courses/{MATH}/submissions/456'),
    ('GET', f'/api/v1/courses/{READING}/gradebook'),
    ('GET', f'/api/v1/courses/{HOMEROOM}/enrollments'),
    ('GET', f'/api/v1/courses/{MATH}/modules'),
    ('GET', f'/api/v1/courses/{READING}/files'),
    ('PATCH', f'/api/v1/courses/{HOMEROOM}/assignments/987654'),
    ('DELETE', f'/api/v1/courses/{HOMEROOM}/pages/agenda'),
    ('POST', f'/api/v1/courses/{HOMEROOM}/files'),
    ('PUT', f'/api/v1/courses/{HOMEROOM}/modules/5'),
]
for method, path in blocked:
    try:
        transport.validate_live_transport_path(method, path)
    except PermissionError:
        continue
    raise AssertionError(f'expected blocked path: {method} {path}')

# Update/remove operations are now allowlisted for the approved manifest.
update_allowed = [
    ('PUT', f'/api/v1/courses/{MATH}/assignments/987654'),
    ('DELETE', f'/api/v1/courses/{MATH}/assignments/987654'),
    ('PUT', f'/api/v1/courses/{HOMEROOM}/pages/agenda'),
    ('PUT', f'/api/v1/courses/{HOMEROOM}/discussion_topics/987'),
    ('DELETE', f'/api/v1/courses/{HOMEROOM}/discussion_topics/987'),
    ('POST', f'/api/v1/courses/{HOMEROOM}/discussion_topics'),
]
for method, path in update_allowed:
    transport.validate_live_transport_path(method, path)

print('PASS GET course allowed')
print('PASS GET page verification allowed')
print('PASS GET assignment verification allowed')
print('PASS GET assignment groups allowed')
print('PASS student endpoints blocked')
print('PASS submission endpoints blocked')
print('PASS grade endpoints blocked')
PY

echo "PASS Canvas LLM live transport read verification tests complete"
