#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/deployment_audit.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/deployment-audit-contract.md"
TEST="tests/canvas-llm-deployment-audit-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Deployment Audit Status"
echo "----------------------------------"
echo

[[ -f "$MODULE" ]] && pass "deployment audit module exists" || fail "deployment audit module missing"
[[ -f "$CONTRACT" ]] && pass "deployment audit contract exists" || fail "deployment audit contract missing"
[[ -f "$TEST" ]] && pass "deployment audit test exists" || fail "deployment audit test missing"
grep -F -- '--canvas-audit-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches audit status" || fail "chief-of-staff dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1 && pass "deployment audit Python syntax passes" || fail "deployment audit Python syntax fails"

python3 "$MODULE" self-test >/tmp/c0y-audit-self-test.txt 2>&1 && pass "deployment audit self-test passes" || { cat /tmp/c0y-audit-self-test.txt; fail "deployment audit self-test fails"; }
bash "$TEST" >/tmp/c0y-audit-test.txt 2>&1 && pass "deployment audit regression test passes" || { cat /tmp/c0y-audit-test.txt; fail "deployment audit regression test fails"; }

bin/chief-of-staff --canvas-audit-status >"$REPORT_OUT" 2>&1 && pass "audit report exits successfully" || { cat "$REPORT_OUT"; fail "audit report failed"; }
grep -Fq 'Audit' "$REPORT_OUT" && pass "audit report header present" || fail "audit report header missing"
grep -Fq 'Events:' "$REPORT_OUT" && pass "audit report includes event count" || fail "audit report missing event count"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
