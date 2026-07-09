#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PHASE_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-20-demo-sandbox-write-gate-approval-packet"
HANDOFF="${ROOT_DIR}/docs/programs/canvas-llm/current-handoff.md"
MEMORY="${ROOT_DIR}/docs/programs/canvas-llm/memory/phase-19a-memory.md"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

emit() {
  local level="$1"
  shift
  case "${level}" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    *) echo "FAIL: invalid status level ${level}"; FAIL_COUNT=$((FAIL_COUNT + 1)); return ;;
  esac
  echo "${level}: $*"
}

check_file() {
  local path="$1"
  local label="$2"
  if [[ -f "${path}" ]]; then
    emit PASS "${label} exists"
  else
    emit FAIL "${label} missing"
  fi
}

check_contains() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "${path}" ]]; then
    emit FAIL "${label}: missing file ${path}"
    return
  fi
  if grep -Fq "${pattern}" "${path}"; then
    emit PASS "${label}"
  else
    emit FAIL "${label}"
  fi
}

echo "Canvas LLM Phase 20 Demo Sandbox Write Gate Approval Packet Status"
echo "------------------------------------------------------------------"

check_file "${PHASE_DIR}/README.md" "Phase 20 README"
check_file "${PHASE_DIR}/owner-designated-demo-sandbox.md" "owner-designated sandbox record"
check_file "${PHASE_DIR}/first-write-approval-packet.md" "first write approval packet"
check_file "${PHASE_DIR}/medical-center-write-gate-review.md" "Medical Center write gate review"
check_file "${PHASE_DIR}/write-execution-stub.md" "write execution stub"
check_file "${PHASE_DIR}/phase-21-next-step-recommendation.md" "Phase 21 next step recommendation"

check_contains "${PHASE_DIR}/owner-designated-demo-sandbox.md" "OWNER_DESIGNATED_DEMO_SANDBOX" "course 24399 is owner-designated demo sandbox"
check_contains "${PHASE_DIR}/owner-designated-demo-sandbox.md" "never_had_students: true" "sandbox has never had students"
check_contains "${PHASE_DIR}/owner-designated-demo-sandbox.md" "no_grades: true" "sandbox has no grades"
check_contains "${PHASE_DIR}/owner-designated-demo-sandbox.md" "no_personal_information: true" "sandbox has no personal information"

check_contains "${PHASE_DIR}/first-write-approval-packet.md" "I APPROVE THIS ONE CANVAS WRITE FOR COURSE <24399>" "approval phrase is recorded"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "target_course_id: 24399" "target course is 24399"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "target_canvas_object_type: page" "target object type is page"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "operation_type: create" "operation type is create"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "published: false" "page is unpublished"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "title: Math Automation Sandbox" "page title is exact"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "Exactly one Canvas page" "scope is exactly one page"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "PASS_WITH_WRITE_STILL_NOT_EXECUTED" "Medical Center result keeps write unexecuted"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "delete the newly created page by page ID" "rollback plan is present"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "no students were accessed" "validation blocks student access"
check_contains "${PHASE_DIR}/first-write-approval-packet.md" "no grades were accessed" "validation blocks grade access"

check_contains "${PHASE_DIR}/medical-center-write-gate-review.md" "PASS_WITH_WRITE_STILL_NOT_EXECUTED" "Medical Center review passes but does not execute"
check_contains "${PHASE_DIR}/medical-center-write-gate-review.md" "Target course is owner-designated demo sandbox" "Medical Center accepts owner sandbox"
check_contains "${PHASE_DIR}/medical-center-write-gate-review.md" "Operation is limited to one Canvas page" "Medical Center limits operation"
check_contains "${PHASE_DIR}/medical-center-write-gate-review.md" "No student data is required" "Medical Center blocks student data"
check_contains "${PHASE_DIR}/medical-center-write-gate-review.md" "No grade data is required" "Medical Center blocks grade data"

check_contains "${PHASE_DIR}/write-execution-stub.md" "POST /api/v1/courses/24399/pages" "future write endpoint is documented"
check_contains "${PHASE_DIR}/write-execution-stub.md" "wiki_page[title]=Math Automation Sandbox" "future write title is documented"
check_contains "${PHASE_DIR}/write-execution-stub.md" "wiki_page[published]=false" "future write unpublished flag is documented"
check_contains "${PHASE_DIR}/write-execution-stub.md" "never print token" "future write must not print token"
check_contains "${PHASE_DIR}/write-execution-stub.md" "never commit school Canvas URL" "future write must not commit school URL"

check_contains "${PHASE_DIR}/phase-21-next-step-recommendation.md" "Phase 21 — Execute One Approved Demo Sandbox Canvas Write" "Phase 21 is recommended"
check_contains "${PHASE_DIR}/phase-21-next-step-recommendation.md" "Create one unpublished Canvas page in course 24399 titled Math Automation Sandbox" "Phase 21 exact operation is recorded"

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check is documentation/data/status only"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not access student data"
emit PASS "status check does not access grades"
emit PASS "status check does not read raw .local metadata"
emit PASS "status check does not implement app behavior"
emit PASS "status check does not create database migrations"
emit PASS "Phase 20 approval packet is prepared but write is not executed"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
