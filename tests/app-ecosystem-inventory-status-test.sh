#!/usr/bin/env bash
# Tests for app ecosystem inventory status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running app ecosystem inventory status tests..."

status_script="scripts/app-ecosystem-inventory-status.sh"
inventory_doc="docs/app-ecosystem-inventory-and-prototype-build-list.md"

for required in \
  "${status_script}" \
  "${inventory_doc}" \
  assistant/app-ecosystem/samples/canonical-inventory-ids.json \
  docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/app-ecosystem-inventory-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Chief of Staff chooses app priority for Owen: no' "${tmp}" || { echo "FAIL: missing CoS no-choose banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'all 52 canonical app concepts represented' "${tmp}" || { echo "FAIL: missing 52-concept proof"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/app-ecosystem-inventory-cli.XXXXXX")"
bin/chief-of-staff --app-ecosystem-inventory-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--app-ecosystem-inventory-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--app-ecosystem-inventory-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

echo "PASS: app ecosystem inventory status tests complete"
