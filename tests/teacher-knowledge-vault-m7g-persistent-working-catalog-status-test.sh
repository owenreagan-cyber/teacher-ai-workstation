#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7g persistent working catalog status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7g persistent working catalog status tests..."

status_script="scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md"
summary_fixture="assistant/teacher-knowledge-vault/m7g/fake-persistent-working-catalog-import-summary.json"
m7c_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

for required in "${status_script}" "${foundation_doc}" "${summary_fixture}" "${m7c_validator}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7g-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'persistent local working catalog prototype' "${tmp}" || { echo "FAIL: missing prototype boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7g_persistent_working_catalog_prototype' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7g is prototype only' "${tmp}" || { echo "FAIL: missing prototype-only boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7c fixture validator still passes' "${tmp}" || { echo "FAIL: M7c validator preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7f status still passes' "${tmp}" || { echo "FAIL: M7f preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7g-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7g-persistent-working-catalog-status' || { echo "FAIL: --help missing M7g status command"; exit 1; }

grep -Fq -- '"--teacher-knowledge-vault-m7g-persistent-working-catalog-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7g status command"; exit 1; }

grep -Fq -- '"catalog_mode": "persistent_working_prototype"' "${summary_fixture}" || { echo "FAIL: fixture must show persistent_working_prototype mode"; exit 1; }
grep -Fq -- '"production_write": false' "${summary_fixture}" || { echo "FAIL: fixture must block production write"; exit 1; }

echo "PASS: Teacher Knowledge Vault M7g persistent working catalog status tests complete"
