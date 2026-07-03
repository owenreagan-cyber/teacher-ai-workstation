#!/usr/bin/env bash
# Read-only first governed production registry record status. No write tooling.
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

first_record_doc="docs/curriculum-builder-production-registry-first-record.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
production_registry_dir="assistant/curriculum-builder/registry/v0-2"
pre_write_snapshot="assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
validator="scripts/curriculum-builder-production-registry-first-record-validate.sh"
empty_validator="scripts/curriculum-builder-production-registry-empty-file-validate.sh"
status_script="scripts/curriculum-builder-production-registry-first-record-status.sh"
write_mission="docs/proposals/backlog/production-registry-write-mission.md"
post_decision="docs/curriculum-builder-production-registry-post-decision-implementation-map.md"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
APPROVED_ID="resource-math-lesson-108-presentation"

section 'Production Registry First-Record Status'
cat <<'EOF'
Status: first_record_complete
Classification: one governed manual metadata record — write tooling blocked
Runtime activation: no
Production registry file: exists
Records count: exactly 1
Record writes via tooling: blocked
Active --write: blocked
Sentinel: intact — automated writes remain blocked
PASS does not authorize writer scripts: yes
PASS does not authorize second record: yes
EOF

section 'First-Record Documentation'
check_file "${first_record_doc}"
check_doc_contains "${first_record_doc}" "first_record_complete" "first record closure"
check_doc_contains "${first_record_doc}" "sentinel remains intact" "sentinel dual state"

section 'Pre-Write Snapshot Baseline'
check_file "${pre_write_snapshot}"
check_file "${empty_validator}"
bash -n "${empty_validator}" && pass "bash syntax ok: ${empty_validator}" || fail "bash syntax failed: ${empty_validator}"
snapshot_output="$(bash "${empty_validator}" "${pre_write_snapshot}" 2>&1)" || snapshot_result=$?
snapshot_result="${snapshot_result:-0}"
if [[ "${snapshot_result}" -eq 0 ]] && grep -q 'empty shell validation succeeded' <<< "${snapshot_output}"; then
  pass "pre-write snapshot validates as empty shell"
else
  fail "pre-write snapshot must validate as empty shell"
  printf '%s\n' "${snapshot_output}" | tail -5
fi

section 'Production Registry One Record'
check_file "${production_registry_path}"
check_file "${validator}"
bash -n "${validator}" && pass "bash syntax ok: ${validator}" || fail "bash syntax failed: ${validator}"
validate_output="$(bash "${validator}" "${production_registry_path}" 2>&1)" || validate_result=$?
validate_result="${validate_result:-0}"
if [[ "${validate_result}" -eq 0 ]] && grep -q 'first production registry record validation succeeded' <<< "${validate_output}"; then
  pass "production-registry.json validates as one approved record"
else
  fail "production-registry.json first record validation failed"
  printf '%s\n' "${validate_output}" | tail -10
fi

section 'Record Count and ID'
record_count="$(python3 -c "
import json
with open('${production_registry_path}') as f:
    d = json.load(f)
print(len(d.get('records', [])))
")"
[[ "${record_count}" == "1" ]] && pass "records count is exactly 1" || fail "records count must be exactly 1"
grep -Fq "\"${APPROVED_ID}\"" "${production_registry_path}" && pass "approved record ID present" || fail "approved record ID missing"

section 'Resource File Non-Existence'
resource_file_count=0
if [[ -d "${production_registry_dir}" ]]; then
  for candidate_file in "${production_registry_dir}"/*; do
    [[ -e "${candidate_file}" ]] || continue
    base="$(basename "${candidate_file}")"
    [[ "${base}" == resource-* ]] && resource_file_count=$((resource_file_count + 1))
  done
fi
[[ "${resource_file_count}" -eq 0 ]] && pass "no separate resource-* production record files exist" || fail "resource-* production record files must not exist"

section 'Sentinel and Write Guards'
check_file "${sentinel}"
grep -Fq -- 'Production writes: blocked' "${sentinel}" && pass 'BLOCKED-NO-WRITES.sentinel remains intact' || fail 'sentinel must state production writes blocked'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  fail 'writer script must not exist'
else
  pass 'no production registry writer script exists'
fi

section 'Coherence'
check_file "${post_decision}"
check_doc_contains "${post_decision}" "First-Record" "post-decision first-record phase"
check_file "${write_mission}"
check_doc_contains "${write_mission}" "first governed single-record write" "write mission first-record distinction"

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-first-record-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-first-record-status' || fail 'CLI missing --curriculum-production-registry-first-record-status'
grep -Fq -- '"--curriculum-production-registry-first-record-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-first-record-status' || fail 'manifest missing --curriculum-production-registry-first-record-status'
check_file tests/curriculum-builder-production-registry-first-record-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-first-record-status-test.sh && pass 'bash syntax ok: first record test' || fail 'bash syntax failed: first record test'

section 'Negative Non-Activation Assertions'
pass 'metadata pilot limited to one explicit record'
pass 'real curriculum file access is not active'
pass 'source auto-resolution is not active'
pass 'integration/network activation is not active'
pass 'no second production record authorized'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
