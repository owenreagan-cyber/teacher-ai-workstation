#!/usr/bin/env bash
# Tests for whole-system coherence maintenance status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running whole-system coherence status tests..."

status_script="scripts/whole-system-coherence-status.sh"

for required in \
  "${status_script}" \
  docs/whole-system-coherence-maintenance-report.md \
  docs/proposals/backlog/whole-system-safe-enhancement-discovery.md; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/whole-system-coherence-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'documentation/status only' "${tmp}" || { echo "FAIL: missing planning boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/whole-system-coherence-cli.XXXXXX")"
bin/chief-of-staff --whole-system-coherence-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--whole-system-coherence-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--whole-system-coherence-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && { echo "FAIL: --write handler must not exist"; exit 1; }

echo "PASS: whole-system coherence status tests complete"
