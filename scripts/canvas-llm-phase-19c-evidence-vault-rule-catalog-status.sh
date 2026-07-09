#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCHEMA_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog"
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

echo "Canvas LLM Phase 19C Evidence Vault + Rule Catalog Status"
echo "---------------------------------------------------------"

check_file "${HANDOFF}" "current handoff"
check_file "${MEMORY}" "Phase 19A memory"
check_file "${HANDOFF_RULE}" "handoff regression rule"

check_file "${SCHEMA_DIR}/evidence-vault-schema.md" "Evidence Vault schema"
check_file "${SCHEMA_DIR}/evidence-classification-schema.md" "evidence classification schema"
check_file "${SCHEMA_DIR}/rule-catalog-schema.md" "Rule Catalog schema"
check_file "${SCHEMA_DIR}/rule-review-workflow.md" "rule review workflow"
check_file "${SCHEMA_DIR}/rule-source-linking-schema.md" "rule source linking schema"
check_file "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "diagnostic readiness schema"
check_file "${SCHEMA_DIR}/preview-only-boundary.md" "preview-only boundary"
check_file "${SCHEMA_DIR}/phase-19c-next-step-recommendation.md" "Phase 19C next-step recommendation"

check_contains "${SCHEMA_DIR}/evidence-vault-schema.md" "EV-CANVAS-0001" "Evidence Vault includes stable evidence ID pattern"
check_contains "${SCHEMA_DIR}/evidence-vault-schema.md" "No rule without evidence" "Evidence Vault includes no-rule-without-evidence principle"
check_contains "${SCHEMA_DIR}/evidence-vault-schema.md" "canvas_write_relevance = preview_only" "Evidence Vault defaults to preview-only write relevance"

check_contains "${SCHEMA_DIR}/evidence-classification-schema.md" "APPROVED_PATTERN" "classification includes APPROVED_PATTERN"
check_contains "${SCHEMA_DIR}/evidence-classification-schema.md" "WORKFLOW_EVIDENCE" "classification includes WORKFLOW_EVIDENCE"
check_contains "${SCHEMA_DIR}/evidence-classification-schema.md" "LEGACY_FORMAT_ONLY" "classification includes LEGACY_FORMAT_ONLY"
check_contains "${SCHEMA_DIR}/evidence-classification-schema.md" "UNKNOWN_NEEDS_REVIEW" "classification includes UNKNOWN_NEEDS_REVIEW"
check_contains "${SCHEMA_DIR}/evidence-classification-schema.md" "Classification does not authorize Canvas writes" "classification blocks Canvas write authorization"

check_contains "${SCHEMA_DIR}/rule-catalog-schema.md" "RULE-CANVAS-0001" "Rule Catalog includes stable rule ID pattern"
check_contains "${SCHEMA_DIR}/rule-catalog-schema.md" "Rule Catalog converts approved evidence into deterministic rules" "Rule Catalog purpose is deterministic rule conversion"
check_contains "${SCHEMA_DIR}/rule-catalog-schema.md" "No rule may imply current Canvas write approval" "Rule Catalog blocks current write approval"

check_contains "${SCHEMA_DIR}/rule-review-workflow.md" "AI may not approve rules" "review workflow blocks AI rule approval"
check_contains "${SCHEMA_DIR}/rule-review-workflow.md" "docs/programs/canvas-llm/handoff-regression-rule.md" "review workflow references handoff regression rule"

check_contains "${SCHEMA_DIR}/rule-source-linking-schema.md" "supports" "source linking includes supports"
check_contains "${SCHEMA_DIR}/rule-source-linking-schema.md" "conflicts_with" "source linking includes conflicts_with"
check_contains "${SCHEMA_DIR}/rule-source-linking-schema.md" "They do not authorize Canvas writes" "source links do not authorize writes"

check_contains "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "NOT_READY" "diagnostic readiness includes NOT_READY"
check_contains "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "PREVIEW_READY" "diagnostic readiness includes PREVIEW_READY"
check_contains "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "DIAGNOSTIC_READY" "diagnostic readiness includes DIAGNOSTIC_READY"
check_contains "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "WRITE_GATE_CANDIDATE" "diagnostic readiness includes WRITE_GATE_CANDIDATE"
check_contains "${SCHEMA_DIR}/diagnostic-readiness-schema.md" "No Phase 19C output is \`WRITE_GATE_CANDIDATE\`" "Phase 19C has no write-gate candidate"

check_contains "${SCHEMA_DIR}/preview-only-boundary.md" "Phase 19C is documentation/schema/status only" "preview boundary states docs/schema/status only"
check_contains "${SCHEMA_DIR}/preview-only-boundary.md" "Canvas API calls" "preview boundary blocks Canvas API calls"
check_contains "${SCHEMA_DIR}/preview-only-boundary.md" "Canvas writes" "preview boundary blocks Canvas writes"
check_contains "${SCHEMA_DIR}/preview-only-boundary.md" "student data access" "preview boundary blocks student data"

check_contains "${SCHEMA_DIR}/phase-19c-next-step-recommendation.md" "Phase 19D — Machine-Readable Seed Rule Catalog Preview" "next step recommends Phase 19D seed catalog preview"
check_contains "${SCHEMA_DIR}/phase-19c-next-step-recommendation.md" "Medical Center Diagnostic Spec Expansion" "next step includes Medical Center alternative"

check_contains "${HANDOFF}" "Phase 19C — Evidence Vault + Rule Catalog Schema" "handoff records Phase 19C"
check_contains "${HANDOFF}" "PR #300" "handoff preserves PR #300 breadcrumb"
check_contains "${HANDOFF}" "PR #301" "handoff preserves PR #301 breadcrumb"
check_contains "${HANDOFF}" "PR #302" "handoff preserves PR #302 breadcrumb"
check_contains "${HANDOFF}" "phase-19b-canonical-rules" "handoff preserves Phase 19B rule directory breadcrumb"
check_contains "${HANDOFF}" "phase-19c-evidence-vault-rule-catalog" "handoff records Phase 19C schema directory"

check_contains "${MEMORY}" "Phase 19C Evidence Vault + Rule Catalog Schema Update" "memory records Phase 19C update"
check_contains "${MEMORY}" "phase-19c-evidence-vault-rule-catalog" "memory records Phase 19C schema directory"

check_contains "${HANDOFF_RULE}" "Preserve historical handoff breadcrumbs" "handoff regression rule remains present"

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check is documentation/schema/status only"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not access student data"
emit PASS "status check does not read raw .local metadata"
emit PASS "status check does not implement app behavior"
emit PASS "status check does not create database migrations"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
