#!/usr/bin/env bash
# Tests for Teacher Knowledge Vault M0 architecture freeze status (expanded).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Knowledge Vault M0 architecture freeze status tests..."

status_script="scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh"
foundation_doc="docs/teacher-knowledge-vault-m0-foundation.md"
m0_freeze_doc="docs/teacher-knowledge-vault/m0-architecture-freeze.md"
boundary_doc="docs/teacher-knowledge-vault/blocked-runtime-boundaries.md"
sample_entries="assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json"
adr_readme="docs/adr/teacher-knowledge-vault/README.md"
v1_spec="docs/teacher-knowledge-vault/v1-architecture-spec.md"
connector_contract="docs/teacher-knowledge-vault/connector-sdk-contract.md"
fake_connector="assistant/teacher-knowledge-vault/samples/fake-connector-capabilities.json"

for required in "${status_script}" "${foundation_doc}" "${m0_freeze_doc}" "${boundary_doc}" \
  "${sample_entries}" "${adr_readme}" "${v1_spec}" "${connector_contract}" "${fake_connector}"; do
  if [[ ! -f "${required}" ]]; then
    echo "FAIL: required file missing: ${required}"
    exit 1
  fi
done

for adr in docs/adr/teacher-knowledge-vault/000{1..9}-*.md docs/adr/teacher-knowledge-vault/0010-*.md; do
  if [[ ! -f "${adr}" ]]; then
    echo "FAIL: required ADR missing: ${adr}"
    exit 1
  fi
done

tmp="$(mktemp "${TMPDIR:-/tmp}/teacher-knowledge-vault-m0-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: teacher-knowledge-vault-m0-architecture-freeze-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: status script reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'documentation/status/fake fixtures only' "${tmp}" || {
  echo "FAIL: missing planning-only boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'complete_teacher_knowledge_vault_m0_expansion_m1_alignment' "${tmp}" || {
  echo "FAIL: missing expansion alignment marker in status output"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no knowledge directory population attempted' "${tmp}" || {
  echo "FAIL: missing negative knowledge population assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/teacher-knowledge-vault-m0-cli.XXXXXX")"
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --teacher-knowledge-vault-m0-architecture-freeze-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--teacher-knowledge-vault-m0-architecture-freeze-status'; then
  echo "FAIL: --help missing --teacher-knowledge-vault-m0-architecture-freeze-status"
  exit 1
fi

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/teacher-knowledge-vault-m0-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--teacher-knowledge-vault-m0-architecture-freeze-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --teacher-knowledge-vault-m0-architecture-freeze-status"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

if ! grep -Fq -- '"--teacher-knowledge-vault-m0-architecture-freeze-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing knowledge vault M0 status command"
  exit 1
fi

if ! grep -Fq -- 'fake_local_planning_only' "${sample_entries}"; then
  echo "FAIL: sample entries missing fake_local_planning_only classification"
  exit 1
fi

if ! grep -Fq -- 'complete_teacher_knowledge_vault_m0_expansion_m1_alignment' "${m0_freeze_doc}"; then
  echo "FAIL: m0-architecture-freeze.md missing expansion alignment marker"
  exit 1
fi

if ! grep -Fq -- '10_TEACHER_ONLY' "${m0_freeze_doc}"; then
  echo "FAIL: m0-architecture-freeze.md missing 10_TEACHER_ONLY taxonomy"
  exit 1
fi

if ! grep -Fq -- 'Auto-loading' "${boundary_doc}"; then
  echo "FAIL: boundary doc missing auto-loading blocked language"
  exit 1
fi

if [[ -d assistant/memory/knowledge ]]; then
  echo "FAIL: assistant/memory/knowledge must not exist in M0"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

if grep -rqiE 'https?://' assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json \
  assistant/teacher-knowledge-vault/samples/ \
  --include='*.json' 2>/dev/null; then
  echo "FAIL: v0 fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Teacher Knowledge Vault M0 architecture freeze status tests complete"
