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

require_contains() {
  if grep -q "$2" "$1"; then pass "$3"; else fail "$3"; fi
}

PKG="scripts/canvas_llm_phase18a"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-phase-18a-canonical-weekly-plan-evidence-model.md"

echo "Canvas LLM Phase 18A: Canonical WeeklyPlan + Evidence Model"
echo "----------------------------------------"

require_file "$PKG/models.py"
require_file "$PKG/validation.py"
require_file "$PKG/source_precedence.py"
require_file "$PKG/precedent.py"
require_file "$PKG/examples.py"
require_file "$CLI"
require_file "$DOC"

echo
echo "Canonical WeeklyPlan Model Presence"
echo "----------------------------------------"
require_contains "$PKG/models.py" 'class WeeklyPlan' "WeeklyPlan model class present"
require_contains "$PKG/models.py" 'class CoursePlan' "CoursePlan model class present"
require_contains "$PKG/models.py" 'class DayEntry' "DayEntry model class present"
require_contains "$PKG/models.py" 'class Evidence' "Evidence provenance class present"
require_contains "$PKG/models.py" 'WEEKDAYS' "Monday-Friday weekday constant present"
require_contains "$PKG/models.py" 'KNOWN_COURSES' "known course names present"

echo
echo "Provenance / Evidence Model"
echo "----------------------------------------"
require_contains "$PKG/models.py" 'sourceMetadata' "top-level source metadata present"
require_contains "$PKG/models.py" 'provenance' "material-decision provenance present"
require_contains "$PKG/models.py" 'decidedSource' "per-day decided source present"
require_contains "$PKG/source_precedence.py" 'teacher_instruction' "teacher instruction source class present"
require_contains "$PKG/source_precedence.py" 'live_pacing' "live pacing source class present"
require_contains "$PKG/source_precedence.py" 'precedent' "precedent source class present"
require_contains "$PKG/source_precedence.py" 'historical_fallback' "historical fallback source class present"

echo
echo "Precedent Classification"
echo "----------------------------------------"
require_contains "$PKG/precedent.py" 'operational_behavior' "precedent class: operational behavior"
require_contains "$PKG/precedent.py" 'canvas_configuration' "precedent class: canvas configuration"
require_contains "$PKG/precedent.py" 'anomaly' "precedent class: anomaly"

echo
echo "Validation + Serialization Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck)"; then
  echo "$selfcheck_output"
  pass "Phase 18A self-check passed"
else
  echo "$selfcheck_output"
  fail "Phase 18A self-check failed"
fi
if echo "$selfcheck_output" | grep -q "PASS: canonical WeeklyPlan model builds a valid example plan"; then
  pass "example plan validates"
else
  fail "example plan did not validate"
fi
if echo "$selfcheck_output" | grep -q "PASS: serialization round trip preserves the canonical plan"; then
  pass "serialization round trip"
else
  fail "serialization round trip failed"
fi

echo
echo "No Canvas Write Path"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|http\.client|urllib\.request' \
  "$PKG"/*.py >/tmp/canvas_phase_18a_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18a_write_scan.txt
  fail "Canvas write-path token found in Phase 18A package"
else
  pass "no Canvas write-path token in Phase 18A package"
fi
rm -f /tmp/canvas_phase_18a_write_scan.txt

echo
echo "Local Artifact Guard"
echo "----------------------------------------"
if git check-ignore -q .local/canvas-llm && git check-ignore -q .local/canvas; then
  pass ".local Canvas artifacts are ignored"
else
  fail ".local Canvas artifacts are not ignored"
fi
if [[ -z "$(git ls-files .local/canvas-llm .local/canvas)" ]]; then
  pass ".local Canvas artifacts are not tracked"
else
  fail ".local Canvas artifacts are tracked"
fi

echo
echo "Previous Phase Regression (14b / 16 / 17)"
echo "----------------------------------------"
for phase_cmd in canvas-llm-phase-14b-status canvas-llm-phase-16-status canvas-llm-phase-17-status; do
  if phase_output="$(bin/chief-of-staff --"$phase_cmd" 2>&1)"; then
    if echo "$phase_output" | grep -q "FAIL: 0"; then
      pass "$phase_cmd reports FAIL: 0"
    else
      echo "$phase_output" | tail -20
      fail "$phase_cmd did not report FAIL: 0"
    fi
  else
    echo "$phase_output" | tail -20
    fail "$phase_cmd failed"
  fi
done

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
