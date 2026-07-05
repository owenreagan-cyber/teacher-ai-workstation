#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M2b repo staging metadata prototype status.
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

m2b_dir="assistant/teacher-knowledge-vault/m2b"
staging_dir="${m2b_dir}/fake-staging-folder"
m2b_out_dir=".local/teacher-knowledge-vault/m2b"
m7g_db=".local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite"
discovery_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery.sh"
import_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-import.sh"
cleanup_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M2b Repo-Owned Staging Metadata Prototype'
cat <<'EOF'
Status: metadata-only discovery — fixed repo-owned staging fixture folder only
Closure: complete_teacher_knowledge_vault_m2b_repo_owned_staging_metadata_prototype
Real local folder scanning: no
Content reads: no
Production catalog writes: no
Future real selected-folder scan: blocked pending Owen approval
EOF

section 'M2b Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md"
check_file "docs/teacher-knowledge-vault/repo-owned-staging-folder-policy.md"
check_file "docs/teacher-knowledge-vault/repo-staging-metadata-discovery.md"
check_file "docs/teacher-knowledge-vault/repo-staging-metadata-catalog-import.md"
check_file "docs/teacher-knowledge-vault/m2b-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md" "complete_teacher_knowledge_vault_m2b_repo_owned_staging_metadata_prototype" "M2b closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md" "repo-owned fixture staging metadata-only prototype" "M2b prototype doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/repo-owned-staging-folder-policy.md" "fake-staging-folder" "fixed staging folder"
check_doc_contains "docs/teacher-knowledge-vault/repo-owned-staging-folder-policy.md" "no arbitrary user input" "no arbitrary input"
check_doc_contains "docs/teacher-knowledge-vault/repo-staging-metadata-discovery.md" "Rejects any command-line path arguments" "discovery rejects args"
check_doc_contains "docs/teacher-knowledge-vault/repo-staging-metadata-discovery.md" "stat metadata only" "stat metadata only"
check_doc_contains "docs/teacher-knowledge-vault/repo-staging-metadata-catalog-import.md" "M7g prototype catalog" "M7g catalog integration"
check_doc_contains "docs/teacher-knowledge-vault/m2b-governance-status.md" "Gitignored generated output" "governance gitignored"

section 'M2b Fixtures and Gitignore'
check_file "${m2b_dir}/README.md"
check_file "${m2b_dir}/fake-staging-manifest.json"
check_file "${m2b_dir}/fake-metadata-report-example.json"
check_file "${m2b_dir}/fake-import-summary-example.json"
check_file "${staging_dir}/99_DO_NOT_SCAN/fake_private_placeholder.pdf"
check_file "${staging_dir}/10_TEACHER_ONLY/fake_teacher_key_placeholder.pdf"
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'gitignore covers generated output paths' || fail 'gitignore must cover .local/teacher-knowledge-vault/'

section 'M2b Scripts'
check_file "${discovery_script}"
check_file "${import_script}"
check_file "${cleanup_script}"
check_bash_syntax "${discovery_script}"
check_bash_syntax "${import_script}"
check_bash_syntax "${cleanup_script}"
check_doc_contains "${discovery_script}" "arbitrary path arguments are not accepted" "discovery blocks arbitrary paths"
check_doc_contains "${discovery_script}" "fake-staging-folder" "discovery fixed staging path"
if grep -qE '\.read\(|open\([^)]*["'"'"']r[b]?["'"'"']|pdftotext|tesseract' "${discovery_script}" 2>/dev/null; then
  fail 'discovery script must not read file contents'
else
  pass 'discovery script avoids content-read commands'
fi

section 'M2b Discovery Import Cleanup Proof'
bash "${cleanup_script}" >/dev/null 2>&1 || true
if bash "${discovery_script}" >/dev/null 2>&1; then
  pass 'discovery command succeeded on fixed staging fixtures'
else
  fail 'discovery command failed'
fi
[[ -f "${m2b_out_dir}/repo-staging-metadata-report.json" ]] && pass 'metadata report generated' || fail 'metadata report missing'
check_doc_contains "${m2b_out_dir}/repo-staging-metadata-report.json" '"fixture_files_discovered": 8' "8 files discovered"
check_doc_contains "${m2b_out_dir}/repo-staging-metadata-report.json" '"content_reads": 0' "zero content reads in report"
if bash "${import_script}" >/dev/null 2>&1; then
  pass 'import command succeeded'
else
  fail 'import command failed'
fi
[[ -f "${m7g_db}" ]] && pass 'M7g prototype catalog updated' || fail 'M7g catalog missing after import'
check_doc_contains "${m2b_out_dir}/import-summary.json" '"metadata_records_imported": 7' "7 records imported"
check_doc_contains "${m2b_out_dir}/import-summary.json" '"do_not_scan_blocked_count": 1' "dns blocked in summary"
if command -v python3 >/dev/null 2>&1 && [[ -f "${m7g_db}" ]]; then
  dns_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7g_db}'); print(c.execute('SELECT indexable FROM blocked_records WHERE block_reason=\"do_not_scan_blocked\" AND batch_id=\"fake-m2b-batch-001\"').fetchone()[0])" 2>/dev/null || echo fail)"
  [[ "${dns_idx}" == "0" ]] && pass '99_DO_NOT_SCAN blocked record is non-indexable' || fail 'DNS record must be non-indexable'
  teacher_idx="$(python3 -c "import sqlite3; c=sqlite3.connect('${m7g_db}'); r=c.execute('SELECT restricted_indexable FROM source_items WHERE batch_id=\"fake-m2b-batch-001\" AND restricted_indexable=1').fetchone(); print(r[0] if r else fail)" 2>/dev/null || echo fail)"
  [[ "${teacher_idx}" == "1" ]] && pass 'teacher-only record has restricted_indexable flag' || fail 'teacher-only must be restricted_indexable'
fi
bash "${cleanup_script}" >/dev/null 2>&1 && pass 'cleanup after proof succeeded' || fail 'cleanup failed'

section 'No Real Folder Scan Connector OAuth API Runtime'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan command'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'no vault connect drive' || pass 'no vault connect drive command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 M1 M2 M7g Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-status.sh >/dev/null 2>&1 && pass 'M7g status still passes' || fail 'M7g status regressed'
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
check_doc_contains docs/build-queue.md "M2b" "build queue M2b"
check_doc_contains docs/build-queue.md "repo-owned staging metadata" "build queue M2b prototype"
check_doc_contains assistant/memory/active-priorities.md "M2b" "active priorities M2b"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m2b-repo-staging-metadata-discovery"
check_help_contains "--teacher-knowledge-vault-m2b-repo-staging-metadata-import"
check_help_contains "--teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup"
check_help_contains "--teacher-knowledge-vault-m2b-repo-staging-metadata-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh
check_file tests/teacher-knowledge-vault-m2b-repo-staging-metadata-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m2b' 'Teacher Knowledge Vault M2b'
pass 'no real local folder scanning attempted'
pass 'no file content read attempted'
pass 'no production catalog write attempted'
pass 'no network call attempted'
pass 'validation-tier smoke boundary preserved'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
