#!/usr/bin/env bash
# Tests for Classroom Timer & Stopwatch runtime status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Classroom Timer & Stopwatch runtime status tests..."

status_script="scripts/classroom-timer-stopwatch-runtime-status.sh"

for required in \
  "${status_script}" \
  apps/classroom-timer-stopwatch/index.html \
  apps/classroom-timer-stopwatch/timer.js; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/timer-runtime-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Runtime-approved apps: Classroom Timer & Stopwatch only' "${tmp}" || { echo "FAIL: missing runtime approved banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'exactly one app runtime_approved in manifest' "${tmp}" || { echo "FAIL: missing single approved app check"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/timer-runtime-cli.XXXXXX")"
bin/chief-of-staff --classroom-timer-stopwatch-runtime-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--classroom-timer-stopwatch-runtime-status' || { echo "FAIL: --help missing command"; exit 1; }

echo "PASS: Classroom Timer & Stopwatch runtime status tests complete"
