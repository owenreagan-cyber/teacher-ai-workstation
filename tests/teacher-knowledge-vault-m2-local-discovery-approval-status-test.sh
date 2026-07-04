#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2 local discovery approval packet status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2 local discovery approval status tests..."

status_script="scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh"
packet_doc="docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md"
discovery_run="assistant/teacher-knowledge-vault/m2/fake-discovery-run.json"
blocked_paths="assistant/teacher-knowledge-vault/m2/fake-blocked-path-examples.json"

for required in "${status_script}" "${packet_doc}" "${discovery_run}" "${blocked_paths}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'approval packet and dry-run design only' "${tmp}" || { echo "FAIL: missing approval packet boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m2_local_discovery_approval_packet' "${tmp}" || { echo "FAIL: missing closure marker in status flow"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real filesystem discovery attempted' "${tmp}" || { echo "FAIL: missing negative discovery assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M0 architecture freeze status still passes' "${tmp}" || { echo "FAIL: M0 preservation check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M1 fake catalog status still passes' "${tmp}" || { echo "FAIL: M1 preservation check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m2-local-discovery-approval-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m2-local-discovery-approval-status' || { echo "FAIL: --help missing M2 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m2-local-discovery-approval-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M2"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m2-local-discovery-approval-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M2 command"; exit 1; }

grep -Fq -- 'fake_local_planning_only' "${discovery_run}" || { echo "FAIL: discovery run missing classification"; exit 1; }
grep -Fq -- 'blocked-placeholder://99_DO_NOT_SCAN' "${blocked_paths}" || { echo "FAIL: blocked paths missing do-not-scan"; exit 1; }
grep -Fq -- 'restricted_indexable' "${blocked_paths}" || { echo "FAIL: blocked paths missing restricted indexable"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m2 --include='*.json' 2>/dev/null; then
  echo "FAIL: M2 fixtures must not contain URLs"
  exit 1
fi

if grep -rE '/Users/|/home/' assistant/teacher-knowledge-vault/m2 --include='*.json' 2>/dev/null; then
  echo "FAIL: M2 fixtures must not contain real local paths"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M2 local discovery approval status tests complete"
