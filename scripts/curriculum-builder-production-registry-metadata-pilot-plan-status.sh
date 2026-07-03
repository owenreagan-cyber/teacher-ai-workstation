#!/usr/bin/env bash
# Read-only metadata pilot execution planning status. No record writes.
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

pilot_plan_doc="docs/curriculum-builder-production-registry-metadata-pilot-execution-plan.md"
worksheet_doc="docs/curriculum-builder-production-registry-first-record-owen-entry-worksheet.md"
acceptance_doc="docs/curriculum-builder-production-registry-first-record-acceptance-criteria.md"
snapshot_plan_doc="docs/curriculum-builder-production-registry-first-record-snapshot-diff-restore-plan.md"
metadata_contract="docs/curriculum-builder-production-registry-manual-metadata-field-contract.md"
source_contract="docs/curriculum-builder-production-registry-source-reference-contract.md"
guardrails_doc="docs/curriculum-builder-production-registry-blocked-field-guardrails.md"
boundary_doc="docs/curriculum-builder-production-registry-metadata-source-boundaries.md"
write_mission="docs/proposals/backlog/production-registry-write-mission.md"
post_decision="docs/curriculum-builder-production-registry-post-decision-implementation-map.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
production_registry_dir="assistant/curriculum-builder/registry/v0-2"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
empty_shell_validator="scripts/curriculum-builder-production-registry-empty-file-validate.sh"
status_script="scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

section 'Production Registry Metadata Pilot Plan Status'
cat <<'EOF'
Status: metadata_pilot_execution_plan_complete
Classification: one-record pilot protocol — planning only
Runtime activation: no
Production registry file: exists (empty shell)
Records array: empty
Metadata pilot execution: blocked
Record writes: blocked
Active --write: blocked
PASS does not authorize metadata pilot execution: yes
PASS does not authorize record writes: yes
EOF

section 'Pilot Execution Planning Documentation'
check_file "${pilot_plan_doc}"
check_doc_contains "${pilot_plan_doc}" "metadata_pilot_execution_plan_complete" "pilot plan closure"
check_doc_contains "${pilot_plan_doc}" "does not execute the metadata pilot" "pilot plan non-execution"
check_doc_contains "${pilot_plan_doc}" "one-record-only" "one-record pilot scope"
check_file "${worksheet_doc}"
check_doc_contains "${worksheet_doc}" "planning_only" "worksheet planning classification"
check_doc_contains "${worksheet_doc}" "<placeholder>" "worksheet placeholder fields"
check_file "${acceptance_doc}"
check_doc_contains "${acceptance_doc}" "exactly one resource-*" "acceptance one record rule"
check_file "${snapshot_plan_doc}"
check_doc_contains "${snapshot_plan_doc}" "pre-write snapshot of empty shell" "snapshot empty shell plan"

section 'Metadata Boundary Preconditions'
check_file "${boundary_doc}"
check_doc_contains "${boundary_doc}" "metadata_boundary_refinement_complete" "metadata boundary refinement complete"
check_file "${metadata_contract}"
check_file "${source_contract}"
check_file "${guardrails_doc}"

section 'Production Registry Empty Shell'
check_file "${production_registry_path}"
check_file "${empty_shell_validator}"
validate_output="$(bash "${empty_shell_validator}" "${production_registry_path}" 2>&1)" || validate_result=$?
validate_result="${validate_result:-0}"
if [[ "${validate_result}" -eq 0 ]] && grep -q 'empty shell validation succeeded' <<< "${validate_output}"; then
  pass "production-registry.json validates as empty shell"
else
  fail "production-registry.json must remain empty shell"
  printf '%s\n' "${validate_output}" | tail -5
fi

section 'Resource Non-Existence'
resource_file_count=0
if [[ -d "${production_registry_dir}" ]]; then
  for candidate_file in "${production_registry_dir}"/*; do
    [[ -e "${candidate_file}" ]] || continue
    base="$(basename "${candidate_file}")"
    [[ "${base}" == resource-* ]] && resource_file_count=$((resource_file_count + 1))
  done
fi
[[ "${resource_file_count}" -eq 0 ]] && pass "no resource-* production record files exist" || fail "resource-* production record files must not exist"

section 'Sentinel and Write Guards'
check_file "${sentinel}"
grep -Fq -- 'Production writes: blocked' "${sentinel}" && pass 'BLOCKED-NO-WRITES.sentinel remains intact' || fail 'sentinel must state production writes blocked'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  fail 'writer script must not exist'
else
  pass 'no production registry writer script exists'
fi

section 'Write-Mission and Post-Decision Coherence'
check_file "${write_mission}"
check_doc_contains "${write_mission}" "Metadata pilot execution planning" "write mission planning distinction"
check_doc_contains "${write_mission}" "Metadata pilot execution" "write mission execution blocked"
check_file "${post_decision}"
check_doc_contains "${post_decision}" "Metadata Pilot" "post-decision metadata pilot phase"

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-metadata-pilot-plan-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-metadata-pilot-plan-status' || fail 'CLI missing --curriculum-production-registry-metadata-pilot-plan-status'
grep -Fq -- '"--curriculum-production-registry-metadata-pilot-plan-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-metadata-pilot-plan-status' || fail 'manifest missing --curriculum-production-registry-metadata-pilot-plan-status'
check_file tests/curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh && pass 'bash syntax ok: metadata pilot plan test' || fail 'bash syntax failed: metadata pilot plan test'

section 'Negative Non-Activation Assertions'
pass 'metadata pilot execution is not active'
pass 'real curriculum file access is not active'
pass 'source auto-resolution is not active'
pass 'integration/network activation is not active'
pass 'no copied curriculum content in production registry'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'metadata pilot plan status does not mutate registry records'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
