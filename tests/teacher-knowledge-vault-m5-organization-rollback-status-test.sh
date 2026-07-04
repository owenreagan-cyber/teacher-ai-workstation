#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M5 organization/rollback status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M5 organization/rollback status tests..."

status_script="scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m5-approved-organization-rollback-foundation.md"
operations_fixture="assistant/teacher-knowledge-vault/m5/fake-approved-operations.json"
review_queue="assistant/teacher-knowledge-vault/m5/fake-organization-review-queue.json"

for required in "${status_script}" "${foundation_doc}" "${operations_fixture}" "${review_queue}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m5-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m5_organization_rollback_foundation' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real organization attempted' "${tmp}" || { echo "FAIL: missing negative organization assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M4 status still passes' "${tmp}" || { echo "FAIL: M4 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m5-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m5-organization-rollback-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m5-organization-rollback-status' || { echo "FAIL: --help missing M5 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m5-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m5-organization-rollback-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M5"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m5-organization-rollback-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M5 command"; exit 1; }

grep -Fq -- '99_DO_NOT_SCAN' "${operations_fixture}" || { echo "FAIL: operations must include do-not-scan exclusion"; exit 1; }
grep -Fq -- '"execution_blocked": true' "${review_queue}" || { echo "FAIL: review queue must block execution"; exit 1; }
grep -Fq -- '"operations_executed": 0' assistant/teacher-knowledge-vault/m5/fake-observability-metrics.json || { echo "FAIL: metrics must show zero operations"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m5 --include='*.json' --include='*.yaml' 2>/dev/null; then
  echo "FAIL: M5 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M5 organization/rollback status tests complete"
