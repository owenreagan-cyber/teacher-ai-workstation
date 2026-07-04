#!/usr/bin/env bash
# Tests for app ecosystem planning lanes program status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running app ecosystem planning lanes status tests..."

status_script="scripts/app-ecosystem-planning-lanes-status.sh"
program_doc="docs/app-ecosystem-planning-lanes-program.md"
manifest="assistant/app-ecosystem/samples/planning-lanes-manifest.json"

for required in \
  "${status_script}" \
  "${program_doc}" \
  "${manifest}" \
  docs/proposals/blocked/high-risk-app-planning-blocked-summary.md \
  docs/classroom-utilities/interactive-bingo-caller-planning.md \
  assistant/classroom-utilities/samples/interactive-bingo-caller-planning/example-settings-001.json; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/planning-lanes-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Tier 1–3 planning lanes: complete' "${tmp}" || { echo "FAIL: missing tier 1-3 complete banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'manifest declares 27 Tier 1–3 planning lanes' "${tmp}" || { echo "FAIL: missing 27 lane count"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/planning-lanes-cli.XXXXXX")"
bin/chief-of-staff --app-ecosystem-planning-lanes-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--app-ecosystem-planning-lanes-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--app-ecosystem-planning-lanes-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

echo "PASS: App ecosystem planning lanes status tests complete"
