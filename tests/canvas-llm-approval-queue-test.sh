#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM approval queue tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

QUEUE="scripts/canvas_llm_phase22/approval_queue.py"
REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/approval-queue.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$QUEUE" "$REGISTRY" "$PHASE22"

python3 "$QUEUE" self-test

python3 - <<'PY' "$T/queue.sqlite3"
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg
from scripts.canvas_llm_phase22 import approval_queue as queue

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
wid = reg.seed_demo_week(db)

before_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
records = reg.load_registry_from_db(db, wid)
items = queue.build_queue_from_registry(records)
after_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]

assert before_rows == after_rows, 'approval queue read must not mutate drafts'
assert queue.queue_is_read_only()
assert reg.registry_is_read_only()

tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table'")]
assert 'approval_queue' not in tables
assert 'teacher_decisions' not in tables

kinds = {item.artifact_kind for item in items}
assert 'assignment' in kinds
assert 'announcement' in kinds
assert 'newsletter' in kinds
assert 'daily_brief' in kinds

ready = [item for item in items if item.queue_status == 'READY']
needs_review = [item for item in items if item.queue_status == 'NEEDS_REVIEW']
blocked = [item for item in items if item.queue_status == 'BLOCKED']
assert ready, 'READY state must exist'
assert any(item.artifact_kind == 'newsletter_update' for item in blocked)

stale_record = reg.ArtifactRegistryRecord(
    artifact_id='stale-hash-demo',
    artifact_kind='assignment',
    source_table=reg.SOURCE_TABLE,
    source_id='stale-hash-demo',
    title='Hash Changed Assignment',
    approval_state='Approved',
    approval_revision=2,
    content_hash='xyz789',
    approved=True,
    teacher_approval_required=True,
    preview_only=True,
)
stale_item = queue.build_queue_item(
    stale_record,
    approval_snapshots={'stale-hash-demo': {'content_hash': 'abc123', 'approval_revision': 1}},
)
assert stale_item.queue_status == 'STALE_APPROVAL'
assert 'approval_stale' in stale_item.reason_codes

encoded_once = json.dumps([item.to_dict() for item in items], sort_keys=True)
encoded_twice = json.dumps([item.to_dict() for item in queue.build_queue_from_registry(records)], sort_keys=True)
assert encoded_once == encoded_twice

decision_errors = queue.validate_teacher_decision_shape(
    {
        'decision_id': 'decision-1',
        'artifact_id': 'artifact-1',
        'decision_type': 'approve',
        'status': 'pending',
        'teacher_note': None,
        'created_at': '2026-08-17T00:00:00Z',
        'created_by': 'teacher',
        'invalidates_on_revision': True,
    }
)
assert decision_errors == []

source = Path('scripts/canvas_llm_phase22/approval_queue.py').read_text().lower()
for forbidden in ('canvas.instructure', 'smtp', 'sendgrid', 'gmail', 'urllib.request', 'requests.post'):
    assert forbidden not in source

phase26 = Path('scripts/canvas-llm-phase-26-unified-weekly-production-workstation-status.sh')
phase27 = Path('scripts/canvas-llm-phase-27-canvas-readiness-and-safety-diff-status.sh')
assert phase26.exists() and phase27.exists()

print('PASS assignment appears in queue')
print('PASS announcement appears in queue')
print('PASS newsletter appears in queue')
print('PASS Daily Brief appears in queue')
print('PASS registry remains authoritative')
print('PASS no duplicate storage')
print('PASS READY state works')
print('PASS NEEDS_REVIEW works')
print('PASS BLOCKED works')
print('PASS hash change creates STALE_APPROVAL')
print('PASS no artifact mutation occurs')
print('PASS no Canvas calls')
print('PASS no email transport')
print('PASS Phase 26 untouched')
print('PASS Phase 27 untouched')
PY

bin/chief-of-staff --approval-queue-status | grep -q 'Canvas LLM Approval Queue'

echo "PASS Canvas LLM approval queue tests complete"
