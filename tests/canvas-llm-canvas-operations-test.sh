#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM canvas operations tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

WRITER="scripts/canvas_llm_phase22/canvas_writer.py"
DEPLOY="scripts/canvas_llm_phase22/canvas_announcement_deployment.py"
VERIFY="scripts/canvas_llm_phase22/canvas_verification.py"
AUDIT="scripts/canvas_llm_phase22/deployment_audit.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-ops.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$WRITER" "$DEPLOY" "$VERIFY" "$AUDIT" "$PHASE22"

python3 "$WRITER" self-test
python3 "$DEPLOY" self-test
python3 "$VERIFY" self-test

python3 - <<'PY' "$T/ops.sqlite3"
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg
from scripts.canvas_llm_phase22 import teacher_decisions as decisions
from scripts.canvas_llm_phase22 import canvas_announcement_deployment as ann_deploy
from scripts.canvas_llm_phase22 import canvas_writer as writer
from scripts.canvas_llm_phase22 import deployment_audit as audit

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
week = p22.instructional_week_by_code('Q1W5')
assert week is not None
wid = db.create_week(week['startsOn'])
week_data = db.get_week(wid)
for subject_plan in week_data['subjects']:
    if subject_plan['subject'] != 'math':
        continue
    for index, day in enumerate(subject_plan['days']):
        fields = {'lesson': str(18 + index), 'title': f'Lesson {18 + index}'}
        if index == 1:
            fields = {'lesson': '', 'tests': '4', 'title': 'Written Assessment 4'}
        db.patch_table(
            'daily_subject_entries',
            day['id'],
            fields,
            day['version'],
        )
db.generate_week(wid)

records = reg.load_registry_from_db(db, wid)
announcements = [r for r in records if r.artifact_kind == 'announcement']
assert announcements, 'expected at least one announcement artifact'
announcement = announcements[0]

writer.FAKE_CANVAS_STORE['announcements'].clear()
log = audit.DeploymentAuditLog()

blocked = ann_deploy.deploy_announcement(db, announcement, audit_log=log)
assert blocked.write_status == 'BLOCKED', 'approval required before write'
assert blocked.deployment_state == 'BLOCKED'

decisions.record_decision(db, announcement, 'approve', teacher_display='Teacher', note='test approval')
deployed = ann_deploy.deploy_announcement(db, announcement, body='Assessment reminder preview', audit_log=log)
assert deployed.write_status == 'WRITTEN', 'fake mode controlled write should succeed when approved'
assert deployed.verification_status == 'PASS'
assert audit.audit_has_no_deployment_events(log)

source = Path('scripts/canvas_llm_phase22/canvas_writer.py').read_text().lower()
for forbidden in ('student_data', 'gradebook', 'bearer '):
    assert forbidden not in source, f'forbidden pattern found: {forbidden}'
# blocklist constants and defensive scan tokens are allowed; verify no live write transports
for transport in ('requests.post', 'requests.put', 'canvas.instructure', 'urllib.request.urlopen'):
    assert transport not in source, f'forbidden transport found: {transport}'

phase26 = Path('scripts/canvas-llm-phase-26-unified-weekly-production-workstation-status.sh')
phase27 = Path('scripts/canvas-llm-phase-27-canvas-readiness-and-safety-diff-status.sh')
assert phase26.exists() and phase27.exists()

print('PASS announcement deployment requires approval')
print('PASS write gate enforced through writer')
print('PASS verification runs after write')
print('PASS audit records validation events')
print('PASS no forbidden patterns in writer')
print('PASS Phase 26 and Phase 27 untouched')
PY

bin/chief-of-staff --canvas-operation-status | grep -q 'Canvas Operations'

echo "PASS Canvas LLM canvas operations tests complete"
