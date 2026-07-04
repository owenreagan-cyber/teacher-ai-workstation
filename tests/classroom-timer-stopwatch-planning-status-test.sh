#!/usr/bin/env bash
# Tests for Classroom Timer & Stopwatch planning lane status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Classroom Timer & Stopwatch planning status tests..."

status_script="scripts/classroom-timer-stopwatch-planning-status.sh"
planning_doc="docs/classroom-utilities/classroom-timer-stopwatch-planning.md"

for required in \
  "${status_script}" \
  "${planning_doc}" \
  assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning/example-timer-presets-001.json; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/timer-planning-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Runtime classroom app: no' "${tmp}" || { echo "FAIL: missing runtime blocked banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Owen selected planning lane: yes' "${tmp}" || { echo "FAIL: missing Owen selection banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/timer-planning-cli.XXXXXX")"
bin/chief-of-staff --classroom-timer-stopwatch-planning-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--classroom-timer-stopwatch-planning-status' || { echo "FAIL: --help missing command"; exit 1; }

echo "PASS: Classroom Timer & Stopwatch planning status tests complete"
