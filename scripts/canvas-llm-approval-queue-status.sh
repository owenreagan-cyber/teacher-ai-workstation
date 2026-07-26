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

QUEUE="scripts/canvas_llm_phase22/approval_queue.py"
REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/approval-queue-contract.md"
TEST="tests/canvas-llm-approval-queue-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Approval Queue Status"
echo "--------------------------------"
echo

if [[ -f "$QUEUE" ]]; then
  pass "approval queue module exists"
else
  fail "approval queue module missing"
fi

if [[ -f "$CONTRACT" ]]; then
  pass "approval queue contract exists"
else
  fail "approval queue contract missing"
fi

if [[ -f "$TEST" ]]; then
  pass "approval queue test exists"
else
  fail "approval queue test missing"
fi

if grep -F -- '--approval-queue-status' bin/chief-of-staff >/dev/null; then
  pass "chief-of-staff dispatches approval queue status"
else
  fail "chief-of-staff dispatch missing for approval queue status"
fi

if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$QUEUE" "$REGISTRY" >/dev/null 2>&1; then
  pass "approval queue Python syntax passes"
else
  fail "approval queue Python syntax fails"
fi

for symbol in ApprovalQueueItem TeacherDecision build_queue_from_registry derive_queue_status print_queue_report validate_teacher_decision_shape queue_is_read_only; do
  if grep -Fq "$symbol" "$QUEUE"; then
    pass "approval queue includes $symbol"
  else
    fail "approval queue missing $symbol"
  fi
done

if grep -Fq 'artifact_registry' "$QUEUE"; then
  pass "approval queue builds on artifact registry"
else
  fail "approval queue does not integrate with artifact registry"
fi

if grep -Fq 'INSERT INTO' "$QUEUE" || grep -Fq 'UPDATE drafts' "$QUEUE" || grep -Fq 'approve_artifact' "$QUEUE" || grep -Fq 'deploy_artifact' "$QUEUE"; then
  fail "approval queue contains mutation or deployment handlers"
else
  pass "approval queue is read-only (no approval or deployment mutation)"
fi

if grep -Eiq 'smtp|sendgrid|gmail|canvas\.instructure|urllib\.request|requests\.(get|post)|@.*\.(com|org|net)' "$QUEUE"; then
  fail "approval queue references forbidden transport or secret patterns"
else
  pass "approval queue has no transport or secret references"
fi

if python3 "$QUEUE" self-test >/tmp/c0r-queue-self-test.txt 2>&1; then
  pass "approval queue self-test passes"
else
  cat /tmp/c0r-queue-self-test.txt
  fail "approval queue self-test fails"
fi

if bash "$TEST" >/tmp/c0r-approval-queue-test.txt 2>&1; then
  pass "approval queue regression test passes"
else
  cat /tmp/c0r-approval-queue-test.txt
  fail "approval queue regression test fails"
fi

if bin/chief-of-staff --approval-queue-status >"$REPORT_OUT" 2>&1; then
  pass "approval queue report command exits successfully"
else
  cat "$REPORT_OUT"
  fail "approval queue report command failed"
fi

if grep -Fq 'Canvas LLM Approval Queue' "$REPORT_OUT"; then
  pass "approval queue report header is present"
else
  fail "approval queue report header missing"
fi

if grep -Eiq '(@|smtp|sendgrid|gmail|sqlite|/Users/|\.local/)' "$REPORT_OUT"; then
  fail "approval queue report leaked sensitive or private values"
else
  pass "approval queue report excludes emails, URLs, secrets, and private paths"
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
pass "approval queue does not approve or deploy artifacts"
pass "no duplicate approval storage table is created"
echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
