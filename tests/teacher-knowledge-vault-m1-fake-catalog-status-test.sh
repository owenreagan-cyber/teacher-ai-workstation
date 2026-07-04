#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M1 fake catalog status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M1 fake catalog status tests..."

status_script="scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md"
catalog_fixture="assistant/teacher-knowledge-vault/m1/fake-catalog.json"
resources_fixture="assistant/teacher-knowledge-vault/m1/fake-resources.json"

for required in "${status_script}" "${foundation_doc}" "${catalog_fixture}" "${resources_fixture}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m1-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no SQLite database created' "${tmp}" || { echo "FAIL: missing SQLite negative assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M0 architecture freeze status still passes' "${tmp}" || { echo "FAIL: M0 preservation check missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m1-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m1-fake-catalog-status' || { echo "FAIL: --help missing M1 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m1-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m1-fake-catalog-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M1"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m1-fake-catalog-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M1 command"; exit 1; }

grep -Fq -- 'fake_local_planning_only' "${catalog_fixture}" || { echo "FAIL: catalog missing classification"; exit 1; }
grep -Fq -- '99_DO_NOT_SCAN' "${resources_fixture}" || { echo "FAIL: resources missing do-not-scan"; exit 1; }
grep -Fq -- '12_AI_GENERATED' "${resources_fixture}" || { echo "FAIL: resources missing AI generated"; exit 1; }

if find assistant/teacher-knowledge-vault/m1 -name '*.db' 2>/dev/null | grep -q .; then
  echo "FAIL: .db files must not exist"
  exit 1
fi

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m1 --include='*.json' 2>/dev/null; then
  echo "FAIL: M1 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M1 fake catalog status tests complete"
