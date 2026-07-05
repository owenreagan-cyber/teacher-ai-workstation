#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2d metadata scan.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2d metadata scan tests..."

preflight_script="scripts/teacher-knowledge-vault-m2d-selected-folder-preflight.sh"
scan_script="scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-scan.sh"
preview_script="scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-preview.sh"
cleanup_script="scripts/teacher-knowledge-vault-m2d-selected-folder-cleanup.sh"
m2d_out=".local/teacher-knowledge-vault/m2d"

bash "${cleanup_script}" >/dev/null 2>&1 || true

if bash "${scan_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: scan must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: scan rejects arbitrary path arguments"

bash "${preflight_script}" >/dev/null 2>&1 || { echo "FAIL: preflight required"; exit 1; }
bash "${scan_script}" >/dev/null 2>&1 || { echo "FAIL: scan exited nonzero"; exit 1; }

for report in selected-folder-metadata-report.json scan-proof.json no-content-read-proof.json rollback-proof.json summary-report.json; do
  [[ -f "${m2d_out}/${report}" ]] || { echo "FAIL: missing report ${report}"; exit 1; }
done

grep -Fq -- '"files_discovered": 4' "${m2d_out}/selected-folder-metadata-report.json" || { echo "FAIL: expected 4 files"; exit 1; }
grep -Fq -- '"content_reads": 0' "${m2d_out}/no-content-read-proof.json" || { echo "FAIL: content_reads must be 0"; exit 1; }
grep -Fq -- '"traversal_confined_to_approved_root": true' "${m2d_out}/scan-proof.json" || { echo "FAIL: root confinement required"; exit 1; }
grep -Fq -- '"filesystem_metadata_only": true' "${m2d_out}/no-content-read-proof.json" || { echo "FAIL: metadata only proof required"; exit 1; }

if grep -qE '\.read\(|open\([^)]*["'"'"']r[b]?["'"'"']|pdftotext|tesseract' "${scan_script}" 2>/dev/null; then
  echo "FAIL: scan script must not read file contents"
  exit 1
fi
echo "PASS: scan script avoids content-read patterns"

bash "${preview_script}" >/dev/null 2>&1 || { echo "FAIL: preview exited nonzero"; exit 1; }
grep -Fq -- '"catalog_import_executed": false' "${m2d_out}/m7g-import-preview.json" || { echo "FAIL: preview must not import"; exit 1; }

bash "${cleanup_script}" >/dev/null 2>&1 || { echo "FAIL: cleanup exited nonzero"; exit 1; }
[[ -f "${m2d_out}/cleanup-proof.json" ]] || { echo "FAIL: cleanup proof missing"; exit 1; }

echo "PASS: Teacher Knowledge Vault M2d metadata scan tests complete"
