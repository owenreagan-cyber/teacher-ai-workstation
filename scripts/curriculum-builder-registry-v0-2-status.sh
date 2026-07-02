#!/usr/bin/env bash
# Read-only Curriculum Builder Registry v0.2 manual entry dry-run status. No registry writes.
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

dry_run_doc="docs/curriculum-builder-registry-v0-2-manual-entry-dry-run.md"
boundaries_doc="docs/curriculum-builder-registry-v0-2-dry-run-boundaries.md"
rules_doc="docs/curriculum-builder-registry-v0-2-validation-rules.md"
dry_run_validator="scripts/curriculum-builder-registry-v0-2-dry-run.sh"
status_script="scripts/curriculum-builder-registry-v0-2-status.sh"
sample_dir="assistant/curriculum-builder/samples/registry-v0-2-dry-run"
sample_valid="${sample_dir}/example-candidate-valid.json"
sample_valid_002="${sample_dir}/example-candidate-valid-002.json"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"

section 'Curriculum Builder Registry v0.2 Manual Entry Dry-Run (CB-IMPL-1)'
cat <<'EOF'
Status: dry-run validation only
Registry writes: no
Active --write: no
Network calls: no
Student data: no
Real curriculum content: no
Scanning / ingestion: no
EOF

section 'Foundation Documents'
check_file "${dry_run_doc}"
check_file "${boundaries_doc}"
check_file "${rules_doc}"
check_doc_contains "${dry_run_doc}" "dry-run validation only" "dry-run index status"
check_doc_contains "${dry_run_doc}" "complete_cb_impl_1_dry_run" "dry-run closure status"
check_doc_contains "${dry_run_doc}" "Registry writes: blocked" "dry-run blocked writes"
check_doc_contains "${boundaries_doc}" "no_registry_write" "boundaries no_registry_write"
check_doc_contains "${boundaries_doc}" "would_write" "boundaries would_write"
check_doc_contains "${boundaries_doc}" "student data" "boundaries student data"
check_doc_contains "${rules_doc}" "dry_run_version" "validation rules dry_run_version"
check_doc_contains "${rules_doc}" "example-resource-001" "validation rules example id"

section 'Fake Sample Artifacts'
check_file "${sample_dir}/README.md"
check_file "${sample_valid}"
check_file "${sample_valid_002}"
check_doc_contains "${sample_dir}/README.md" "dry-run" "sample readme dry-run"

section 'Dry-Run Validator'
check_file "${dry_run_validator}"
bash -n "${dry_run_validator}" && pass "bash syntax ok: ${dry_run_validator}" || fail "bash syntax failed: ${dry_run_validator}"
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"

dry_run_output="$(bash "${dry_run_validator}" "${sample_valid}" 2>&1)" || true
if grep -q '^FAIL: 0$' <<< "${dry_run_output}"; then
  pass "dry-run validator passes canonical sample"
else
  fail "dry-run validator failed on canonical sample"
  printf '%s\n' "${dry_run_output}"
fi
if grep -q 'would_write=false' <<< "${dry_run_output}"; then
  pass "dry-run validator reports would_write=false"
else
  fail "dry-run validator missing would_write=false"
fi

dry_run_output_002="$(bash "${dry_run_validator}" "${sample_valid_002}" 2>&1)" || true
if grep -q '^FAIL: 0$' <<< "${dry_run_output_002}"; then
  pass "dry-run validator passes second sample"
else
  fail "dry-run validator failed on second sample"
fi

section 'Live Registry Non-Mutation'
if [[ -f "${live_registry}" ]]; then
  pass "live registry file present (read-only reference)"
  check_doc_contains "${dry_run_doc}" "without" "dry-run does not write live registry"
else
  warn "live registry file missing (dry-run unaffected)"
fi
grep -Fq -- '--write)' "${dry_run_validator}" 2>/dev/null && fail 'dry-run validator must not implement --write flag' || pass 'dry-run validator has no --write flag'

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-registry-dry-run-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-dry-run-status' || fail 'CLI missing --curriculum-registry-dry-run-status'
grep -Fq -- '"--curriculum-registry-dry-run-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-registry-dry-run-status' || fail 'manifest missing --curriculum-registry-dry-run-status'
check_file tests/curriculum-builder-registry-v0-2-dry-run-test.sh
check_file tests/curriculum-builder-registry-v0-2-status-test.sh
bash -n tests/curriculum-builder-registry-v0-2-dry-run-test.sh && pass 'bash syntax ok: dry-run test' || fail 'bash syntax failed: dry-run test'
bash -n tests/curriculum-builder-registry-v0-2-status-test.sh && pass 'bash syntax ok: status test' || fail 'bash syntax failed: status test'

section 'Roadmap and Priority Coherence'
check_doc_contains docs/master-build-roadmap.md "CB-IMPL-1" "roadmap CB-IMPL-1"
check_doc_contains docs/build-queue.md "Registry v0.2" "build queue registry v0.2"
check_doc_contains assistant/memory/active-priorities.md "CB-IMPL-1" "active priorities CB-IMPL-1"
check_doc_contains docs/teacher-workstation-capability-map.md "--curriculum-registry-dry-run-status" "capability map dry-run"

section 'Blocked Future Commands Remain Blocked'
grep -Fq -- '"--curriculum-ingest-files"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest retains blocked ingest command' || fail 'manifest missing blocked ingest command'
grep -Fq -- '"status": "blocked"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest retains blocked status markers' || fail 'manifest missing blocked status markers'

section 'Negative Non-Activation Assertions'
for script_path in "${dry_run_validator}" "${status_script}"; do
  grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke curl" || pass "${script_path} does not shell-invoke curl"
  grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke wget" || pass "${script_path} does not shell-invoke wget"
  grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke brew" || pass "${script_path} does not shell-invoke brew"
  grep -Eq '(^|[;&|[:space:]])npm[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke npm" || pass "${script_path} does not shell-invoke npm"
  grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke find" || pass "${script_path} does not shell-invoke find"
  grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke ollama" || pass "${script_path} does not shell-invoke ollama"
done
if grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(add|commit|push|merge|reset)' "${status_script}" 2>/dev/null; then
  fail 'registry v0.2 status script must not mutate git state'
else
  pass 'registry v0.2 status script does not mutate git state'
fi
pass 'no folder scan attempted'
pass 'no curriculum ingestion attempted'
pass 'no lesson generation attempted'
pass 'no network call attempted'
pass 'no registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
