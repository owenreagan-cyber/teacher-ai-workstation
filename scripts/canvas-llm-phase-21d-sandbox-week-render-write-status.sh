#!/usr/bin/env bash
set -u

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
warn() { echo "WARN: $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

check_file() {
  local path="$1"
  local label="$2"
  if [ -f "$path" ]; then pass "$label exists"; else fail "$label missing"; fi
}

check_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if [ ! -f "$path" ]; then fail "$label missing file"; return; fi
  if grep -Fq -- "$needle" "$path"; then pass "$label"; else fail "$label"; fi
}

echo "Canvas LLM Phase 21D Sandbox Week Render Write Status"
echo "------------------------------------------------------"

PHASE_DIR="docs/programs/canvas-llm/phase-21d-sandbox-week-render-write"
AGENT="scripts/canvas-llm/canvas_learning_agent.py"
GUARDRAIL="scripts/canvas-llm-handoff-breadcrumb-repair.py"

check_file "${PHASE_DIR}/README.md" "Phase 21D README"
check_file "${PHASE_DIR}/rendered-week-plan.md" "rendered week plan"
check_file "${PHASE_DIR}/assignment-creation-rules.md" "assignment creation rules"
check_file "${PHASE_DIR}/people-sandbox-verification.md" "People sandbox verification"
check_file "${PHASE_DIR}/write-gate.md" "write gate"
check_file "${PHASE_DIR}/rollback-plan.md" "rollback plan"
check_file "${PHASE_DIR}/safety-boundary.md" "safety boundary"
check_file "${AGENT}" "Canvas learning agent"

if python3 -m py_compile "${AGENT}" >/tmp/canvas-llm-phase-21d-agent-pycompile.txt 2>&1; then
  pass "Canvas learning agent Python syntax passes"
else
  cat /tmp/canvas-llm-phase-21d-agent-pycompile.txt
  fail "Canvas learning agent Python syntax fails"
fi

check_contains "${AGENT}" "phase21d-sandbox-people-verify" "agent supports People sandbox verification mode"
check_contains "${AGENT}" "phase21d-sandbox-week-render-preview" "agent supports render preview mode"
check_contains "${AGENT}" "phase21d-sandbox-week-write" "agent supports sandbox week write mode"
check_contains "${AGENT}" "phase21d-sandbox-week-rollback-preview" "agent supports rollback preview mode"
check_contains "${AGENT}" "phase21d-sandbox-week-rollback" "agent supports rollback mode"
check_contains "${AGENT}" "PHASE_21D_SANDBOX_WEEK_WRITE_APPROVED" "agent has write approval phrase"
check_contains "${AGENT}" "PHASE_21D_SANDBOX_WEEK_ROLLBACK_APPROVED" "agent has rollback approval phrase"
check_contains "${AGENT}" "PHASE_21D_TARGET_COURSE_ID = \"24399\"" "agent locks Phase 21D target course to 24399"
check_contains "${AGENT}" "PHASE_21D_TARGET_PAGE_SLUG = \"q1w1\"" "agent locks Phase 21D page slug to q1w1"
check_contains "${AGENT}" "BLOCKED_UNEXPECTED_PEOPLE_IN_SANDBOX_COURSE" "agent blocks unexpected People"
check_contains "${AGENT}" "owner_user_present" "agent writes sanitized People summary"
check_contains "${AGENT}" "unexpected_people_count" "agent records unexpected People count only"
check_contains "${AGENT}" "reused_existing_assignment" "agent reuses existing assignments"
check_contains "${AGENT}" "Phase 21D Sandbox Math Lesson 1 Homework Odd" "agent includes odd homework naming"
check_contains "${AGENT}" "Phase 21D Sandbox Math Lesson 2 Homework Even" "agent includes even homework naming"
check_contains "${AGENT}" "Friday" "agent includes Friday"
check_contains "${AGENT}" "no_homework" "agent includes Friday no homework rule"
check_contains "${AGENT}" "teacher-ai-workstation phase-21d sandbox-week-write" "agent has page marker"

check_contains "${PHASE_DIR}/README.md" "Monday: Lesson 1, odd homework" "README documents Monday Lesson 1 odd homework"
check_contains "${PHASE_DIR}/README.md" "Tuesday: Lesson 2, even homework" "README documents Tuesday Lesson 2 even homework"
check_contains "${PHASE_DIR}/README.md" "Friday: Lesson 5, no homework" "README documents Friday no homework"
check_contains "${PHASE_DIR}/README.md" "BLOCKED_UNEXPECTED_PEOPLE_IN_SANDBOX_COURSE" "README documents People blocking condition"
check_contains "${PHASE_DIR}/assignment-creation-rules.md" "reused_existing_assignment" "assignment rules require idempotency"
check_contains "${PHASE_DIR}/people-sandbox-verification.md" "read-only sandbox confidence gate" "People doc limits People check to safety"
check_contains "${PHASE_DIR}/people-sandbox-verification.md" "People writes" "People doc blocks People writes"
check_contains "${PHASE_DIR}/write-gate.md" "PHASE_21D_SANDBOX_WEEK_WRITE_APPROVED" "write gate has write approval"
check_contains "${PHASE_DIR}/rollback-plan.md" "PHASE_21D_SANDBOX_WEEK_ROLLBACK_APPROVED" "rollback doc has rollback approval"

if python3 "${GUARDRAIL}" --check >/tmp/canvas-llm-phase-21d-guardrail.txt 2>&1; then
  pass "handoff breadcrumb guardrail check passes"
else
  cat /tmp/canvas-llm-phase-21d-guardrail.txt
  fail "handoff breadcrumb guardrail check fails"
fi

if git ls-files .local | grep -q .; then
  fail ".local output is tracked by git"
else
  pass ".local output is not tracked by git"
fi

if git grep -n -E '(^|[[:space:]])(export[[:space:]]+)?CANVAS_TOKEN=' -- docs scripts bin >/tmp/canvas-llm-phase-21d-token-scan.txt 2>/dev/null; then
  cat /tmp/canvas-llm-phase-21d-token-scan.txt
  fail "committed files contain a CANVAS_TOKEN assignment"
else
  pass "committed files do not contain a CANVAS_TOKEN assignment"
fi

echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not fetch live Canvas data"
pass "status check does not write to Canvas"
pass "status check does not call People APIs"
pass "status check does not read raw .local metadata"
pass "status check does not print CANVAS_TOKEN"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
