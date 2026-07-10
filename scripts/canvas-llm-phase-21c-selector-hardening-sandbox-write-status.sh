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

check_executable() {
  local path="$1"
  local label="$2"
  if [ -x "$path" ]; then pass "$label is executable"; else fail "$label is not executable"; fi
}

check_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if [ ! -f "$path" ]; then fail "$label missing file"; return; fi
  if grep -Fq -- "$needle" "$path"; then pass "$label"; else fail "$label"; fi
}

echo "Canvas LLM Phase 21C Selector Hardening + Sandbox Write Status"
echo "---------------------------------------------------------------"

PHASE_DIR="docs/programs/canvas-llm/phase-21c-selector-hardening-sandbox-write"
AGENT="scripts/canvas-llm/canvas_learning_agent.py"
GUARDRAIL="scripts/canvas-llm-handoff-breadcrumb-repair.py"

check_file "${PHASE_DIR}/README.md" "Phase 21C README"
check_file "${PHASE_DIR}/selector-rules.md" "Phase 21C selector rules"
check_file "${PHASE_DIR}/learning-expansion-map.md" "Phase 21C learning expansion map"
check_file "${PHASE_DIR}/write-gate.md" "Phase 21C write gate"
check_file "${AGENT}" "Canvas learning agent"

if python3 -m py_compile "${AGENT}" >/tmp/canvas-llm-phase-21c-agent-pycompile.txt 2>&1; then
  pass "Canvas learning agent Python syntax passes"
else
  cat /tmp/canvas-llm-phase-21c-agent-pycompile.txt
  fail "Canvas learning agent Python syntax fails"
fi
check_file "${GUARDRAIL}" "handoff breadcrumb guardrail"
check_executable "${GUARDRAIL}" "handoff breadcrumb guardrail"

check_contains "${PHASE_DIR}/README.md" "WARN: no sandbox QxWy candidate page found" "README records Phase 21B selector failure"
check_contains "${PHASE_DIR}/README.md" "course_id == 24399" "README locks write target to 24399"
check_contains "${PHASE_DIR}/README.md" "PHASE_21C_SANDBOX_EXISTING_PAGE_WRITE_APPROVED" "README records approval phrase"
check_contains "${PHASE_DIR}/README.md" "No production write is approved." "README blocks production writes"
check_contains "${PHASE_DIR}/README.md" "No reference course write is approved." "README blocks reference writes"
check_contains "${PHASE_DIR}/README.md" "announcements" "README includes announcements learning"
check_contains "${PHASE_DIR}/README.md" "attachments/files" "README includes attachment/file learning"
check_contains "${PHASE_DIR}/README.md" "Math Power Ups" "README includes Math Power Ups"
check_contains "${PHASE_DIR}/README.md" "Reading lesson numbers" "README includes Reading lesson numbers"
check_contains "${PHASE_DIR}/README.md" "comprehension letters" "README includes comprehension letters"

check_contains "${PHASE_DIR}/selector-rules.md" "course_id: 24399" "selector rules target 24399"
check_contains "${PHASE_DIR}/selector-rules.md" "must not create a page" "selector rules block page creation"
check_contains "${PHASE_DIR}/selector-rules.md" "unpublished page" "selector rules prefer unpublished"
check_contains "${PHASE_DIR}/selector-rules.md" "non-front-page" "selector rules prefer non-front-page"
check_contains "${PHASE_DIR}/selector-rules.md" "Q4W10" "selector rules avoid Q4W10"

check_contains "${PHASE_DIR}/learning-expansion-map.md" "without sending notifications" "announcement learning blocks notification sends"
check_contains "${PHASE_DIR}/learning-expansion-map.md" "Power Up resources" "file learning includes Power Up resources"
check_contains "${PHASE_DIR}/learning-expansion-map.md" "Math fact test" "assignment learning includes fact tests"
check_contains "${PHASE_DIR}/learning-expansion-map.md" "Reading comprehension letter" "assignment learning includes comprehension letters"
check_contains "${PHASE_DIR}/learning-expansion-map.md" "No grade, student, people" "learning map blocks protected data"

check_contains "${PHASE_DIR}/write-gate.md" "WRITE_PREVIEW_ONLY_UNTIL_OWNER_APPROVAL" "write gate remains preview until approval"
check_contains "${PHASE_DIR}/write-gate.md" "operation: update body" "write gate limits operation"
check_contains "${PHASE_DIR}/write-gate.md" "--allow-writes" "write gate requires allow-writes"
check_contains "${PHASE_DIR}/write-gate.md" "PHASE_21C_SANDBOX_EXISTING_PAGE_WRITE_APPROVED" "write gate requires approval phrase"
check_contains "${PHASE_DIR}/write-gate.md" "production courses" "write gate blocks production courses"
check_contains "${PHASE_DIR}/write-gate.md" "announcements send/notify" "write gate blocks announcement sends"

check_contains "${AGENT}" "phase21c-select-existing-page" "agent has Phase 21C select mode"
check_contains "${AGENT}" "phase21c-learning-expansion" "agent has Phase 21C learning mode"
check_contains "${AGENT}" "phase21c-existing-page-write-preview" "agent has Phase 21C write preview mode"
check_contains "${AGENT}" "PHASE_21C_SAFE_WRITE_MARKER" "agent has safe write marker"
check_contains "${AGENT}" "PHASE_21C_SANDBOX_EXISTING_PAGE_WRITE_APPROVED" "agent records approval phrase"
check_contains "${AGENT}" "Reference courses 21944, 21957, and 21919 are read-only." "agent preserves reference read-only rule"

if python3 "${GUARDRAIL}" --check >/tmp/canvas-llm-phase-21c-guardrail.txt 2>&1; then
  pass "handoff breadcrumb guardrail check passes"
else
  cat /tmp/canvas-llm-phase-21c-guardrail.txt
  fail "handoff breadcrumb guardrail check fails"
fi

if git ls-files .local | grep -q .; then
  fail ".local output is tracked by git"
else
  pass ".local output is not tracked by git"
fi

if git grep -n -E '(^|[[:space:]])(export[[:space:]]+)?CANVAS_TOKEN=' -- docs scripts bin >/tmp/canvas-llm-phase-21c-token-scan.txt 2>/dev/null; then
  cat /tmp/canvas-llm-phase-21c-token-scan.txt
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
