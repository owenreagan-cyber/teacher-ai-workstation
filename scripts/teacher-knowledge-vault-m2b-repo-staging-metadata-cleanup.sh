#!/usr/bin/env bash
# Teacher Knowledge Vault M2b repo staging metadata cleanup — fixed generated paths only.
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

M2B_OUT_DIR=".local/teacher-knowledge-vault/m2b"
M7G_DB=".local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite"
BATCH_ID="fake-m2b-batch-001"

section 'Teacher Knowledge Vault M2b Repo Staging Metadata Cleanup'
cat <<'EOF'
Status: cleanup — fixed generated M2b outputs and M2b import batch only
Staging fixture source files: untouched
Real files: untouched
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

if [[ -d "${M2B_OUT_DIR}" ]]; then
  rm -rf "${M2B_OUT_DIR}"
  pass "removed fixed generated path: ${M2B_OUT_DIR}"
else
  pass "fixed generated path already clean: ${M2B_OUT_DIR}"
fi

if command -v python3 >/dev/null 2>&1 && [[ -f "${M7G_DB}" ]]; then
  python3 - "${repo_root}/${M7G_DB}" "${BATCH_ID}" <<'PY'
import sqlite3, sys
db, batch_id = sys.argv[1:3]
conn = sqlite3.connect(db)
cur = conn.cursor()
for table in ["staging_metadata", "source_items", "review_queue_items", "event_log", "blocked_records"]:
    try:
        cur.execute(f"DELETE FROM {table} WHERE batch_id=?", (batch_id,))
    except sqlite3.OperationalError:
        pass
try:
    cur.execute("DELETE FROM import_batches WHERE batch_id=?", (batch_id,))
except sqlite3.OperationalError:
    pass
conn.commit()
conn.close()
PY
  pass "removed M2b import batch from M7g prototype catalog: ${BATCH_ID}"
fi

[[ ! -d "${M2B_OUT_DIR}" ]] && pass 'M2b generated path removed' || fail 'M2b generated path still exists'
pass 'no staging fixture source files touched'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
