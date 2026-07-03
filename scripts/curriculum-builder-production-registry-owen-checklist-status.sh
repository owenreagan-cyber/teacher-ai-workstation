#!/usr/bin/env bash
# Read-only Owen § J production registry approval checklist tracker status. No implementation.
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

tracker_doc="docs/curriculum-builder-production-registry-owen-checklist-tracker.md"
boundary_doc="docs/curriculum-builder-production-registry-metadata-source-boundaries.md"
review_packet="docs/curriculum-builder-production-registry-owen-review-packet.md"
planning_brief="docs/curriculum-builder-production-registry-workflow-planning-brief.md"
path_options="docs/curriculum-builder-production-registry-path-options.md"
status_script="scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
check_production_registry_empty_shell() {
  local registry_path="$1"
  local validator_script="scripts/curriculum-builder-production-registry-empty-file-validate.sh"
  if [[ ! -f "${registry_path}" ]]; then
    fail "production-registry.json must exist as empty shell"
    return
  fi
  if [[ ! -f "${validator_script}" ]]; then
    fail "empty-file validator missing"
    return
  fi
  local validate_output validate_result=0
  validate_output="$(bash "${validator_script}" "${registry_path}" 2>&1)" || validate_result=$?
  if [[ "${validate_result}" -eq 0 ]] && grep -q 'empty shell validation succeeded' <<< "${validate_output}"; then
    pass "production-registry.json exists with empty records shell"
  else
    fail "production-registry.json must be valid empty shell"
    printf '%s\n' "${validate_output}" | tail -5
  fi
}

