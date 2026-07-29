#!/usr/bin/env bash
# Tests for Lesson Package status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running lesson package status tests..."

status_script="scripts/lesson-package-status.sh"
[[ -f "${status_script}" ]] || { echo "FAIL: missing ${status_script}"; exit 1; }

tmp="$(mktemp "${TMPDIR:-/tmp}/lesson-package-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: lesson-package-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: status script reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/lesson-package-cli.XXXXXX")"
bin/chief-of-staff --lesson-package-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --lesson-package-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--lesson-package-status' || {
  echo "FAIL: --help missing --lesson-package-status"
  exit 1
}

echo "PASS: lesson package status tests complete"
