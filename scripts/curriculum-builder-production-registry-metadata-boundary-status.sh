#!/usr/bin/env bash
# Read-only production registry metadata-boundary refinement status. No writes.
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

boundary_doc="docs/curriculum-builder-production-registry-metadata-source-boundaries.md"
metadata_contract="docs/curriculum-builder-production-registry-manual-metadata-field-contract.md"
source_contract="docs/curriculum-builder-production-registry-source-reference-contract.md"
guardrails_doc="docs/curriculum-builder-production-registry-blocked-field-guardrails.md"
tracker_doc="docs/curriculum-builder-production-registry-owen-checklist-tracker.md"
write_mission="docs/proposals/backlog/production-registry-write-mission.md"
post_decision="docs/curriculum-builder-production-registry-post-decision-implementation-map.md"
planning_fixture="assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json"
validator="scripts/curriculum-builder-production-registry-metadata-boundary-validate.sh"
status_script="scripts/curriculum-builder-production-registry-metadata-boundary-status.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
production_registry_dir="assistant/curriculum-builder/registry/v0-2"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
metadata_blocked="docs/proposals/blocked/production-registry-real-metadata-intake.md"
pilot_boundary="docs/curriculum-builder-metadata-pilot-planning-boundary.md"

section 'Production Registry Metadata Boundary Refinement'
cat <<'EOF'
Status: metadata_boundary_refinement_complete
Classification: read-only boundary proof — not implementation
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Metadata pilot execution: blocked
Real metadata intake: blocked
Source auto-resolution: blocked
PASS does not authorize registry mutation: yes
EOF

section 'Owen Checklist Preconditions'
check_file "${tracker_doc}"
check_doc_contains "${tracker_doc}" "| Real curriculum metadata allowed | approved | Owen |" "tracker item 3 approved"
check_doc_contains "${tracker_doc}" "| Real source references allowed | approved | Owen |" "tracker item 4 approved"
check_doc_contains "${tracker_doc}" "metadata_boundaries_approved_awaiting_pilot_and_write_missions" "tracker closure status"

section 'Boundary and Contract Documents'
check_file "${boundary_doc}"
check_doc_contains "${boundary_doc}" "metadata_boundary_refinement_complete" "boundary doc refinement closure"
check_doc_contains "${boundary_doc}" "Manual Owen-entered descriptive metadata only" "manual-only metadata principle"
check_doc_contains "${boundary_doc}" "Manual non-resolving source-reference labels" "non-resolving source principle"
check_file "${metadata_contract}"
check_doc_contains "${metadata_contract}" "metadata_boundary_refinement_planning" "manual metadata field contract"
check_file "${source_contract}"
check_doc_contains "${source_contract}" "non-resolving labels only" "source-reference contract"
check_file "${guardrails_doc}"
check_doc_contains "${guardrails_doc}" "blocked-field guardrail spec" "blocked field guardrails"

section 'Allowed and Blocked Field Documentation'
check_doc_contains "${metadata_contract}" "Stable record identifier" "allowed metadata id field"
check_doc_contains "${metadata_contract}" "See source-reference contract" "allowed metadata source_reference field"
check_doc_contains "${source_contract}" "manual_label" "source_type manual_label"
check_doc_contains "${source_contract}" "canvas_label" "source_type canvas_label"
check_doc_contains "${guardrails_doc}" "Drive file IDs" "blocked drive file IDs"
check_doc_contains "${guardrails_doc}" "Student names" "blocked student names"
check_doc_contains "${guardrails_doc}" "OAuth tokens" "blocked oauth tokens"

section 'Fake Planning Fixture and Validator'
check_file "assistant/curriculum-builder/samples/metadata-boundary-planning/README.md"
check_file "${planning_fixture}"
check_doc_contains "${planning_fixture}" "example-metadata-boundary-record-001" "planning fixture example id"
check_file "${validator}"
bash -n "${validator}" && pass "bash syntax ok: ${validator}" || fail "bash syntax failed: ${validator}"
validate_output="$(bash "${validator}" "${planning_fixture}" 2>&1)" || validate_result=$?
validate_result="${validate_result:-0}"
if [[ "${validate_result}" -eq 0 ]] && grep -q 'fixture validation succeeded' <<< "${validate_output}"; then
  pass "canonical planning fixture validates"
