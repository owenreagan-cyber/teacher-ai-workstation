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

PKG="scripts/canvas_llm_phase18c"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-phase-18c-end-to-end-preview-contract-hardening.md"
TEST="tests/canvas-llm-phase-18c-preview-assembly-test.sh"

echo "Canvas LLM Phase 18C: End-to-End Preview Assembly & Contract Hardening"
echo "----------------------------------------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/contracts.py"
require_file "$PKG/preview.py"
require_file "$PKG/drift.py"
require_file "$CLI"
require_file "$DOC"
require_file "$TEST"
require_file "scripts/canvas_llm_phase22/contracts.py"
require_file "scripts/canvas_llm_phase24/contracts.py"
require_file "scripts/canvas_llm_phase26/contracts.py"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "Phase 18C modules compile"
else
  fail "Phase 18C modules failed to compile"
fi
for f in scripts/canvas_llm_phase22/contracts.py scripts/canvas_llm_phase24/contracts.py scripts/canvas_llm_phase26/contracts.py; do
  if python3 -m py_compile "$f"; then pass "$f compiles"; else fail "$f failed to compile"; fi
done

echo
echo "Import-Safe Contract Boundaries"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase22.contracts import WeeklyAgendaPage
from scripts.canvas_llm_phase24.contracts import WeekPrediction
from scripts.canvas_llm_phase26.contracts import WorkstationPacket, SubjectSnapshot
from scripts.canvas_llm_phase18c.contracts import TeacherPreview
for mod in ("canvas_connector", "canvas_writer", "canvas_verification", "scripts.canvas_llm_phase22.phase22_workstation"):
    assert mod not in sys.modules, mod
print("OK")
PY
then
  pass "contracts import without execution modules"
else
  fail "contracts pulled execution modules"
fi

echo
echo "Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck 2>&1)"; then
  echo "$selfcheck_output"
  pass "Phase 18C self-check passed"
else
  echo "$selfcheck_output"
  fail "Phase 18C self-check failed"
fi

echo
echo "End-to-End Preview Behavior"
echo "----------------------------------------"
if python3 - <<'PY'
import json
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext

plan = build_example_plan()

# Missing config blocks.
bare = assemble_teacher_preview(plan, RuntimeContext())
assert bare.readiness == "BLOCKED_MISSING_CONFIG"

# Due-time unresolved propagates as policy blocker.
with_config = RuntimeContext(canvas_config={
    "math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"},
    "reading-spelling": {"course_id": "R", "module_id": "RM", "assignment_group_id": "RA"},
    "language-arts": {"course_id": "L", "module_id": "LM", "assignment_group_id": "LA"},
    "history": {"course_id": "H", "module_id": "HM", "assignment_group_id": "HA"},
})
p = assemble_teacher_preview(plan, with_config)
assert p.readiness == "BLOCKED_POLICY", p.readiness
assert any("due-time" in w.lower() for w in p.unresolved_policy)

# Resolved due-time + config -> unresolved canonical content remains the blocker.
resolved = RuntimeContext(canvas_config=with_config.canvas_config, due_time_policy="resolved")
p2 = assemble_teacher_preview(plan, resolved)
assert p2.readiness == "BLOCKED_UNRESOLVED", p2.readiness

# Drift clean.
assert p2.drift["invalid_drift"] == [], p2.drift["invalid_drift"]

# Idempotence.
a = json.dumps(assemble_teacher_preview(plan, resolved).to_dict(), sort_keys=True)
b = json.dumps(assemble_teacher_preview(plan, resolved).to_dict(), sort_keys=True)
assert a == b
print("OK")
PY
then
  pass "preview readiness / drift / idempotence verified"
else
  fail "preview behavior verification failed"
fi

echo
echo "No Canvas Write Path / Token Use"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request' \
  "$PKG"/*.py >/tmp/canvas_phase_18c_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18c_write_scan.txt
  fail "Canvas write-path token found in Phase 18C package"
else
  pass "no Canvas write-path token in Phase 18C package"
fi
rm -f /tmp/canvas_phase_18c_write_scan.txt

if grep -RInE 'CANVAS_TOKEN|CANVAS_API_TOKEN' "$PKG"/*.py >/tmp/canvas_phase_18c_token_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18c_token_scan.txt
  fail "Canvas token reference found in Phase 18C package"
else
  pass "no Canvas token consumption in Phase 18C package"
fi
rm -f /tmp/canvas_phase_18c_token_scan.txt

echo
echo "CLI Wiring"
echo "----------------------------------------"
if grep -q 'canvas-llm-phase-18c-status' bin/chief-of-staff; then
  pass "chief-of-staff dispatches Phase 18C status"
else
  fail "chief-of-staff missing Phase 18C dispatch"
fi

echo
echo "Due-Time Unresolved Propagation Consistency"
echo "----------------------------------------"
if bin/chief-of-staff --canvas-llm-phase-26-unified-weekly-production-workstation-status 2>/dev/null | grep -q 'FAIL: 0'; then
  pass "Phase 26 due-time propagation is consistent (FAIL: 0)"
else
  fail "Phase 26 due-time propagation inconsistent"
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
