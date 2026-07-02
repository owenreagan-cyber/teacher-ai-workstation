#!/usr/bin/env bash
# Tests for aggregate workstation operations lane status (H+I).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running workstation ops lane status tests..."

status_script="scripts/workstation-ops-lane-status.sh"

tmp="$(mktemp "${TMPDIR:-/tmp}/workstation-ops-lane-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: workstation ops lane status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: workstation ops lane status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Health Monitor (H)' "${tmp}" || { echo "FAIL: missing health monitor component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'System Updater (I)' "${tmp}" || { echo "FAIL: missing system updater component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Apply/install/repair: blocked' "${tmp}" || { echo "FAIL: missing blocked apply banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'aggregate ops status does not hide component failures' "${tmp}" || { echo "FAIL: missing non-hiding assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/workstation-ops-lane-cli.XXXXXX")"
bin/chief-of-staff --workstation-ops-lane-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --workstation-ops-lane-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI workstation ops lane status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--workstation-ops-lane-status'; then
  echo "FAIL: --help missing --workstation-ops-lane-status"
  exit 1
fi

for flag in --system-health --system-update-check; do
  out="$(mktemp "${TMPDIR:-/tmp}/workstation-ops-component.XXXXXX")"
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

echo "PASS: workstation ops lane status tests passed."
