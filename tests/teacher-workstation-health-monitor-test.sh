#!/usr/bin/env bash
# Lightweight tests for Teacher Workstation Health Monitor read-only surfaces.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Workstation Health Monitor tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/health-monitor-status.XXXXXX")"
bash scripts/teacher-workstation-health-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: teacher-workstation-health-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: health status script reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'observe and report only' "${tmp}" || {
  echo "FAIL: health status missing observe-only header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Health vs Updater' "${tmp}" || {
  echo "FAIL: health status missing health vs updater boundary banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Canvas LLM: frozen' "${tmp}" || {
  echo "FAIL: health status missing canvas frozen banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

for cmd in --system-health --workstation-health; do
  tmp="$(mktemp "${TMPDIR:-/tmp}/health-monitor-${cmd#--}.XXXXXX")"
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

echo "PASS: Teacher Workstation Health Monitor tests passed."
