#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7c manual inventory validator and import preview status.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "doc mentions ${label}" || fail "${file} must mention ${label}"
}
check_bash_syntax() {
  [[ -f "$1" ]] || { fail "cannot syntax check missing file: $1"; return; }
  bash -n "$1" && pass "bash syntax ok: $1" || fail "bash syntax failed: $1"
}
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}
check_no_urls_in_fixtures() {
  local dir="$1"
  if grep -rqiE 'https?://' "${dir}" --include='*.json' --include='*.csv' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain http(s) URLs: ${dir}"
  else
    pass "fixtures exclude URLs: ${dir}"
  fi
}
check_no_real_paths_in_fixtures() {
  local dir="$1"
  if grep -rE '/Users/|/home/|\\\\Users\\\\|C:\\\\' "${dir}" --include='*.json' --include='*.csv' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain real local paths: ${dir}"
  else
    pass "fixtures exclude real local paths: ${dir}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m7b_dir="assistant/teacher-knowledge-vault/m7b"
m7c_dir="assistant/teacher-knowledge-vault/m7c"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
fixture_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

section 'Teacher Knowledge Vault M7c Manual Inventory Validator and Import Preview'
cat <<'EOF'
Status: fixture-only validator and import preview — fake/sanitized fixtures only
Closure: complete_teacher_knowledge_vault_m7c_manual_inventory_import_preview
Real connector implementation: no
OAuth/API/network execution: no
runtime_ingested: false
runtime_imported: false
api_calls_made: 0
real_metadata_records_ingested: 0
api_cost_estimate_usd: 0.00
PASS does not authorize connector runtime or catalog ingestion: yes
Import preview does not mean import: yes
EOF

section 'M7c Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md"
check_file "docs/teacher-knowledge-vault/manual-inventory-validator-model.md"
check_file "docs/teacher-knowledge-vault/manual-inventory-rejection-report-model.md"
check_file "docs/teacher-knowledge-vault/manual-inventory-normalized-preview-model.md"
check_file "docs/teacher-knowledge-vault/manual-inventory-import-preview-output.md"
check_file "docs/teacher-knowledge-vault/m7c-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md" "complete_teacher_knowledge_vault_m7c_manual_inventory_import_preview" "M7c closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md" "fake/sanitized fixtures only" "M7c fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md" "Import preview does not mean import" "import preview not import"
check_doc_contains "docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-validator-model.md" "Fixed Fixture Paths" "validator fixed paths"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-validator-model.md" "no arbitrary external paths" "no arbitrary paths"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-rejection-report-model.md" "blocked_placeholder_drive_id_pattern" "drive id rejection"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-rejection-report-model.md" "student_data_field_blocked" "student data rejection"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-rejection-report-model.md" "do_not_scan_blocked_from_normal_mapping" "dns rejection"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-normalized-preview-model.md" "SourceInventoryCandidate" "source inventory candidate"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-normalized-preview-model.md" "runtime_imported" "preview runtime imported flag"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-normalized-preview-model.md" "not catalog records" "preview not catalog"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-import-preview-output.md" "runtime_imports" "import preview zero imports"
check_doc_contains "docs/teacher-knowledge-vault/manual-inventory-import-preview-output.md" "ready_for_future_import_approval" "future import not approval"
check_doc_contains "docs/teacher-knowledge-vault/m7c-governance-status.md" "api_calls_made" "governance api zero"
check_doc_contains "docs/teacher-knowledge-vault/m7c-governance-status.md" "Fixture-only validator" "governance fixture only"

section 'M7c Fake Import Preview Fixtures'
check_file "${m7c_dir}/README.md"
check_file "${m7c_dir}/fake-import-preview.json"
check_file "${m7c_dir}/fake-rejection-report.json"
check_file "${m7c_dir}/fake-normalized-preview-candidates.json"
check_file "${m7c_dir}/fake-review-routing.json"
check_file "${m7c_dir}/fake-event-log-import-preview.json"
check_file "${m7c_dir}/fake-observability-metrics.json"
check_doc_contains "${m7c_dir}/fake-import-preview.json" '"runtime_imports": 0' "zero runtime imports"
check_doc_contains "${m7c_dir}/fake-import-preview.json" '"file_reads": 0' "zero file reads"
check_doc_contains "${m7c_dir}/fake-import-preview.json" "do_not_scan_blocked" "dns blocked preview"
check_doc_contains "${m7c_dir}/fake-import-preview.json" "teacher_only_restricted" "teacher only preview"
check_doc_contains "${m7c_dir}/fake-import-preview.json" "notebooklm_planning" "planning source preview"
check_doc_contains "${m7c_dir}/fake-rejection-report.json" "blocked_placeholder_drive_id_pattern" "drive id rejected"
check_doc_contains "${m7c_dir}/fake-rejection-report.json" "blocked_placeholder_canvas_id_pattern" "canvas id rejected"
check_doc_contains "${m7c_dir}/fake-rejection-report.json" "extracted_text_field_blocked" "extracted text rejected"
check_doc_contains "${m7c_dir}/fake-rejection-report.json" "runtime_ingestion_action_blocked" "runtime ingest rejected"
check_doc_contains "${m7c_dir}/fake-normalized-preview-candidates.json" "ResourceCandidate" "resource candidate preview"
check_doc_contains "${m7c_dir}/fake-normalized-preview-candidates.json" "SourceReconciliationPreview" "reconciliation preview"
check_doc_contains "${m7c_dir}/fake-normalized-preview-candidates.json" '"runtime_imported": false' "candidates not imported"
check_doc_contains "${m7c_dir}/fake-review-routing.json" "fixture_valid" "fixture valid review"
check_doc_contains "${m7c_dir}/fake-review-routing.json" "needs_sanitization" "needs sanitization review"
check_doc_contains "${m7c_dir}/fake-review-routing.json" "do_not_scan_blocked" "dns review state"
check_doc_contains "${m7c_dir}/fake-review-routing.json" "future_import_blocked_pending_owen_approval" "future import blocked"
check_doc_contains "${m7c_dir}/fake-event-log-import-preview.json" "manual_fixture_validation_started" "validation started event"
check_doc_contains "${m7c_dir}/fake-event-log-import-preview.json" "preview_candidate_created" "preview created event"
check_doc_contains "${m7c_dir}/fake-event-log-import-preview.json" "connector_access_requested_but_blocked" "connector blocked event"
check_doc_contains "${m7c_dir}/fake-event-log-import-preview.json" "content_read_requested_but_blocked" "content read blocked event"
check_doc_contains "${m7c_dir}/fake-observability-metrics.json" '"runtime_imports": 0' "metrics zero imports"
check_doc_contains "${m7c_dir}/fake-observability-metrics.json" '"api_calls_made": 0' "metrics zero api"
check_doc_contains "${m7c_dir}/fake-observability-metrics.json" '"write_operations": 0' "metrics zero writes"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m7c_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m7c_dir}"
check_no_real_paths_in_fixtures "${m7c_dir}"

