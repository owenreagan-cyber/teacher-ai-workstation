#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7e local test catalog import.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7e local test catalog import tests..."

import_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-import.sh"
cleanup_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh"
m7e_out=".tmp/teacher-knowledge-vault/m7e"

bash "${cleanup_script}" >/dev/null 2>&1 || true

# Reject arbitrary paths
if bash "${import_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: import must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: import rejects arbitrary path arguments"

if bash "${cleanup_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: cleanup must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: cleanup rejects arbitrary path arguments"

# Import succeeds
bash "${cleanup_script}" >/dev/null 2>&1 || true
tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7e-import.XXXXXX")"
bash "${import_script}" >"${tmp}" 2>&1 || { echo "FAIL: import exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: import reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

[[ -f "${m7e_out}/test-catalog.sqlite" ]] || { echo "FAIL: test catalog sqlite missing"; exit 1; }
[[ -f "${m7e_out}/import-summary.json" ]] || { echo "FAIL: import summary missing"; exit 1; }

grep -Fq -- '"preview_candidates_imported": 8' "${m7e_out}/import-summary.json" || { echo "FAIL: expected 8 preview candidates imported"; exit 1; }
grep -Fq -- '"blocked_count": 2' "${m7e_out}/import-summary.json" || { echo "FAIL: expected 2 blocked records"; exit 1; }
grep -Fq -- '"production_write": false' "${m7e_out}/import-summary.json" || { echo "FAIL: production_write must be false"; exit 1; }

if command -v python3 >/dev/null 2>&1; then
  python3 - "${m7e_out}/test-catalog.sqlite" <<'PY' || { echo "FAIL: sqlite catalog checks failed"; exit 1; }
import sqlite3, sys
db = sys.argv[1]
c = sqlite3.connect(db)
assert c.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0] == 1
assert c.execute("SELECT indexable FROM blocked_records WHERE block_reason='do_not_scan_blocked'").fetchone()[0] == 0
assert c.execute("SELECT restricted_indexable FROM resources WHERE manual_inventory_id='fake-m7b-man-007'").fetchone()[0] == 1
assert c.execute("SELECT production_write FROM import_batches").fetchone()[0] == 0
print("PASS: sqlite catalog schema and policy checks")
PY
fi

# Cleanup succeeds
bash "${cleanup_script}" >/dev/null 2>&1 || { echo "FAIL: cleanup exited nonzero"; exit 1; }
[[ ! -d "${m7e_out}" ]] || { echo "FAIL: generated path should be removed after cleanup"; exit 1; }

echo "PASS: Teacher Knowledge Vault M7e local test catalog import tests complete"
