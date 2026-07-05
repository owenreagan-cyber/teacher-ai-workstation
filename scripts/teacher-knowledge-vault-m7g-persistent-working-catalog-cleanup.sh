#!/usr/bin/env bash
# Teacher Knowledge Vault M7g persistent working catalog cleanup — fixed generated path only.
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

M7G_OUT_DIR=".local/teacher-knowledge-vault/working-catalog"
M7G_ROLLBACK_LOG=".local/teacher-knowledge-vault/working-catalog-rollback-log.json"

section 'Teacher Knowledge Vault M7g Persistent Working Catalog Cleanup'
cat <<'EOF'
Status: rollback/removal — fixed prototype catalog path only
Production catalog writes: no
Source file operations: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

rollback_id="fake-m7g-rollback-cleanup-001"
created_at="2026-07-05T00:00:00Z"

if [[ -d "${M7G_OUT_DIR}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 - "${repo_root}" "${M7G_ROLLBACK_LOG}" "${rollback_id}" "${created_at}" "${M7G_OUT_DIR}" <<'PY'
import json, os, sys
repo_root, log_path, rollback_id, created_at, out_dir = sys.argv[1:6]
record = {
    "classification": "fake_local_planning_only",
    "rollback_id": rollback_id,
    "import_batch_id": "fake-m7g-batch-001",
    "catalog_mode": "persistent_working_prototype",
    "removed_path": out_dir,
    "cleanup_removes_only_fixed_path": True,
    "no_source_file_deletion": True,
    "production_write": False,
    "created_at": created_at,
}
os.makedirs(os.path.dirname(os.path.join(repo_root, log_path)), exist_ok=True)
with open(os.path.join(repo_root, log_path), "w", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
PY
    pass "rollback record written: ${M7G_ROLLBACK_LOG}"
  fi
  rm -rf "${M7G_OUT_DIR}"
  pass "removed fixed generated path: ${M7G_OUT_DIR}"
else
  pass "fixed generated path already clean: ${M7G_OUT_DIR}"
fi

[[ ! -d "${M7G_OUT_DIR}" ]] && pass 'cleanup verified — generated path removed' || fail 'cleanup failed — path still exists'
pass 'no source files touched'
pass 'no production catalog touched'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
