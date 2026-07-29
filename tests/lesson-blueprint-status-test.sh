#!/usr/bin/env bash
# Tests for Lesson Blueprint status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running lesson blueprint status tests..."

status_script="scripts/lesson-blueprint-status.sh"
[[ -f "${status_script}" ]] || { echo "FAIL: missing ${status_script}"; exit 1; }

tmp="$(mktemp "${TMPDIR:-/tmp}/lesson-blueprint-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: lesson-blueprint-status.sh exited nonzero"
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

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/lesson-blueprint-cli.XXXXXX")"
bin/chief-of-staff --lesson-blueprint-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --lesson-blueprint-status exited nonzero"
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

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--lesson-blueprint-status' || {
  echo "FAIL: --help missing --lesson-blueprint-status"
  exit 1
}

echo "PASS: lesson blueprint status tests complete"