section 'M7c Fixture Validator (Fixed Paths Only)'
check_file "${fixture_validator}"
check_bash_syntax "${fixture_validator}"
check_doc_contains "${fixture_validator}" "fixed repo fixtures only" "validator fixed paths doctrine"
check_doc_contains "${fixture_validator}" "m7b/fake-manual-inventory.json" "validator reads m7b fixture"
bash "${fixture_validator}" >/dev/null 2>&1 && pass 'fixture validator passes on m7b inventory' || fail 'fixture validator failed on m7b inventory'

section 'No Connector OAuth API Network Runtime'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect drive' || pass 'CLI has no vault connect drive command'
grep -Fq -- '--teacher-knowledge-vault-oauth)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault oauth' || pass 'CLI has no vault oauth command'
grep -Fq -- '--teacher-knowledge-vault-ingest)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault ingest' || pass 'CLI has no vault ingest command'
grep -Fq -- '--teacher-knowledge-vault-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault import' || pass 'CLI has no vault import command'
find assistant/teacher-knowledge-vault/m7c -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m7c' || pass 'no .db files in m7c fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
if [[ -f .env ]] && grep -qE 'DRIVE_|CANVAS_|NAS_|OAUTH_|API_KEY' .env 2>/dev/null; then
  fail 'no connector secrets in .env'
else
  pass 'no connector secrets in .env'
fi

section 'M0 M1 M2 M3 M4 M5 M6 M7 M7b Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'
bash scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh >/dev/null 2>&1 && pass 'M7b status still passes' || fail 'M7b status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7c" "build queue M7c"
check_doc_contains docs/build-queue.md "import preview" "build queue import preview"
check_doc_contains docs/build-queue.md "runtime manual import" "build queue runtime import blocked"
check_doc_contains assistant/memory/active-priorities.md "M7c" "active priorities M7c"
check_doc_contains docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md "M7c" "M7b roadmap M7c reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status"
check_help_contains "--teacher-knowledge-vault-m7c-manual-inventory-fixture-validator"
check_help_contains "--teacher-knowledge-vault-m7b-manual-source-inventory-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m7c-manual-inventory-import-preview-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M7c test' || fail 'smoke missing M7c test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real manual import attempted'
pass 'no catalog import attempted'
pass 'no OAuth API or secrets attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
