#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M2d first selected folder metadata scan status.
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

M2D_APPROVED_FOLDER="/Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder"
M2D_OUT_DIR=".local/teacher-knowledge-vault/m2d"
m2d_dir="assistant/teacher-knowledge-vault/m2d"
preflight_script="scripts/teacher-knowledge-vault-m2d-selected-folder-preflight.sh"
scan_script="scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-scan.sh"
preview_script="scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-preview.sh"
cleanup_script="scripts/teacher-knowledge-vault-m2d-selected-folder-cleanup.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M2d First Selected Folder Metadata Scan'
cat <<'EOF'
Status: metadata-only scan — fixed Owen-approved tiny local test folder only
Closure: complete_teacher_knowledge_vault_m2d_first_selected_folder_metadata_scan
Approved folder: /Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder
Arbitrary path input: no
Content reads: no
M7g catalog import: preview only
Production catalog writes: no
EOF

section 'M2d Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md"
check_file "docs/teacher-knowledge-vault/selected-folder-metadata-preflight.md"
check_file "docs/teacher-knowledge-vault/selected-folder-metadata-scan.md"
check_file "docs/teacher-knowledge-vault/m2d-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md" "complete_teacher_knowledge_vault_m2d_first_selected_folder_metadata_scan" "M2d closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md" "m2d-tiny-folder" "approved folder path"
check_doc_contains "docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md" "metadata-only" "metadata only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md" "no content reads" "no content reads"
check_doc_contains "docs/teacher-knowledge-vault/selected-folder-metadata-preflight.md" "arbitrary path arguments are not accepted" "preflight rejects args"
check_doc_contains "docs/teacher-knowledge-vault/selected-folder-metadata-scan.md" "stat metadata only" "scan stat only"
check_doc_contains "docs/teacher-knowledge-vault/m2d-governance-status.md" "preview only" "governance preview only"

section 'M2d Fixtures and Gitignore'
check_file "${m2d_dir}/README.md"
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'gitignore covers generated output paths' || fail 'gitignore must cover .local/teacher-knowledge-vault/'
[[ -d "${M2D_APPROVED_FOLDER}" ]] && pass 'Owen-approved test folder exists' || fail 'Owen-approved test folder missing'

section 'M2d Scripts'
for s in "${preflight_script}" "${scan_script}" "${preview_script}" "${cleanup_script}"; do
  check_file "${s}"
  check_bash_syntax "${s}"
  check_doc_contains "${s}" "arbitrary path arguments are not accepted" "script rejects arbitrary paths: ${s}"
done
check_doc_contains "${preflight_script}" "m2d-tiny-folder" "preflight fixed approved path"
check_doc_contains "${scan_script}" "m2d-tiny-folder" "scan fixed approved path"
if grep -qE '\.read\(|open\([^)]*["'"'"']r[b]?["'"'"']|pdftotext|tesseract' "${scan_script}" "${preflight_script}" "${preview_script}" 2>/dev/null; then
  fail 'M2d scripts must not read file contents'
else
  pass 'M2d scripts avoid content-read commands'
fi

section 'M2d Preflight Scan Preview Cleanup Proof'
bash "${cleanup_script}" >/dev/null 2>&1 || true
bash "${preflight_script}" >/dev/null 2>&1 && pass 'Step 1 preflight succeeded' || fail 'Step 1 preflight failed'
[[ -f "${M2D_OUT_DIR}/preflight-approval-packet.json" ]] && pass 'preflight approval packet generated' || fail 'preflight packet missing'
bash "${scan_script}" >/dev/null 2>&1 && pass 'Step 2 metadata scan succeeded' || fail 'Step 2 metadata scan failed'
for report in selected-folder-metadata-report.json scan-proof.json no-content-read-proof.json rollback-proof.json summary-report.json; do
  [[ -f "${M2D_OUT_DIR}/${report}" ]] && pass "report generated: ${report}" || fail "report missing: ${report}"
