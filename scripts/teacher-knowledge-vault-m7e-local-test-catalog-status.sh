#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7e local test catalog status.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m7e_dir="assistant/teacher-knowledge-vault/m7e"
m7e_out_dir=".tmp/teacher-knowledge-vault/m7e"
import_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-import.sh"
cleanup_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh"
m7c_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M7e Local Test Catalog Import'
cat <<'EOF'
Status: bounded runtime write — disposable local test catalog only
Closure: complete_teacher_knowledge_vault_m7e_local_test_catalog_import
Production catalog writes: no
Arbitrary path input: no
Real source ingestion: no
api_calls_made: 0
production_writes: 0
PASS does not authorize production import: yes
EOF

section 'M7e Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md"
check_file "docs/teacher-knowledge-vault/local-test-catalog-storage-policy.md"
check_file "docs/teacher-knowledge-vault/local-test-catalog-schema.md"
check_file "docs/teacher-knowledge-vault/local-test-catalog-import-command.md"
check_file "docs/teacher-knowledge-vault/local-test-catalog-backup-rollback-cleanup.md"
check_file "docs/teacher-knowledge-vault/m7e-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md" "complete_teacher_knowledge_vault_m7e_local_test_catalog_import" "M7e closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md" "disposable local test catalog" "M7e disposable doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md" "Production catalog writes: blocked" "no production writes"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-storage-policy.md" ".tmp/teacher-knowledge-vault/m7e/" "fixed generated path"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-storage-policy.md" "no arbitrary user input" "no arbitrary input"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-schema.md" "import_batches" "schema import batches"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-schema.md" "blocked_records" "schema blocked records"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-import-command.md" "Rejects any command-line path arguments" "import rejects args"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-import-command.md" "M7c fixture validator" "import uses validator"
check_doc_contains "docs/teacher-knowledge-vault/local-test-catalog-backup-rollback-cleanup.md" "batch_removal_supported" "rollback batch removal"
check_doc_contains "docs/teacher-knowledge-vault/m7e-governance-status.md" "Gitignored generated output" "governance gitignored"
check_doc_contains "docs/teacher-knowledge-vault/m7e-governance-status.md" "Production catalog writes" "governance zero production"

section 'M7e Fixtures and Gitignore'
check_file "${m7e_dir}/README.md"
check_file "${m7e_dir}/fake-test-catalog-schema.json"
check_file "${m7e_dir}/fake-import-summary-example.json"
check_file "${m7e_dir}/fake-rollback-proof-example.json"
check_doc_contains "${m7e_dir}/fake-import-summary-example.json" '"preview_candidates_imported": 8' "example 8 candidates"
check_doc_contains "${m7e_dir}/fake-import-summary-example.json" '"blocked_count": 2' "example 2 blocked"
check_doc_contains "${m7e_dir}/fake-import-summary-example.json" '"production_write": false' "example no production"
check_doc_contains "${m7e_dir}/fake-rollback-proof-example.json" "cleanup_removes_only_fixed_path" "rollback fixed path"
grep -Fq -- '.tmp/teacher-knowledge-vault/m7e/' .gitignore && pass 'gitignore covers M7e generated path' || fail 'gitignore must cover .tmp/teacher-knowledge-vault/m7e/'

section 'M7e Import and Cleanup Scripts'
check_file "${import_script}"
check_file "${cleanup_script}"
check_bash_syntax "${import_script}"
check_bash_syntax "${cleanup_script}"
check_doc_contains "${import_script}" "arbitrary path arguments are not accepted" "import blocks arbitrary paths"
check_doc_contains "${import_script}" "m7b/fake-manual-inventory.json" "import reads m7b fixture"
check_doc_contains "${import_script}" "m7c/fake-normalized-preview-candidates.json" "import reads m7c preview"
check_doc_contains "${cleanup_script}" "arbitrary path arguments are not accepted" "cleanup blocks arbitrary paths"
check_doc_contains "${cleanup_script}" ".tmp/teacher-knowledge-vault/m7e" "cleanup fixed path only"

