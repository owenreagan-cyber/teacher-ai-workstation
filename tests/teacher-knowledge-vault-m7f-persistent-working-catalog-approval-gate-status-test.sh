#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7f persistent working catalog approval gate status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7f persistent working catalog approval gate status tests..."

status_script="scripts/teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md"
approval_packet="assistant/teacher-knowledge-vault/m7f/fake-persistent-catalog-approval-packet.json"
metrics_fixture="assistant/teacher-knowledge-vault/m7f/fake-observability-metrics.json"
m7c_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

for required in "${status_script}" "${foundation_doc}" "${approval_packet}" "${metrics_fixture}" "${m7c_validator}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7f-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'approval gate only' "${tmp}" || { echo "FAIL: missing approval gate boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7f_persistent_working_catalog_approval_gate' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7f approval gate is not persistent catalog runtime' "${tmp}" || { echo "FAIL: missing gate not runtime boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no persistent catalog write attempted' "${tmp}" || { echo "FAIL: missing negative persistent write assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7e status still passes' "${tmp}" || { echo "FAIL: M7e preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7c fixture validator still passes' "${tmp}" || { echo "FAIL: M7c validator preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7f-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status' || { echo "FAIL: --help missing M7f command"; exit 1; }

grep -Fq -- '"--teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7f command"; exit 1; }

grep -Fq -- '"persistent_catalog_write_executed": false' "${approval_packet}" || { echo "FAIL: approval packet must block persistent write"; exit 1; }
grep -Fq -- '"persistent_catalog_writes": 0' "${metrics_fixture}" || { echo "FAIL: metrics must show zero persistent catalog writes"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m7f --include='*.json' 2>/dev/null; then
  echo "FAIL: M7f fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M7f persistent working catalog approval gate status tests complete"
