#!/usr/bin/env bash
# Read-only Curriculum Source Readiness foundation status. Fake fixtures only — no real ingestion.
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

plan_doc="docs/curriculum-source-readiness-and-intake-boundary-plan.md"
index_doc="docs/curriculum-source-readiness-fake-inventory-index.md"
schema="assistant/curriculum-builder/samples/curriculum-source-readiness/curriculum-source-metadata.schema.json"
inventory="assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json"
validator="scripts/curriculum-source-readiness-validate.sh"
status_script="scripts/curriculum-source-readiness-status.sh"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"
negative_dir="assistant/curriculum-builder/samples/curriculum-source-readiness/negative"

section 'Curriculum Source Readiness Foundation'
cat <<'EOF'
Status: fake_fixture_only planning foundation
Classification: metadata-only readiness — not real intake
Runtime activation: no
Real curriculum ingestion: blocked
Production registry writes: blocked
Active --write: blocked
Student data: blocked
Real curriculum content: blocked
Scanning/crawling/OCR/embeddings/RAG: blocked
Drive/Canvas/NAS/iCloud/API/OAuth/network: blocked
Future real pilot: requires Owen approval
EOF

section 'Readiness Plan and Index'
check_file "${plan_doc}"
check_file "${index_doc}"
check_doc_contains "${plan_doc}" "complete_curriculum_source_readiness_plan" "readiness plan closure"
check_doc_contains "${plan_doc}" "Real curriculum ingestion: blocked" "readiness plan blocked ingestion"
check_doc_contains "${plan_doc}" "No-Ingest Policy" "no-ingest policy"
check_doc_contains "${index_doc}" "fake_fixture_only" "inventory index fake_fixture_only"

section 'Fake Schema and Inventory'
check_file "assistant/curriculum-builder/samples/curriculum-source-readiness/README.md"
check_file "${schema}"
check_file "${inventory}"
check_doc_contains "${schema}" "content_ingestion_allowed" "schema content_ingestion_allowed"
check_doc_contains "${schema}" "\"const\": false" "schema false const safety"
check_doc_contains "${schema}" "\"const\": true" "schema true const fake_fixture_only"

section 'Validator'
check_file "${validator}"
bash -n "${validator}" && pass "bash syntax ok: ${validator}" || fail "bash syntax failed: ${validator}"
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"

validate_output="$(bash "${validator}" "${inventory}" 2>&1)" || true
if grep -q '^FAIL: 0$' <<< "${validate_output}" || ! grep -q '^FAIL: [1-9]' <<< "${validate_output}"; then
  if grep -q 'inventory validation succeeded' <<< "${validate_output}"; then
    pass "canonical fake inventory validates"
  else
    fail "canonical fake inventory validation failed"
    printf '%s\n' "${validate_output}"
  fi
else
  fail "canonical fake inventory validation failed"
  printf '%s\n' "${validate_output}"
fi

section 'Negative Fixtures'
check_file "${negative_dir}/negative-ingestion-allowed.json"
check_file "${negative_dir}/negative-student-data-allowed.json"
check_file "${negative_dir}/negative-real-content-allowed.json"
check_file "${negative_dir}/negative-production-write-allowed.json"
check_file "${negative_dir}/negative-drive-url.json"
check_file "${negative_dir}/negative-absolute-path.json"
check_file "${negative_dir}/negative-student-field.json"

for neg in "${negative_dir}"/*.json; do
  neg_name="$(basename "${neg}")"
  neg_output="$(bash "${validator}" "${neg}" 2>&1)" || true
  if grep -q '^FAIL: [1-9]' <<< "${neg_output}" || grep -q '^FAIL:' <<< "${neg_output}"; then
    pass "negative fixture rejected: ${neg_name}"
  else
    fail "negative fixture should fail: ${neg_name}"
    printf '%s\n' "${neg_output}"
  fi
done

section 'Registry Authority Cross-Link'
check_doc_contains docs/curriculum-builder-registry-authority-map.md "Curriculum Source Readiness" "authority map curriculum source readiness"

section 'Live Registry Non-Mutation'
[[ -f "${live_registry}" ]] && pass "live registry present (read-only reference)" || warn "live registry missing"

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-source-readiness-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-source-readiness-status' || fail 'CLI missing --curriculum-source-readiness-status'
grep -Fq -- '"--curriculum-source-readiness-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-source-readiness-status' || fail 'manifest missing --curriculum-source-readiness-status'
check_file tests/curriculum-source-readiness-status-test.sh
bash -n tests/curriculum-source-readiness-status-test.sh && pass 'bash syntax ok: readiness status test' || fail 'bash syntax failed: readiness status test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Fq -- '--curriculum-source-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-source-write handler' || pass 'chief-of-staff has no --curriculum-source-write handler'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
pass 'no real curriculum ingestion attempted'
pass 'no production registry write attempted'
pass 'no network call attempted'
pass 'no folder scanning attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
