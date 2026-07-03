#!/usr/bin/env bash
# Tests for Curriculum Builder Registry aggregate lane status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry lane status tests..."

status_script="scripts/curriculum-builder-registry-lane-status.sh"
fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-lane-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: lane status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: lane status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'CB-IMPL-1 dry-run' "${tmp}" || { echo "FAIL: missing CB-IMPL-1 component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'CB-IMPL-4 retrieval' "${tmp}" || { echo "FAIL: missing CB-IMPL-4 component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'production registry planning' "${tmp}" || { echo "FAIL: missing planning component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'A4–A7 fixture schema' "${tmp}" || { echo "FAIL: missing A4–A7 component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'curriculum source readiness' "${tmp}" || { echo "FAIL: missing curriculum source readiness component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'production registry governance' "${tmp}" || { echo "FAIL: missing governance component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'production registry Phase 2 preflight' "${tmp}" || { echo "FAIL: missing Phase 2 preflight component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'production registry metadata boundary' "${tmp}" || { echo "FAIL: missing metadata boundary component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Owen § J approval checklist' "${tmp}" || { echo "FAIL: missing Owen checklist component"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-registry-lane-live-before.XXXXXX")"
  cp assistant/curriculum-builder/registry/v0/registry.json "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${before}"; then
    echo "FAIL: lane status mutated live registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

if [[ -f "${fixture}" ]]; then
  before_fixture="$(mktemp "${TMPDIR:-/tmp}/cb-registry-lane-fixture-before.XXXXXX")"
  cp "${fixture}" "${before_fixture}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s "${fixture}" "${before_fixture}"; then
    echo "FAIL: lane status mutated fixture registry"
    rm -f "${before_fixture}"
    exit 1
  fi
  rm -f "${before_fixture}"
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-lane-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-lane-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-registry-lane-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI lane status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-registry-lane-status'; then
  echo "FAIL: --help missing --curriculum-registry-lane-status"
  exit 1
fi

# Existing component commands still work
for flag in \
  --curriculum-registry-dry-run-status \
  --curriculum-registry-records-status \
  --curriculum-registry-renderer-status \
  --curriculum-registry-retrieval-status \
  --curriculum-production-registry-planning-status \
  --curriculum-production-registry-governance-status \
  --curriculum-production-registry-phase-2-preflight-status \
  --curriculum-production-registry-metadata-boundary-status \
  --curriculum-production-registry-empty-file-status \
  --curriculum-production-registry-metadata-pilot-plan-status \
  --curriculum-production-registry-first-record-status \
  --curriculum-production-registry-next-gate-status \
  --curriculum-production-registry-owen-checklist-status \
  --curriculum-source-readiness-status; do
  out="$(mktemp "${TMPDIR:-/tmp}/cb-registry-lane-component.XXXXXX")"
  bin/chief-of-staff "${flag}" >"${out}" 2>&1 || {
    echo "FAIL: ${flag} exited nonzero"
    cat "${out}"
    rm -f "${out}"
    exit 1
  }
  grep -q '^FAIL: 0$' "${out}" || {
    echo "FAIL: ${flag} reported failures"
    cat "${out}"
    rm -f "${out}"
    exit 1
  }
  rm -f "${out}"
done

echo "PASS: Curriculum Builder Registry lane status tests passed."
