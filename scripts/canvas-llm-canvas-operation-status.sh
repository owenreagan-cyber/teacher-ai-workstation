#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/canvas_operations.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/canvas-operations-contract.md"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas Operations Status"
echo "------------------------"
echo

[[ -f "$MODULE" ]] && pass "canvas operations module exists" || fail "canvas operations module missing"
[[ -f "$CONTRACT" ]] && pass "canvas operations contract exists" || fail "canvas operations contract missing"
grep -F -- '--canvas-operation-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches canvas operation status" || fail "chief-of-staff dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1 && pass "canvas operations Python syntax passes" || fail "canvas operations Python syntax fails"

python3 "$MODULE" self-test >/tmp/c1-operations-self-test.txt 2>&1 && pass "canvas operations self-test passes" || { cat /tmp/c1-operations-self-test.txt; fail "canvas operations self-test fails"; }
bin/chief-of-staff --canvas-operation-status >"$REPORT_OUT" 2>&1 && pass "canvas operation report exits successfully" || { cat "$REPORT_OUT"; fail "canvas operation report failed"; }
grep -Fq 'Announcements:' "$REPORT_OUT" && pass "canvas operation report shows announcements" || fail "canvas operation report missing announcements"
grep -Fq 'Assignments:' "$REPORT_OUT" && pass "canvas operation report shows assignments blocked" || fail "canvas operation report missing assignments"
grep -Fq 'BLOCKED' "$REPORT_OUT" && pass "canvas operation report shows assignments blocked state" || fail "canvas operation report missing blocked state"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
