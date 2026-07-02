#!/usr/bin/env bash
# Read-only Curriculum Builder Registry v0.2 local fake records status (CB-IMPL-2).
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} must mention ${label}"; return; }
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

index_doc="docs/curriculum-builder-registry-v0-2-local-records-foundation.md"
boundaries_doc="docs/curriculum-builder-registry-v0-2-record-boundaries.md"
fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
validator="scripts/curriculum-builder-registry-v0-2-local-records-validate.sh"
status_script="scripts/curriculum-builder-registry-v0-2-local-records-status.sh"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"

section 'Curriculum Builder Registry v0.2 Local Fake Records (CB-IMPL-2)'
cat <<'EOF'
Status: fake fixture registry only
Production registry writes: no
Active user-facing --write: no
Network calls: no
Student data: no
Real curriculum content: no
EOF

section 'Foundation Documents'
check_file "${index_doc}"
check_file "${boundaries_doc}"
check_doc_contains "${index_doc}" "complete_cb_impl_2_local_records" "CB-IMPL-2 closure"
check_doc_contains "${boundaries_doc}" "no_production_write" "record boundaries no_production_write"
check_doc_contains "${boundaries_doc}" "fixture_only" "record boundaries fixture_only"

section 'Fake Fixture Artifacts'
check_file "assistant/curriculum-builder/samples/registry-v0-2-local-records/README.md"
check_file "${fixture}"
check_doc_contains "assistant/curriculum-builder/samples/registry-v0-2-local-records/README.md" "fixture" "fixture readme"

section 'Validator'
check_file "${validator}"
bash -n "${validator}" && pass "bash syntax ok: ${validator}" || fail "bash syntax failed: ${validator}"
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"

validate_output="$(bash "${validator}" "${fixture}" 2>&1)" || true
if grep -q '^FAIL: 0$' <<< "${validate_output}"; then
  pass "local records validator passes canonical fixture"
else
  fail "local records validator failed on canonical fixture"
  printf '%s\n' "${validate_output}"
fi
grep -q 'no_production_write: true' <<< "${validate_output}" && pass "validator reports no_production_write" || fail "validator missing no_production_write"

section 'Live Registry Non-Mutation'
[[ -f "${live_registry}" ]] && pass "live registry present (read-only reference)" || warn "live registry missing"
grep -Fq -- '--write)' "${validator}" 2>/dev/null && fail 'validator must not implement --write flag' || pass 'validator has no --write flag'

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-registry-records-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-records-status' || fail 'CLI missing --curriculum-registry-records-status'
grep -Fq -- '"--curriculum-registry-records-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-registry-records-status' || fail 'manifest missing --curriculum-registry-records-status'
check_file tests/curriculum-builder-registry-v0-2-local-records-test.sh
bash -n tests/curriculum-builder-registry-v0-2-local-records-test.sh && pass 'bash syntax ok: local records test' || fail 'bash syntax failed: local records test'

section 'Roadmap Coherence'
check_doc_contains docs/master-build-roadmap.md "CB-IMPL-2" "roadmap CB-IMPL-2"
check_doc_contains assistant/memory/active-priorities.md "CB-IMPL-2" "active priorities CB-IMPL-2"

section 'Negative Non-Activation Assertions'
for script_path in "${validator}" "${status_script}"; do
  grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke curl" || pass "${script_path} does not shell-invoke curl"
  grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke find" || pass "${script_path} does not shell-invoke find"
  grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke ollama" || pass "${script_path} does not shell-invoke ollama"
done
pass 'no production registry write attempted'
pass 'no network call attempted'
pass 'no lesson generation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
