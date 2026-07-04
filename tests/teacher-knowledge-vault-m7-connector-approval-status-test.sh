#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7 connector approval status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7 connector approval status tests..."

status_script="scripts/teacher-knowledge-vault-m7-connector-approval-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md"
capabilities_fixture="assistant/teacher-knowledge-vault/m7/fake-connector-capabilities.json"
review_routing="assistant/teacher-knowledge-vault/m7/fake-review-routing.json"

for required in "${status_script}" "${foundation_doc}" "${capabilities_fixture}" "${review_routing}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7_read_only_connector_approval_packet' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real connector attempted' "${tmp}" || { echo "FAIL: missing negative connector assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no OAuth API or secrets attempted' "${tmp}" || { echo "FAIL: missing negative OAuth assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M6 status still passes' "${tmp}" || { echo "FAIL: M6 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7-connector-approval-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7-connector-approval-status' || { echo "FAIL: --help missing M7 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m7-connector-approval-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M7"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m7-connector-approval-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7 command"; exit 1; }

grep -Fq -- '"blocked_by_default": true' "${capabilities_fixture}" || { echo "FAIL: connectors must be blocked by default"; exit 1; }
grep -Fq -- 'oauth_requested_but_blocked' "${review_routing}" || { echo "FAIL: review routing must block OAuth"; exit 1; }
grep -Fq -- '"api_calls_made": 0' assistant/teacher-knowledge-vault/m7/fake-observability-metrics.json || { echo "FAIL: metrics must show zero API calls"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m7 --include='*.json' --include='*.yaml' 2>/dev/null; then
  echo "FAIL: M7 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M7 connector approval status tests complete"
