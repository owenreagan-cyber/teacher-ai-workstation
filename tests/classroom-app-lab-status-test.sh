#!/usr/bin/env bash
# Lightweight tests for Classroom App Lab read-only prototype rescue foundation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Classroom App Lab status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/classroom-app-lab-status.XXXXXX")"
bash scripts/classroom-app-lab-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: classroom-app-lab-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: classroom-app-lab-status.sh reported failures"
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
grep -q 'no zip extraction attempted' "${tmp}" || {
  echo "FAIL: missing negative zip extraction assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no automatic Cursor execution attempted' "${tmp}" || {
  echo "FAIL: missing negative automatic Cursor execution assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/classroom-app-lab-cli.XXXXXX")"
bin/chief-of-staff --classroom-app-lab-status >"${tmp}" 2>&1 || {
  echo "FAIL: --classroom-app-lab-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --classroom-app-lab-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Classroom App Lab status tests passed."
