#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/canvas_repair.py"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas Repair Status"
echo "--------------------"
echo

[[ -f "$MODULE" ]] && pass "canvas repair module exists" || fail "canvas repair module missing"
grep -F -- '--canvas-repair-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches canvas repair status" || fail "chief-of-staff dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1 && pass "canvas repair Python syntax passes" || fail "canvas repair Python syntax fails"

python3 "$MODULE" self-test >/tmp/c1-repair-self-test.txt 2>&1 && pass "canvas repair self-test passes" || { cat /tmp/c1-repair-self-test.txt; fail "canvas repair self-test fails"; }
bin/chief-of-staff --canvas-repair-status >"$REPORT_OUT" 2>&1 && pass "canvas repair report exits successfully" || { cat "$REPORT_OUT"; fail "canvas repair report failed"; }
grep -Fq 'No automatic repairs' "$REPORT_OUT" && pass "canvas repair report confirms no auto repair" || fail "canvas repair report missing no-auto-repair message"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
