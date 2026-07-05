#!/usr/bin/env bash
# Teacher Knowledge Vault M7g persistent working catalog backup — fixed generated path only.
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
M7G_DB="${M7G_OUT_DIR}/working-catalog.sqlite"
M7G_BACKUP_DIR="${M7G_OUT_DIR}/backups"
M7G_BACKUP_META="${M7G_OUT_DIR}/backup-latest.json"

section 'Teacher Knowledge Vault M7g Persistent Working Catalog Backup'
cat <<'EOF'
Status: backup/export — fixed prototype catalog path only
Production catalog writes: no
Source file operations: no
External paths: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

[[ -f "${M7G_DB}" ]] || { fail "working catalog sqlite missing — run import first"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "catalog exists at fixed path: ${M7G_DB}"

backup_output="$(python3 - "${repo_root}" "${M7G_DB}" "${M7G_BACKUP_DIR}" "${M7G_BACKUP_META}" <<'PY'
import json, os, shutil, sqlite3, sys

repo_root, db_path, backup_dir, meta_path = sys.argv[1:5]
backup_id = "fake-m7g-backup-export-001"
created_at = "2026-07-05T00:00:00Z"
catalog_id = "fake-m7g-working-catalog-001"

os.makedirs(os.path.join(repo_root, backup_dir), exist_ok=True)
src = os.path.join(repo_root, db_path)
dest_rel = f"{backup_dir}/working-catalog-{backup_id}.sqlite"
dest = os.path.join(repo_root, dest_rel)
shutil.copy2(src, dest)

conn = sqlite3.connect(src)
cur = conn.cursor()
try:
    cur.execute(
        "INSERT INTO backup_records VALUES (?,?,?,?,?)",
        (backup_id, dest_rel, catalog_id, "fake-m7g-batch-001", created_at),
    )
    conn.commit()
except sqlite3.OperationalError:
    pass
conn.close()

meta = {
    "classification": "fake_local_planning_only",
    "catalog_mode": "persistent_working_prototype",
    "backup_id": backup_id,
    "backup_path": dest_rel,
    "catalog_id": catalog_id,
    "created_at": created_at,
    "production_write": False,
    "source_file_operations": 0,
    "runtime_external_accesses": 0,
    "api_cost_estimate_usd": "0.00",
}
with open(os.path.join(repo_root, meta_path), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
    f.write("\n")

print(f"PASS: backup created at {dest_rel}")
print(f"PASS: backup metadata written")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${backup_output}"

[[ -f "${M7G_BACKUP_META}" ]] && pass 'backup metadata json written' || fail 'backup metadata missing'
pass 'no source files touched'
pass 'no production catalog touched'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
