#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7d runtime import approval gate status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7d runtime import approval gate status tests..."

status_script="scripts/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md"
approval_packet="assistant/teacher-knowledge-vault/m7d/fake-import-approval-packet.json"
blockers_fixture="assistant/teacher-knowledge-vault/m7d/fake-import-blockers.json"
m7c_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

for required in "${status_script}" "${foundation_doc}" "${approval_packet}" "${blockers_fixture}" "${m7c_validator}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7d-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'approval gate only' "${tmp}" || { echo "FAIL: missing approval gate boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7d_runtime_manual_import_approval_gate' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7d approval gate is not import' "${tmp}" || { echo "FAIL: missing gate not import boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no runtime manual import attempted' "${tmp}" || { echo "FAIL: missing negative import assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7c status still passes' "${tmp}" || { echo "FAIL: M7c preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7c fixture validator still passes' "${tmp}" || { echo "FAIL: M7c fixture validator preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7d-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7d-runtime-import-approval-gate-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7d-runtime-import-approval-gate-status' || { echo "FAIL: --help missing M7d command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7d-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m7d-runtime-import-approval-gate-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M7d"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m7d-runtime-import-approval-gate-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7d command"; exit 1; }

grep -Fq -- '"runtime_import_executed": false' "${approval_packet}" || { echo "FAIL: approval packet must block runtime import"; exit 1; }
grep -Fq -- 'do_not_scan_normal_import' "${blockers_fixture}" || { echo "FAIL: blockers must include do_not_scan"; exit 1; }
grep -Fq -- '"catalog_writes": 0' assistant/teacher-knowledge-vault/m7d/fake-observability-metrics.json || { echo "FAIL: metrics must show zero catalog writes"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m7d --include='*.json' 2>/dev/null; then
  echo "FAIL: M7d fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M7d runtime import approval gate status tests complete"
