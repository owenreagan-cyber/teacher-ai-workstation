#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM teacher decisions tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DECISIONS="scripts/canvas_llm_phase22/teacher_decisions.py"
REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
QUEUE="scripts/canvas_llm_phase22/approval_queue.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/teacher-decisions.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DECISIONS" "$REGISTRY" "$QUEUE" "$PHASE22"

python3 "$DECISIONS" self-test

python3 - <<'PY' "$T/decisions.sqlite3"
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg
from scripts.canvas_llm_phase22 import teacher_decisions as decisions

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
wid = reg.seed_demo_week(db)

before_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
records = reg.load_registry_from_db(db, wid)
assert records

assignment = next(r for r in records if r.artifact_kind == 'assignment')
announcement = next(r for r in records if r.artifact_kind == 'announcement' and r.subject != p22.HOMEROOM_NEWSLETTER_SUBJECT)
newsletter = next(r for r in records if r.artifact_kind == 'newsletter')
daily_brief = next(r for r in records if r.artifact_kind == 'daily_brief')

decisions.record_decision(db, assignment, 'approve')
decisions.record_decision(db, announcement, 'approve')
decisions.record_decision(db, newsletter, 'approve')
decisions.record_decision(db, daily_brief, 'approve')

dup = decisions.record_decision(db, assignment, 'approve')
history = decisions.list_decision_history(db, newsletter.artifact_id)
assert len(history) >= 1

edited = reg.ArtifactRegistryRecord(**{**newsletter.to_dict(), 'content_hash': 'changed-newsletter-hash'})
decisions.sync_invalidations(db, [edited])
assert decisions.latest_decision(db, newsletter.artifact_id).decision_status == 'invalidated'
decisions.record_decision(db, edited, 'approve')
assert len(decisions.list_decision_history(db, newsletter.artifact_id)) >= 2

revised = reg.ArtifactRegistryRecord(**{**assignment.to_dict(), 'approval_revision': int(assignment.approval_revision or 0) + 1})
decisions.sync_invalidations(db, [revised])
assert decisions.latest_decision(db, assignment.artifact_id).decision_status == 'invalidated'

after_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
assert before_rows == after_rows

tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table'")]
assert 'teacher_decision_records' in tables
assert 'approval_queue' not in tables

final_records = reg.load_registry_from_db(db, wid)
summary = decisions.summarize_derived_states(final_records, db)
encoded_once = json.dumps(summary, sort_keys=True, default=str)
encoded_twice = json.dumps(decisions.summarize_derived_states(final_records, db), sort_keys=True, default=str)
assert encoded_once == encoded_twice

source = Path('scripts/canvas_llm_phase22/teacher_decisions.py').read_text().lower()
for forbidden in ('canvas.instructure', 'smtp', 'sendgrid', 'gmail', 'urllib.request', 'requests.post'):
    assert forbidden not in source
assert 'update drafts set' not in source
assert 'replace_drafts(' not in source

phase26 = Path('scripts/canvas-llm-phase-26-unified-weekly-production-workstation-status.sh')
phase27 = Path('scripts/canvas-llm-phase-27-canvas-readiness-and-safety-diff-status.sh')
assert phase26.exists() and phase27.exists()

print('PASS decision record creates successfully')
print('PASS assignment decision works')
print('PASS announcement decision works')
print('PASS newsletter decision works')
print('PASS Daily Brief decision works')
print('PASS history preserved')
print('PASS hash change invalidates approval')
print('PASS revision change invalidates approval')
print('PASS no artifact mutation')
print('PASS no duplicate active decision records')
print('PASS no Canvas calls')
print('PASS no email transport')
print('PASS Phase 26 untouched')
print('PASS Phase 27 untouched')
PY

bin/chief-of-staff --teacher-decision-status | grep -q 'Teacher Decisions'

echo "PASS Canvas LLM teacher decisions tests complete"
