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

PKG="scripts/canvas_llm_phase18b"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-phase-18b-canonical-weekly-plan-integration.md"

echo "Canvas LLM Phase 18B: Canonical WeeklyPlan Integration"
echo "----------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/translation.py"
require_file "$PKG/precedent_loader.py"
require_file "$CLI"
require_file "$DOC"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "Phase 18B modules compile"
else
  fail "Phase 18B modules failed to compile"
fi

echo
echo "Phase 18A Dependency"
echo "----------------------------------------"
require_file "scripts/canvas_llm_phase18a/models.py"
require_file "scripts/canvas_llm_phase18a/validation.py"
require_contains "$PKG/translation.py" 'canvas_llm_phase18a.validation' "reuses Phase 18A validation"
require_contains "$PKG/translation.py" 'canvas_llm_phase18a.models' "reuses Phase 18A models"
require_contains "$PKG/translation.py" 'canvas_llm_phase18a.source_precedence' "reuses Phase 18A source precedence"

echo
echo "Adapter / Translation Layer"
echo "----------------------------------------"
require_contains "$PKG/translation.py" 'def translate_weekly_plan' "canonical adapter entrypoint present"
require_contains "$PKG/translation.py" 'validate_plan(plan)' "validates before translation"

echo
echo "Translation + Semantics Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck 2>&1)"; then
  echo "$selfcheck_output"
  pass "Phase 18B self-check passed"
else
  echo "$selfcheck_output"
  fail "Phase 18B self-check failed"
fi
for marker in \
  "valid WeeklyPlan translates" \
  "teacher instruction preserved" \
  "blanks recorded" \
  "ambiguity recorded" \
  "protected Science blocked" \
  "invalid WeeklyPlan rejected" \
  "provenance trace survives"; do
  if echo "$selfcheck_output" | grep -q "$marker"; then
    pass "$marker"
  else
    fail "self-check missing: $marker"
  fi
done

echo
echo "No Canvas Write Path"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|http\.client|urllib\.request' \
  "$PKG"/*.py >/tmp/canvas_phase_18b_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18b_write_scan.txt
  fail "Canvas write-path token found in Phase 18B package"
else
  pass "no Canvas write-path token in Phase 18B package"
fi
rm -f /tmp/canvas_phase_18b_write_scan.txt

if grep -RInE 'CANVAS_TOKEN|CANVAS_API_TOKEN' "$PKG"/*.py >/tmp/canvas_phase_18b_token_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18b_token_scan.txt
  fail "Canvas token reference found in Phase 18B package"
else
  pass "no Canvas token consumption in Phase 18B package"
fi
rm -f /tmp/canvas_phase_18b_token_scan.txt

echo
echo "Precedent Bundle Handling"
echo "----------------------------------------"
if precedent_output="$(python3 "$CLI" --precedent-status 2>&1)"; then
  echo "$precedent_output"
  pass "optional precedent bundle absence handled safely"
else
  echo "$precedent_output"
  fail "precedent bundle status command failed"
fi

echo
echo "CLI Wiring"
echo "----------------------------------------"
require_contains "bin/chief-of-staff" 'canvas-llm-phase-18b-status' "chief-of-staff dispatches Phase 18B status"

echo
echo "Previous Phase Regression (18a / 18)"
echo "----------------------------------------"
for phase_cmd in canvas-llm-phase-18a-status canvas-llm-phase-18-status; do
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
