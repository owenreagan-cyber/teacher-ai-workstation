#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M4 smart rename status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M4 smart rename status tests..."

status_script="scripts/teacher-knowledge-vault-m4-smart-rename-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m4-smart-rename-foundation.md"
suggestions_fixture="assistant/teacher-knowledge-vault/m4/fake-smart-rename-suggestions.json"
review_cards="assistant/teacher-knowledge-vault/m4/fake-review-cards.json"

for required in "${status_script}" "${foundation_doc}" "${suggestions_fixture}" "${review_cards}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m4-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m4_smart_rename_foundation' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real smart rename attempted' "${tmp}" || { echo "FAIL: missing negative rename assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M3 status still passes' "${tmp}" || { echo "FAIL: M3 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m4-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m4-smart-rename-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m4-smart-rename-status' || { echo "FAIL: --help missing M4 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m4-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m4-smart-rename-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M4"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m4-smart-rename-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M4 command"; exit 1; }

grep -Fq -- 'execute_rename_now' "${suggestions_fixture}" || { echo "FAIL: suggestions must list blocked rename"; exit 1; }
grep -Fq -- '99_DO_NOT_SCAN' "${suggestions_fixture}" || { echo "FAIL: missing do-not-scan exclusion"; exit 1; }
grep -Fq -- 'student_facing_mode_blocked' "${review_cards}" || { echo "FAIL: review card missing student mode block"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m4 --include='*.json' --include='*.yaml' 2>/dev/null; then
  echo "FAIL: M4 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M4 smart rename status tests complete"
