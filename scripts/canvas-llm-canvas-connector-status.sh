#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/canvas_connector.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/canvas-connector-contract.md"
TEST="tests/canvas-llm-canvas-connector-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Canvas Connector Status"
echo "----------------------------------"
echo

[[ -f "$MODULE" ]] && pass "canvas connector module exists" || fail "canvas connector module missing"
[[ -f "$CONTRACT" ]] && pass "canvas connector contract exists" || fail "canvas connector contract missing"
[[ -f "$TEST" ]] && pass "canvas connector test exists" || fail "canvas connector test missing"

grep -F -- '--canvas-connector-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches canvas connector status" || fail "chief-of-staff dispatch missing"

if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1; then
  pass "canvas connector Python syntax passes"
else
  fail "canvas connector Python syntax fails"
fi

for symbol in CanvasConnector CanvasConnectionConfig read_course read_page read_assignment read_announcement redact_log; do
  grep -Fq "$symbol" "$MODULE" && pass "canvas connector includes $symbol" || fail "canvas connector missing $symbol"
done

grep -Fq 'writes_allowed' "$MODULE" && pass "canvas connector exposes write disable guard" || fail "canvas connector missing write disable guard"

if python3 "$MODULE" self-test >/tmp/c0u-connector-self-test.txt 2>&1; then
  pass "canvas connector self-test passes"
else
  cat /tmp/c0u-connector-self-test.txt
  fail "canvas connector self-test fails"
fi

if python3 - <<'PY' >/dev/null 2>&1
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connector as connector
assert connector.connector_has_no_writes()
assert 'token' not in connector.default_connection_config().to_dict()
PY
then
  pass "canvas connector has no write transport references"
else
  fail "canvas connector references forbidden transport patterns"
fi
bash "$TEST" >/tmp/c0u-connector-test.txt 2>&1 && pass "canvas connector regression test passes" || { cat /tmp/c0u-connector-test.txt; fail "canvas connector regression test fails"; }

bin/chief-of-staff --canvas-connector-status >"$REPORT_OUT" 2>&1 && pass "canvas connector report exits successfully" || { cat "$REPORT_OUT"; fail "canvas connector report failed"; }
grep -Fq 'Canvas Connector' "$REPORT_OUT" && pass "canvas connector report header present" || fail "canvas connector report header missing"
grep -Fq 'disabled' "$REPORT_OUT" && pass "canvas connector report shows writes disabled" || fail "canvas connector report missing writes disabled"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
