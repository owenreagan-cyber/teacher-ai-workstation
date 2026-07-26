#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM canvas connector tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONNECTOR="scripts/canvas_llm_phase22/canvas_connector.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-connector.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$CONNECTOR"
python3 "$CONNECTOR" self-test

python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connector as connector

fake = connector.CanvasConnector(connector.default_connection_config())
assert fake.config.mode == 'fake'
assert fake.config.credential_state == 'missing'
assert fake.connector_available() is True
course = fake.read_course(26427)
assert course.course_id == 26427

sandbox = connector.CanvasConnector(connector.sandbox_connection_config())
assert sandbox.config.mode == 'sandbox'
assert sandbox.config.enabled is False
assert sandbox.connector_available() is False

assert connector.connector_has_no_writes()
assert 'token' not in connector.default_connection_config().to_dict()

print('PASS fake connector reads normalized records')
print('PASS sandbox mode disabled by default')
print('PASS no credentials stored')
print('PASS no write transport references')
PY

bin/chief-of-staff --canvas-connector-status | grep -q 'Writes:'
bin/chief-of-staff --canvas-connector-status | grep -q 'disabled'

echo "PASS Canvas LLM canvas connector tests complete"
