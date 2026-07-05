#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2b repo staging metadata discovery.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2b repo staging metadata discovery tests..."

discovery_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery.sh"
import_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-import.sh"
cleanup_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup.sh"
m2b_out=".local/teacher-knowledge-vault/m2b"
staging="assistant/teacher-knowledge-vault/m2b/fake-staging-folder"

bash "${cleanup_script}" >/dev/null 2>&1 || true

if bash "${discovery_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: discovery must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: discovery rejects arbitrary path arguments"

bash "${cleanup_script}" >/dev/null 2>&1 || true
tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2b-discovery.XXXXXX")"
bash "${discovery_script}" >"${tmp}" 2>&1 || { echo "FAIL: discovery exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: discovery reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

[[ -f "${m2b_out}/repo-staging-metadata-report.json" ]] || { echo "FAIL: metadata report missing"; exit 1; }
grep -Fq -- '"fixture_files_discovered": 8' "${m2b_out}/repo-staging-metadata-report.json" || { echo "FAIL: expected 8 fixture files"; exit 1; }
grep -Fq -- '"content_reads": 0' "${m2b_out}/repo-staging-metadata-report.json" || { echo "FAIL: content_reads must be 0"; exit 1; }
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore || { echo "FAIL: generated path must be gitignored"; exit 1; }

if grep -qE '\.read\(|open\([^)]*["'"'"']r[b]?["'"'"']|pdftotext|tesseract' "${discovery_script}" 2>/dev/null; then
  echo "FAIL: discovery script must not read file contents"
  exit 1
fi
echo "PASS: discovery script avoids content-read patterns"

if bash "${import_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: import must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: import rejects arbitrary path arguments"

bash "${import_script}" >/dev/null 2>&1 || { echo "FAIL: import exited nonzero"; exit 1; }
[[ -f ".local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite" ]] || { echo "FAIL: M7g catalog missing"; exit 1; }
grep -Fq -- '"metadata_records_imported": 7' "${m2b_out}/import-summary.json" || { echo "FAIL: expected 7 imported records"; exit 1; }

if command -v python3 >/dev/null 2>&1; then
  python3 - ".local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite" <<'PY' || { echo "FAIL: sqlite policy checks failed"; exit 1; }
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
assert c.execute("SELECT indexable FROM blocked_records WHERE block_reason='do_not_scan_blocked' AND batch_id='fake-m2b-batch-001'").fetchone()[0] == 0
assert c.execute("SELECT COUNT(*) FROM source_items WHERE batch_id='fake-m2b-batch-001' AND restricted_indexable=1").fetchone()[0] >= 1
print("PASS: sqlite policy checks for M2b batch")
PY
fi

bash "${cleanup_script}" >/dev/null 2>&1 || { echo "FAIL: cleanup exited nonzero"; exit 1; }
[[ ! -d "${m2b_out}" ]] || { echo "FAIL: M2b generated path should be removed"; exit 1; }
[[ -d "${staging}" ]] || { echo "FAIL: staging fixture folder must remain"; exit 1; }

echo "PASS: Teacher Knowledge Vault M2b repo staging metadata discovery tests complete"
