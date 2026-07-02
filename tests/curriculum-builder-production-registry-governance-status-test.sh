#!/usr/bin/env bash
# Tests for governance-first production registry foundation status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running production registry governance status tests..."

status_script="scripts/curriculum-builder-production-registry-governance-status.sh"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"
fixture_registry="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-prod-gov-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: governance status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: governance status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Production registry writes: blocked' "${tmp}" || {
  echo "FAIL: missing blocked writes banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'PASS does not authorize writes: yes' "${tmp}" || {
  echo "FAIL: missing PASS does not authorize writes banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'candidate path remains non-production' "${tmp}" || {
  echo "FAIL: missing candidate path non-production assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel missing"
  exit 1
fi
grep -q 'Production writes: blocked' "${sentinel}" || {
  echo "FAIL: sentinel must state production writes blocked"
  exit 1
}

if [[ -f "${live_registry}" ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-prod-gov-live-before.XXXXXX")"
  cp "${live_registry}" "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s "${live_registry}" "${before}"; then
    echo "FAIL: governance status mutated live v0 registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

if [[ -f "${fixture_registry}" ]]; then
  before_fixture="$(mktemp "${TMPDIR:-/tmp}/cb-prod-gov-fixture-before.XXXXXX")"
  cp "${fixture_registry}" "${before_fixture}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s "${fixture_registry}" "${before_fixture}"; then
    echo "FAIL: governance status mutated v0.2 fixture registry"
    rm -f "${before_fixture}"
    exit 1
  fi
  rm -f "${before_fixture}"
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-prod-gov-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-governance-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-governance-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI governance status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-governance-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-governance-status"
  exit 1
fi

echo "PASS: Production registry governance status tests passed."
