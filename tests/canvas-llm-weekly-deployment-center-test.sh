#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM weekly deployment center tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CENTER="scripts/canvas_llm_phase22/weekly_deployment_center.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$CENTER"
python3 "$CENTER" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import weekly_deployment_center as center

packet = {
    'weekCode': 'Q1W5',
    'approvalState': 'draft',
    'instructionalWeek': {'code': 'Q1W5'},
    'artifacts': [
        {'kind': 'agenda', 'title': 'Weekly Agenda Page'},
        {'kind': 'announcement', 'title': 'Math Assessment Announcement'},
        {'kind': 'newsletter', 'title': 'Newsletter Page', 'existing': True},
        {'kind': 'assignment', 'title': 'Math Lesson 18'},
    ],
}
preview = center.build_preview_from_packet(packet)
assert preview.week_code == 'Q1W5'
assert preview.artifact_count >= 3
assert preview.blocked_count >= 1
assert preview.requires_teacher_action is True
assert any(c.operation == 'BLOCKED' and 'Assignment' in c.reason for c in preview.changes)
assert any(c.operation == 'UPDATE' for c in preview.changes)
assert center.preview_performs_no_execution()

print('PASS preview generation')
print('PASS multiple artifacts listed')
print('PASS assignments blocked')
print('PASS no execution paths')
PY

echo "PASS Canvas LLM weekly deployment center tests complete"
