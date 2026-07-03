#!/usr/bin/env bash
# Tests for Owen § J production registry approval checklist tracker status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Owen production registry checklist tracker tests..."

status_script="scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
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
grep -q 'Approved governance rows do not authorize production writes: yes' "${tmp}" || {
  echo "FAIL: missing governance non-write boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'No write mission is authorized: yes' "${tmp}" || {
  echo "FAIL: missing no write mission authorized header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '3 Owen checklist items deferred — write behavior, metadata intake, and source references remain blocked' "${tmp}" || {
  echo "FAIL: missing expected deferred checklist WARN"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'path and namespace recorded: 8 approved, 3 deferred' "${tmp}" || {
  echo "FAIL: missing path and namespace recorded PASS"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'production-registry.json does not exist yet (blocked)' "${tmp}" || {
  echo "FAIL: missing production-registry.json non-existence check"
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

if [[ -f "${production_registry_path}" ]]; then
  echo "FAIL: production-registry.json must not exist until write mission"
  exit 1
fi

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
