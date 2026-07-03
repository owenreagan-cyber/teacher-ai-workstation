#!/usr/bin/env bash
# Read-only production registry next-gate decision prep status. No implementation.
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

decision_packet="docs/curriculum-builder-production-registry-next-gate-decision-packet.md"
writer_boundary="docs/curriculum-builder-production-registry-writer-tooling-design-boundary.md"
second_record_plan="docs/curriculum-builder-production-registry-second-record-worksheet-plan.md"
next_gate_classification="docs/curriculum-builder-production-registry-next-gate-classification.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
first_record_validator="scripts/curriculum-builder-production-registry-first-record-validate.sh"
status_script="scripts/curriculum-builder-production-registry-next-gate-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
APPROVED_ID="resource-math-lesson-108-presentation"

section 'Production Registry Next-Gate Status'
cat <<'EOF'
Status: next_gate_decision_prep_complete
Classification: decision packet only — no gate approved
Runtime activation: no
Records count: exactly 1
Next gates: blocked pending Owen decision
Writer tooling: blocked
Second record: blocked
Metadata pilot expansion: blocked
Parked state: allowed
PASS does not authorize implementation: yes
EOF

section 'Decision Packet Documentation'
check_file "${decision_packet}"
check_doc_contains "${decision_packet}" "next_gate_decision_packet_complete" "decision packet closure"
check_doc_contains "${decision_packet}" "Option D — Parked State" "parked state option"
check_doc_contains "${decision_packet}" "parked_state_allowed" "parked state allowed"
check_doc_contains "${decision_packet}" "blocked pending explicit Owen decision" "gates blocked language"
check_file "${writer_boundary}"
check_doc_contains "${writer_boundary}" "writer_tooling_design_boundary_planning_only" "writer boundary planning only"
check_doc_contains "${writer_boundary}" "No writer scripts" "writer boundary no scripts"
check_file "${second_record_plan}"
check_doc_contains "${second_record_plan}" "second_record_worksheet_planning_only" "second record worksheet planning only"
check_doc_contains "${second_record_plan}" "<placeholder>" "worksheet placeholder fields"
check_file "${next_gate_classification}"
check_doc_contains "${next_gate_classification}" "blocked pending explicit Owen decision" "classification blocked gates"

section 'First Record Unchanged'
check_file "${production_registry_path}"
check_file "${first_record_validator}"
validate_output="$(bash "${first_record_validator}" "${production_registry_path}" 2>&1)" || validate_result=$?
validate_result="${validate_result:-0}"
if [[ "${validate_result}" -eq 0 ]] && grep -q 'first production registry record validation succeeded' <<< "${validate_output}"; then
  pass "production-registry.json validates as one approved record"
else
  fail "first record must remain valid and unchanged"
  printf '%s\n' "${validate_output}" | tail -5
fi
record_count="$(python3 -c "
import json
with open('${production_registry_path}') as f:
    d = json.load(f)
print(len(d.get('records', [])))
")"
[[ "${record_count}" == "1" ]] && pass "records count remains exactly 1" || fail "records count must remain exactly 1"
grep -Fq "\"${APPROVED_ID}\"" "${production_registry_path}" && pass "approved first record ID unchanged" || fail "approved first record ID missing"

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
grep -Fq -- '--curriculum-production-registry-next-gate-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-next-gate-status' || fail 'CLI missing --curriculum-production-registry-next-gate-status'
grep -Fq -- '"--curriculum-production-registry-next-gate-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-next-gate-status' || fail 'manifest missing --curriculum-production-registry-next-gate-status'
check_file tests/curriculum-builder-production-registry-next-gate-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-next-gate-status-test.sh && pass 'bash syntax ok: next gate test' || fail 'bash syntax failed: next gate test'

section 'Negative Non-Activation Assertions'
pass 'next gates blocked pending Owen decision'
pass 'real curriculum file access is not active'
pass 'source auto-resolution is not active'
pass 'integration/network activation is not active'
pass 'no second production record authorized'
pass 'metadata pilot expansion beyond first record is not active'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
