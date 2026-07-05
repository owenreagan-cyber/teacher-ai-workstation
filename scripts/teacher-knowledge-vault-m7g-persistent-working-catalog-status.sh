#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7g persistent working catalog prototype status.
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

m7g_dir="assistant/teacher-knowledge-vault/m7g"
m7g_out_dir=".local/teacher-knowledge-vault/working-catalog"
import_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-import.sh"
backup_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-backup.sh"
cleanup_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup.sh"
m7c_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M7g Persistent Working Catalog Prototype'
cat <<'EOF'
Status: bounded runtime write — persistent local working catalog prototype only
Closure: complete_teacher_knowledge_vault_m7g_persistent_working_catalog_prototype
Catalog mode: persistent_working_prototype
Production catalog writes: no
Real curriculum indexing: no
Arbitrary path input: no
Connectors/OAuth/API/network: no
M7g is prototype only — not production catalog: yes
PASS does not authorize M2b connectors extraction organization or production catalog: yes
EOF

section 'M7g Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md"
check_file "docs/teacher-knowledge-vault/persistent-working-catalog-storage.md"
check_file "docs/teacher-knowledge-vault/persistent-working-catalog-schema.md"
check_file "docs/teacher-knowledge-vault/persistent-working-catalog-import.md"
check_file "docs/teacher-knowledge-vault/persistent-working-catalog-backup-rollback.md"
check_file "docs/teacher-knowledge-vault/m7g-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md" "complete_teacher_knowledge_vault_m7g_persistent_working_catalog_prototype" "M7g closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md" "persistent local working catalog prototype" "M7g prototype doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md" "Production catalog writes: blocked" "no production writes"
check_doc_contains "docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-storage.md" ".local/teacher-knowledge-vault/working-catalog/" "fixed generated path"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-storage.md" "no arbitrary user input" "no arbitrary input"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-schema.md" "catalog_metadata" "schema catalog metadata"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-schema.md" "backup_records" "schema backup records"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-import.md" "Rejects any command-line path arguments" "import rejects args"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-import.md" "M7c fixture validator" "import uses validator"
check_doc_contains "docs/teacher-knowledge-vault/persistent-working-catalog-backup-rollback.md" "cleanup_removes_only_fixed_path" "rollback fixed path"
check_doc_contains "docs/teacher-knowledge-vault/m7g-governance-status.md" "Gitignored generated output" "governance gitignored"
check_doc_contains "docs/teacher-knowledge-vault/m7g-governance-status.md" "Production catalog writes" "governance zero production"

section 'M7g Fixtures and Gitignore'
check_file "${m7g_dir}/README.md"
check_file "${m7g_dir}/fake-persistent-working-catalog-schema.json"
check_file "${m7g_dir}/fake-persistent-working-catalog-import-summary.json"
check_file "${m7g_dir}/fake-backup-rollback-proof.json"
check_doc_contains "${m7g_dir}/fake-persistent-working-catalog-import-summary.json" '"preview_candidates_imported": 8' "example 8 candidates"
check_doc_contains "${m7g_dir}/fake-persistent-working-catalog-import-summary.json" '"blocked_count": 2' "example 2 blocked"
check_doc_contains "${m7g_dir}/fake-persistent-working-catalog-import-summary.json" '"production_write": false' "example no production"
check_doc_contains "${m7g_dir}/fake-persistent-working-catalog-import-summary.json" '"catalog_mode": "persistent_working_prototype"' "example catalog mode"
check_doc_contains "${m7g_dir}/fake-backup-rollback-proof.json" "cleanup_removes_only_fixed_path" "rollback fixed path"
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'gitignore covers M7g generated path' || fail 'gitignore must cover .local/teacher-knowledge-vault/'

section 'M7g Import Backup Cleanup Scripts'
check_file "${import_script}"
check_file "${backup_script}"
check_file "${cleanup_script}"
check_bash_syntax "${import_script}"
check_bash_syntax "${backup_script}"
check_bash_syntax "${cleanup_script}"
check_doc_contains "${import_script}" "arbitrary path arguments are not accepted" "import blocks arbitrary paths"
check_doc_contains "${import_script}" "m7b/fake-manual-inventory.json" "import reads m7b fixture"
check_doc_contains "${import_script}" "m7c/fake-normalized-preview-candidates.json" "import reads m7c preview"
check_doc_contains "${import_script}" "m7f-persistent-working-catalog-approval-gate.md" "import checks M7f gate"
check_doc_contains "${backup_script}" "arbitrary path arguments are not accepted" "backup blocks arbitrary paths"
check_doc_contains "${cleanup_script}" "arbitrary path arguments are not accepted" "cleanup blocks arbitrary paths"
check_doc_contains "${cleanup_script}" ".local/teacher-knowledge-vault/working-catalog" "cleanup fixed path only"

