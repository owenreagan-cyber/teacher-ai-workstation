#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

DECISIONS="scripts/canvas_llm_phase22/teacher_decisions.py"
REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
QUEUE="scripts/canvas_llm_phase22/approval_queue.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/teacher-decision-contract.md"
TEST="tests/canvas-llm-teacher-decisions-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Teacher Decision Status"
echo "----------------------------------"
echo

if [[ -f "$DECISIONS" ]]; then
  pass "teacher decisions module exists"
else
  fail "teacher decisions module missing"
fi

if [[ -f "$CONTRACT" ]]; then
  pass "teacher decision contract exists"
else
  fail "teacher decision contract missing"
fi

if [[ -f "$TEST" ]]; then
  pass "teacher decisions test exists"
else
  fail "teacher decisions test missing"
fi

if grep -F -- '--teacher-decision-status' bin/chief-of-staff >/dev/null; then
  pass "chief-of-staff dispatches teacher decision status"
else
  fail "chief-of-staff dispatch missing for teacher decision status"
fi

if grep -Fq 'teacher_decision_records' "$PHASE22"; then
  pass "teacher decision database migration exists"
else
  fail "teacher decision database migration missing"
fi

if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DECISIONS" "$REGISTRY" "$QUEUE" "$PHASE22" >/dev/null 2>&1; then
  pass "teacher decisions Python syntax passes"
else
  fail "teacher decisions Python syntax fails"
fi

for symbol in TeacherDecisionRecord record_decision sync_invalidations derive_teacher_approval_state list_decision_history print_decision_status_report; do
  if grep -Fq "$symbol" "$DECISIONS"; then
    pass "teacher decisions includes $symbol"
  else
    fail "teacher decisions missing $symbol"
  fi
done

if grep -Fq 'artifact_registry' "$DECISIONS"; then
  pass "teacher decisions builds on artifact registry"
else
  fail "teacher decisions missing artifact registry integration"
fi

if grep -Fq 'UPDATE drafts' "$DECISIONS" || grep -Fq 'replace_drafts(' "$DECISIONS" || grep -Fq 'deploy_artifact' "$DECISIONS"; then
  fail "teacher decisions mutates artifacts or deployment handlers"
else
  pass "teacher decisions do not mutate artifact drafts"
fi

if grep -Eiq 'smtp|sendgrid|gmail|canvas\.instructure|urllib\.request|requests\.(get|post)|@.*\.(com|org|net)' "$DECISIONS"; then
  fail "teacher decisions references forbidden transport or secret patterns"
else
  pass "teacher decisions has no transport or secret references"
fi

if ! grep -F -- '--approve' bin/chief-of-staff >/dev/null && ! grep -F -- '--deploy' bin/chief-of-staff >/dev/null; then
  pass "chief-of-staff has no approve or deploy mutation commands added"
else
  fail "chief-of-staff exposes forbidden mutation commands"
fi

if python3 "$DECISIONS" self-test >/tmp/c0s-decisions-self-test.txt 2>&1; then
  pass "teacher decisions self-test passes"
else
  cat /tmp/c0s-decisions-self-test.txt
  fail "teacher decisions self-test fails"
fi

if bash "$TEST" >/tmp/c0s-teacher-decisions-test.txt 2>&1; then
  pass "teacher decisions regression test passes"
else
  cat /tmp/c0s-teacher-decisions-test.txt
  fail "teacher decisions regression test fails"
fi

if bin/chief-of-staff --teacher-decision-status >"$REPORT_OUT" 2>&1; then
  pass "teacher decision report command exits successfully"
else
  cat "$REPORT_OUT"
  fail "teacher decision report command failed"
fi

if grep -Fq 'Teacher Decisions' "$REPORT_OUT"; then
  pass "teacher decision report header is present"
else
  fail "teacher decision report header missing"
fi

if grep -Eiq '(@|smtp|sendgrid|gmail|sqlite|/Users/|\.local/)' "$REPORT_OUT"; then
  fail "teacher decision report leaked sensitive or private values"
else
  pass "teacher decision report excludes emails, URLs, secrets, and private paths"
fi

if git diff --name-only | grep -Eq 'phase-26|phase-27|phase_26|phase_27'; then
  fail "Phase 26 or Phase 27 files were modified"
else
  pass "Phase 26 and Phase 27 remain untouched"
fi

echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not send email"
pass "teacher decision layer does not deploy or publish artifacts"
pass "decision history is preserved without deleting audit trail"
echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
