#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM communication status tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMM="scripts/canvas_llm_phase22/communication_status.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$COMM"
python3 "$COMM" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import communication_status as comm

report = comm.build_communication_status()
assert report.canvas_announcements.state == 'READY'
assert report.daily_teacher_brief.state == 'READY'
assert report.morning_email.state == 'PLANNED'
assert report.automatic_sending.state == 'DISABLED'
assert report.template_validation == 'PASS'

valid, issues = comm.validate_announcement_template(comm.SAMPLE_ANNOUNCEMENT)
assert valid is True
assert not issues

blocked, blocked_issues = comm.validate_announcement_template({
    'body': 'Attached study guide and answer key.',
})
assert blocked is False
assert any('study guide' in item for item in blocked_issues)

assert comm.scan_for_blocked_content('practice word list here')
assert comm.communication_has_no_sends()

print('PASS announcement rules')
print('PASS morning email status')
print('PASS no automatic sending')
PY

bin/chief-of-staff --communication-status | grep -q 'Communication System'
bin/chief-of-staff --communication-status | grep -q 'DISABLED'

echo "PASS Canvas LLM communication status tests complete"
