#!/usr/bin/env bash
# Tests for app runtime approval gate status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running app runtime approval gate status tests..."

status_script="scripts/app-runtime-approval-gate-status.sh"

for required in \
  "${status_script}" \
  docs/app-ecosystem/runtime-implementation-approval-gate.md \
  docs/app-ecosystem/app-production-readiness-matrix.md \
  assistant/app-ecosystem/samples/runtime-approval-manifest.json \
  docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md \
  docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-implementation-packet.md; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/runtime-approval-gate.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Runtime-approved apps: 0' "${tmp}" || { echo "FAIL: missing zero runtime approved banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'manifest declares 27 Tier 1–3 packets' "${tmp}" || { echo "FAIL: missing 27 packet count"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/runtime-approval-cli.XXXXXX")"
bin/chief-of-staff --app-runtime-approval-gate-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--app-runtime-approval-gate-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--app-runtime-approval-gate-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

echo "PASS: App runtime approval gate status tests complete"
