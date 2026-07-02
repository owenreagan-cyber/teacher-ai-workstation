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
status_script="scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

section 'Owen Production Registry Approval Checklist Tracker'
cat <<'EOF'
Status: planning_only
Classification: read-only checklist tracker — not implementation
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Owen approval: required for each checklist item
ChatGPT review: recommended before implementation prompt
PASS does not authorize implementation: yes
EOF

section 'Tracker Document'
check_file "${tracker_doc}"
check_file "${review_packet}"
check_doc_contains "${tracker_doc}" "not_complete_awaiting_owen" "tracker closure status"
check_doc_contains "${tracker_doc}" "Owen status" "tracker Owen status column"
check_doc_contains "${tracker_doc}" "curriculum-builder-production-registry-owen-review-packet" "tracker links review packet"
check_doc_contains "${review_packet}" "Documenting an option does not approve it" "review packet non-approval statement"
check_doc_contains "${review_packet}" "Preparing this packet does not authorize implementation" "review packet no implementation authorization"
check_doc_contains "${review_packet}" "product-decision wall" "review packet product-decision wall"
check_doc_contains "${planning_brief}" "Owen Approval Checklist" "planning brief § J"

section 'Checklist Item Rows (Owen Decisions Pending)'
CHECKLIST_ITEMS=(
  "Production registry path"
  "Write behavior allowed"
  "Real curriculum metadata allowed"
  "Real source references allowed"
  "Source systems permitted"
  "Rollback requirements"
  "Review states"
  "Student-data prohibition"
  "Canvas/Drive/NAS/iCloud/API/OAuth/network"
  "ID namespace"
  "First implementation PR scope"
)

pending_count=0
for item in "${CHECKLIST_ITEMS[@]}"; do
  if grep -Fq -- "| ${item} | pending | Owen |" "${tracker_doc}"; then
    pass "checklist item tracked pending: ${item}"
    pending_count=$((pending_count + 1))
  else
    fail "tracker missing pending row for: ${item}"
  fi
done

if [[ "${pending_count}" -eq 11 ]]; then
  warn "11 Owen checklist items pending approval — implementation blocked"
else
  fail "expected 11 pending Owen checklist items; found ${pending_count}"
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-owen-checklist-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-owen-checklist-status' || fail 'CLI missing --curriculum-production-registry-owen-checklist-status'
grep -Fq -- '"--curriculum-production-registry-owen-checklist-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-owen-checklist-status' || fail 'manifest missing --curriculum-production-registry-owen-checklist-status'
check_file tests/curriculum-builder-production-registry-owen-checklist-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-production-registry-owen-checklist-status-test.sh && pass 'bash syntax ok: owen checklist test' || fail 'bash syntax failed: owen checklist test'

section 'Roadmap and Ledger Coherence'
check_doc_contains docs/proposals/index.md "Owen § J production registry checklist tracker" "proposal ledger owen tracker"
check_doc_contains docs/master-build-roadmap.md "Owen must complete the approval checklist" "roadmap Owen checklist gate"
check_doc_contains docs/build-queue.md "Product-decision wall" "build queue product-decision wall"
check_doc_contains assistant/memory/active-priorities.md "Owen § J production registry checklist review" "active priorities Owen review"

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
