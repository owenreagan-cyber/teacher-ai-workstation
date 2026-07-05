#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7c manual inventory import preview status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7c manual inventory import preview status tests..."

status_script="scripts/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md"
import_preview_fixture="assistant/teacher-knowledge-vault/m7c/fake-import-preview.json"
rejection_fixture="assistant/teacher-knowledge-vault/m7c/fake-rejection-report.json"
validator_script="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

for required in "${status_script}" "${foundation_doc}" "${import_preview_fixture}" "${rejection_fixture}" "${validator_script}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7c-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake/sanitized fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7c_manual_inventory_import_preview' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Import preview does not mean import' "${tmp}" || { echo "FAIL: missing import preview boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real manual import attempted' "${tmp}" || { echo "FAIL: missing negative import assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7b status still passes' "${tmp}" || { echo "FAIL: M7b preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7c-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7c-manual-inventory-import-preview-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status' || { echo "FAIL: --help missing M7c command"; exit 1; }
bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7c-manual-inventory-fixture-validator' || { echo "FAIL: --help missing M7c validator"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7c-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M7c"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7c command"; exit 1; }

grep -Fq -- '"runtime_imports": 0' "${import_preview_fixture}" || { echo "FAIL: import preview must show zero runtime imports"; exit 1; }
grep -Fq -- 'blocked_placeholder_drive_id_pattern' "${rejection_fixture}" || { echo "FAIL: rejection report must include drive id rejection"; exit 1; }
grep -Fq -- 'do_not_scan_blocked' assistant/teacher-knowledge-vault/m7c/fake-review-routing.json || { echo "FAIL: review routing must include do_not_scan_blocked"; exit 1; }

val_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7c-val.XXXXXX")"
bash "${validator_script}" >"${val_tmp}" 2>&1 || { echo "FAIL: fixture validator exited nonzero"; cat "${val_tmp}"; rm -f "${val_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${val_tmp}" || { echo "FAIL: fixture validator reported failures"; cat "${val_tmp}"; rm -f "${val_tmp}"; exit 1; }
rm -f "${val_tmp}"

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m7c --include='*.json' 2>/dev/null; then
  echo "FAIL: M7c fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M7c manual inventory import preview status tests complete"
