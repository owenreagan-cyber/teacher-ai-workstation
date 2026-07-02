#!/usr/bin/env bash
# Read-only Curriculum Builder metadata contract schemas status (Programs A4–A7).
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

status_script="scripts/curriculum-builder-contract-schemas-status.sh"
index_doc="docs/curriculum-builder-canonical-contract-schemas.md"
boundaries_doc="docs/curriculum-builder-contract-boundaries.md"

section 'Curriculum Builder Metadata Contract Schemas (Programs A4–A7)'
cat <<'EOF'
Status: read-only planning only
A4–A7 schemas: inactive (planning only)
Runtime activation: no
Validators: none (inactive schemas)
Ingestion: blocked
Scanning: blocked
Generation: blocked
Network calls: no
Student data: no
EOF

section 'Foundation Documents'
check_file "${index_doc}"
check_file "${boundaries_doc}"
check_file docs/curriculum-resource-contract-schema.md
check_file docs/curriculum-source-reference-contract-schema.md
check_file docs/curriculum-review-state-contract-schema.md
check_file docs/curriculum-lesson-link-contract-schema.md
check_file docs/curriculum-builder-local-first-foundation-plan.md

section 'Program A4 — Resource Contract'
check_doc_contains docs/curriculum-resource-contract-schema.md "resource_id" "resource contract resource_id"
check_doc_contains docs/curriculum-resource-contract-schema.md "source_reference_id" "resource contract source reference link"
check_doc_contains docs/curriculum-resource-contract-schema.md "inactive schema draft" "resource contract inactive"

section 'Program A5 — Source Reference Contract'
check_doc_contains docs/curriculum-source-reference-contract-schema.md "source_reference_id" "source reference id"
check_doc_contains docs/curriculum-source-reference-contract-schema.md "not_scanned" "source reference not_scanned"
check_doc_contains docs/curriculum-source-reference-contract-schema.md "not_ingested" "source reference not_ingested"
check_doc_contains docs/curriculum-source-reference-contract-schema.md "google_drive" "source system google_drive planning"

section 'Program A6 — Review State Contract'
check_doc_contains docs/curriculum-review-state-contract-schema.md "review_status" "review state status"
check_doc_contains docs/curriculum-review-state-contract-schema.md "requires_manual_review" "review state manual review"
check_doc_contains docs/curriculum-review-state-contract-schema.md "Review generation: blocked" "review generation blocked"

section 'Program A7 — Lesson Link Contract'
check_doc_contains docs/curriculum-lesson-link-contract-schema.md "lesson_link_id" "lesson link id"
check_doc_contains docs/curriculum-lesson-link-contract-schema.md "generation_blocked" "lesson link generation blocked"
check_doc_contains docs/curriculum-lesson-link-contract-schema.md "canvas_reference_future" "lesson link canvas future"

section 'Inactive Sample Artifacts'
check_file assistant/curriculum-builder/metadata-contract/v0/README.md
check_file assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json
check_file assistant/curriculum-builder/metadata-contract/v0/samples/sample-resource-001.json
check_file assistant/curriculum-builder/metadata-contract/v0/samples/sample-source-reference-001.json
check_file assistant/curriculum-builder/metadata-contract/v0/samples/sample-review-state-001.json
check_file assistant/curriculum-builder/metadata-contract/v0/samples/sample-lesson-link-001.json
check_doc_contains assistant/curriculum-builder/metadata-contract/v0/README.md "inactive" "metadata contract readme inactive"

section 'Non-Activation Boundaries'
check_doc_contains "${boundaries_doc}" "document scanning" "boundaries block scanning"
check_doc_contains "${boundaries_doc}" "folder scanning" "boundaries block folder scanning"
check_doc_contains "${boundaries_doc}" "OCR" "boundaries block OCR"
check_doc_contains "${boundaries_doc}" "embeddings" "boundaries block embeddings"
check_doc_contains "${boundaries_doc}" "vector DB" "boundaries block vector db"
check_doc_contains "${boundaries_doc}" "RAG" "boundaries block RAG"
check_doc_contains "${boundaries_doc}" "lesson generation" "boundaries block lesson generation"
check_doc_contains "${boundaries_doc}" "student data" "boundaries block student data"
check_doc_contains "${boundaries_doc}" "Drive crawling" "boundaries block drive crawling"
check_doc_contains "${boundaries_doc}" "Canvas crawling" "boundaries block canvas crawling"
check_doc_contains "${boundaries_doc}" "OAuth" "boundaries block oauth"
check_doc_contains "${index_doc}" "complete_a4_a7_metadata_contracts" "index closure status"

section 'Governance and Roadmap Coherence'
check_doc_contains docs/cursor-operating-modes-and-approval-gates.md "Proposal Lifecycle" "governance proposal lifecycle"
check_doc_contains docs/teacher-workstation-domain-boundaries.md "Curriculum / Lesson" "domain boundaries curriculum"
check_doc_contains docs/master-build-roadmap.md "curriculum-builder-canonical-contract-schemas" "roadmap links contract schemas index"
check_doc_contains docs/build-queue.md "Curriculum Builder" "build queue curriculum builder"
check_doc_contains assistant/memory/active-priorities.md "Curriculum Builder" "active priorities curriculum builder"

section 'CLI, Manifest, Status Script, and Tests'
grep -Fq -- '--curriculum-contracts-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-contracts-status' || fail 'CLI missing --curriculum-contracts-status'
grep -Fq -- '"--curriculum-contracts-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-contracts-status' || fail 'manifest missing --curriculum-contracts-status'
check_file "${status_script}"
check_file tests/curriculum-builder-contract-schemas-status-test.sh
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n tests/curriculum-builder-contract-schemas-status-test.sh && pass 'bash syntax ok: tests/curriculum-builder-contract-schemas-status-test.sh' || fail 'bash syntax failed: contract schemas test'

section 'Negative Non-Activation Assertions'
status_script_path="scripts/curriculum-builder-contract-schemas-status.sh"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script_path}" 2>/dev/null && fail 'contract schemas status script must not shell-invoke curl' || pass 'contract schemas status script does not shell-invoke curl'
grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${status_script_path}" 2>/dev/null && fail 'contract schemas status script must not shell-invoke wget' || pass 'contract schemas status script does not shell-invoke wget'
grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' "${status_script_path}" 2>/dev/null && fail 'contract schemas status script must not shell-invoke brew' || pass 'contract schemas status script does not shell-invoke brew'
grep -Eq '(^|[;&|[:space:]])npm[[:space:]]' "${status_script_path}" 2>/dev/null && fail 'contract schemas status script must not shell-invoke npm' || pass 'contract schemas status script does not shell-invoke npm'
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script_path}" 2>/dev/null && fail 'contract schemas status script must not shell-invoke find' || pass 'contract schemas status script does not shell-invoke find'
if grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(add|commit|push|merge|reset)' "${status_script}" 2>/dev/null; then
  fail 'contract schemas status script must not mutate git state'
else
  pass 'contract schemas status script does not mutate git state'
fi
pass 'no folder scan attempted'
pass 'no curriculum ingestion attempted'
pass 'no lesson generation attempted'
pass 'no network call attempted'
pass 'no write action attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
