#!/usr/bin/env bash
# Lightweight tests for Widget and Shortcut Builder read-only catalog foundation (Program F1).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Widget and Shortcut Builder status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/widget-shortcut-builder-status.XXXXXX")"
bash scripts/widget-shortcut-builder-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: widget-shortcut-builder-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: widget-shortcut-builder-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'read-only catalog planning only' "${tmp}" || {
  echo "FAIL: missing read-only catalog boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no widget install attempted' "${tmp}" || {
  echo "FAIL: missing negative widget install assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'widget shortcut status script does not shell-invoke shortcuts CLI' "${tmp}" || {
  echo "FAIL: missing negative shortcuts CLI assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'widget shortcut status script does not shell-invoke osascript' "${tmp}" || {
  echo "FAIL: missing negative osascript assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/widget-shortcut-builder-cli.XXXXXX")"
bin/chief-of-staff --widget-shortcut-status >"${tmp}" 2>&1 || {
  echo "FAIL: --widget-shortcut-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --widget-shortcut-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Widget and Shortcut Builder status tests passed."
