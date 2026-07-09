#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
RULE_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-19b-canonical-rules"
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

echo "Canvas LLM Phase 19B Canonical Rules Status"
echo "-------------------------------------------"

check_file "${HANDOFF}" "current handoff"
check_file "${MEMORY}" "Phase 19A memory"
check_file "${HANDOFF_RULE}" "handoff regression rule"
check_file "${RULE_DIR}/canonical-rule-constitution.md" "canonical rule constitution"
check_file "${RULE_DIR}/canonical-subject-prefixes.md" "canonical subject prefixes"
check_file "${RULE_DIR}/canonical-assignment-title-rules.md" "canonical assignment title rules"
check_file "${RULE_DIR}/canonical-study-guide-grading.md" "canonical study guide grading"
check_file "${RULE_DIR}/canonical-reading-spelling-together.md" "canonical Reading/Spelling Together"
check_file "${RULE_DIR}/canonical-friday-rules.md" "canonical Friday rules"
check_file "${RULE_DIR}/canonical-newsletter-rules.md" "canonical newsletter rules"
check_file "${RULE_DIR}/canonical-file-management-policy.md" "canonical file management policy"
check_file "${RULE_DIR}/canonical-source-authority-policy.md" "canonical source authority policy"
check_file "${RULE_DIR}/canonical-medical-center-diagnostics.md" "canonical Medical Center diagnostics"
check_file "${RULE_DIR}/canonical-write-gate-policy.md" "canonical write gate policy"

check_contains "${RULE_DIR}/canonical-rule-constitution.md" "Evidence Vault" "constitution includes Evidence Vault architecture"
check_contains "${RULE_DIR}/canonical-rule-constitution.md" "APPROVED_PATTERN" "constitution includes evidence classification"
check_contains "${RULE_DIR}/canonical-rule-constitution.md" "AI may not" "constitution includes AI boundary"

check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| Math | SM5 |" "prefix table includes Math SM5"
check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| Reading | RM4 |" "prefix table includes Reading RM4"
check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| Spelling | RM4 |" "prefix table includes Spelling RM4"
check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| Language Arts / Shurley | ELA4 |" "prefix table includes ELA4"
check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| History | HIST4 |" "prefix table includes HIST4"
check_contains "${RULE_DIR}/canonical-subject-prefixes.md" "| Science | SCI4 |" "prefix table includes SCI4"

check_contains "${RULE_DIR}/canonical-assignment-title-rules.md" "SM5: Test {number}" "assignment titles include SM5 test"
check_contains "${RULE_DIR}/canonical-assignment-title-rules.md" "SM5: Fact Test {number}" "assignment titles include SM5 fact test"
check_contains "${RULE_DIR}/canonical-assignment-title-rules.md" "SM5: Study Guide {number}" "assignment titles include SM5 study guide"
check_contains "${RULE_DIR}/canonical-assignment-title-rules.md" "AI may not invent assignments" "assignment rules block AI assignment invention"

check_contains "${RULE_DIR}/canonical-study-guide-grading.md" "points_possible = 0" "Study Guide points rule is zero"
check_contains "${RULE_DIR}/canonical-study-guide-grading.md" "exclude_from_final_grade = true" "Study Guide exclude-from-final rule exists"
check_contains "${RULE_DIR}/canonical-study-guide-grading.md" "Does Not Count Toward Final Grade" "Study Guide Canvas checkbox rule exists"

check_contains "${RULE_DIR}/canonical-reading-spelling-together.md" "Standalone Spelling announcements are blocked" "Reading/Spelling blocks standalone Spelling announcements"
check_contains "${RULE_DIR}/canonical-reading-spelling-together.md" "Reading-owned Canvas page" "Reading/Spelling uses Reading-owned page"

check_contains "${RULE_DIR}/canonical-friday-rules.md" "no normal homework assignments" "Friday blocks normal homework"
check_contains "${RULE_DIR}/canonical-friday-rules.md" "tests are allowed" "Friday allows tests"
check_contains "${RULE_DIR}/canonical-friday-rules.md" "omit At Home" "Friday omits At Home by default"

check_contains "${RULE_DIR}/canonical-newsletter-rules.md" "Newsletter = Homeroom Canvas Page" "newsletter is Homeroom Canvas Page"
check_contains "${RULE_DIR}/canonical-newsletter-rules.md" "The newsletter has been updated for the week of {date range}." "newsletter announcement text is canonical"

check_contains "${RULE_DIR}/canonical-file-management-policy.md" "READ ONLY" "file assistant starts read-only"
check_contains "${RULE_DIR}/canonical-file-management-policy.md" "AI may not silently alter source materials" "file policy blocks silent mutation"

check_contains "${RULE_DIR}/canonical-source-authority-policy.md" "Historical Canvas data is evidence, not authority" "source authority treats historical Canvas as evidence"
check_contains "${RULE_DIR}/canonical-source-authority-policy.md" "AI suggestions are lowest authority" "source authority places AI suggestions lowest"

check_contains "${RULE_DIR}/canonical-medical-center-diagnostics.md" "PASS" "Medical Center includes PASS"
check_contains "${RULE_DIR}/canonical-medical-center-diagnostics.md" "WARN" "Medical Center includes WARN"
check_contains "${RULE_DIR}/canonical-medical-center-diagnostics.md" "FAIL" "Medical Center includes FAIL"
check_contains "${RULE_DIR}/canonical-medical-center-diagnostics.md" "BLOCKED" "Medical Center includes BLOCKED"

check_contains "${RULE_DIR}/canonical-write-gate-policy.md" "Canvas writes remain disabled" "write gate keeps Canvas writes disabled"
check_contains "${RULE_DIR}/canonical-write-gate-policy.md" "exact human approval phrase" "write gate requires exact approval phrase"
check_contains "${RULE_DIR}/canonical-write-gate-policy.md" "Phase 19B does not approve a first write" "write gate does not approve first write"

check_contains "${HANDOFF}" "Phase 19B — Canonical Rule Constitution" "handoff records Phase 19B"
check_contains "${HANDOFF}" "f61dae2" "handoff records PR #301 baseline"
check_contains "${HANDOFF}" "phase-19b-canonical-rules" "handoff records Phase 19B rule directory"

check_contains "${MEMORY}" "Phase 19B Canonical Rule Constitution Update" "memory records Phase 19B update"
check_contains "${MEMORY}" "phase-19b-canonical-rules" "memory records Phase 19B rule directory"
check_contains "${HANDOFF_RULE}" "Preserve historical handoff breadcrumbs" "handoff regression rule preserves historical breadcrumbs"
check_contains "${HANDOFF_RULE}" "restore the historical breadcrumb" "handoff regression rule prefers restoring breadcrumbs"
check_contains "${HANDOFF}" "handoff-regression-rule.md" "handoff references handoff regression rule"
check_contains "${MEMORY}" "Handoff Regression Rule Added During Phase 19B" "memory records handoff regression rule"

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check is documentation-only"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not access student data"
emit PASS "status check does not read raw .local metadata"
emit PASS "status check does not implement app behavior"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
