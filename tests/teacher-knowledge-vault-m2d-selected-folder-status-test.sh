#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2d status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2d status tests..."

status_script="scripts/teacher-knowledge-vault-m2d-selected-folder-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md"

[[ -f "${status_script}" ]] || { echo "FAIL: status script missing"; exit 1; }
[[ -f "${foundation_doc}" ]] || { echo "FAIL: foundation doc missing"; exit 1; }

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m2d-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m2d_first_selected_folder_metadata_scan' "${tmp}" || { echo "FAIL: missing closure marker"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'm2d-tiny-folder' "${tmp}" || { echo "FAIL: missing approved folder"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M2c status still passes' "${tmp}" || { echo "FAIL: M2c preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no file content read attempted' "${tmp}" || { echo "FAIL: missing no content read assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m2d-selected-folder-status' || { echo "FAIL: --help missing M2d status"; exit 1; }

echo "PASS: Teacher Knowledge Vault M2d status tests complete"
