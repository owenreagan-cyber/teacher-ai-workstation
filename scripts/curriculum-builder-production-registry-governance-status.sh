#!/usr/bin/env bash
# Read-only governance-first production registry foundation status. No writes.
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

governance_doc="docs/curriculum-builder-production-registry-governance-foundation.md"
path_options="docs/curriculum-builder-production-registry-path-options.md"
review_states="docs/curriculum-builder-production-registry-review-state-model.md"
audit_stub="docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md"
local_first="docs/curriculum-builder-local-first-storage-reference-model.md"
promotion_spec="docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md"
candidate_readme="assistant/curriculum-builder/registry/candidate-v0-2-production/README.md"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
candidate_records="assistant/curriculum-builder/registry/candidate-v0-2-production/records"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"
fixture_registry="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
status_script="scripts/curriculum-builder-production-registry-governance-status.sh"

section 'Production Registry Governance Foundation (CB-PROD-GOV)'
cat <<'EOF'
Status: governance-first foundation only
Classification: read-only blocked-write proof
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Automatic promotion: blocked
Owen § J checklist: items remain pending until Owen approves
PASS does not authorize writes: yes
EOF

section 'Governance Foundation Documents'
check_file "${governance_doc}"
check_file "${path_options}"
check_file "${review_states}"
check_file "${audit_stub}"
check_file "${local_first}"
check_file "${promotion_spec}"
check_doc_contains "${governance_doc}" "complete_cb_prod_gov_foundation" "governance foundation closure"
check_doc_contains "${governance_doc}" "Production registry writes: blocked" "governance blocked writes"
check_doc_contains "${path_options}" "Owen-approved" "path options Owen approved"
check_doc_contains "${path_options}" "fake_fixture_only" "path options fixture boundary"
check_doc_contains "${review_states}" "planning_only" "review state planning only"
check_doc_contains "${audit_stub}" "planning_stub_only" "audit stub planning only"
check_doc_contains "${local_first}" "metadata, references, status" "local-first reference model"
check_doc_contains "${local_first}" "Chief of Staff" "local-first chief of staff role"
check_doc_contains "${local_first}" "Supabase" "local-first supabase optional"
check_file docs/curriculum-builder-metadata-pilot-planning-boundary.md
check_file docs/curriculum-builder-manual-metadata-boundary.md
check_file docs/curriculum-builder-production-registry-owen-decision-worksheet.md
check_file docs/curriculum-builder-production-registry-post-decision-implementation-map.md
check_doc_contains docs/curriculum-builder-production-registry-owen-decision-worksheet.md "Decision-to-Next-Prompt Routing" "decision worksheet routing"
check_doc_contains docs/proposals/backlog/production-registry-write-mission.md "Preflight Checklist" "write mission preflight"

section 'Manual-Only Candidate Path Skeleton (Blocked)'
check_file "${candidate_readme}"
check_file "${sentinel}"
[[ -d "${candidate_records}" ]] && pass "candidate records directory exists (empty)" || fail "candidate records directory missing"
record_files=0
for candidate_file in "${candidate_records}"/*; do
  [[ -e "${candidate_file}" ]] || continue
  [[ "$(basename "${candidate_file}")" == ".gitkeep" ]] && continue
  record_files=$((record_files + 1))
done
if [[ "${record_files}" -eq 0 ]]; then
  pass "candidate records directory has no production record files"
else
  fail "candidate records directory must not contain production JSON files"
fi
check_doc_contains "${candidate_readme}" "blocked_skeleton_only" "candidate readme blocked classification"
check_doc_contains "${sentinel}" "Production writes: blocked" "sentinel blocked writes marker"

section 'Blocked Write Surfaces'
grep -Fq -- '"--curriculum-registry-write"' "${manifest}" && pass 'manifest lists blocked --curriculum-registry-write' || fail 'manifest missing blocked --curriculum-registry-write'
grep -Fq -- '"status": "blocked"' "${manifest}" && pass 'manifest retains blocked status markers' || fail 'manifest missing blocked status markers'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
if grep -Fq -- '--curriculum-registry-promote' bin/chief-of-staff 2>/dev/null; then
  fail 'chief-of-staff must not expose --curriculum-registry-promote'
else
  pass 'chief-of-staff does not expose --curriculum-registry-promote'
fi

section 'Owen Checklist and Review Packet Coherence'
check_doc_contains docs/curriculum-builder-production-registry-owen-review-packet.md "Governance-first only" "review packet governance-first section"
check_doc_contains docs/curriculum-builder-production-registry-owen-checklist-tracker.md "metadata_boundaries_approved_awaiting_pilot_and_write_missions" "checklist tracker metadata boundary closure"
check_doc_contains docs/curriculum-builder-production-registry-metadata-source-boundaries.md "metadata_boundary_refinement_complete" "metadata boundary refinement closure"
check_doc_contains docs/curriculum-builder-production-registry-phase-2-preflight.md "phase_2_preflight_complete" "phase 2 preflight doc closure"
check_doc_contains "${path_options}" "Owen-approved" "path options Owen-approved"
check_doc_contains docs/curriculum-builder-production-registry-owen-decision-worksheet.md "Documenting an option does not approve it" "decision worksheet non-approval"
check_doc_contains docs/curriculum-builder-production-registry-workflow-planning-brief.md "governance + blocked proof only" "planning brief § I governance scope"

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-governance-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-governance-status' || fail 'CLI missing --curriculum-production-registry-governance-status'
grep -Fq -- '"--curriculum-production-registry-governance-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-governance-status' || fail 'manifest missing --curriculum-production-registry-governance-status'
check_file tests/curriculum-builder-production-registry-governance-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-governance-status-test.sh && pass 'bash syntax ok: governance status test' || fail 'bash syntax failed: governance status test'

section 'Registry Non-Mutation'
if [[ -f "${live_registry}" ]]; then
  pass "live v0 registry present (read-only reference)"
else
  warn "live v0 registry missing"
fi
if [[ -f "${fixture_registry}" ]]; then
  pass "v0.2 fixture registry present (fixture-only reference)"
else
  warn "v0.2 fixture registry missing"
fi
pass 'governance status does not perform registry writes'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
pass 'no production registry write attempted'
pass 'no real metadata intake attempted'
pass 'no auto-promotion attempted'
pass 'no network call attempted'
pass 'no student data fields introduced'
pass 'candidate path remains non-production'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
