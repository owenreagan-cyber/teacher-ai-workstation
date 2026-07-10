#!/usr/bin/env bash
# Tests for AGENTS.md governance status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running AGENTS.md governance status tests..."

status_script="scripts/agents-governance-status.sh"
agents_md="AGENTS.md"

for required in \
  "${status_script}" \
  "${agents_md}" \
  docs/secrets-and-agent-access-policy.md; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/agents-governance-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Implementation approval: not granted by AGENTS.md' "${tmp}" || { echo "FAIL: missing non-approval banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/agents-governance-cli.XXXXXX")"
bin/chief-of-staff --agents-governance-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--agents-governance-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--agents-governance-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

grep -Fq -- 'Phase-Specific Instructions (Not Global Rules)' "${agents_md}" || { echo "FAIL: AGENTS.md missing phase-specific exclusion section"; exit 1; }
grep -Fq -- 'explicit mission prompt' "${agents_md}" || { echo "FAIL: AGENTS.md missing explicit mission autonomous scope"; exit 1; }

echo "PASS: AGENTS.md governance status tests complete"
