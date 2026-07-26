#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM sandbox connector tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONNECTOR="scripts/canvas_llm_phase22/canvas_connector.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$CONNECTOR" "$WRITER"
python3 "$CONNECTOR" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connector as connector
from scripts.canvas_llm_phase22 import canvas_writer as writer

writer.FAKE_CANVAS_STORE['pages'].clear()
writer.FAKE_CANVAS_STORE['announcements'].clear()

fake_cfg = connector.default_connection_config()
fake = connector.CanvasConnector(fake_cfg)
assert fake_cfg.mode == 'fake'
assert fake.connector_available() is True

sandbox_cfg = connector.sandbox_connection_config()
sandbox = connector.CanvasConnector(sandbox_cfg)
assert sandbox_cfg.mode == 'sandbox'
assert sandbox.connector_available() is False

sandbox_config = connector.CanvasSandboxConfig()
assert sandbox_config.stores_credentials() is False
assert 'token' not in sandbox_config.to_dict()
assert connector.production_mode_disabled()

writer.FAKE_CANVAS_STORE['pages']['agenda-q1w5'] = {
    'course_id': connector.SANDBOX_COURSE_ID,
    'title': 'Weekly Agenda',
    'body': '<p>agenda</p>',
    'body_hash': writer.body_hash('Weekly Agenda', '<p>agenda</p>'),
}
pages = fake.list_pages(connector.SANDBOX_COURSE_ID)
assert len(pages) >= 1

missing = fake.find_existing_object(
    connector.SANDBOX_COURSE_ID,
    'page',
    target_id='new-page',
    title='New Page',
    expected_hash='xyz',
)
assert missing.result == 'MISSING'

matched = fake.find_existing_object(
    connector.SANDBOX_COURSE_ID,
    'page',
    target_id='agenda-q1w5',
    title='Weekly Agenda',
    expected_hash=writer.body_hash('Weekly Agenda', '<p>agenda</p>'),
)
assert matched.result == 'MATCH'

conflict = fake.find_existing_object(
    connector.SANDBOX_COURSE_ID,
    'page',
    target_id='agenda-q1w5',
    title='Weekly Agenda',
    expected_hash='different',
)
assert conflict.result == 'CONFLICT'

assert connector.connector_has_no_writes()
assert connector.CanvasSandboxConfig().stores_credentials() is False

print('PASS fake mode available')
print('PASS sandbox mode gated')
print('PASS no credentials stored')
print('PASS duplicate prevention MATCH/CONFLICT/MISSING')
PY

echo "PASS Canvas LLM sandbox connector tests complete"