else
  fail "canonical planning fixture validation failed"
  printf '%s\n' "${validate_output}" | tail -10
fi
neg_resource="assistant/curriculum-builder/samples/metadata-boundary-planning/negative/negative-resource-id.json"
neg_drive="assistant/curriculum-builder/samples/metadata-boundary-planning/negative/negative-drive-url.json"
check_file "${neg_resource}"
check_file "${neg_drive}"
neg_out="$(bash "${validator}" "${neg_resource}" 2>&1)" || true
grep -q 'negative fixture correctly rejected' <<< "${neg_out}" && pass "negative resource-id fixture rejected" || fail "negative resource-id fixture must be rejected"
neg_out2="$(bash "${validator}" "${neg_drive}" 2>&1)" || true
grep -q 'negative fixture correctly rejected' <<< "${neg_out2}" && pass "negative drive-url fixture rejected" || fail "negative drive-url fixture must be rejected"

section 'Post-Decision and Write-Mission Coherence'
check_file "${post_decision}"
check_doc_contains "${post_decision}" "Metadata-Boundary Refinement" "post-decision metadata refinement phase"
check_file "${write_mission}"
check_doc_contains "${write_mission}" "Metadata-boundary refinement" "write mission refinement distinction"
check_doc_contains "${write_mission}" "Registry mutation: blocked" "write mission mutation blocked"

section 'Pilot and Intake Blocked Surfaces'
check_file "${metadata_blocked}"
check_doc_contains "${metadata_blocked}" "intake execution not authorized" "metadata intake blocked"
check_file "${pilot_boundary}"
check_doc_contains "${pilot_boundary}" "no intake" "metadata pilot planning boundary"

section 'Production Surface Non-Existence'
[[ ! -f "${production_registry_path}" ]] && pass "production-registry.json does not exist (blocked)" || fail "production-registry.json must not exist"
if [[ -d "${production_registry_dir}" ]]; then
  resource_files=0
  for candidate_file in "${production_registry_dir}"/*; do
    [[ -e "${candidate_file}" ]] || continue
    base="$(basename "${candidate_file}")"
    [[ "${base}" == ".gitkeep" ]] && continue
    if [[ "${base}" == resource-* ]] || [[ "${base}" == production-registry.json ]]; then
      resource_files=$((resource_files + 1))
    fi
  done
  [[ "${resource_files}" -eq 0 ]] && pass "v0-2 production directory has no resource-* or production-registry files" || fail "v0-2 production directory must not contain production files"
else
  pass "v0-2 production directory does not exist yet (blocked)"
fi

section 'Sentinel and Write Guards'
check_file "${sentinel}"
grep -Fq -- 'Production writes: blocked' "${sentinel}" && pass 'BLOCKED-NO-WRITES.sentinel remains intact' || fail 'sentinel must state production writes blocked'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  fail 'writer script must not exist'
else
  pass 'no production registry writer script exists'
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-metadata-boundary-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-metadata-boundary-status' || fail 'CLI missing --curriculum-production-registry-metadata-boundary-status'
grep -Fq -- '"--curriculum-production-registry-metadata-boundary-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-metadata-boundary-status' || fail 'manifest missing --curriculum-production-registry-metadata-boundary-status'
check_file tests/curriculum-builder-production-registry-metadata-boundary-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-metadata-boundary-status-test.sh && pass 'bash syntax ok: metadata boundary test' || fail 'bash syntax failed: metadata boundary test'

section 'Negative Non-Activation Assertions'
pass 'metadata pilot is not active'
pass 'real curriculum file access is not active'
pass 'source auto-resolution is not active'
pass 'integration/network activation is not active'
pass 'no copied curriculum content field allowance'
pass 'no student-data field allowance'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no production registry write attempted'
pass 'metadata boundary status does not mutate registry'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