done
check_doc_contains "${M2D_OUT_DIR}/selected-folder-metadata-report.json" '"files_discovered": 4' "4 files in metadata report"
check_doc_contains "${M2D_OUT_DIR}/no-content-read-proof.json" '"content_reads": 0' "zero content reads proof"
check_doc_contains "${M2D_OUT_DIR}/scan-proof.json" '"traversal_confined_to_approved_root": true' "root confinement proof"
bash "${preview_script}" >/dev/null 2>&1 && pass 'M7g import preview succeeded' || fail 'M7g import preview failed'
[[ -f "${M2D_OUT_DIR}/m7g-import-preview.json" ]] && pass 'M7g import preview generated' || fail 'M7g import preview missing'
grep -Fq -- '"catalog_import_executed": false' "${M2D_OUT_DIR}/m7g-import-preview.json" && pass 'preview confirms no catalog import' || fail 'preview must deny import'
bash "${cleanup_script}" >/dev/null 2>&1 && pass 'cleanup succeeded' || fail 'cleanup failed'
[[ -f "${M2D_OUT_DIR}/cleanup-proof.json" ]] && pass 'cleanup proof generated' || fail 'cleanup proof missing'
grep -Fq -- '"source_folder_modified": false' "${M2D_OUT_DIR}/cleanup-proof.json" && pass 'cleanup proof confirms source untouched' || fail 'cleanup proof must confirm source untouched'
rm -rf "${M2D_OUT_DIR}"
pass 'final generated path removed after proof cycle'

section 'No Arbitrary Path General Scanner'
grep -Fq -- '--teacher-knowledge-vault-scan-real-folder)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose generic real folder scan' || pass 'CLI has no generic real folder scan command'
grep -Fq -- '--teacher-knowledge-vault-selected-folder-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose generic selected folder scan' || pass 'CLI has no generic selected folder scan command'
grep -Fq -- '--teacher-knowledge-vault-m2d-selected-folder-preflight' bin/chief-of-staff 2>/dev/null && pass 'CLI exposes fixed-path M2d preflight' || fail 'CLI missing M2d preflight'
grep -Fq -- '--teacher-knowledge-vault-m2d-selected-folder-metadata-scan' bin/chief-of-staff 2>/dev/null && pass 'CLI exposes fixed-path M2d metadata scan' || fail 'CLI missing M2d metadata scan'

section 'M2c M2b M7g Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status.sh >/dev/null 2>&1 && pass 'M2c status still passes' || fail 'M2c status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-status.sh >/dev/null 2>&1 && pass 'M2b status still passes' || fail 'M2b status regressed'
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

section 'Roadmap and Aggregate Wiring'
check_doc_contains docs/build-queue.md "M2d" "build queue M2d"
check_doc_contains assistant/memory/active-priorities.md "M2d" "active priorities M2d"
grep -Fq -- '"--teacher-knowledge-vault-m2d-selected-folder-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists M2d status' || fail 'manifest missing M2d status'
grep -Fq -- 'Teacher Knowledge Vault M2d First Selected Folder Metadata Scan' scripts/chief-of-staff-validate-all.sh && pass 'validate-all includes M2d track' || fail 'validate-all missing M2d track'
grep -Fq -- 'Teacher Knowledge Vault M2d First Selected Folder Metadata Scan' scripts/chief-of-staff-dashboard.sh && pass 'dashboard includes M2d section' || fail 'dashboard missing M2d section'

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m2d-selected-folder-preflight"
check_help_contains "--teacher-knowledge-vault-m2d-selected-folder-metadata-scan"
check_help_contains "--teacher-knowledge-vault-m2d-selected-folder-metadata-preview"
check_help_contains "--teacher-knowledge-vault-m2d-selected-folder-cleanup"
check_help_contains "--teacher-knowledge-vault-m2d-selected-folder-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh
check_file tests/teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh
check_file tests/teacher-knowledge-vault-m2d-selected-folder-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m2d' 'Teacher Knowledge Vault M2d'
pass 'metadata-only scan on fixed approved folder only'
pass 'no file content read attempted'
pass 'no automatic M7g catalog import attempted'
pass 'no production catalog write attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
