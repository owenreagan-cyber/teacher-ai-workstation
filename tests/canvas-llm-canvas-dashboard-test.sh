#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM canvas dashboard tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DASHBOARD="scripts/canvas_llm_phase22/canvas_operations_dashboard.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-dashboard.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DASHBOARD"
python3 "$DASHBOARD" self-test

python3 - <<'PY' "$T/dashboard.sqlite3"
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg
from scripts.canvas_llm_phase22 import teacher_decisions as decisions
from scripts.canvas_llm_phase22 import canvas_operations_dashboard as dashboard_mod
from scripts.canvas_llm_phase22 import canvas_drift as drift

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
wid = reg.seed_demo_week(db)
records = reg.load_registry_from_db(db, wid)
announcement = next(r for r in records if r.artifact_kind == 'announcement')
decisions.record_decision(db, announcement, 'approve', teacher_display='Teacher')

drift_reports = [
    drift.CanvasDriftReport(
        artifact_id=records[0].artifact_id,
        expected_hash='abc',
        actual_hash='def',
        difference_type='STALE_VERSION',
        recommendation='Update Newsletter Page',
        requires_teacher_approval=True,
    )
]
board = dashboard_mod.build_dashboard(db, wid, drift_reports=drift_reports)
assert board.ready_items or board.needs_review_items or board.blocked_items
assert any(item.artifact_kind == 'assignment' for item in board.blocked_items)
assert len(board.drift_items) == 1
assert dashboard_mod.dashboard_performs_no_publishing()

print('PASS dashboard states populated')
print('PASS ready and blocked items classified')
print('PASS drift items surfaced')
print('PASS no publishing performed')
PY

bin/chief-of-staff --canvas-operations-dashboard | grep -q 'Canvas Operations Dashboard'
bin/chief-of-staff --canvas-operations-dashboard | grep -q 'No publishing performed'

echo "PASS Canvas LLM canvas dashboard tests complete"
