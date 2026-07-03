#!/usr/bin/env bash
# Lightweight tests for Mac Workstation Experience read-only foundation (Program E1).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Mac Workstation Experience status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/mac-workstation-experience-status.XXXXXX")"
bash scripts/mac-workstation-experience-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: mac-workstation-experience-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: mac-workstation-experience-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Planning-only: yes' "${tmp}" || {
  echo "FAIL: missing planning-only banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Widget/Shortcut lane (F1)' "${tmp}" || {
  echo "FAIL: missing F1 widget cross-link banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'does not shell-invoke PlistBuddy' "${tmp}" || {
  echo "FAIL: missing negative PlistBuddy assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no Mac system mutation attempted' "${tmp}" || {
  echo "FAIL: missing negative Mac mutation assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/mac-workstation-cli.XXXXXX")"
bin/chief-of-staff --mac-workstation-status >"${tmp}" 2>&1 || {
  echo "FAIL: --mac-workstation-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --mac-workstation-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Mac Workstation Experience status tests passed."
