#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM deployment readiness tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

READINESS="scripts/canvas_llm_phase22/deployment_readiness.py"
PLANNER="scripts/canvas_llm_phase22/deployment_planner.py"
ROLLBACK="scripts/canvas_llm_phase22/rollback.py"
WRITE_GATE="scripts/canvas_llm_phase22/write_gate.py"
CONNECTOR="scripts/canvas_llm_phase22/canvas_connector.py"
AUDIT="scripts/canvas_llm_phase22/deployment_audit.py"
REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
DECISIONS="scripts/canvas_llm_phase22/teacher_decisions.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/deployment-readiness.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$READINESS" "$PLANNER" "$ROLLBACK" "$WRITE_GATE" "$CONNECTOR" "$AUDIT" "$REGISTRY" "$DECISIONS" "$PHASE22"

python3 "$READINESS" self-test
python3 "$PLANNER" self-test

python3 - <<'PY' "$T/readiness.sqlite3"
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg
from scripts.canvas_llm_phase22 import teacher_decisions as decisions
from scripts.canvas_llm_phase22 import deployment_readiness as readiness
from scripts.canvas_llm_phase22 import deployment_planner as planner
from scripts.canvas_llm_phase22 import rollback as rollback_mod
from scripts.canvas_llm_phase22 import write_gate as write_gate
from scripts.canvas_llm_phase22 import canvas_connector as connector
from scripts.canvas_llm_phase22 import deployment_audit as audit

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
wid = reg.seed_demo_week(db)

before_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
records = reg.load_registry_from_db(db, wid)
assignment = next(r for r in records if r.artifact_kind == 'assignment')
announcement = next(r for r in records if r.artifact_kind == 'announcement' and r.subject != p22.HOMEROOM_NEWSLETTER_SUBJECT)

decisions.record_decision(db, assignment, 'approve')
decisions.record_decision(db, announcement, 'approve')

audit_log = audit.DeploymentAuditLog()
items = readiness.build_readiness_records(db, records, audit_log=audit_log)
ready = [item for item in items if item.readiness_status == 'READY']
assert ready, 'expected at least one READY artifact with approvals'

blocked = [item for item in items if item.readiness_status == 'BLOCKED']
assert blocked, 'expected blocked artifacts in demo week'

missing_decision = next(item for item in items if item.teacher_decision_status != 'PASS')
assert missing_decision.readiness_status in {'BLOCKED', 'NEEDS_REVIEW'}

disabled_items = readiness.build_readiness_records(db, records, config=connector.sandbox_connection_config(), audit_log=audit_log)
assert all(item.readiness_status == 'BLOCKED' for item in disabled_items)

for item in ready[:1]:
    record = next(r for r in records if r.artifact_id == item.artifact_id)
    rollback_plan = rollback_mod.generate_rollback_plan(item.deployment_id, record.artifact_id, record.artifact_kind)
    assert rollback_plan.is_complete()
    plan = planner.build_deployment_plan(record, item, rollback_plan)
    packet = planner.build_sandbox_deployment_packet(record, item, plan)
    assert packet['result'] in {'READY FOR HUMAN-AUTHORIZED TEST', 'BLOCKED'}
    assert item.rollback_plan

    blocked_write = write_gate.evaluate_write('create', 'announcement', record.artifact_id, approved=False)
    assert blocked_write.gate_state == 'BLOCKED'
    assert write_gate.attempt_write(blocked_write).gate_state == 'BLOCKED'

after_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
assert before_rows == after_rows

assert audit.audit_has_no_deployment_events(audit_log)
assert audit.audit_output_is_redacted(audit_log)

source = Path('scripts/canvas_llm_phase22/deployment_readiness.py').read_text().lower()
for forbidden in ('canvas.instructure', 'smtp', 'sendgrid', 'gmail', 'requests.post', 'urllib.request'):
    assert forbidden not in source

print('PASS artifact readiness evaluation works')
print('PASS approval required for READY state')
print('PASS teacher decision required')
print('PASS connector disabled blocks readiness')
print('PASS write gate blocked')
print('PASS rollback required')
print('PASS audit events recorded')
print('PASS no artifact mutation')
PY

bin/chief-of-staff --canvas-deployment-readiness-status | grep -q 'Deployment Readiness'
bin/chief-of-staff --canvas-deployment-plan-status | grep -q 'Deployment Plan'

echo "PASS Canvas LLM deployment readiness tests complete"
