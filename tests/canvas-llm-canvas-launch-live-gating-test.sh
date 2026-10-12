#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas launcher live-transport gating tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LAUNCH="scripts/canvas_llm_phase22/canvas_launcher.py"

python3 -m py_compile "$LAUNCH"

python3 - <<'PY'
import contextlib
import io
import os
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_phase22 import canvas_launcher as launcher
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport

APPROVED = {
    'weekCode': 'Q1W5',
    'approval': {'teacherApproved': True, 'approvedBy': 'Owen Reagan', 'approvedAt': '2026-08-16T14:00:00-04:00'},
    'actions': [],
}
UNAPPROVED = {
    'weekCode': 'Q1W5',
    'approval': {'teacherApproved': False, 'approvedBy': None, 'approvedAt': None},
    'actions': [],
}
FAKE_TOKEN = 'gating-test-secret-token-7f3a'


# 1. approved launch + valid credentials selects the live transport.
captured = {}
def fake_apply(rows, *, test_mode=False, client=None):
    captured['client'] = client
    captured['test_mode'] = test_mode
    return 0

def load_fake_creds():
    os.environ['CANVAS_BASE_URL'] = 'https://thalesacademy.instructure.com'
    os.environ['CANVAS_TOKEN'] = FAKE_TOKEN

buf = io.StringIO()
with mock.patch.object(launcher, 'load_manifest', return_value=dict(APPROVED)), \
     mock.patch.object(launcher.credentials, 'load_credentials', side_effect=load_fake_creds), \
     mock.patch.object(launcher, '_fetch_live_inventory', return_value={'courses': {}}), \
     mock.patch.object(launcher, 'run_preflight', return_value=([], [])), \
     mock.patch.object(launcher, '_write_backup', return_value=Path('/tmp/gating-backup.json')), \
     mock.patch.object(launcher, '_apply_approved', side_effect=fake_apply), \
     contextlib.redirect_stdout(buf):
    rc = launcher.command_launch('Q1W5', test_mode=False)
assert rc == 0, rc
assert captured['test_mode'] is False
assert isinstance(captured['client'], transport.Phase22LiveCanvasClient), type(captured['client'])
assert FAKE_TOKEN not in buf.getvalue(), 'token must not appear in launch output'
print('PASS approved launch + valid credentials selects live transport')

# 2. unapproved launch never selects the live transport.
with mock.patch.object(launcher, 'load_manifest', return_value=dict(UNAPPROVED)), \
     mock.patch.object(launcher.credentials, 'load_credentials',
                       side_effect=AssertionError('creds must not load when unapproved')), \
     mock.patch.object(launcher, '_build_live_client',
                       side_effect=AssertionError('live client must not build when unapproved')), \
     mock.patch.object(launcher, '_fetch_live_inventory',
                       side_effect=AssertionError('no live GET when unapproved')):
    rc = launcher.command_launch('Q1W5', test_mode=False)
assert rc == 1, rc
print('PASS unapproved launch never selects live transport')

# 3. preflight never writes (GET-only).
with mock.patch.object(launcher.credentials, 'load_credentials', return_value={'CANVAS_BASE_URL': 'x', 'CANVAS_TOKEN': 'y'}), \
     mock.patch.object(launcher, '_fetch_live_inventory', return_value={'courses': {}}), \
     mock.patch.object(launcher, 'run_preflight', return_value=([], [])), \
     mock.patch.object(launcher, '_build_live_client',
                       side_effect=AssertionError('preflight must not build a write client')), \
     mock.patch.object(launcher, '_apply_approved',
                       side_effect=AssertionError('preflight must never apply writes')):
    rc = launcher.command_preflight('Q1W5')
assert rc == 0, rc
print('PASS preflight never writes')

# 4. missing credentials still block.
with mock.patch.object(launcher, 'load_manifest', return_value=dict(APPROVED)), \
     mock.patch.object(launcher.credentials, 'load_credentials',
                       side_effect=launcher.credentials.CredentialError('missing credentials')), \
     mock.patch.object(launcher, '_build_live_client',
                       side_effect=AssertionError('live client must not build without creds')), \
     mock.patch.object(launcher, '_fetch_live_inventory',
                       side_effect=AssertionError('no live GET without creds')):
    rc = launcher.command_launch('Q1W5', test_mode=False)
assert rc == 1, rc
print('PASS missing credentials still block')

print('PASS Canvas launcher live-transport gating tests complete')
PY

echo "PASS Canvas launcher live-transport gating tests complete"
