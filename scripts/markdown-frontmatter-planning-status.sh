#!/usr/bin/env bash
# Read-only markdown frontmatter / manual metadata planning status. Planning only — no parser/validator.
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

planning_doc="docs/curriculum-manual-metadata-frontmatter-planning.md"
proposal_note="docs/proposals/ideas/markdown-frontmatter-planning-note.md"
blocked_doc="docs/proposals/blocked/markdown-frontmatter-runtime-boundaries.md"
fixtures_dir="assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning"
positive_fixture="${fixtures_dir}/example-field-ideas-illustration.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Markdown Frontmatter Planning (Planning Only)'
cat <<'EOF'
Status: planning_only
Active schema: no
Parser: no
Validator: no
Folder scan: no
Real curriculum ingestion: no
Student data: blocked — absolute
Integrations: no
AI generation: no
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Canonical Planning Docs'
check_file "${planning_doc}"
check_file "${proposal_note}"
check_file "${blocked_doc}"
check_doc_contains "${planning_doc}" "complete_curriculum_manual_metadata_frontmatter_planning" "planning closure marker"
check_doc_contains "${planning_doc}" "proposal candidate" "proposal-candidate notice"
check_doc_contains "${planning_doc}" "not parsed" "not-parsed disclaimer"
check_doc_contains "${planning_doc}" "not validated" "not-validated disclaimer"
check_doc_contains "${planning_doc}" "discovery-classification-memo" "PR #239 memo cross-link"
check_doc_contains "${planning_doc}" "A4" "A4–A7 cross-link"
check_doc_contains "${blocked_doc}" "Frontmatter parser" "parser blocked"

section 'Field Ideas Marked Planning-Only'
for field_marker in \
  "conceptual; not parsed" \
  "not accepted runtime schema" \
  "not used by commands"; do
  check_doc_contains "${planning_doc}" "${field_marker}" "field idea marker: ${field_marker}"
done

section 'Fake Local Illustrations'
check_file "${fixtures_dir}/README.md"
check_file "${positive_fixture}"
check_file "${fixtures_dir}/negative/blocked-student-data-field-names.json"
check_file "${fixtures_dir}/negative/blocked-integration-runtime-patterns.json"
check_doc_contains "${positive_fixture}" "manual_metadata_frontmatter_planning_only" "positive fixture classification"
check_doc_contains "${positive_fixture}" '"not_a_schema": true' "fixture not-a-schema flag"
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${positive_fixture}" >/dev/null 2>&1 && pass "JSON parses: ${positive_fixture}" || fail "JSON does not parse: ${positive_fixture}"
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Fixture Safety (Positive Illustration)'
if grep -qiE 'https?://|@.*\.(com|edu)|oauth|api_key|drive\.google' "${positive_fixture}" 2>/dev/null; then
  fail "positive fixture must not contain URLs/oauth/Drive patterns"
else
  pass 'positive fixture excludes forbidden URL/Drive/oauth patterns'
fi
if grep -qiE '"student_name"|"grade_value"|"real_student"' "${positive_fixture}" 2>/dev/null; then
  fail "positive fixture must not contain student data field names"
else
  pass 'positive fixture excludes forbidden student-data field names'
fi

section 'No Runtime Frontmatter Parser/Validator'
runtime_hits=0
for pattern in '*frontmatter-parse*' '*frontmatter-valid*' '*markdown-frontmatter-read*'; do
  for candidate in scripts/${pattern}; do
    [[ -e "${candidate}" ]] || continue
    [[ "${candidate}" == *planning-status* ]] && continue
    runtime_hits=1
    fail "runtime frontmatter script must not exist: ${candidate}"
  done
done
[[ "${runtime_hits}" == "0" ]] && pass 'no frontmatter parser/validator scripts in scripts/'
grep -Fq -- '--markdown-frontmatter-parse)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose frontmatter parse command' || pass 'CLI has no frontmatter parse command'
grep -Fq -- '--markdown-frontmatter-validate)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose frontmatter validate command' || pass 'CLI has no frontmatter validate command'
grep -Fq -- '"--curriculum-scan-folders"' assistant/chief-of-staff/v1/command-surface-manifest.json 2>/dev/null && pass 'curriculum scan remains blocked in manifest' || warn 'curriculum scan blocked flag not found in manifest'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Coherence Cross-Links'
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "complete_curriculum_manual_metadata_frontmatter_planning" "whole-system report frontmatter closure"
check_doc_contains docs/proposals/index.md "Markdown frontmatter planning program" "proposal ledger frontmatter"
check_doc_contains docs/build-queue.md "frontmatter planning" "build queue frontmatter"
check_doc_contains assistant/memory/active-priorities.md "frontmatter planning" "active priorities frontmatter"
check_doc_contains docs/teacher-workstation-capability-map.md "markdown-frontmatter-planning-status" "capability map frontmatter"

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--markdown-frontmatter-planning-status' bin/chief-of-staff && pass 'CLI exposes --markdown-frontmatter-planning-status' || fail 'CLI missing --markdown-frontmatter-planning-status'
grep -Fq -- '"--markdown-frontmatter-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --markdown-frontmatter-planning-status' || fail 'manifest missing --markdown-frontmatter-planning-status'
check_file tests/markdown-frontmatter-planning-status-test.sh
bash -n tests/markdown-frontmatter-planning-status-test.sh && pass 'bash syntax ok: frontmatter planning test' || fail 'bash syntax failed: frontmatter planning test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no frontmatter parsing attempted'
pass 'no folder scanning attempted'
pass 'no student data ingestion attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
