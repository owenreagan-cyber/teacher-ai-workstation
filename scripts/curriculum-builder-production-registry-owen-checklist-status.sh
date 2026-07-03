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
review_packet="docs/curriculum-builder-production-registry-owen-review-packet.md"
planning_brief="docs/curriculum-builder-production-registry-workflow-planning-brief.md"
path_options="docs/curriculum-builder-production-registry-path-options.md"
status_script="scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"

section 'Owen Production Registry Approval Checklist Tracker'
cat <<'EOF'
Status: planning_only
Classification: read-only checklist tracker — not implementation
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Real source references: blocked
Path and namespace: approved (items 1 and 10 — 2026-07-02)
Write behavior: deferred (item 2)
Deferred items: 3 — write behavior, metadata intake, source references
Approved governance rows do not authorize production writes: yes
No write mission is authorized: yes
ChatGPT review: recommended before implementation prompt
PASS does not authorize implementation: yes
EOF

section 'Tracker Document'
check_file "${tracker_doc}"
check_file "${review_packet}"
check_file docs/curriculum-builder-production-registry-owen-decision-worksheet.md
check_file docs/curriculum-builder-production-registry-post-decision-implementation-map.md
check_doc_contains docs/curriculum-builder-production-registry-owen-decision-worksheet.md "Documenting an option does not approve it" "decision worksheet non-approval"
check_doc_contains "${tracker_doc}" "path_namespace_recorded_awaiting_write_decision" "tracker closure status"
check_doc_contains "${tracker_doc}" "Owen status" "tracker Owen status column"
check_doc_contains "${tracker_doc}" "curriculum-builder-production-registry-owen-review-packet" "tracker links review packet"
check_doc_contains "${review_packet}" "Documenting an option does not approve it" "review packet non-approval statement"
check_doc_contains "${review_packet}" "Preparing this packet does not authorize implementation" "review packet no implementation authorization"
check_doc_contains "${review_packet}" "product-decision wall" "review packet product-decision wall"
check_doc_contains "${planning_brief}" "Owen Approval Checklist" "planning brief § J"
check_doc_contains "${tracker_doc}" "Governance Affirmation Batch" "tracker governance affirmation batch section"
check_file docs/curriculum-builder-production-registry-governance-foundation.md
check_doc_contains docs/curriculum-builder-production-registry-governance-foundation.md "complete_cb_prod_gov_foundation" "governance foundation closure"

section 'Path and Namespace Decisions'
check_file "${path_options}"
check_doc_contains "${path_options}" "Owen-approved" "path options Owen-approved Option B"
check_doc_contains "${path_options}" "production-registry.json" "path options canonical production path"
check_doc_contains "${path_options}" "resource-*" "path options resource namespace"
[[ ! -f "${production_registry_path}" ]] && pass "production-registry.json does not exist yet (blocked)" || fail "production-registry.json must not exist until write mission"

section 'Checklist Item Rows (Owen Decisions)'
CHECKLIST_EXPECTED=(
  "Production registry path|approved"
  "Write behavior allowed|deferred"
  "Real curriculum metadata allowed|deferred"
  "Real source references allowed|deferred"
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

if [[ "${approved_count}" -eq 8 && "${deferred_count}" -eq 3 && "${pending_count}" -eq 0 ]]; then
  pass "path and namespace recorded: 8 approved, 3 deferred"
else
  fail "expected 8 approved and 3 deferred; found approved=${approved_count} deferred=${deferred_count} pending=${pending_count}"
fi

if [[ "${deferred_count}" -gt 0 ]]; then
  warn "${deferred_count} Owen checklist items deferred — write behavior, metadata intake, and source references remain blocked"
else
  pass "no deferred Owen checklist items"
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-owen-checklist-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-owen-checklist-status' || fail 'CLI missing --curriculum-production-registry-owen-checklist-status'
grep -Fq -- '"--curriculum-production-registry-owen-checklist-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-owen-checklist-status' || fail 'manifest missing --curriculum-production-registry-owen-checklist-status'
check_file tests/curriculum-builder-production-registry-owen-checklist-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-owen-checklist-status-test.sh && pass 'bash syntax ok: owen checklist test' || fail 'bash syntax failed: owen checklist test'

section 'Roadmap and Ledger Coherence'
check_doc_contains docs/proposals/index.md "Owen § J production registry checklist tracker" "proposal ledger owen tracker"
check_doc_contains docs/master-build-roadmap.md "Next decision step: item 2 write behavior" "roadmap Owen checklist gate"
check_doc_contains docs/build-queue.md "Product-decision wall" "build queue product-decision wall"
check_doc_contains assistant/memory/active-priorities.md "item 2 write behavior" "active priorities write behavior next step"

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
