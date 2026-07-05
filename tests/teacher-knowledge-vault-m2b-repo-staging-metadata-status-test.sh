#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2b repo staging metadata status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2b repo staging metadata status tests..."

status_script="scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md"
summary_fixture="assistant/teacher-knowledge-vault/m2b/fake-import-summary-example.json"

for required in "${status_script}" "${foundation_doc}" "${summary_fixture}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2b-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'repo-owned staging fixture folder only' "${tmp}" || { echo "FAIL: missing prototype boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m2b_repo_owned_staging_metadata_prototype' "${tmp}" || { echo "FAIL: missing closure marker"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7g status still passes' "${tmp}" || { echo "FAIL: M7g preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-status >"${tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: CLI reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m2b-repo-staging-metadata-status' || { echo "FAIL: --help missing M2b status command"; exit 1; }
grep -Fq -- '"--teacher-knowledge-vault-m2b-repo-staging-metadata-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M2b status command"; exit 1; }

echo "PASS: Teacher Knowledge Vault M2b repo staging metadata status tests complete"
