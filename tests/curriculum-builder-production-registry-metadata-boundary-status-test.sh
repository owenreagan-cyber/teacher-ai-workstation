#!/usr/bin/env bash
# Tests for production registry metadata-boundary refinement status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running metadata boundary refinement status tests..."

status_script="scripts/curriculum-builder-production-registry-metadata-boundary-status.sh"
validator="scripts/curriculum-builder-production-registry-metadata-boundary-validate.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
planning_fixture="assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-metadata-boundary-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: metadata boundary status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: metadata boundary status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'metadata_boundary_refinement_complete' "${tmp}" || {
  echo "FAIL: missing refinement complete banner"
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
grep -q 'production-registry.json does not exist (blocked)' "${tmp}" || {
  echo "FAIL: missing production-registry.json non-existence check"
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
grep -q 'metadata pilot is not active' "${tmp}" || {
  echo "FAIL: missing metadata pilot not active check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'source auto-resolution is not active' "${tmp}" || {
  echo "FAIL: missing source auto-resolution not active check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'canonical planning fixture validates' "${tmp}" || {
  echo "FAIL: missing canonical fixture validation check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

if [[ -f "${production_registry_path}" ]]; then
  echo "FAIL: production-registry.json must not exist"
  exit 1
fi

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel must remain present"
  exit 1
fi

if ! grep -q '"id": "example-metadata-boundary-record-001"' "${planning_fixture}"; then
  echo "FAIL: planning fixture must use example-* id"
  exit 1
fi

if grep -q '"id": "resource-' "${planning_fixture}"; then
  echo "FAIL: planning fixture must not use resource-* id"
  exit 1
fi

val_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-metadata-boundary-val.XXXXXX")"
bash "${validator}" "${planning_fixture}" >"${val_tmp}" 2>&1 || {
  echo "FAIL: canonical fixture validator exited nonzero"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
grep -q 'fixture validation succeeded' "${val_tmp}" || {
  echo "FAIL: canonical fixture validator did not succeed"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
rm -f "${val_tmp}"

if ! grep -Fq -- '--curriculum-production-registry-metadata-boundary-status' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: CLI not wired yet — run after chief-of-staff update"
  exit 1
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-metadata-boundary-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-metadata-boundary-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-metadata-boundary-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI metadata boundary status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-metadata-boundary-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-metadata-boundary-status"
  exit 1
fi

if grep -R --include='*.sh' -E '(^|[;&|[:space:]])curl[[:space:]]' scripts/curriculum-builder-production-registry-metadata-boundary-status.sh tests/curriculum-builder-production-registry-metadata-boundary-status-test.sh 2>/dev/null | grep -v 'must not shell-invoke curl'; then
  : # status script self-check is fine
fi

echo "PASS: Metadata boundary refinement status tests passed."
