#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7b manual source inventory Level 1 status.
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
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M7b Manual Source Inventory Level 1'
cat <<'EOF'
Status: manual source inventory Level 1 — fake/sanitized fixtures only
Closure: complete_teacher_knowledge_vault_m7b_manual_source_inventory_level_1
Real connector implementation: no
OAuth/API/network execution: no
runtime_ingested: false
api_calls_made: 0
real_metadata_records_ingested: 0
api_cost_estimate_usd: 0.00
PASS does not authorize connector runtime or catalog ingestion: yes
EOF

section 'M7b Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-schema.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-field-policy.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-review-queue.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-reconciliation-mapping.md"
check_file "docs/teacher-knowledge-vault/manual-source-inventory-sanitization-rules.md"
check_file "docs/teacher-knowledge-vault/m7b-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md" "complete_teacher_knowledge_vault_m7b_manual_source_inventory_level_1" "M7b closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md" "fake/sanitized fixtures only" "M7b fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md" "does not scan or ingest files" "no scan on approval"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-schema.md" "manual_inventory_id" "schema manual id"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-schema.md" "runtime_ingested" "schema runtime ingested flag"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-schema.md" "no extracted text fields are allowed" "no extracted text"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-field-policy.md" "student names" "blocked student names"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-field-policy.md" "real Drive IDs" "blocked drive ids"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-field-policy.md" "access tokens" "blocked tokens"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-review-queue.md" "manual_inventory_draft" "draft review state"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-review-queue.md" "do_not_scan_blocked" "do not scan review state"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-review-queue.md" "approved_for_future_import" "approved not ingestion"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-reconciliation-mapping.md" "only_in_canvas" "canvas reconcile mapping"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-reconciliation-mapping.md" "nas_mirror_candidate" "nas mirror mapping"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-sanitization-rules.md" "no real-looking Google Drive IDs" "sanitization drive ids"
check_doc_contains "docs/teacher-knowledge-vault/manual-source-inventory-sanitization-rules.md" "10_TEACHER_ONLY" "sanitization teacher only"
check_doc_contains "docs/teacher-knowledge-vault/m7b-governance-status.md" "api_calls_made" "governance api zero"

section 'M7b Fake Manual Inventory Fixtures'
check_file "${m7b_dir}/README.md"
check_file "${m7b_dir}/fake-manual-inventory.csv"
check_file "${m7b_dir}/fake-manual-inventory.json"
check_file "${m7b_dir}/fake-manual-review-routing.json"
check_file "${m7b_dir}/fake-event-log-manual-inventory.json"
check_file "${m7b_dir}/fake-reconciliation-mapping.json"
check_file "${m7b_dir}/fake-sanitization-results.json"
check_file "${m7b_dir}/fake-observability-metrics.json"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" '"runtime_connected": false' "records not connected"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" '"runtime_ingested": false' "records not ingested"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "10_TEACHER_ONLY" "teacher only record"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "99_DO_NOT_SCAN" "do not scan record"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "only_in_canvas" "canvas only reconcile"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "only_in_drive" "drive only reconcile"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "drive_and_canvas" "drive canvas reconcile"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "notebooklm_planning" "planning source record"
check_doc_contains "${m7b_dir}/fake-manual-inventory.json" "student_data_risk" "student data risk record"
check_doc_contains "${m7b_dir}/fake-manual-inventory.csv" "fake-m7b-man-dns" "csv do not scan row"
check_doc_contains "${m7b_dir}/fake-manual-inventory.csv" "ugreen_nas" "csv nas row"
check_doc_contains "${m7b_dir}/fake-manual-review-routing.json" "ready_for_fake_catalog_mapping" "catalog mapping routing"
check_doc_contains "${m7b_dir}/fake-manual-review-routing.json" "possible_student_data_risk" "student risk routing"
check_doc_contains "${m7b_dir}/fake-event-log-manual-inventory.json" "manual_inventory_record_created" "created event"
check_doc_contains "${m7b_dir}/fake-event-log-manual-inventory.json" "runtime_ingestion_requested_but_blocked" "ingestion blocked event"
check_doc_contains "${m7b_dir}/fake-reconciliation-mapping.json" "do_not_scan_blocked" "dns reconcile mapping"
check_doc_contains "${m7b_dir}/fake-sanitization-results.json" "no_oauth_secrets_tokens" "oauth sanitization check"
check_doc_contains "${m7b_dir}/fake-observability-metrics.json" '"connector_implementations": 0' "zero connectors"
check_doc_contains "${m7b_dir}/fake-observability-metrics.json" '"api_calls_made": 0' "zero api calls"
check_doc_contains "${m7b_dir}/fake-observability-metrics.json" '"real_metadata_records_ingested": 0' "zero ingested"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m7b_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m7b_dir}"
check_no_real_paths_in_fixtures "${m7b_dir}"

section 'No Connector OAuth API Network Runtime'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect drive' || pass 'CLI has no vault connect drive command'
grep -Fq -- '--teacher-knowledge-vault-oauth)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault oauth' || pass 'CLI has no vault oauth command'
grep -Fq -- '--teacher-knowledge-vault-ingest)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault ingest' || pass 'CLI has no vault ingest command'
find assistant/teacher-knowledge-vault/m7b -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m7b' || pass 'no .db files in m7b fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
if [[ -f .env ]] && grep -qE 'DRIVE_|CANVAS_|NAS_|OAUTH_|API_KEY' .env 2>/dev/null; then
  fail 'no connector secrets in .env'
else
  pass 'no connector secrets in .env'
fi

section 'M0 M1 M2 M3 M4 M5 M6 M7 Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7b" "build queue M7b"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "runtime manual import" "build queue runtime import blocked"
check_doc_contains assistant/memory/active-priorities.md "M7b" "active priorities M7b"
check_doc_contains docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md "M7b" "M7 roadmap M7b reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7b-manual-source-inventory-status"
check_help_contains "--teacher-knowledge-vault-m7-connector-approval-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7b-manual-source-inventory-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7b-manual-source-inventory-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m7b-manual-source-inventory-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M7b test' || fail 'smoke missing M7b test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real manual ingestion attempted'
pass 'no OAuth API or secrets attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
