#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7b manual source inventory status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7b manual source inventory status tests..."

status_script="scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7b-manual-source-inventory-level-1.md"
inventory_fixture="assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json"
review_routing="assistant/teacher-knowledge-vault/m7b/fake-manual-review-routing.json"

for required in "${status_script}" "${foundation_doc}" "${inventory_fixture}" "${review_routing}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7b-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake/sanitized fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7b_manual_source_inventory_level_1' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real manual ingestion attempted' "${tmp}" || { echo "FAIL: missing negative ingestion assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7 status still passes' "${tmp}" || { echo "FAIL: M7 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7b-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7b-manual-source-inventory-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7b-manual-source-inventory-status' || { echo "FAIL: --help missing M7b command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7b-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m7b-manual-source-inventory-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M7b"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m7b-manual-source-inventory-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7b command"; exit 1; }

grep -Fq -- '99_DO_NOT_SCAN' "${inventory_fixture}" || { echo "FAIL: inventory must include do-not-scan"; exit 1; }
grep -Fq -- '"runtime_ingested": false' "${inventory_fixture}" || { echo "FAIL: inventory must block ingestion"; exit 1; }
grep -Fq -- 'approved_for_future_import' "${review_routing}" || { echo "FAIL: routing must show future import only"; exit 1; }
[[ -f assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.csv ]] || { echo "FAIL: CSV fixture missing"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m7b --include='*.json' --include='*.csv' 2>/dev/null; then
  echo "FAIL: M7b fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M7b manual source inventory status tests complete"
