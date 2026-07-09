#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PHASE_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner"
HANDOFF="${ROOT_DIR}/docs/programs/canvas-llm/current-handoff.md"
MEMORY="${ROOT_DIR}/docs/programs/canvas-llm/memory/phase-19a-memory.md"
HANDOFF_RULE="${ROOT_DIR}/docs/programs/canvas-llm/handoff-regression-rule.md"

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
    emit FAIL "${label} is missing"
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

check_json() {
  local path="$1"
  local label="$2"
  if python3 -m json.tool "${path}" >/dev/null 2>&1; then
    emit PASS "${label} is valid JSON"
  else
    emit FAIL "${label} is invalid JSON"
  fi
}

echo "Canvas LLM Phase 19D Seed Rule Catalog + Title Cleaner Status"
echo "-------------------------------------------------------------"

check_file "${HANDOFF}" "current handoff"
check_file "${MEMORY}" "Phase 19A memory"
check_file "${HANDOFF_RULE}" "handoff regression rule"

check_file "${PHASE_DIR}/README.md" "Phase 19D README"
check_file "${PHASE_DIR}/evidence.json" "evidence seed data"
check_file "${PHASE_DIR}/rules.json" "rule seed data"
check_file "${PHASE_DIR}/links.json" "link seed data"
check_file "${PHASE_DIR}/title-normalization-rules.json" "title normalization rules"
check_file "${PHASE_DIR}/title-normalization-fixtures.md" "title normalization fixtures"
check_file "${PHASE_DIR}/preview-only-boundary.md" "preview-only boundary"
check_file "${PHASE_DIR}/phase-19d-next-step-recommendation.md" "Phase 19D next-step recommendation"

check_json "${PHASE_DIR}/evidence.json" "evidence.json"
check_json "${PHASE_DIR}/rules.json" "rules.json"
check_json "${PHASE_DIR}/links.json" "links.json"
check_json "${PHASE_DIR}/title-normalization-rules.json" "title-normalization-rules.json"

check_contains "${PHASE_DIR}/evidence.json" "EV-CANVAS-0001" "evidence includes stable IDs"
check_contains "${PHASE_DIR}/evidence.json" "EV-CANVAS-0006" "evidence includes owner title cleaner requirement"
check_contains "${PHASE_DIR}/evidence.json" "APPROVED_PATTERN" "evidence includes approved classification"

check_contains "${PHASE_DIR}/rules.json" "RULE-CANVAS-PREFIX-MATH-001" "rules include Math prefix rule"
check_contains "${PHASE_DIR}/rules.json" "RULE-CANVAS-PREFIX-SPELLING-001" "rules include Spelling RM4 prefix rule"
check_contains "${PHASE_DIR}/rules.json" "RULE-CANVAS-NORMALIZER-TITLE-001" "rules include title normalizer rule"
check_contains "${PHASE_DIR}/rules.json" "SM5: Test {number}" "rules include canonical Math Test pattern"
check_contains "${PHASE_DIR}/rules.json" "SM5: Fact Test {number}" "rules include canonical Math Fact Test pattern"
check_contains "${PHASE_DIR}/rules.json" "SM5: Study Guide {number}" "rules include canonical Math Study Guide pattern"
check_contains "${PHASE_DIR}/rules.json" "RM4: Spelling Test {number}" "rules include Spelling normalized to RM4"

check_contains "${PHASE_DIR}/links.json" "LINK-CANVAS-0001" "links include stable IDs"
check_contains "${PHASE_DIR}/links.json" "supports" "links include support relationship"

check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-MATH-TEST-001" "normalizer includes Math Test cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-MATH-FACT-TEST-001" "normalizer includes Math Fact Test cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-MATH-STUDY-GUIDE-001" "normalizer includes Math Study Guide cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-ELA-TEST-001" "normalizer includes ELA Test cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-READING-TEST-001" "normalizer includes Reading Test cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "NORM-CANVAS-SPELLING-TEST-001" "normalizer includes Spelling Test cleaner"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "never_silently_mutate_canvas" "normalizer blocks silent Canvas mutation"
check_contains "${PHASE_DIR}/title-normalization-rules.json" "ambiguous_input_requires_review" "normalizer requires review for ambiguous input"

check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'SM5 Test 1` | math_test | `SM5: Test 1' "fixtures normalize SM5 Test"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'SM 5: Test 1` | math_test | `SM5: Test 1' "fixtures normalize spaced SM5"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'SM5 Fact Test 2` | math_fact_test | `SM5: Fact Test 2' "fixtures normalize Math Fact Test"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'SM5 Study Guide 3` | math_study_guide | `SM5: Study Guide 3' "fixtures normalize Math Study Guide"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'ELA4 Test 4` | ela_test | `ELA4: Test 4' "fixtures normalize ELA Test"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'RM4 Test 5` | reading_test | `RM4: Test 5' "fixtures normalize Reading Test"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'Spelling Test 6` | spelling_test | `RM4: Spelling Test 6' "fixtures normalize Spelling Test to RM4"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'SP4 Spelling Test 6` | spelling_test | `RM4: Spelling Test 6' "fixtures correct SP4 Spelling to RM4"
check_contains "${PHASE_DIR}/title-normalization-fixtures.md" 'Test 7` | ambiguous | needs review' "fixtures require review for ambiguous Test"

check_contains "${PHASE_DIR}/preview-only-boundary.md" "Canvas API calls" "boundary blocks Canvas API calls"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "Canvas writes" "boundary blocks Canvas writes"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "student data access" "boundary blocks student data"
check_contains "${PHASE_DIR}/preview-only-boundary.md" "classify ambiguous inputs without review" "boundary blocks ambiguous auto-classification"

check_contains "${PHASE_DIR}/phase-19d-next-step-recommendation.md" "Phase 19E — Title Cleaner Validator Preview" "next step recommends Phase 19E cleaner validator"

check_contains "${HANDOFF}" "Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview" "handoff records Phase 19D"
check_contains "${HANDOFF}" "PR #300" "handoff preserves PR #300 breadcrumb"
check_contains "${HANDOFF}" "PR #301" "handoff preserves PR #301 breadcrumb"
check_contains "${HANDOFF}" "PR #302" "handoff preserves PR #302 breadcrumb"
check_contains "${HANDOFF}" "PR #303" "handoff preserves PR #303 breadcrumb"
check_contains "${HANDOFF}" "phase-19c-evidence-vault-rule-catalog" "handoff preserves Phase 19C schema directory breadcrumb"
check_contains "${HANDOFF}" "phase-19d-seed-rule-catalog-title-cleaner" "handoff records Phase 19D directory"

check_contains "${MEMORY}" "Phase 19D Machine-Readable Seed Rule Catalog + Title Cleaner Preview Update" "memory records Phase 19D update"
check_contains "${MEMORY}" "SM5 Test 1 -> SM5: Test 1" "memory records Math cleaner example"
check_contains "${MEMORY}" "Spelling Test 1 -> RM4: Spelling Test 1" "memory records Spelling cleaner example"
check_contains "${MEMORY}" "phase-19d-seed-rule-catalog-title-cleaner" "memory records Phase 19D directory"

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
emit PASS "title cleaner is preview-only and does not mutate Canvas"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
