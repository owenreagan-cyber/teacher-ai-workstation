#!/usr/bin/env bash
# Read-only Curriculum Output Contract v0 foundation status only. No generation or network calls.
set -euo pipefail

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

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "cannot syntax check missing file: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_doc_contains() {
  local path="$1"
  local needle="$2"
  if [[ ! -f "${path}" ]]; then
    fail "cannot search missing doc: ${path}"
    return
  fi
  if grep -Fq "${needle}" "${path}"; then
    pass "doc contains: ${needle}"
  else
    fail "doc missing required text: ${needle}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

contract_doc="docs/curriculum-output-contract-v0.md"
teacher_script_doc="docs/curriculum-teacher-script-contract-v0.md"
worksheet_doc="docs/curriculum-worksheet-contract-v0.md"
contract_root="assistant/curriculum-builder/output-contract/v0"
contract_validator="scripts/curriculum-output-contract-v0-validator.sh"
planning_foundation_doc="docs/curriculum-builder-output-contract-foundation.md"
registry_doc="docs/curriculum-registry-v0.md"
chief_of_staff="bin/chief-of-staff"

section 'Curriculum Output Contract v0 Bounded Validator Foundation'
cat <<'EOF'
Status: read-only contract validation foundation active
Lesson generation: no
Renderers: no
HTML/PDF generation: no
Canvas package building: no
Ingestion: no
Scanning: no
OCR: no
Embeddings: no
RAG: no
Vector database: no
APIs: no
OAuth: no
Network calls: no
Student data: no
Contract writes: no
EOF

check_file "${contract_doc}"
check_file "${contract_root}/README.md"
check_file "${contract_root}/contract-envelope-schema.json"
check_file "${contract_root}/direct-instruction-slide-deck-schema.json"
check_file "${contract_root}/teacher-script-contract-schema.json"
check_file "${contract_root}/worksheet-contract-schema.json"
check_file "${contract_root}/contracts/sample-di-slide-deck-001.json"
check_file "${contract_root}/contracts/sample-teacher-script-001.json"
check_file "${contract_root}/contracts/sample-worksheet-001.json"
check_file "${contract_root}/placeholder-manifest.json"
check_file "${contract_root}/placeholders/review-game-contract-placeholder.json"
check_file "${contract_root}/placeholders/canvas-export-package-contract-placeholder.json"
check_file "${contract_validator}"
check_bash_syntax "${contract_validator}"
check_bash_syntax "${BASH_SOURCE[0]}"

section 'Documentation Boundaries'
check_doc_contains "${contract_doc}" "metadata only"
check_doc_contains "${contract_doc}" "read-only"
check_doc_contains "${contract_doc}" "direct_instruction_slide_deck_contract"
check_doc_contains "${contract_doc}" "no lesson generation"
check_doc_contains "${contract_doc}" "no renderers"
check_doc_contains "${contract_doc}" "registry_references"
check_doc_contains "${contract_doc}" "no student data"
check_doc_contains "${planning_foundation_doc}" "direct_instruction_slide_deck_contract"
check_doc_contains "${planning_foundation_doc}" "Output Contract Schema v0 Implementation Activation"
check_doc_contains "${contract_doc}" "teacher_script_contract"
check_doc_contains "${teacher_script_doc}" "teacher_script_contract"
check_doc_contains "${teacher_script_doc}" "no lesson generation"
check_doc_contains "${contract_doc}" "worksheet_contract"
check_doc_contains "${worksheet_doc}" "worksheet_contract"
check_doc_contains "${worksheet_doc}" "no lesson generation"
check_doc_contains "${registry_doc}" "output contract"

section 'Chief of Staff Command Wiring'
if [[ -f "${chief_of_staff}" ]]; then
  if grep -Fq -- '--curriculum-output-contract-v0-status' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-output-contract-v0-status"
  else
    fail "chief-of-staff missing --curriculum-output-contract-v0-status"
  fi
  if grep -Fq -- '--curriculum-output-contract-v0-validate' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-output-contract-v0-validate"
  else
    fail "chief-of-staff missing --curriculum-output-contract-v0-validate"
  fi
else
  fail "chief-of-staff missing: ${chief_of_staff}"
fi

section 'Output Contract v0 Validator Dry Run'
if [[ -f "${contract_validator}" ]]; then
  validator_result=0
  validator_output="$(bash "${contract_validator}" 2>&1)" || validator_result=$?
  validator_summary_fail="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"

  if [[ "${validator_result}" != "0" ]]; then
    printf '%s\n' "${validator_output}"
    fail "output contract v0 validator reported failures"
  elif [[ "${validator_summary_fail}" -gt 0 ]]; then
    printf '%s\n' "${validator_output}"
    fail "output contract v0 validator reported failures"
  else
    pass "output contract v0 validator completed without failures"
    validator_pass="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^PASS:/{v=$2} END{print v+0}')"
    pass "output contract v0 validator PASS count: ${validator_pass}"
    validator_warn="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^WARN:/{v=$2} END{print v+0}')"
    if [[ "${validator_warn}" -gt 0 ]]; then
      warn "output contract v0 validator WARN count: ${validator_warn}"
    fi
  fi
else
  fail "contract validator missing: ${contract_validator}"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
