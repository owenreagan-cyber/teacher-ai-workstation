#!/usr/bin/env bash
# Tests for agent builder compatibility governance status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running agent builder compatibility governance status tests..."

status_script="scripts/agent-builder-compatibility-governance-status.sh"
governance_doc="docs/agent-builder-compatibility-and-external-tool-governance.md"

for required in \
  "${status_script}" \
  "${governance_doc}" \
  docs/agent-builder-safe-tool-trial-checklist.md \
  docs/agent-builder-mission-proof-template.md \
  docs/proposals/blocked/agent-builder-external-tool-runtime-boundaries.md \
  assistant/agent-builder-governance/samples/classification-summary.json; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/agent-builder-governance-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'External agent launch from Chief of Staff: no' "${tmp}" || { echo "FAIL: missing CoS no-launch banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/agent-builder-governance-cli.XXXXXX")"
bin/chief-of-staff --agent-builder-compatibility-governance-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--agent-builder-compatibility-governance-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--agent-builder-compatibility-governance-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && { echo "FAIL: --write handler must not exist"; exit 1; }

echo "PASS: agent builder compatibility governance status tests complete"
