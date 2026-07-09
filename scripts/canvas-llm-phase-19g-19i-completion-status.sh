#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
HANDOFF="${ROOT_DIR}/docs/programs/canvas-llm/current-handoff.md"
MEMORY="${ROOT_DIR}/docs/programs/canvas-llm/memory/phase-19a-memory.md"
PHASE_19G="${ROOT_DIR}/docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview"
PHASE_19H="${ROOT_DIR}/docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview"
PHASE_19I="${ROOT_DIR}/docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet"

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

echo "Canvas LLM Phase 19G-I Completion Status"
echo "----------------------------------------"

check_file "${PHASE_19G}/README.md" "Phase 19G README"
check_file "${PHASE_19G}/title-cleaner-review-packet-spec.md" "Phase 19G review packet spec"
check_file "${PHASE_19G}/title-cleaner-review-packet.md" "Phase 19G review packet"

check_file "${PHASE_19H}/README.md" "Phase 19H README"
check_file "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "Phase 19H Medical Center diagnostics"

check_file "${PHASE_19I}/README.md" "Phase 19I README"
check_file "${PHASE_19I}/minimum-write-gate-checklist.md" "Phase 19I minimum write gate checklist"
check_file "${PHASE_19I}/phase-19-closure.md" "Phase 19 closure"
check_file "${PHASE_19I}/phase-20-next-step-recommendation.md" "Phase 20 next-step recommendation"

check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "SM5 Test 1" "review packet includes SM5 Test input"
check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "SM5: Test 1" "review packet includes SM5 canonical output"
check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "RM4: Spelling Test 6" "review packet includes RM4 Spelling canonical output"
check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "Test 7" "review packet includes ambiguous Test input"
check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "Chapter 4 Test" "review packet includes ambiguous Chapter Test input"
check_contains "${PHASE_19G}/title-cleaner-review-packet.md" "ambiguous_input_requires_review" "review packet blocks ambiguous input"

check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "PASS" "Medical Center includes PASS"
check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "WARN" "Medical Center includes WARN"
check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "FAIL" "Medical Center includes FAIL"
check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "BLOCKED" "Medical Center includes BLOCKED"
check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "Ambiguous input must not produce a final title" "Medical Center blocks ambiguous final title"
check_contains "${PHASE_19H}/medical-center-title-cleaner-diagnostics.md" "Canvas writes remain disabled" "Medical Center blocks Canvas writes"

check_contains "${PHASE_19I}/minimum-write-gate-checklist.md" "CANVAS_WRITES_REMAIN_BLOCKED" "write gate keeps Canvas writes blocked"
check_contains "${PHASE_19I}/minimum-write-gate-checklist.md" "I APPROVE THIS ONE CANVAS WRITE" "write gate requires explicit approval phrase"
check_contains "${PHASE_19I}/minimum-write-gate-checklist.md" "medical_center_result" "write gate requires Medical Center result"
check_contains "${PHASE_19I}/minimum-write-gate-checklist.md" "student data would be accessed" "write gate blocks student data"
check_contains "${PHASE_19I}/phase-19-closure.md" "Phase 19I — Minimum write gate design packet" "closure includes Phase 19I"
check_contains "${PHASE_19I}/phase-19-closure.md" "Phase 20 — Canvas LLM Minimum Write Gate Approval Packet" "closure recommends Phase 20"
check_contains "${PHASE_19I}/phase-20-next-step-recommendation.md" "must not perform a write unless Owen provides the exact approval phrase" "Phase 20 recommendation keeps writes blocked"

check_contains "${HANDOFF}" "Phase 19G-I" "handoff records Phase 19G-I"
check_contains "${HANDOFF}" "PR #300" "handoff preserves PR #300 breadcrumb"
check_contains "${HANDOFF}" "PR #301" "handoff preserves PR #301 breadcrumb"
check_contains "${HANDOFF}" "PR #302" "handoff preserves PR #302 breadcrumb"
check_contains "${HANDOFF}" "PR #303" "handoff preserves PR #303 breadcrumb"
check_contains "${HANDOFF}" "PR #304" "handoff preserves PR #304 breadcrumb"
check_contains "${HANDOFF}" "PR #305" "handoff preserves PR #305 breadcrumb"
check_contains "${HANDOFF}" "PR #306" "handoff preserves PR #306 breadcrumb"
check_contains "${HANDOFF}" "phase-19b-canonical-rules" "handoff preserves Phase 19B directory breadcrumb"
check_contains "${HANDOFF}" "phase-19c-evidence-vault-rule-catalog" "handoff preserves Phase 19C directory breadcrumb"
check_contains "${HANDOFF}" "phase-19d-seed-rule-catalog-title-cleaner" "handoff preserves Phase 19D directory breadcrumb"
check_contains "${HANDOFF}" "phase-19e-title-cleaner-validator-preview" "handoff preserves Phase 19E directory breadcrumb"
check_contains "${HANDOFF}" "phase-19f-title-cleaner-deterministic-prototype-preview" "handoff preserves Phase 19F directory breadcrumb"
check_contains "${HANDOFF}" "handoff-regression-rule.md" "handoff preserves regression rule breadcrumb"

check_contains "${MEMORY}" "Phase 19G-I Completion Update" "memory records Phase 19G-I update"
check_contains "${MEMORY}" "CANVAS_WRITES_REMAIN_BLOCKED" "memory records Phase 19 final write-blocked decision"
check_contains "${MEMORY}" "Phase 20 — Canvas LLM Minimum Write Gate Approval Packet" "memory records Phase 20 next step"

for file in \
  "${PHASE_19G}/README.md" \
  "${PHASE_19H}/README.md" \
  "${PHASE_19I}/README.md" \
  "${PHASE_19I}/minimum-write-gate-checklist.md"; do
  check_contains "${file}" "Canvas API calls" "${file#${ROOT_DIR}/} blocks Canvas API calls"
  check_contains "${file}" "Canvas writes" "${file#${ROOT_DIR}/} blocks Canvas writes"
  check_contains "${file}" "student data" "${file#${ROOT_DIR}/} blocks student data"
  check_contains "${file}" "school Canvas URL" "${file#${ROOT_DIR}/} blocks school Canvas URLs"
done

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check is documentation/data/status only"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not access student data"
emit PASS "status check does not read raw .local metadata"
emit PASS "status check does not implement app behavior"
emit PASS "status check does not create database migrations"
emit PASS "Phase 19 closes with Canvas writes blocked"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
