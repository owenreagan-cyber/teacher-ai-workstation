#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/write_gate.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/write-gate-contract.md"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Write Gate Status"
echo "----------------------------"
echo

[[ -f "$MODULE" ]] && pass "write gate module exists" || fail "write gate module missing"
[[ -f "$CONTRACT" ]] && pass "write gate contract exists" || fail "write gate contract missing"
grep -F -- '--canvas-write-gate-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches write gate status" || fail "chief-of-staff dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1 && pass "write gate Python syntax passes" || fail "write gate Python syntax fails"

for symbol in WriteGateDecision evaluate_write validate_write_packet attempt_write; do
  grep -Fq "$symbol" "$MODULE" && pass "write gate includes $symbol" || fail "write gate missing $symbol"
done

python3 "$MODULE" self-test >/tmp/c0v-write-gate-self-test.txt 2>&1 && pass "write gate self-test passes" || { cat /tmp/c0v-write-gate-self-test.txt; fail "write gate self-test fails"; }
bin/chief-of-staff --canvas-write-gate-status >"$REPORT_OUT" 2>&1 && pass "write gate report exits successfully" || { cat "$REPORT_OUT"; fail "write gate report failed"; }
grep -Fq 'BLOCKED' "$REPORT_OUT" && pass "write gate report shows blocked state" || fail "write gate report missing blocked state"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
