#!/usr/bin/env bash
# Lightweight tests for Program B2–B5 daily operations commands.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Chief of Staff daily operations command tests..."

for cmd in --daily-status --closeout --approval-queue --blocker-queue --mode-status; do
  tmp="$(mktemp "${TMPDIR:-/tmp}/chief-of-staff-daily-${cmd#--}.XXXXXX")"
  bin/chief-of-staff "${cmd}" >"${tmp}" 2>&1 || {
    echo "FAIL: ${cmd} exited nonzero"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  grep -q '^FAIL: 0$' "${tmp}" || {
    echo "FAIL: ${cmd} reported failures"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  rm -f "${tmp}"
done

echo "PASS: Chief of Staff daily operations command tests passed."
