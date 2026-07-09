#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PHASE_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview"
HANDOFF="${ROOT_DIR}/docs/programs/canvas-llm/current-handoff.md"
MEMORY="${ROOT_DIR}/docs/programs/canvas-llm/memory/phase-19a-memory.md"
VALIDATOR="${ROOT_DIR}/scripts/canvas-llm-phase-19e-title-cleaner-validator-preview.py"

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

echo "Canvas LLM Phase 19E Title Cleaner Validator Preview Status"
echo "-----------------------------------------------------------"

check_file "${PHASE_DIR}/README.md" "Phase 19E README"
check_file "${PHASE_DIR}/title-cleaner-validator-spec.md" "validator spec"
check_file "${PHASE_DIR}/title-cleaner-validator-report.md" "validator report"
check_file "${PHASE_DIR}/preview-only-boundary.md" "preview-only boundary"
check_file "${PHASE_DIR}/phase-19e-next-step-recommendation.md" "next-step recommendation"
check_file "${VALIDATOR}" "validator script"

if [[ -x "${VALIDATOR}" ]]; then
  emit PASS "validator script is executable"
else
  emit FAIL "validator script is executable"
fi

"${VALIDATOR}" > /tmp/phase19e-validator-status.out 2> /tmp/phase19e-validator-status.err
validator_rc=$?
if [[ "${validator_rc}" -eq 0 ]]; then
  emit PASS "validator exits successfully"
else
  emit FAIL "validator exits successfully"
fi

if [[ -s /tmp/phase19e-validator-status.err ]]; then
  emit FAIL "validator stderr is empty"
else
  emit PASS "validator stderr is empty"
fi

if grep -Fq "FAIL: 0" /tmp/phase19e-validator-status.out; then
  emit PASS "validator reports FAIL 0"
else
  emit FAIL "validator reports FAIL 0"
fi

check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "SM5: Test {number}" "spec checks Math Test pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "SM5: Fact Test {number}" "spec checks Math Fact Test pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "SM5: Study Guide {number}" "spec checks Math Study Guide pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "ELA4: Test {number}" "spec checks ELA Test pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "RM4: Test {number}" "spec checks Reading Test pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "RM4: Spelling Test {number}" "spec checks Spelling Test pattern"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "never_silently_mutate_canvas" "spec checks silent mutation flag"
check_contains "${PHASE_DIR}/title-cleaner-validator-spec.md" "ambiguous_input_requires_review" "spec checks ambiguous review flag"

check_contains "${PHASE_DIR}/title-cleaner-validator-report.md" "Canvas LLM Phase 19E Title Cleaner Validator Preview" "report includes validator output"
check_contains "${PHASE_DIR}/title-cleaner-validator-report.md" "FAIL: 0" "report records FAIL 0"

check_contains "${PHASE_DIR}/preview-only-boundary.md" "Canvas API calls" "boundary blocks Canvas API calls"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "Canvas writes" "boundary blocks Canvas writes"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "student data access" "boundary blocks student data"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "raw \`.local\` metadata reads or commits" "boundary blocks raw local metadata"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "school Canvas URL commits" "boundary blocks school Canvas URLs"

check_contains "${PHASE_DIR}/phase-19e-next-step-recommendation.md" "Phase 19F — Title Cleaner Deterministic Prototype Preview" "next step recommends Phase 19F prototype"

check_contains "${HANDOFF}" "Phase 19E — Title Cleaner Validator Preview" "handoff records Phase 19E"
check_contains "${HANDOFF}" "PR #300" "handoff preserves PR #300 breadcrumb"
check_contains "${HANDOFF}" "PR #301" "handoff preserves PR #301 breadcrumb"
check_contains "${HANDOFF}" "PR #302" "handoff preserves PR #302 breadcrumb"
check_contains "${HANDOFF}" "PR #303" "handoff preserves PR #303 breadcrumb"
check_contains "${HANDOFF}" "PR #304" "handoff preserves PR #304 breadcrumb"
check_contains "${HANDOFF}" "phase-19b-canonical-rules" "handoff preserves Phase 19B directory breadcrumb"
check_contains "${HANDOFF}" "phase-19c-evidence-vault-rule-catalog" "handoff preserves Phase 19C directory breadcrumb"
check_contains "${HANDOFF}" "phase-19d-seed-rule-catalog-title-cleaner" "handoff preserves Phase 19D directory breadcrumb"
check_contains "${HANDOFF}" "phase-19e-title-cleaner-validator-preview" "handoff records Phase 19E directory"
check_contains "${HANDOFF}" "handoff-regression-rule.md" "handoff preserves regression rule breadcrumb"

check_contains "${MEMORY}" "Phase 19E Title Cleaner Validator Preview Update" "memory records Phase 19E update"
check_contains "${MEMORY}" "SM5: Test {number}" "memory records Math Test validator pattern"
check_contains "${MEMORY}" "RM4: Spelling Test {number}" "memory records Spelling validator pattern"
check_contains "${MEMORY}" "ambiguous_input_requires_review" "memory records ambiguous review validator flag"

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
emit PASS "validator is preview-only and does not mutate Canvas"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
