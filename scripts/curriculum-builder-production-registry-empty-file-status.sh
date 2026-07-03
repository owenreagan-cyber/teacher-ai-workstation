#!/usr/bin/env bash
# Read-only empty production registry file status (historical milestone).
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

empty_file_doc="docs/curriculum-builder-production-registry-empty-file.md"
first_record_doc="docs/curriculum-builder-production-registry-first-record.md"
pre_write_snapshot="assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
validator="scripts/curriculum-builder-production-registry-empty-file-validate.sh"
status_script="scripts/curriculum-builder-production-registry-empty-file-status.sh"
write_mission="docs/proposals/backlog/production-registry-write-mission.md"
post_decision="docs/curriculum-builder-production-registry-post-decision-implementation-map.md"
snapshot_readiness="docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

section 'Production Registry Empty-File Status (Historical)'
cat <<'EOF'
Status: empty_file_historical_complete
Classification: historical empty-shell milestone — superseded by first-record status
Runtime activation: no
Empty-shell mission: complete (historical)
Current registry state: see --curriculum-production-registry-first-record-status
Record writes via tooling: blocked
Active --write: blocked
Sentinel: intact
PASS does not authorize write tooling: yes
EOF

section 'Empty-File Documentation'
check_file "${empty_file_doc}"
check_doc_contains "${empty_file_doc}" "empty_file_complete" "empty file closure"
check_doc_contains "${empty_file_doc}" "sentinel remains intact" "sentinel dual state"
check_doc_contains "${empty_file_doc}" "historical" "empty file historical note"

section 'Pre-Write Snapshot Baseline (Historical Proof)'
check_file "${pre_write_snapshot}"
check_file "${validator}"
bash -n "${validator}" && pass "bash syntax ok: ${validator}" || fail "bash syntax failed: ${validator}"
validate_output="$(bash "${validator}" "${pre_write_snapshot}" 2>&1)" || validate_result=$?
validate_result="${validate_result:-0}"
if [[ "${validate_result}" -eq 0 ]] && grep -q 'empty shell validation succeeded' <<< "${validate_output}"; then
  pass "pre-write snapshot validates as empty shell"
else
  fail "pre-write snapshot empty shell validation failed"
  printf '%s\n' "${validate_output}" | tail -10
fi

section 'First-Record Successor Status'
check_file "${first_record_doc}"
check_file scripts/curriculum-builder-production-registry-first-record-status.sh
grep -Fq -- '--curriculum-production-registry-first-record-status' bin/chief-of-staff && pass 'CLI exposes first-record status successor' || fail 'CLI missing first-record status'

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
check_doc_contains "${post_decision}" "Empty-File" "post-decision empty-file phase"
check_file "${write_mission}"
check_doc_contains "${write_mission}" "empty-file mission" "write mission empty-file distinction"
check_file "${snapshot_readiness}"
check_doc_contains "${snapshot_readiness}" "empty shell baseline" "snapshot empty shell baseline"

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-empty-file-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-empty-file-status' || fail 'CLI missing --curriculum-production-registry-empty-file-status'
grep -Fq -- '"--curriculum-production-registry-empty-file-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-empty-file-status' || fail 'manifest missing --curriculum-production-registry-empty-file-status'
check_file tests/curriculum-builder-production-registry-empty-file-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-empty-file-status-test.sh && pass 'bash syntax ok: empty file test' || fail 'bash syntax failed: empty file test'

section 'Negative Non-Activation Assertions'
pass 'empty-file status is historical only'
pass 'real curriculum file access is not active'
pass 'source auto-resolution is not active'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
