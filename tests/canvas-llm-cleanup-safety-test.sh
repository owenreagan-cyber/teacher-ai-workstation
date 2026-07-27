#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM cleanup safety tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CLEANUP="scripts/canvas_llm_phase22/canvas_cleanup_manager.py"
DETECTOR="scripts/canvas_llm_phase22/canvas_duplicate_detector.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$CLEANUP" "$DETECTOR"
python3 "$CLEANUP" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_cleanup_manager as cleanup

plan = cleanup.build_cleanup_plan()
assert plan.safe_candidates
assert plan.protected_objects
assert plan.rollback_steps

blocked = cleanup.execute_cleanup(plan)
assert blocked.executed is False
assert not blocked.deleted_object_ids
assert 'approval required' in blocked.message.lower()

approval = cleanup.approve_cleanup(
    plan,
    approved_by='teacher',
    reason='Remove duplicate copies after review',
    object_ids=[plan.safe_candidates[0].object_id],
)
assert approval.reason
assert approval.timestamp

executed = cleanup.execute_cleanup(plan, approval, explicit_approval=True)
assert executed.executed is True
assert executed.rollback_plan_id
assert executed.deleted_object_ids
assert 'no Canvas delete transport' in executed.message

assert cleanup.cleanup_manager_has_no_automatic_deletion()

print('PASS no automatic deletion')
print('PASS approval required')
print('PASS rollback plan')
PY

bin/chief-of-staff --canvas-cleanup-preview | grep -q 'Cleanup Preview'

echo "PASS Canvas LLM cleanup safety tests complete"
