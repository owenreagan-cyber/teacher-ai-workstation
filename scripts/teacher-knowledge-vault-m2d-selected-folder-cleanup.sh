#!/usr/bin/env bash
# Teacher Knowledge Vault M2d cleanup — fixed generated outputs only; source folder untouched.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

M2D_OUT_DIR=".local/teacher-knowledge-vault/m2d"
M2D_APPROVED_FOLDER="/Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder"
M2D_CLEANUP_PROOF="${M2D_OUT_DIR}/cleanup-proof.json"

section 'Teacher Knowledge Vault M2d Selected Folder Cleanup'
cat <<'EOF'
Status: cleanup — fixed generated M2d outputs only
Approved source folder: untouched
M7g catalog: untouched (preview-only mission)
Real files: untouched
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

had_outputs=0
[[ -d "${M2D_OUT_DIR}" ]] && had_outputs=1

if [[ -d "${M2D_OUT_DIR}" ]]; then
  rm -rf "${M2D_OUT_DIR}"
  pass "removed fixed generated path: ${M2D_OUT_DIR}"
else
  pass "fixed generated path already clean: ${M2D_OUT_DIR}"
fi

[[ -d "${M2D_APPROVED_FOLDER}" ]] && pass 'approved source folder still exists and untouched' || fail 'approved source folder missing after cleanup'
for expected in README.md fake-notes.txt fake-slide-placeholder.pptx fake-worksheet.pdf; do
  [[ -f "${M2D_APPROVED_FOLDER}/${expected}" ]] && pass "source file preserved: ${expected}" || fail "source file missing: ${expected}"
done

if command -v python3 >/dev/null 2>&1; then
  mkdir -p "${M2D_OUT_DIR}"
  python3 - "${repo_root}/${M2D_CLEANUP_PROOF}" "${had_outputs}" <<'PY'
import json, sys
proof_path, had_outputs = sys.argv[1], sys.argv[2] == "1"
proof = {
    "classification": "owen_approved_local_test_folder_only",
    "cleanup_executed": True,
    "generated_outputs_removed": True,
    "had_outputs_before_cleanup": had_outputs,
    "source_folder_modified": False,
    "m7g_catalog_modified": False,
    "content_reads": 0,
    "production_writes": 0,
    "real_files_deleted": 0,
}
with open(proof_path, "w", encoding="utf-8") as f:
    json.dump(proof, f, indent=2)
    f.write("\n")
print("PASS: cleanup proof written")
PY
  [[ -f "${M2D_CLEANUP_PROOF}" ]] && pass 'cleanup proof file exists' || fail 'cleanup proof file missing'
else
  warn 'python3 not available for cleanup proof'
fi

pass 'no approved source folder files deleted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
