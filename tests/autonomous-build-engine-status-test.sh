#!/usr/bin/env bash
# Tests for Autonomous Build Engine governance status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Autonomous Build Engine status tests..."

status_script="scripts/autonomous-build-engine-status.sh"
governance_doc="docs/cursor-autonomous-build-engine.md"

tmp="$(mktemp "${TMPDIR:-/tmp}/autonomous-build-engine-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: autonomous-build-engine-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Autonomous Build Engine' "${tmp}" || { echo "FAIL: missing autonomous build engine header context"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/autonomous-build-engine-cli.XXXXXX")"
bin/chief-of-staff --autonomous-build-engine-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --autonomous-build-engine-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--autonomous-build-engine-status'; then
  echo "FAIL: --help missing --autonomous-build-engine-status"
  exit 1
fi

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/autonomous-build-engine-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--autonomous-build-engine-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --autonomous-build-engine-status"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

if ! grep -Fq -- '"--autonomous-build-engine-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing autonomous build engine status command"
  exit 1
fi

grep -q 'complete_autonomous_build_engine_governance' "${governance_doc}" || {
  echo "FAIL: governance doc missing closure status"
  exit 1
}

if grep -Fq -- '--write)' "${status_script}" 2>/dev/null; then
  if ! grep -Fq "grep -Fq" "${status_script}" 2>/dev/null; then
    echo "FAIL: status script implements --write"
    exit 1
  fi
fi

echo "PASS: Autonomous Build Engine status tests passed."
