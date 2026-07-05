#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7g persistent working catalog import.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7g persistent working catalog import tests..."

import_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-import.sh"
backup_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-backup.sh"
cleanup_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup.sh"
m7g_out=".local/teacher-knowledge-vault/working-catalog"

bash "${cleanup_script}" >/dev/null 2>&1 || true

if bash "${import_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: import must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: import rejects arbitrary path arguments"

if bash "${backup_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: backup must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: backup rejects arbitrary path arguments"

if bash "${cleanup_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: cleanup must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: cleanup rejects arbitrary path arguments"

bash "${cleanup_script}" >/dev/null 2>&1 || true
tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7g-import.XXXXXX")"
bash "${import_script}" >"${tmp}" 2>&1 || { echo "FAIL: import exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: import reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

[[ -f "${m7g_out}/working-catalog.sqlite" ]] || { echo "FAIL: working catalog sqlite missing"; exit 1; }
[[ -f "${m7g_out}/import-summary.json" ]] || { echo "FAIL: import summary missing"; exit 1; }

grep -Fq -- '"preview_candidates_imported": 8' "${m7g_out}/import-summary.json" || { echo "FAIL: expected 8 preview candidates imported"; exit 1; }
grep -Fq -- '"blocked_count": 2' "${m7g_out}/import-summary.json" || { echo "FAIL: expected 2 blocked records"; exit 1; }
grep -Fq -- '"production_write": false' "${m7g_out}/import-summary.json" || { echo "FAIL: production_write must be false"; exit 1; }
grep -Fq -- '"catalog_mode": "persistent_working_prototype"' "${m7g_out}/import-summary.json" || { echo "FAIL: catalog_mode must be persistent_working_prototype"; exit 1; }

grep -Fq -- '.local/teacher-knowledge-vault/working-catalog/' .gitignore || { echo "FAIL: generated path must be gitignored"; exit 1; }
echo "PASS: generated path is gitignored"

if command -v python3 >/dev/null 2>&1; then
  python3 - "${m7g_out}/working-catalog.sqlite" <<'PY' || { echo "FAIL: sqlite catalog checks failed"; exit 1; }
import sqlite3, sys
db = sys.argv[1]
c = sqlite3.connect(db)
assert c.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0] == 1
assert c.execute("SELECT catalog_mode FROM catalog_metadata").fetchone()[0] == "persistent_working_prototype"
assert c.execute("SELECT production_catalog FROM catalog_metadata").fetchone()[0] == 0
assert c.execute("SELECT indexable FROM blocked_records WHERE block_reason='do_not_scan_blocked'").fetchone()[0] == 0
assert c.execute("SELECT restricted_indexable FROM resources WHERE manual_inventory_id='fake-m7b-man-007'").fetchone()[0] == 1
assert c.execute("SELECT production_write FROM import_batches").fetchone()[0] == 0
print("PASS: sqlite catalog schema and policy checks")
PY
fi

bash "${backup_script}" >/dev/null 2>&1 || { echo "FAIL: backup exited nonzero"; exit 1; }
[[ -f "${m7g_out}/backup-latest.json" ]] || { echo "FAIL: backup metadata missing"; exit 1; }
echo "PASS: backup command succeeded"

bash "${cleanup_script}" >/dev/null 2>&1 || { echo "FAIL: cleanup exited nonzero"; exit 1; }
[[ ! -d "${m7g_out}" ]] || { echo "FAIL: generated path should be removed after cleanup"; exit 1; }

echo "PASS: Teacher Knowledge Vault M7g persistent working catalog import tests complete"
