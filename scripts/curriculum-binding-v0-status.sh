#!/usr/bin/env bash
# Read-only Registry–Contract Binding v0 foundation status only. No generation or network calls.
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

binding_doc="docs/curriculum-binding-v0.md"
binding_root="assistant/curriculum-builder/binding/v0"
binding_validator="scripts/curriculum-binding-v0-validator.sh"
binding_lookup="scripts/curriculum-binding-v0-lookup.sh"
registry_doc="docs/curriculum-registry-v0.md"
contract_doc="docs/curriculum-output-contract-v0.md"
chief_of_staff="bin/chief-of-staff"

section 'Curriculum Registry–Contract Binding v0 Foundation'
cat <<'EOF'
Status: read-only binding lookup and validation active
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
Drive/NAS/iCloud resolution: no
Student data: no
Registry writes: no
Contract writes: no
EOF

check_file "${binding_doc}"
check_file "${binding_root}/README.md"
check_file "${binding_root}/binding-manifest.json"
check_file "${binding_validator}"
check_file "${binding_lookup}"
check_bash_syntax "${binding_validator}"
check_bash_syntax "${binding_lookup}"
check_bash_syntax "${BASH_SOURCE[0]}"

section 'Documentation Boundaries'
check_doc_contains "${binding_doc}" "read-only"
check_doc_contains "${binding_doc}" "registry_id"
check_doc_contains "${binding_doc}" "no lesson generation"
check_doc_contains "${binding_doc}" "no renderers"
check_doc_contains "${binding_doc}" "no network calls"
check_doc_contains "${binding_doc}" "no student data"
check_doc_contains "${binding_doc}" "Registry v0"
check_doc_contains "${binding_doc}" "Output Contract v0"
check_doc_contains "${registry_doc}" "output contract"
check_doc_contains "${contract_doc}" "registry_references"

section 'Chief of Staff Command Wiring'
if [[ -f "${chief_of_staff}" ]]; then
  if grep -Fq -- '--curriculum-binding-v0-status' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-binding-v0-status"
  else
    fail "chief-of-staff missing --curriculum-binding-v0-status"
  fi
  if grep -Fq -- '--curriculum-binding-v0-lookup' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-binding-v0-lookup"
  else
    fail "chief-of-staff missing --curriculum-binding-v0-lookup"
  fi
  if grep -Fq -- '--curriculum-binding-v0-validate' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --curriculum-binding-v0-validate"
  else
    fail "chief-of-staff missing --curriculum-binding-v0-validate"
  fi
else
  fail "chief-of-staff missing: ${chief_of_staff}"
fi

section 'Binding v0 Validator Dry Run'
if [[ -f "${binding_validator}" ]]; then
  validator_result=0
  validator_output="$(bash "${binding_validator}" 2>&1)" || validator_result=$?
  validator_summary_fail="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"

  if [[ "${validator_result}" != "0" ]]; then
    printf '%s\n' "${validator_output}"
    fail "binding v0 validator reported failures"
  elif [[ "${validator_summary_fail}" -gt 0 ]]; then
    printf '%s\n' "${validator_output}"
    fail "binding v0 validator reported failures"
  else
    pass "binding v0 validator completed without failures"
    validator_pass="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^PASS:/{v=$2} END{print v+0}')"
    pass "binding v0 validator PASS count: ${validator_pass}"
    validator_warn="$(printf '%s\n' "${validator_output}" | awk '/^Summary$/{p=1; next} p && /^WARN:/{v=$2} END{print v+0}')"
    if [[ "${validator_warn}" -gt 0 ]]; then
      warn "binding v0 validator WARN count: ${validator_warn}"
    fi
  fi
else
  fail "binding validator missing: ${binding_validator}"
fi

section 'Binding v0 Lookup Dry Run'
if [[ -f "${binding_lookup}" ]]; then
  lookup_result=0
  lookup_output="$(bash "${binding_lookup}" sample-sm5-textbook-001 2>&1)" || lookup_result=$?
  lookup_summary_fail="$(printf '%s\n' "${lookup_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"

  if [[ "${lookup_result}" != "0" ]]; then
    printf '%s\n' "${lookup_output}"
    fail "binding v0 lookup reported failures"
  elif [[ "${lookup_summary_fail}" -gt 0 ]]; then
    printf '%s\n' "${lookup_output}"
    fail "binding v0 lookup reported failures"
  elif ! printf '%s\n' "${lookup_output}" | grep -Fq 'sample-contract-di-slide-deck-001'; then
    fail "binding v0 lookup missing expected DI slide deck contract reference"
  elif ! printf '%s\n' "${lookup_output}" | grep -Fq 'sample-contract-teacher-script-001'; then
    fail "binding v0 lookup missing expected teacher script contract reference"
  else
    pass "binding v0 lookup sample-sm5-textbook-001 succeeded"
  fi
else
  fail "binding lookup missing: ${binding_lookup}"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
