#!/usr/bin/env bash
# Tests for Owen § J production registry approval checklist tracker status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Owen production registry checklist tracker tests..."

status_script="scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
tmp="$(mktemp "${TMPDIR:-/tmp}/cb-owen-checklist-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: owen checklist status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: owen checklist status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Owen approval: required for each checklist item' "${tmp}" || {
  echo "FAIL: missing Owen approval boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '11 Owen checklist items pending approval' "${tmp}" || {
  echo "FAIL: missing expected pending checklist WARN"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'doc mentions build queue product-decision wall' "${tmp}" || {
  echo "FAIL: missing build queue product-decision wall coherence check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'doc mentions decision worksheet non-approval' "${tmp}" || {
  echo "FAIL: missing decision worksheet coherence check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-owen-checklist-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-owen-checklist-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI owen checklist status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-owen-checklist-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-owen-checklist-status"
  exit 1
fi

echo "PASS: Owen production registry checklist tracker tests passed."
