#!/usr/bin/env bash
# Lightweight tests for Lovable Classroom App Builder read-only planning foundation (Program G1).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Lovable Classroom App Builder status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/lovable-classroom-app-builder-status.XXXXXX")"
bash scripts/lovable-classroom-app-builder-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: lovable-classroom-app-builder-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: lovable-classroom-app-builder-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'read-only planning only' "${tmp}" || {
  echo "FAIL: missing read-only planning boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no Lovable API call attempted' "${tmp}" || {
  echo "FAIL: missing negative Lovable API assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/lovable-classroom-app-builder-cli.XXXXXX")"
bin/chief-of-staff --lovable-status >"${tmp}" 2>&1 || {
  echo "FAIL: --lovable-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --lovable-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Lovable Classroom App Builder status tests passed."
