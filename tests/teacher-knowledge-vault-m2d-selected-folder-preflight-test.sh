#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M2d preflight.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M2d preflight tests..."

preflight_script="scripts/teacher-knowledge-vault-m2d-selected-folder-preflight.sh"
cleanup_script="scripts/teacher-knowledge-vault-m2d-selected-folder-cleanup.sh"
m2d_out=".local/teacher-knowledge-vault/m2d"

bash "${cleanup_script}" >/dev/null 2>&1 || true

if bash "${preflight_script}" /tmp/evil-path 2>/dev/null; then
  echo "FAIL: preflight must reject arbitrary path arguments"
  exit 1
fi
echo "PASS: preflight rejects arbitrary path arguments"

bash "${cleanup_script}" >/dev/null 2>&1 || true
bash "${preflight_script}" >/dev/null 2>&1 || { echo "FAIL: preflight exited nonzero"; exit 1; }
[[ -f "${m2d_out}/preflight-approval-packet.json" ]] || { echo "FAIL: preflight packet missing"; exit 1; }
grep -Fq -- '"allowed_decision": true' "${m2d_out}/preflight-approval-packet.json" || { echo "FAIL: preflight must allow approved folder"; exit 1; }
grep -Fq -- '"content_reads": 0' "${m2d_out}/preflight-approval-packet.json" || { echo "FAIL: content_reads must be 0"; exit 1; }
grep -Fq -- 'm2d-tiny-folder' "${m2d_out}/preflight-approval-packet.json" || { echo "FAIL: must reference approved folder"; exit 1; }

echo "PASS: Teacher Knowledge Vault M2d preflight tests complete"
