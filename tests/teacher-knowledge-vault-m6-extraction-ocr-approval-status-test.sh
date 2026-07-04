#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M6 extraction/OCR approval status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M6 extraction/OCR approval status tests..."

status_script="scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh"
foundation_doc="docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md"
requests_fixture="assistant/teacher-knowledge-vault/m6/fake-extraction-requests.json"
review_routing="assistant/teacher-knowledge-vault/m6/fake-review-routing.json"

for required in "${status_script}" "${foundation_doc}" "${requests_fixture}" "${review_routing}"; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m6-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake fixtures only' "${tmp}" || { echo "FAIL: missing fake-only boundary header"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'complete_teacher_knowledge_vault_m6_extraction_ocr_approval_packet' "${tmp}" || { echo "FAIL: missing closure marker in output"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real extraction attempted' "${tmp}" || { echo "FAIL: missing negative extraction assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no real OCR attempted' "${tmp}" || { echo "FAIL: missing negative OCR assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'M5 status still passes' "${tmp}" || { echo "FAIL: M5 preservation missing"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m6-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m6-extraction-ocr-approval-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m6-extraction-ocr-approval-status' || { echo "FAIL: --help missing M6 command"; exit 1; }

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/tkv-m6-cmds.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
grep -Fq -- '--teacher-knowledge-vault-m6-extraction-ocr-approval-status' "${cmds_tmp}" || { echo "FAIL: --commands missing M6"; rm -f "${cmds_tmp}"; exit 1; }
rm -f "${cmds_tmp}"

grep -Fq -- '"--teacher-knowledge-vault-m6-extraction-ocr-approval-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing M6 command"; exit 1; }

grep -Fq -- '99_DO_NOT_SCAN extraction blocked' "${requests_fixture}" || { echo "FAIL: requests must include do-not-scan exclusion"; exit 1; }
grep -Fq -- 'cloud OCR blocked by budget gate' "${requests_fixture}" || { echo "FAIL: requests must block cloud OCR"; exit 1; }
grep -Fq -- 'FAKE_SNIPPET_PLACEHOLDER' assistant/teacher-knowledge-vault/m6/fake-extraction-cache-records.json || { echo "FAIL: cache must use fake snippet placeholders"; exit 1; }
grep -Fq -- '"ocr_jobs_executed": 0' assistant/teacher-knowledge-vault/m6/fake-observability-metrics.json || { echo "FAIL: metrics must show zero OCR jobs"; exit 1; }

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/m6 --include='*.json' --include='*.yaml' 2>/dev/null; then
  echo "FAIL: M6 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M6 extraction/OCR approval status tests complete"
