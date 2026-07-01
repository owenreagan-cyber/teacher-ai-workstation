#!/usr/bin/env bash
# Read-only Curriculum Registry v0 foundation status only. No network calls, writes, or ingestion.
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

registry_doc="docs/curriculum-registry-v0.md"
registry_schema="assistant/curriculum-builder/registry/v0/registry-schema.json"
registry_data="assistant/curriculum-builder/registry/v0/registry.json"
registry_readme="assistant/curriculum-builder/registry/v0/README.md"
registry_validator="scripts/curriculum-registry-v0-validator.sh"
manual_schema_plan="docs/curriculum-builder-manual-registry-schema-plan.md"
sample_proof="docs/curriculum-builder-manual-registry-sample-proof.md"
chief_of_staff="bin/chief-of-staff"

section 'Curriculum Registry v0 Manual Metadata Foundation'
cat <<'EOF'
Status: read-only registry v0 foundation active
Network calls: no
Drive scanning: no
NAS scanning: no
Folder crawling: no
OCR: no
Embeddings: no
Vector database: no
RAG: no
Lesson generation: no
Canvas API: no
Google Drive API: no
OAuth: no
Student data: no
Registry writes: no
EOF

check_file "${registry_doc}"
check_file "${registry_schema}"
check_file "${registry_data}"
check_file "${registry_readme}"
check_file "${registry_validator}"
check_bash_syntax "${registry_validator}"
check_bash_syntax "${BASH_SOURCE[0]}"

section 'Documentation Boundaries'
check_doc_contains "${registry_doc}" "metadata only"
check_doc_contains "${registry_doc}" "read-only operation"
check_doc_contains "${registry_doc}" "manual metadata entries"
check_doc_contains "${registry_doc}" "registry_version"
check_doc_contains "${registry_doc}" "no scanning"
check_doc_contains "${registry_doc}" "no student data"
check_doc_contains "${manual_schema_plan}" "source_reference"
check_doc_contains "${sample_proof}" "sample-sm5-textbook-001"

section 'Chief of Staff Command Wiring'
if [[ -f "${chief_of_staff}" ]]; then
  if grep -Fq -- '--curriculum-registry-v0-status' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-registry-v0-status"
  else
    fail "chief-of-staff missing --curriculum-registry-v0-status"
  fi
  if grep -Fq -- '--curriculum-registry-v0-validate' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-registry-v0-validate"
  else
    fail "chief-of-staff missing --curriculum-registry-v0-validate"
  fi
else
  fail "chief-of-staff missing: ${chief_of_staff}"
fi

section 'Registry v0 Validator Dry Run'
if [[ -x "${registry_validator}" || -f "${registry_validator}" ]]; then
  validator_result=0
  validator_output="$(bash "${registry_validator}" 2>&1)" || validator_result=$?
  validator_summary_fail="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"

  if [[ "${validator_result}" != "0" ]]; then
    printf '%s\n' "${validator_output}"
    fail "registry v0 validator reported failures"
  elif [[ "${validator_summary_fail}" -gt 0 ]]; then
    printf '%s\n' "${validator_output}"
    fail "registry v0 validator reported failures"
  else
    pass "registry v0 validator completed without failures"
    validator_pass="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^PASS:/{v=$2} END{print v+0}')"
    pass "registry v0 validator PASS count: ${validator_pass}"
    validator_warn="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^WARN:/{v=$2} END{print v+0}')"
    if [[ "${validator_warn}" -gt 0 ]]; then
      warn "registry v0 validator WARN count: ${validator_warn}"
    fi
  fi
else
  fail "registry validator missing: ${registry_validator}"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
