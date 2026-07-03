#!/usr/bin/env bash
# Tests for whole-system master roadmap build-state status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running whole-system master roadmap status tests..."

status_script="scripts/whole-system-master-roadmap-status.sh"
report="docs/whole-system-master-roadmap-build-state-report.md"

tmp="$(mktemp "${TMPDIR:-/tmp}/whole-system-master-roadmap-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: whole-system-master-roadmap-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'whole_system_master_roadmap_status_complete' "${tmp}" || { echo "FAIL: missing closure status"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/whole-system-master-roadmap-cli.XXXXXX")"
bin/chief-of-staff --whole-system-master-roadmap-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --whole-system-master-roadmap-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--whole-system-master-roadmap-status'; then
  echo "FAIL: --help missing --whole-system-master-roadmap-status"
  exit 1
fi

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/whole-system-master-roadmap-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--whole-system-master-roadmap-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --whole-system-master-roadmap-status"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

if ! grep -Fq -- '"--whole-system-master-roadmap-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing whole-system master roadmap status command"
  exit 1
fi

if ! grep -Fq -- 'whole_system_master_roadmap_status_complete' "${report}"; then
  echo "FAIL: report missing closure marker"
  exit 1
fi

if ! grep -Fq -- 'next_safe_lane_selector_complete' "${report}"; then
  echo "FAIL: report missing next safe lane selector closure"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

echo "PASS: whole-system master roadmap status tests complete"