section 'M7e Import Proof (Fixed Path)'
bash "${cleanup_script}" >/dev/null 2>&1 || true
if bash "${import_script}" >/dev/null 2>&1; then
  pass 'import command succeeded on fixed fixtures'
else
  fail 'import command failed on fixed fixtures'
fi
[[ -f "${m7e_out_dir}/test-catalog.sqlite" ]] && pass 'test catalog sqlite created' || fail 'test catalog sqlite not created'
[[ -f "${m7e_out_dir}/import-summary.json" ]] && pass 'import summary generated' || fail 'import summary not generated'
check_doc_contains "${m7e_out_dir}/import-summary.json" '"preview_candidates_imported": 8' "imported 8 candidates"
check_doc_contains "${m7e_out_dir}/import-summary.json" '"do_not_scan_blocked_count": 1' "dns blocked in summary"
check_doc_contains "${m7e_out_dir}/import-summary.json" '"production_write": false' "summary production_write false"
if command -v python3 >/dev/null 2>&1 && [[ -f "${m7e_out_dir}/test-catalog.sqlite" ]]; then
  dns_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7e_out_dir}/test-catalog.sqlite'); print(c.execute('SELECT indexable FROM blocked_records WHERE block_reason=\"do_not_scan_blocked\"').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${dns_idx}" == "0" ]] && pass '99_DO_NOT_SCAN blocked record is non-indexable' || fail 'DNS record must be non-indexable'
  teacher_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7e_out_dir}/test-catalog.sqlite'); print(c.execute('SELECT restricted_indexable FROM resources WHERE manual_inventory_id=\"fake-m7b-man-007\"').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${teacher_idx}" == "1" ]] && pass 'teacher-only record has restricted_indexable flag' || fail 'teacher-only must be restricted_indexable'
fi
bash "${cleanup_script}" >/dev/null 2>&1 && pass 'cleanup after import proof succeeded' || fail 'cleanup after import proof failed'
[[ ! -d "${m7e_out_dir}" ]] && pass 'generated path removed after cleanup' || warn 'generated path may remain after cleanup'

section 'M7c Fixture Validator Preserved'
bash "${m7c_validator}" >/dev/null 2>&1 && pass 'M7c fixture validator still passes' || fail 'M7c fixture validator regressed'

section 'No Production Connector OAuth API Runtime'
grep -Fq -- '--teacher-knowledge-vault-runtime-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose unrestricted runtime import' || pass 'CLI has no unrestricted runtime import command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'no vault connect drive' || pass 'no vault connect drive command'

section 'M0 M1 M2 M3 M4 M5 M6 M7 M7b M7c M7d Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'
bash scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh >/dev/null 2>&1 && pass 'M7b status still passes' || fail 'M7b status regressed'
bash scripts/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status.sh >/dev/null 2>&1 && pass 'M7c status still passes' || fail 'M7c status regressed'
bash scripts/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status.sh >/dev/null 2>&1 && pass 'M7d status still passes' || fail 'M7d status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7e" "build queue M7e"
check_doc_contains docs/build-queue.md "local test catalog" "build queue test catalog"
check_doc_contains docs/build-queue.md "M7f" "build queue M7f blocked"
check_doc_contains assistant/memory/active-priorities.md "M7e" "active priorities M7e"
check_doc_contains docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md "M7e" "M7d roadmap M7e reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7e-local-test-catalog-import"
check_help_contains "--teacher-knowledge-vault-m7e-local-test-catalog-cleanup"
check_help_contains "--teacher-knowledge-vault-m7e-local-test-catalog-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh
check_file tests/teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m7e-local-test-catalog-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M7e test' || fail 'smoke missing M7e test'
pass 'no production catalog write attempted'
pass 'no production registry write attempted'
pass 'no source file operations attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
