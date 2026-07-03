#!/usr/bin/env bash
# Tests for Phase 2 production registry preflight status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Phase 2 production registry preflight status tests..."

status_script="scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-phase2-preflight-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: phase 2 preflight status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: phase 2 preflight status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Record writes via tooling: blocked' "${tmp}" || {
  echo "FAIL: missing blocked writes banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'PASS does not authorize registry mutation: yes' "${tmp}" || {
  echo "FAIL: missing non-mutation banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'production-registry.json exists with one approved record' "${tmp}" || {
  echo "FAIL: missing production-registry.json one approved record check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'BLOCKED-NO-WRITES.sentinel remains intact' "${tmp}" || {
  echo "FAIL: missing sentinel intact check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'chief-of-staff has no --curriculum-registry-write handler' "${tmp}" || {
  echo "FAIL: missing no write handler check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no production registry writer script exists' "${tmp}" || {
  echo "FAIL: missing no writer script check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'items 3 and 4 approved as manual-only boundaries' "${tmp}" || {
  echo "FAIL: missing metadata boundaries approved PASS"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'metadata pilot execution remains blocked' "${tmp}" || {
  echo "FAIL: missing metadata pilot blocked check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
if grep -q 'items 3 and 4 remain deferred' "${tmp}"; then
  echo "FAIL: unexpected deferred metadata WARN after items 3 and 4 approved"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
fi
rm -f "${tmp}"

if [[ ! -f "${production_registry_path}" ]]; then
  echo "FAIL: production-registry.json must exist with one approved record"
  exit 1
fi

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel must remain present"
  exit 1
fi

if [[ -f "${live_registry}" ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-phase2-live-before.XXXXXX")"
  cp "${live_registry}" "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s "${live_registry}" "${before}"; then
    echo "FAIL: phase 2 preflight status mutated live v0 registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-phase2-preflight-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-phase-2-preflight-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-phase-2-preflight-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI phase 2 preflight status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-phase-2-preflight-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-phase-2-preflight-status"
  exit 1
fi

echo "PASS: Phase 2 production registry preflight status tests passed."
