#!/usr/bin/env bash
# Lightweight tests for System Updater read-only surfaces.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Teacher Workstation System Updater tests..."

for script in scripts/teacher-workstation-system-updater-status.sh scripts/teacher-workstation-system-update-plan.sh; do
  tmp="$(mktemp "${TMPDIR:-/tmp}/system-updater-script.XXXXXX")"
  bash "${script}" >"${tmp}" 2>&1 || {
    echo "FAIL: ${script} exited nonzero"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  grep -q '^FAIL: 0$' "${tmp}" || {
    echo "FAIL: ${script} reported failures"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  rm -f "${tmp}"
done

for cmd in --system-update-check --system-update-plan; do
  tmp="$(mktemp "${TMPDIR:-/tmp}/system-updater-${cmd#--}.XXXXXX")"
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
  grep -q 'read-only' "${tmp}" || {
    echo "FAIL: ${cmd} missing read-only boundary text"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  rm -f "${tmp}"
done

tmp="$(mktemp "${TMPDIR:-/tmp}/system-updater-check-cli.XXXXXX")"
bin/chief-of-staff --system-update-check >"${tmp}" 2>&1 || {
  echo "FAIL: --system-update-check exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Check-only: yes' "${tmp}" || {
  echo "FAIL: --system-update-check missing check-only banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/system-updater-status-banner.XXXXXX")"
bash scripts/teacher-workstation-system-updater-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: updater status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'does not shell-invoke brew install' "${tmp}" || {
  echo "FAIL: updater status missing negative brew install assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Teacher Workstation System Updater tests passed."