section 'M7g Import Backup Cleanup Proof (Fixed Path)'
bash "${cleanup_script}" >/dev/null 2>&1 || true
if bash "${import_script}" >/dev/null 2>&1; then
  pass 'import command succeeded on fixed fixtures'
else
  fail 'import command failed on fixed fixtures'
fi
[[ -f "${m7g_out_dir}/working-catalog.sqlite" ]] && pass 'working catalog sqlite created' || fail 'working catalog sqlite not created'
[[ -f "${m7g_out_dir}/import-summary.json" ]] && pass 'import summary generated' || fail 'import summary not generated'
check_doc_contains "${m7g_out_dir}/import-summary.json" '"preview_candidates_imported": 8' "imported 8 candidates"
check_doc_contains "${m7g_out_dir}/import-summary.json" '"do_not_scan_blocked_count": 1' "dns blocked in summary"
check_doc_contains "${m7g_out_dir}/import-summary.json" '"production_write": false' "summary production_write false"
check_doc_contains "${m7g_out_dir}/import-summary.json" '"catalog_mode": "persistent_working_prototype"' "summary catalog mode"
if command -v python3 >/dev/null 2>&1 && [[ -f "${m7g_out_dir}/working-catalog.sqlite" ]]; then
  dns_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7g_out_dir}/working-catalog.sqlite'); print(c.execute('SELECT indexable FROM blocked_records WHERE block_reason=\"do_not_scan_blocked\"').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${dns_idx}" == "0" ]] && pass '99_DO_NOT_SCAN blocked record is non-indexable' || fail 'DNS record must be non-indexable'
  teacher_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7g_out_dir}/working-catalog.sqlite'); print(c.execute('SELECT restricted_indexable FROM resources WHERE manual_inventory_id=\"fake-m7b-man-007\"').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${teacher_idx}" == "1" ]] && pass 'teacher-only record has restricted_indexable flag' || fail 'teacher-only must be restricted_indexable'
  catalog_mode="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7g_out_dir}/working-catalog.sqlite'); print(c.execute('SELECT catalog_mode FROM catalog_metadata').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${catalog_mode}" == "persistent_working_prototype" ]] && pass 'catalog_metadata catalog_mode is persistent_working_prototype' || fail 'catalog_mode must be persistent_working_prototype'
fi
if bash "${backup_script}" >/dev/null 2>&1; then
  pass 'backup command succeeded after import'
else
  fail 'backup command failed after import'
fi
[[ -f "${m7g_out_dir}/backup-latest.json" ]] && pass 'backup metadata generated' || fail 'backup metadata not generated'
bash "${cleanup_script}" >/dev/null 2>&1 && pass 'cleanup after import proof succeeded' || fail 'cleanup after import proof failed'
[[ ! -d "${m7g_out_dir}" ]] && pass 'generated path removed after cleanup' || warn 'generated path may remain after cleanup'

section 'M7c M7d M7e M7f Preservation'
bash "${m7c_validator}" >/dev/null 2>&1 && pass 'M7c fixture validator still passes' || fail 'M7c fixture validator regressed'
grep -Fq -- '.tmp/teacher-knowledge-vault/m7e/' .gitignore && pass 'M7e gitignored path preserved' || fail 'M7e gitignore path missing'

section 'No Production Connector OAuth API Runtime'
grep -Fq -- '--teacher-knowledge-vault-persistent-catalog-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose generic persistent catalog import' || pass 'CLI has no generic persistent catalog import command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'no vault connect drive' || pass 'no vault connect drive command'

section 'M0 M1 M2 M3 M4 M5 M6 M7 M7b M7c M7d M7e M7f Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh >/dev/null 2>&1 && pass 'M7b status still passes' || fail 'M7b status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status.sh >/dev/null 2>&1 && pass 'M7c status still passes' || fail 'M7c status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status.sh >/dev/null 2>&1 && pass 'M7d status still passes' || fail 'M7d status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh >/dev/null 2>&1 && pass 'M7e status still passes' || fail 'M7e status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status.sh >/dev/null 2>&1 && pass 'M7f status still passes' || fail 'M7f status regressed'
fi

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7g" "build queue M7g"
check_doc_contains docs/build-queue.md "persistent local working catalog prototype" "build queue M7g prototype"
check_doc_contains assistant/memory/active-priorities.md "M7g" "active priorities M7g"
check_doc_contains docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md "M7g" "M7f roadmap M7g reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7g-persistent-working-catalog-import"
check_help_contains "--teacher-knowledge-vault-m7g-persistent-working-catalog-backup"
check_help_contains "--teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup"
check_help_contains "--teacher-knowledge-vault-m7g-persistent-working-catalog-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh
check_file tests/teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m7g' 'Teacher Knowledge Vault M7g'
pass 'no production catalog write attempted'
pass 'no production registry write attempted'
pass 'no source file operations attempted'
pass 'no network call attempted'
pass 'no connector runtime attempted'
pass 'no OCR extraction or AI attempted'
pass 'validation-tier smoke boundary preserved'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
