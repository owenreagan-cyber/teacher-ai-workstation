#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2c selected local folder approval gate status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2c selected local folder approval gate status tests..."

status_script="scripts/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md"
readiness_doc="docs/teacher-knowledge-vault/m2d-readiness-checklist.md"
approval_packet="assistant/teacher-knowledge-vault/m2c/fake-selected-folder-approval-packet.json"
denials_fixture="assistant/teacher-knowledge-vault/m2c/fake-path-preflight-denials.json"
rollback_fixture="assistant/teacher-knowledge-vault/m2c/fake-rollback-cleanup-plan.json"
metrics_fixture="assistant/teacher-knowledge-vault/m2c/fake-observability-metrics.json"

for required in "${status_script}" "${foundation_doc}" "${readiness_doc}" "${approval_packet}" "${denials_fixture}" "${rollback_fixture}" "${metrics_fixture}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2c-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'approval gate only' "${tmp}" || { echo "FAIL: missing approval gate boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m2c_selected_local_folder_approval_gate' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M2c approval gate is not selected-folder scan runtime' "${tmp}" || { echo "FAIL: missing gate not runtime boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real folder scan attempted' "${tmp}" || { echo "FAIL: missing negative real scan assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M2b status still passes' "${tmp}" || { echo "FAIL: M2b preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7g status still passes' "${tmp}" || { echo "FAIL: M7g preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'dashboard includes M2c section' "${tmp}" || { echo "FAIL: dashboard wiring check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'validate-all includes M2c track' "${tmp}" || { echo "FAIL: validate-all wiring check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'coherence checks M2c closure marker' "${tmp}" || { echo "FAIL: coherence wiring check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'manifest lists fixed-path M2d preflight' "${tmp}" || { echo "FAIL: manifest M2d fixed-path check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2c-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status' || { echo "FAIL: --help missing M2c command"; exit 1; }

grep -Fq -- '"--teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M2c command"; exit 1; }
grep -Fq -- 'Teacher Knowledge Vault M2c Selected Local Folder Approval Gate' scripts/chief-of-staff-validate-all.sh || { echo "FAIL: validate-all missing M2c track"; exit 1; }
grep -Fq -- 'Teacher Knowledge Vault M2c Selected Local Folder Approval Gate' scripts/chief-of-staff-dashboard.sh || { echo "FAIL: dashboard missing M2c section"; exit 1; }
grep -Fq -- 'm2d-readiness-checklist.md' "${foundation_doc}" || { echo "FAIL: foundation doc must link M2d readiness checklist"; exit 1; }

grep -Fq -- '"owen_approval": false' "${approval_packet}" || { echo "FAIL: approval packet must require owen approval false"; exit 1; }
grep -Fq -- '"real_scans_executed": 0' "${metrics_fixture}" || { echo "FAIL: metrics must show zero real scans"; exit 1; }
grep -Fq -- 'home_directory' "${denials_fixture}" || { echo "FAIL: denial rules must include home directory"; exit 1; }
grep -Fq -- 'file_content_reads' "${denials_fixture}" || { echo "FAIL: denial rules must include content reads"; exit 1; }
grep -Fq -- 'organization_operations' "${denials_fixture}" || { echo "FAIL: denial rules must include organization operations"; exit 1; }
grep -Fq -- '"no_content_read_proof_required": true' "${rollback_fixture}" || { echo "FAIL: rollback plan must require no-content-read proof"; exit 1; }
grep -Fq -- 'General folder scanning' "${readiness_doc}" || { echo "FAIL: readiness checklist must note general scan blocked"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m2c --include='*.json' 2>/dev/null; then
  echo "FAIL: M2c fixtures must not contain URLs"
  exit 1
fi
if grep -rE '/Users/|/home/' assistant/teacher-knowledge-vault/m2c --include='*.json' 2>/dev/null; then
  echo "FAIL: M2c fixtures must not contain real local paths"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M2c selected local folder approval gate status tests complete"
