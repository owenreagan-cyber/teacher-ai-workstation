#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M3 fake duplicate/search status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M3 fake duplicate search status tests..."

status_script="scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m3-fake-duplicate-search-package-foundation.md"
dup_fixture="assistant/teacher-knowledge-vault/m3/fake-duplicate-candidates.json"
search_fixture="assistant/teacher-knowledge-vault/m3/fake-search-queries.json"

for required in "${status_script}" "${foundation_doc}" "${dup_fixture}" "${search_fixture}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m3-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake duplicate/search/package foundation only' "${tmp}" || { echo "FAIL: missing foundation boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m3_fake_duplicate_search_foundation' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real search over local files attempted' "${tmp}" || { echo "FAIL: missing negative search assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M0 status still passes' "${tmp}" || { echo "FAIL: M0 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M1 status still passes' "${tmp}" || { echo "FAIL: M1 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M2 status still passes' "${tmp}" || { echo "FAIL: M2 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m3-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m3-fake-duplicate-search-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m3-fake-duplicate-search-status' || { echo "FAIL: --help missing M3 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m3-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m3-fake-duplicate-search-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M3"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m3-fake-duplicate-search-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M3 command"; exit 1; }

grep -Fq -- '"auto_merge": false' "${dup_fixture}" || { echo "FAIL: duplicates must not auto merge"; exit 1; }
grep -Fq -- 'possible duplicates' "${search_fixture}" || { echo "FAIL: search missing duplicate query"; exit 1; }
grep -Fq -- '99_DO_NOT_SCAN' assistant/teacher-knowledge-vault/m3/fake-duplicate-candidates.json || { echo "FAIL: missing do-not-scan exclusion"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m3 --include='*.json' 2>/dev/null; then
  echo "FAIL: M3 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M3 fake duplicate search status tests complete"
