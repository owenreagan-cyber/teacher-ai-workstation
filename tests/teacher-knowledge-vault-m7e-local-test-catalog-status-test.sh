#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M7e local test catalog status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M7e local test catalog status tests..."

status_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md"
import_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-import.sh"
cleanup_script="scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh"

for required in "${status_script}" "${foundation_doc}" "${import_script}" "${cleanup_script}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

bash scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh >/dev/null 2>&1 || true

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7e-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'disposable local test catalog' "${tmp}" || { echo "FAIL: missing disposable catalog boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m7e_local_test_catalog_import' "${tmp}" || { echo "FAIL: missing closure marker"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7d status still passes' "${tmp}" || { echo "FAIL: M7d preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M7c fixture validator still passes' "${tmp}" || { echo "FAIL: M7c validator preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no production catalog write attempted' "${tmp}" || { echo "FAIL: missing production write boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m7e-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m7e-local-test-catalog-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7e-local-test-catalog-import' || { echo "FAIL: --help missing M7e import"; exit 1; }
bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7e-local-test-catalog-cleanup' || { echo "FAIL: --help missing M7e cleanup"; exit 1; }
bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m7e-local-test-catalog-status' || { echo "FAIL: --help missing M7e status"; exit 1; }

grep -Fq -- '"--teacher-knowledge-vault-m7e-local-test-catalog-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M7e status"; exit 1; }

grep -Fq -- '.tmp/teacher-knowledge-vault/m7e/' .gitignore || { echo "FAIL: gitignore must cover M7e path"; exit 1; }

bash scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh >/dev/null 2>&1 || true

echo "PASS: Teacher Knowledge Vault M7e local test catalog status tests complete"
