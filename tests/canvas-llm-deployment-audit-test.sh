#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM deployment audit tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

AUDIT="scripts/canvas_llm_phase22/deployment_audit.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$AUDIT"
python3 "$AUDIT" self-test

python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import deployment_audit as audit

log = audit.DeploymentAuditLog()
log.record('artifact-001', 'validation', 'system', 'PASS')
log.record('artifact-001', 'readiness_check', 'system', 'Authorization: Bearer secret-token-abc')
assert log.count() == 2
payload = log.events[-1].to_dict()['result']
assert 'secret-token' not in payload
assert 'Bearer' not in payload

try:
    log.record('artifact-001', 'deployment_attempt', 'system', 'blocked')
    raise AssertionError('deployment_attempt must be blocked')
except ValueError:
    pass

print('PASS audit creation works')
print('PASS audit redaction works')
print('PASS no secret leakage in audit output')
print('PASS deployment_attempt events blocked')
PY

bin/chief-of-staff --canvas-audit-status | grep -q 'Events:'

echo "PASS Canvas LLM deployment audit tests complete"
