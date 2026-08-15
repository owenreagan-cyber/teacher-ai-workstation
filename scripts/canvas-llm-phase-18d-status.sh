#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); echo "PASS: $1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); echo "WARN: $1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); echo "FAIL: $1"; }

require_file() {
  if [[ -f "$1" ]]; then pass "file exists: $1"; else fail "missing file: $1"; fi
}

PKG="scripts/canvas_llm_phase18d"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-phase-18d-write-readiness-dry-run-safety-diff.md"
TEST="tests/canvas-llm-phase-18d-write-readiness-dry-run-test.sh"

echo "Canvas LLM Phase 18D: Write-Readiness Gate, Dry-Run Packet & Safety Diff"
echo "------------------------------------------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/contracts.py"
require_file "$PKG/snapshot.py"
require_file "$PKG/diff.py"
require_file "$PKG/readiness.py"
require_file "$PKG/deployment.py"
require_file "$CLI"
require_file "$DOC"
require_file "$TEST"
require_file "scripts/canvas_llm_phase18c/preview.py"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "Phase 18D modules compile"
else
  fail "Phase 18D modules failed to compile"
fi

echo
echo "Import-Safe Contract Boundaries"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18d.contracts import DeploymentIntent, DryRunPacket, CanvasSnapshot, ApprovalRecord
from scripts.canvas_llm_phase18d.diff import build_safety_diff_item
from scripts.canvas_llm_phase18d.readiness import evaluate_packet_readiness, approval_is_valid
from scripts.canvas_llm_phase18d.snapshot import validate_snapshot
for mod in ("canvas_connector", "canvas_writer", "canvas_verification",
            "scripts.canvas_llm_phase22.phase22_workstation",
            "scripts.canvas_llm_phase22.weekly_agenda_publisher",
            "scripts.canvas_llm_phase22.canvas_operations",
            "scripts.canvas_llm_phase26.pipeline"):
    assert mod not in sys.modules, mod
print("OK")
PY
then
  pass "contracts/diff/readiness import without execution modules"
else
  fail "contracts pulled execution modules"
fi

echo
echo "Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck 2>&1)"; then
  echo "$selfcheck_output"
  pass "Phase 18D self-check passed"
else
  echo "$selfcheck_output"
  fail "Phase 18D self-check failed"
fi

echo
echo "Dry-Run Behavior Verification"
echo "----------------------------------------"
if python3 - <<'PY'
import json
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext
from scripts.canvas_llm_phase18d.deployment import assemble_dry_run_packet, build_safety_diff
from scripts.canvas_llm_phase18d.contracts import DryRunContext, CanvasSnapshot

cfg = {
    "math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"},
    "reading-spelling": {"course_id": "R", "module_id": "RM", "assignment_group_id": "RA"},
    "language-arts": {"course_id": "L", "module_id": "LM", "assignment_group_id": "LA"},
    "history": {"course_id": "H", "module_id": "HM", "assignment_group_id": "HA"},
}
preview = assemble_teacher_preview(build_example_plan(), RuntimeContext(canvas_config=cfg, due_time_policy="resolved"))

# Missing config blocks.
bare = assemble_dry_run_packet(preview, CanvasSnapshot(week_code="Q1W3", snapshot_id="s"), DryRunContext(canvas_config={}))
assert bare.readiness == "BLOCKED_MISSING_CONFIG", bare.readiness
assert any("missing config" in b for b in bare.blocked)

# Due-time unresolved propagates as policy blocker.
due = assemble_dry_run_packet(preview, CanvasSnapshot(week_code="Q1W3", snapshot_id="s"),
                              DryRunContext(canvas_config=cfg, publish_policy="resolved", resolved_publish_state="published"))
assert due.readiness == "BLOCKED_POLICY", due.readiness
assert not any("11:59" in json.dumps(due.to_dict()) for _ in [0]), "fabricated due time"
blob = json.dumps(due.to_dict())
assert "15:00" not in blob or due.readiness == "BLOCKED_POLICY"

# Protected Science -> zero writable intents.
assert not [i for i in due.intents if i.course == "science" and i.operation not in ("SKIP",)]

# Determinism.
a = json.dumps(assemble_dry_run_packet(preview, CanvasSnapshot(week_code="Q1W3", snapshot_id="s"), DryRunContext(canvas_config=cfg)).to_dict(), sort_keys=True)
b = json.dumps(assemble_dry_run_packet(preview, CanvasSnapshot(week_code="Q1W3", snapshot_id="s"), DryRunContext(canvas_config=cfg)).to_dict(), sort_keys=True)
assert a == b
print("OK")
PY
then
  pass "dry-run readiness / due-time / protected / determinism verified"
else
  fail "dry-run behavior verification failed"
fi

echo
echo "No Canvas Write Path / Mutation HTTP / Token Use"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request' \
  "$PKG"/*.py >/tmp/canvas_phase_18d_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18d_write_scan.txt
  fail "Canvas write/mutation-path token found in Phase 18D package"
else
  pass "no Canvas write/mutation-path token in Phase 18D package"
fi
rm -f /tmp/canvas_phase_18d_write_scan.txt

if grep -RInE 'CANVAS_TOKEN|CANVAS_API_TOKEN' "$PKG"/*.py >/tmp/canvas_phase_18d_token_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18d_token_scan.txt
  fail "Canvas token reference found in Phase 18D package"
else
  pass "no Canvas token consumption in Phase 18D package"
fi
rm -f /tmp/canvas_phase_18d_token_scan.txt

echo
echo "CLI Wiring"
echo "----------------------------------------"
if grep -q 'canvas-llm-phase-18d-status' bin/chief-of-staff; then
  pass "chief-of-staff dispatches Phase 18D status"
else
  fail "chief-of-staff missing Phase 18D dispatch"
fi

echo
echo "Write Gate Remains Closed"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase22.write_gate import attempt_write, evaluate_write, write_gate_blocks_execution
# Even an "approved" decision must never execute: the gate stays blocked.
decision = evaluate_write("create", "page", "p-1", approved=True, approved_by="Teacher", approved_at="2026-07-25T00:00:00Z")
assert attempt_write(decision).gate_state == "BLOCKED"
assert write_gate_blocks_execution()
print("OK")
PY
then
  pass "existing write gate remains closed (execution BLOCKED)"
else
  fail "write gate execution unexpectedly open"
fi

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