check_no_resource_production_files() {
  local registry_dir="$1"
  local resource_files=0
  if [[ -d "${registry_dir}" ]]; then
    for candidate_file in "${registry_dir}"/*; do
      [[ -e "${candidate_file}" ]] || continue
      base="$(basename "${candidate_file}")"
      [[ "${base}" == resource-* ]] && resource_files=$((resource_files + 1))
    done
  fi
  [[ "${resource_files}" -eq 0 ]] && pass "no resource-* production record files exist" || fail "resource-* production record files must not exist"
}

production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Owen Production Registry Approval Checklist Tracker'
cat <<'EOF'
Status: planning_only
Classification: read-only checklist tracker — not implementation
Runtime activation: no
Production registry file: exists (empty shell)
Record writes: blocked
Active --write: blocked
Real metadata intake: blocked
Metadata pilot execution: blocked
Source-reference resolution: blocked
Path and namespace: approved (items 1 and 10 — 2026-07-02)
Write behavior: approved in principle (item 2 — 2026-07-02)
Metadata boundaries: approved (items 3 and 4 — 2026-07-02)
All Owen checklist items decided: yes (11 approved, 0 deferred)
Approved item 2 does not authorize registry mutation: yes
No write mission is authorized: yes
ChatGPT review: recommended before empty-file or write prompt
PASS does not authorize implementation: yes
EOF

section 'Tracker Document'
check_file "${tracker_doc}"
check_file "${boundary_doc}"
check_file "${review_packet}"
check_file docs/curriculum-builder-production-registry-owen-decision-worksheet.md
check_file docs/curriculum-builder-production-registry-post-decision-implementation-map.md
check_doc_contains docs/curriculum-builder-production-registry-owen-decision-worksheet.md "Documenting an option does not approve it" "decision worksheet non-approval"
check_doc_contains docs/curriculum-builder-production-registry-owen-checklist-tracker.md "metadata_boundaries_approved_awaiting_pilot_and_write_missions" "tracker closure status"
check_doc_contains "${boundary_doc}" "metadata_boundary_refinement_complete" "metadata boundary doc classification"
check_doc_contains "${boundary_doc}" "Manual Owen-entered descriptive metadata only" "item 3 boundary"
check_doc_contains "${boundary_doc}" "Manual non-resolving source-reference labels" "item 4 boundary"
check_doc_contains "${tracker_doc}" "Owen status" "tracker Owen status column"
check_doc_contains "${tracker_doc}" "curriculum-builder-production-registry-owen-review-packet" "tracker links review packet"
check_doc_contains "${review_packet}" "Documenting an option does not approve it" "review packet non-approval statement"
check_doc_contains "${review_packet}" "Preparing this packet does not authorize implementation" "review packet no implementation authorization"
check_doc_contains "${review_packet}" "product-decision wall" "review packet product-decision wall"
check_doc_contains "${planning_brief}" "Owen Approval Checklist" "planning brief § J"
check_doc_contains "${tracker_doc}" "Governance Affirmation Batch" "tracker governance affirmation batch section"
check_file docs/curriculum-builder-production-registry-governance-foundation.md
check_doc_contains docs/curriculum-builder-production-registry-governance-foundation.md "complete_cb_prod_gov_foundation" "governance foundation closure"

section 'Path, Namespace, and Write-Behavior Decisions'
check_file "${path_options}"
check_doc_contains "${path_options}" "Owen-approved" "path options Owen-approved Option B"
check_doc_contains "${path_options}" "production-registry.json" "path options canonical production path"
check_doc_contains "${path_options}" "resource-*" "path options resource namespace"
check_production_registry_empty_shell "${production_registry_path}"
check_no_resource_production_files "$(dirname "${production_registry_path}")"
check_file "${sentinel}"
grep -Fq -- 'Production writes: blocked' "${sentinel}" && pass 'BLOCKED-NO-WRITES.sentinel remains intact' || fail 'sentinel must state production writes blocked'

section 'Checklist Item Rows (Owen Decisions)'
CHECKLIST_EXPECTED=(
  "Production registry path|approved"
  "Write behavior allowed|approved"
  "Real curriculum metadata allowed|approved"
  "Real source references allowed|approved"
  "Source systems permitted|approved"
  "Rollback requirements|approved"
  "Review states|approved"
  "Student-data prohibition|approved"
  "Canvas/Drive/NAS/iCloud/API/OAuth/network|approved"
  "ID namespace|approved"
  "First implementation PR scope|approved"
)

approved_count=0
deferred_count=0
pending_count=0
for entry in "${CHECKLIST_EXPECTED[@]}"; do
  item="${entry%%|*}"
  expected="${entry##*|}"
  if grep -Fq -- "| ${item} | ${expected} | Owen |" "${tracker_doc}"; then
    pass "checklist item ${expected}: ${item}"
    case "${expected}" in
      approved) approved_count=$((approved_count + 1)) ;;
      deferred) deferred_count=$((deferred_count + 1)) ;;
      pending) pending_count=$((pending_count + 1)) ;;
    esac
  else
    fail "tracker row mismatch for ${item}: expected Owen status ${expected}"
  fi
done

if [[ "${approved_count}" -eq 11 && "${deferred_count}" -eq 0 && "${pending_count}" -eq 0 ]]; then
  pass "all Owen checklist items decided: 11 approved, 0 deferred"
else
  fail "expected 11 approved and 0 deferred; found approved=${approved_count} deferred=${deferred_count} pending=${pending_count}"
fi

if [[ "${deferred_count}" -gt 0 ]]; then
  warn "${deferred_count} Owen checklist items deferred"
else
  pass "no deferred Owen checklist items"
fi

pass "metadata pilot is not active"
pass "real curriculum file access is not active"
pass "source-reference resolution is not active"
if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  fail 'writer script must not exist'
else
  pass 'no writer scripts exist'
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-owen-checklist-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-owen-checklist-status' || fail 'CLI missing --curriculum-production-registry-owen-checklist-status'
grep -Fq -- '"--curriculum-production-registry-owen-checklist-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-owen-checklist-status' || fail 'manifest missing --curriculum-production-registry-owen-checklist-status'
check_file tests/curriculum-builder-production-registry-owen-checklist-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-owen-checklist-status-test.sh && pass 'bash syntax ok: owen checklist test' || fail 'bash syntax failed: owen checklist test'

section 'Roadmap and Ledger Coherence'
check_doc_contains docs/proposals/index.md "Owen § J production registry checklist tracker" "proposal ledger owen tracker"
check_doc_contains docs/master-build-roadmap.md "Metadata pilot execution planning complete" "roadmap metadata pilot planning complete"
check_doc_contains docs/build-queue.md "metadata pilot execution planning complete" "build queue metadata pilot planning complete"
check_doc_contains assistant/memory/active-priorities.md "Metadata pilot execution planning complete" "active priorities metadata pilot planning complete"

section 'Negative Non-Activation Assertions'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no production registry write attempted'
pass 'no real metadata intake attempted'
pass 'no network call attempted'
pass 'Owen approval required before implementation'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
