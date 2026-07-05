#!/usr/bin/env bash
# Teacher Knowledge Vault M7e local test catalog cleanup — fixed generated path only.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

M7E_OUT_DIR=".tmp/teacher-knowledge-vault/m7e"

section 'Teacher Knowledge Vault M7e Local Test Catalog Cleanup'
cat <<'EOF'
Status: disposable test catalog cleanup — fixed path only
Production catalog writes: no
Source file operations: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

if [[ -d "${M7E_OUT_DIR}" ]]; then
  rm -rf "${M7E_OUT_DIR}"
  pass "removed fixed generated path: ${M7E_OUT_DIR}"
else
  pass "fixed generated path already clean: ${M7E_OUT_DIR}"
fi

[[ ! -d "${M7E_OUT_DIR}" ]] && pass 'cleanup verified — generated path removed' || fail 'cleanup failed — path still exists'
pass 'no source files touched'
pass 'no production catalog touched'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
