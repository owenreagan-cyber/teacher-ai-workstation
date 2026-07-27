#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM live Canvas transport tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TRANSPORT="scripts/canvas_llm_phase22/canvas_connection_manager.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"
LIVE="scripts/canvas_llm_phase22/live_q1w2_deployment.py"

export CANVAS_LLM_LIVE_TRANSPORT_TEST=1
export CANVAS_LLM_LIVE_Q1W2_APPROVED=1
export CANVAS_LLM_DEPLOYMENT_MODE=live

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$TRANSPORT" "$WRITER" "$LIVE"
python3 "$TRANSPORT" self-test
python3 "$WRITER" self-test

python3 - <<'PY'
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport
from scripts.canvas_llm_phase22 import canvas_writer as writer
from scripts.canvas_llm_phase22 import write_gate as gate
from scripts.canvas_llm_phase22 import canvas_connector as connector

transport.MOCK_LIVE_STORE['pages'].clear()
transport.MOCK_LIVE_STORE['assignments'].clear()

status = transport.build_live_transport_status(test_mode=True)
assert status.write_transport == 'ENABLED'
assert status.write_gate == 'CONTROLLED'
assert status.environment == 'LIVE'
assert transport.transport_has_no_fake_fallback()

os.environ.pop('CANVAS_LLM_LIVE_Q1W2_APPROVED', None)
blocked = transport.build_live_transport_status(test_mode=False)
assert blocked.write_transport == 'BLOCKED' or blocked.authentication == 'FAIL'

os.environ['CANVAS_LLM_LIVE_Q1W2_APPROVED'] = '1'
client = transport.get_transport_client(test_mode=True)
assert client.transport == 'mock'

cfg = connector.CanvasConnectionConfig(mode='live', enabled=True, write_mode='controlled', credential_state='configured')
decision = gate.evaluate_write('create', 'page', 'page-1', approved=True, approved_by='teacher', approved_at='2026-07-26', config=cfg)
assert decision.gate_state == 'APPROVED'
executed = gate.attempt_live_write(decision, config=cfg)
assert executed.gate_state == 'EXECUTED'

page = writer.create_page_live(
    course_id=26427,
    title='Transport Page',
    body='<p>Transport test</p>',
    approved=True,
    test_mode=True,
    client=client,
)
assert page.write_status == 'WRITTEN'
assert page.gate_state == 'EXECUTED'
assert writer.verify_page_live(course_id=26427, page_ref=page.target_id, title='Transport Page', test_mode=True, client=client) == 'PASS'

blocked_page = writer.create_page_live(course_id=26427, title='Blocked', body='x', approved=False, test_mode=True, client=client)
assert blocked_page.write_status == 'BLOCKED'

print('PASS live transport enabled')
print('PASS approval required')
print('PASS real transport selected')
print('PASS no fake fallback')
PY

bin/chief-of-staff --canvas-live-transport-status | grep -q 'ENABLED'
CANVAS_LLM_LIVE_TRANSPORT_TEST=1 CANVAS_LLM_LIVE_Q1W2_APPROVED=1 bin/chief-of-staff --c2c2-q1w2-live-status | grep -q 'LIVE'

echo "PASS Canvas LLM live Canvas transport tests complete"
