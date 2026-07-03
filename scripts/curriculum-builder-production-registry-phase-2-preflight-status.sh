#!/usr/bin/env bash
# Read-only Phase 2 production registry preflight status. No writes.
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

preflight_doc="docs/curriculum-builder-production-registry-phase-2-preflight.md"
audit_preflight="docs/curriculum-builder-production-registry-audit-rollback-preflight.md"
snapshot_readiness="docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md"
audit_stub="docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md"
tracker_doc="docs/curriculum-builder-production-registry-owen-checklist-tracker.md"
path_options="docs/curriculum-builder-production-registry-path-options.md"
post_decision="docs/curriculum-builder-production-registry-post-decision-implementation-map.md"
write_mission="docs/proposals/backlog/production-registry-write-mission.md"
metadata_blocked="docs/proposals/blocked/production-registry-real-metadata-intake.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
production_registry_dir="assistant/curriculum-builder/registry/v0-2"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
status_script="scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh"

section 'Production Registry Phase 2 Preflight'
cat <<'EOF'
Status: phase_2_preflight_readiness
Classification: read-only preflight proof — not implementation
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Real source references: blocked
Write behavior: approved in principle (item 2)
First implementation scope: Phase 2 preflight only — no file, no record, no --write
PASS does not authorize registry mutation: yes
EOF

section 'Phase 2 Preflight Documents'
check_file "${preflight_doc}"
check_file "${audit_preflight}"
check_file "${snapshot_readiness}"
check_file "${audit_stub}"
check_doc_contains "${preflight_doc}" "phase_2_preflight_complete" "phase 2 preflight closure"
check_doc_contains "${preflight_doc}" "does not create production-registry.json" "phase 2 no file creation"
check_doc_contains "${audit_preflight}" "audit_rollback_preflight_only" "audit rollback preflight classification"
check_doc_contains "${snapshot_readiness}" "planning_readiness_only" "snapshot readiness classification"
check_doc_contains "${snapshot_readiness}" "No snapshot of production-registry.json" "snapshot non-activation"

section 'Owen Checklist Preconditions'
check_file "${tracker_doc}"
check_doc_contains "${tracker_doc}" "| Write behavior allowed | approved | Owen |" "tracker item 2 approved"
check_doc_contains "${tracker_doc}" "| Real curriculum metadata allowed | deferred | Owen |" "tracker item 3 deferred"
check_doc_contains "${tracker_doc}" "| Real source references allowed | deferred | Owen |" "tracker item 4 deferred"
check_doc_contains "${tracker_doc}" "| Production registry path | approved | Owen |" "tracker item 1 approved"
check_doc_contains "${tracker_doc}" "| Rollback requirements | approved | Owen |" "tracker item 6 approved"
check_doc_contains "${tracker_doc}" "| Review states | approved | Owen |" "tracker item 7 approved"
check_doc_contains "${tracker_doc}" "| ID namespace | approved | Owen |" "tracker item 10 approved"

section 'Path and Namespace'
check_file "${path_options}"
check_doc_contains "${path_options}" "production-registry.json" "approved production path documented"
check_doc_contains "${path_options}" "resource-*" "approved namespace documented"

section 'Post-Decision and Write-Mission Coherence'
check_file "${post_decision}"
check_doc_contains "${post_decision}" "Phase 2" "post-decision map Phase 2"
check_file "${write_mission}"
check_doc_contains "${write_mission}" "Phase 2 preflight" "write mission Phase 2 distinction"
check_doc_contains "${write_mission}" "Registry mutation: blocked" "write mission mutation blocked"

section 'Blocked Intake Surfaces'
check_file "${metadata_blocked}"
check_doc_contains "${metadata_blocked}" "blocked" "real metadata intake blocked doc"
check_doc_contains docs/curriculum-builder-metadata-pilot-planning-boundary.md "no intake" "metadata pilot no intake"

section 'Production Surface Non-Existence'
[[ ! -f "${production_registry_path}" ]] && pass "production-registry.json does not exist (blocked)" || fail "production-registry.json must not exist in Phase 2"
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
  if [[ "${resource_files}" -eq 0 ]]; then
    pass "v0-2 production directory has no resource-* or production-registry files"
  else
    fail "v0-2 production directory must not contain production files yet"
  fi
else
  pass "v0-2 production directory does not exist yet (blocked)"
fi

section 'Sentinel and Write Guards'
check_file "${sentinel}"
grep -Fq -- 'Production writes: blocked' "${sentinel}" && pass 'BLOCKED-NO-WRITES.sentinel remains intact' || fail 'sentinel must state production writes blocked'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
grep -Fq -- '"--curriculum-registry-write"' "${manifest}" && pass 'manifest lists blocked --curriculum-registry-write' || fail 'manifest missing blocked --curriculum-registry-write'
if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  fail 'writer script must not exist'
else
  pass 'no production registry writer script exists'
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-phase-2-preflight-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-phase-2-preflight-status' || fail 'CLI missing --curriculum-production-registry-phase-2-preflight-status'
grep -Fq -- '"--curriculum-production-registry-phase-2-preflight-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-phase-2-preflight-status' || fail 'manifest missing --curriculum-production-registry-phase-2-preflight-status'
check_file tests/curriculum-builder-production-registry-phase-2-preflight-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-phase-2-preflight-status-test.sh && pass 'bash syntax ok: phase 2 preflight test' || fail 'bash syntax failed: phase 2 preflight test'

section 'Deferred Metadata WARN (Expected)'
warn "items 3 and 4 remain deferred — real metadata and source references blocked until Owen approves"

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no production registry write attempted'
pass 'no real metadata intake attempted'
pass 'no network call attempted'
pass 'Phase 2 preflight does not mutate registry'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
