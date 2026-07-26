#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/deployment_planner.py"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Deployment Plan Status"
echo "---------------------------------"
echo

[[ -f "$MODULE" ]] && pass "deployment planner module exists" || fail "deployment planner module missing"
grep -F -- '--canvas-deployment-plan-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches deployment plan status" || fail "chief-of-staff dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1 && pass "deployment planner Python syntax passes" || fail "deployment planner Python syntax fails"

for symbol in DeploymentPlan build_deployment_plan build_sandbox_deployment_packet; do
  grep -Fq "$symbol" "$MODULE" && pass "deployment planner includes $symbol" || fail "deployment planner missing $symbol"
done

python3 "$MODULE" self-test >/tmp/c0w-plan-self-test.txt 2>&1 && pass "deployment planner self-test passes" || { cat /tmp/c0w-plan-self-test.txt; fail "deployment planner self-test fails"; }
bin/chief-of-staff --canvas-deployment-plan-status >"$REPORT_OUT" 2>&1 && pass "deployment plan report exits successfully" || { cat "$REPORT_OUT"; fail "deployment plan report failed"; }
grep -Fq 'Deployment Plan' "$REPORT_OUT" && pass "deployment plan report header present" || fail "deployment plan report header missing"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
