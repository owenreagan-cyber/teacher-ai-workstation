#!/usr/bin/env bash
# Tests for aggregate governance lane status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running governance lane status tests..."

status_script="scripts/governance-lane-status.sh"

tmp="$(mktemp "${TMPDIR:-/tmp}/governance-lane-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: governance lane status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: governance lane status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Cursor Operating Modes Governance' "${tmp}" || { echo "FAIL: missing operating modes component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Autonomous Build Engine Governance' "${tmp}" || { echo "FAIL: missing ABE component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Runtime activation: no' "${tmp}" || { echo "FAIL: missing runtime activation banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'aggregate governance status does not hide component failures' "${tmp}" || { echo "FAIL: missing non-hiding assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/governance-lane-cli.XXXXXX")"
bin/chief-of-staff --governance-lane-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --governance-lane-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI governance lane status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--governance-lane-status'; then
  echo "FAIL: --help missing --governance-lane-status"
  exit 1
fi

for flag in --cursor-operating-modes-status --autonomous-build-engine-status; do
  out="$(mktemp "${TMPDIR:-/tmp}/governance-lane-component.XXXXXX")"
  bin/chief-of-staff "${flag}" >"${out}" 2>&1 || {
    echo "FAIL: ${flag} exited nonzero"
    cat "${out}"
    rm -f "${out}"
    exit 1
  }
  grep -q '^FAIL: 0$' "${out}" || {
    echo "FAIL: ${flag} reported failures"
    cat "${out}"
    rm -f "${out}"
    exit 1
  }
  rm -f "${out}"
done

echo "PASS: governance lane status tests passed."
