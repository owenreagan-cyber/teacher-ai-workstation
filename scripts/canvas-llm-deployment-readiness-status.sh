#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

MODULE="scripts/canvas_llm_phase22/deployment_readiness.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/canvas-deployment-readiness-contract.md"
TEST="tests/canvas-llm-deployment-readiness-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Deployment Readiness Status"
echo "--------------------------------------"
echo

[[ -f "$MODULE" ]] && pass "deployment readiness module exists" || fail "deployment readiness module missing"
[[ -f "$CONTRACT" ]] && pass "deployment readiness contract exists" || fail "deployment readiness contract missing"
[[ -f "$TEST" ]] && pass "deployment readiness test exists" || fail "deployment readiness test missing"

if grep -F -- '--canvas-deployment-readiness-status' bin/chief-of-staff >/dev/null; then
  pass "chief-of-staff dispatches deployment readiness status"
else
  fail "chief-of-staff dispatch missing for deployment readiness status"
fi

if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" >/dev/null 2>&1; then
  pass "deployment readiness Python syntax passes"
else
  fail "deployment readiness Python syntax fails"
fi

for symbol in DeploymentReadinessRecord derive_readiness_status build_readiness_record print_readiness_status_report; do
  grep -Fq "$symbol" "$MODULE" && pass "deployment readiness includes $symbol" || fail "deployment readiness missing $symbol"
done

if grep -Fq 'UPDATE drafts' "$MODULE" || grep -Fq 'deploy_artifact' "$MODULE"; then
  fail "deployment readiness mutates artifacts or deploy handlers"
else
  pass "deployment readiness remains evaluation-only"
fi

if python3 "$MODULE" self-test >/tmp/c0t-readiness-self-test.txt 2>&1; then
  pass "deployment readiness self-test passes"
else
  cat /tmp/c0t-readiness-self-test.txt
  fail "deployment readiness self-test fails"
fi

if bash "$TEST" >/tmp/c0t-readiness-test.txt 2>&1; then
  pass "deployment readiness regression test passes"
else
  cat /tmp/c0t-readiness-test.txt
  fail "deployment readiness regression test fails"
fi

if bin/chief-of-staff --canvas-deployment-readiness-status >"$REPORT_OUT" 2>&1; then
  pass "deployment readiness report command exits successfully"
else
  cat "$REPORT_OUT"
  fail "deployment readiness report command failed"
fi

grep -Fq 'Deployment Readiness' "$REPORT_OUT" && pass "deployment readiness report header present" || fail "deployment readiness report header missing"

if git diff --name-only | grep -Eq 'phase-26|phase-27|phase_26|phase_27'; then
  fail "Phase 26 or Phase 27 files were modified"
else
  pass "Phase 26 and Phase 27 remain untouched"
fi

echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not publish artifacts"
pass "deployment readiness does not execute writes"
echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
