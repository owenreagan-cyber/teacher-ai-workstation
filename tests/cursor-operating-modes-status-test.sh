#!/usr/bin/env bash
# Lightweight tests for Cursor operating modes and proposal governance foundation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Cursor operating modes status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/cursor-operating-modes-status.XXXXXX")"
bash scripts/cursor-operating-modes-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: cursor-operating-modes-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: cursor-operating-modes-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Discovery ≠ implementation approval' "${tmp}" || {
  echo "FAIL: missing discovery not implementation banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'documentation/status only' "${tmp}" || {
  echo "FAIL: missing documentation/status boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no network call attempted' "${tmp}" || {
  echo "FAIL: missing negative network assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'cursor operating modes status script does not shell-invoke curl' "${tmp}" || {
  echo "FAIL: missing negative curl assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'cursor operating modes status script does not mutate git state' "${tmp}" || {
  echo "FAIL: missing negative git mutation assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/cursor-operating-modes-cli.XXXXXX")"
bin/chief-of-staff --cursor-operating-modes-status >"${tmp}" 2>&1 || {
  echo "FAIL: --cursor-operating-modes-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --cursor-operating-modes-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/cursor-operating-modes-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--cursor-operating-modes-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --cursor-operating-modes-status"
  cat "${cmds_tmp}"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

help_tmp="$(mktemp "${TMPDIR:-/tmp}/cursor-operating-modes-help.XXXXXX")"
bin/chief-of-staff --help >"${help_tmp}" 2>&1 || true
if ! grep -Fq -- '--cursor-operating-modes-status' "${help_tmp}"; then
  echo "FAIL: --help does not list --cursor-operating-modes-status"
  cat "${help_tmp}"
  rm -f "${help_tmp}"
  exit 1
fi
rm -f "${help_tmp}"

echo "PASS: Cursor operating modes status tests passed."
