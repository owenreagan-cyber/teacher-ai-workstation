#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M2c selected local folder metadata scan approval gate status.
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
  if grep -rqiE 'https?://' "${dir}" --include='*.json' 2>/dev/null; then
    fail "fixtures must not contain http(s) URLs: ${dir}"
  else
    pass "fixtures exclude URLs: ${dir}"
  fi
}
check_no_real_paths_in_fixtures() {
  local dir="$1"
  if grep -rE '/Users/|/home/|\\\\Users\\\\|C:\\\\' "${dir}" --include='*.json' 2>/dev/null; then
    fail "fixtures must not contain real local paths: ${dir}"
  else
    pass "fixtures exclude real local paths: ${dir}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m2c_dir="assistant/teacher-knowledge-vault/m2c"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M2c Selected Local Folder Metadata Scan Approval Gate'
cat <<'EOF'
Status: approval gate only — no real folder scan implementation
Closure: complete_teacher_knowledge_vault_m2c_selected_local_folder_approval_gate
M2b repo-owned fixture scan: preserved
Real folder scans executed: 0
Real-folder metadata imports: 0
Content reads: 0
Production catalog writes: 0
OAuth/API/network execution: no
api_cost_estimate_usd: 0.00
PASS does not authorize real folder scanning or M2d runtime: yes
M2c approval gate is not selected-folder scan runtime: yes
Future M2d remains blocked pending explicit Owen approval: yes
EOF

section 'M2c Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md"
check_file "docs/teacher-knowledge-vault/selected-local-folder-path-policy.md"
check_file "docs/teacher-knowledge-vault/selected-local-folder-preflight.md"
check_file "docs/teacher-knowledge-vault/selected-local-folder-approval-packet.md"
check_file "docs/teacher-knowledge-vault/selected-local-folder-denial-rules.md"
check_file "docs/teacher-knowledge-vault/m2c-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md" "complete_teacher_knowledge_vault_m2c_selected_local_folder_approval_gate" "M2c closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md" "approval gate only" "M2c gate doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md" "does not scan real folders" "no real folder scan"
check_doc_contains "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md" "M2d" "M2d future reference"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-path-policy.md" "Desktop" "desktop blocked"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-path-policy.md" "Google Drive" "drive blocked"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-preflight.md" "max file count" "preflight file count"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-preflight.md" "no symlink traversal" "symlink policy"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-preflight.md" "no package/archive expansion" "no archive expansion"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-approval-packet.md" "owen_approval" "owen approval field"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-approval-packet.md" "catalog_import_blocked_until_second_approval" "second approval required"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-denial-rules.md" "student-data-likely" "student data denial"
check_doc_contains "docs/teacher-knowledge-vault/selected-local-folder-denial-rules.md" "file content reads" "content read denial"
check_doc_contains "docs/teacher-knowledge-vault/m2c-governance-status.md" "Approval gate only" "governance gate only"
check_doc_contains "docs/teacher-knowledge-vault/m2c-governance-status.md" "Future M2d" "governance M2d blocked"

section 'M2c Fake Approval Gate Fixtures'
check_file "${m2c_dir}/README.md"
check_file "${m2c_dir}/fake-selected-folder-approval-packet.json"
check_file "${m2c_dir}/fake-path-preflight-denials.json"
check_file "${m2c_dir}/fake-safe-test-folder-preflight.json"
check_file "${m2c_dir}/fake-risk-register.json"
check_file "${m2c_dir}/fake-review-queue-items.json"
check_file "${m2c_dir}/fake-event-log.json"
check_file "${m2c_dir}/fake-observability-metrics.json"
check_doc_contains "${m2c_dir}/fake-selected-folder-approval-packet.json" '"owen_approval": false' "packet owen approval false"
check_doc_contains "${m2c_dir}/fake-selected-folder-approval-packet.json" '"real_folder_scan_executed": false' "packet no real scan"
check_doc_contains "${m2c_dir}/fake-selected-folder-approval-packet.json" '"catalog_import_blocked_until_second_approval": true' "import blocked until second approval"
check_doc_contains "${m2c_dir}/fake-selected-folder-approval-packet.json" "LOCAL_TEST_FOLDER_PLACEHOLDER" "placeholder path only"
check_doc_contains "${m2c_dir}/fake-path-preflight-denials.json" "home_directory" "denial home directory"
check_doc_contains "${m2c_dir}/fake-path-preflight-denials.json" "google_drive" "denial google drive"
check_doc_contains "${m2c_dir}/fake-path-preflight-denials.json" "99_DO_NOT_SCAN" "denial do not scan"
check_doc_contains "${m2c_dir}/fake-safe-test-folder-preflight.json" '"content_reads_allowed": false' "preflight no content reads"
check_doc_contains "${m2c_dir}/fake-safe-test-folder-preflight.json" '"owen_second_approval_required": true' "preflight second approval"
check_doc_contains "${m2c_dir}/fake-risk-register.json" "student_data_exposure" "risk student data"
check_doc_contains "${m2c_dir}/fake-review-queue-items.json" '"owen_approval": false' "review owen approval false"
check_doc_contains "${m2c_dir}/fake-event-log.json" "real_folder_scan_requested_but_blocked" "event scan blocked"
check_doc_contains "${m2c_dir}/fake-event-log.json" "m2d_runtime_blocked_pending_owen_approval" "event m2d blocked"
check_doc_contains "${m2c_dir}/fake-observability-metrics.json" '"real_scans_executed": 0' "metrics zero real scans"
check_doc_contains "${m2c_dir}/fake-observability-metrics.json" '"paths_approved": 0' "metrics zero paths approved"
check_doc_contains "${m2c_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": "0.00"' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m2c_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m2c_dir}"
check_no_real_paths_in_fixtures "${m2c_dir}"

section 'M2b and M7g Preserved'
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'M7g gitignored path preserved' || fail 'M7g gitignore path missing'
check_file "assistant/teacher-knowledge-vault/m2b/fake-staging-folder/99_DO_NOT_SCAN/fake_private_placeholder.pdf"
check_file scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery.sh

section 'No Real Folder Scan Import Connector Runtime'
grep -Fq -- '--teacher-knowledge-vault-m2d-' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose M2d runtime commands in M2c gate' || pass 'CLI has no M2d runtime commands'
grep -Fq -- '--teacher-knowledge-vault-scan-real-folder)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose real folder scan' || pass 'CLI has no real folder scan command'
grep -Fq -- '--teacher-knowledge-vault-selected-folder-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose selected folder scan' || pass 'CLI has no selected folder scan command'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan command'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'no vault connect drive' || pass 'no vault connect drive command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
m2c_runtime_scripts=()
for candidate in scripts/teacher-knowledge-vault-m2c-*; do
  [[ -f "${candidate}" && "${candidate}" != *-status.sh ]] && m2c_runtime_scripts+=("${candidate}")
done
if ((${#m2c_runtime_scripts[@]} > 0)); then
  if grep -qE 'os\.walk|readdir|find /|stat /Users' "${m2c_runtime_scripts[@]}" 2>/dev/null; then
    fail 'M2c runtime scripts must not contain real folder scanning patterns'
  else
    pass 'M2c runtime scripts exclude dangerous scanning patterns'
  fi
  if grep -qE '\.read\(|open\([^)]*["'"'"']r[b]?["'"'"']|pdftotext|tesseract' "${m2c_runtime_scripts[@]}" 2>/dev/null; then
    fail 'M2c runtime scripts must not contain content-read or OCR patterns'
  else
    pass 'M2c runtime scripts exclude content-read/OCR patterns'
  fi
else
  pass 'M2c has no runtime scripts beyond approval gate status'
  pass 'M2c excludes dangerous scanning patterns (no runtime scripts)'
  pass 'M2c excludes content-read/OCR patterns (no runtime scripts)'
fi

section 'M0 M1 M2 M2b M7g Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
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

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M2c" "build queue M2c"
check_doc_contains docs/build-queue.md "approval gate" "build queue approval gate"
check_doc_contains docs/build-queue.md "M2d" "build queue M2d blocked"
check_doc_contains assistant/memory/active-priorities.md "M2c" "active priorities M2c"
check_doc_contains docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md "M2c" "M2b roadmap M2c reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status"
check_help_contains "--teacher-knowledge-vault-m2b-repo-staging-metadata-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m2c' 'Teacher Knowledge Vault M2c'
pass 'no real folder scan attempted'
pass 'no real-folder metadata import attempted'
pass 'no production catalog write attempted'
pass 'no production registry write attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no content read attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
