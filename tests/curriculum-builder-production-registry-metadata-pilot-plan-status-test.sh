#!/usr/bin/env bash
# Tests for metadata pilot execution planning status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running metadata pilot execution planning status tests..."

status_script="scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-metadata-pilot-plan-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: metadata pilot plan status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: metadata pilot plan status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'metadata_pilot_execution_plan_complete' "${tmp}" || {
  echo "FAIL: missing pilot plan complete banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Records array: empty' "${tmp}" || {
  echo "FAIL: missing empty records banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'PASS does not authorize metadata pilot execution: yes' "${tmp}" || {
  echo "FAIL: missing non-execution banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'production-registry.json validates as empty shell' "${tmp}" || {
  echo "FAIL: missing empty shell validation check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'no resource-* production record files exist' "${tmp}" || {
  echo "FAIL: missing no resource files check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'BLOCKED-NO-WRITES.sentinel remains intact' "${tmp}" || {
  echo "FAIL: missing sentinel intact check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'chief-of-staff has no --curriculum-registry-write handler' "${tmp}" || {
  echo "FAIL: missing no write handler check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'metadata pilot execution is not active' "${tmp}" || {
  echo "FAIL: missing metadata pilot not active assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

if [[ ! -f "${production_registry_path}" ]]; then
  echo "FAIL: production-registry.json must exist"
  exit 1
fi

if ! python3 -c "
import json
with open('${production_registry_path}') as f:
    d = json.load(f)
assert d.get('records') == []
"; then
  echo "FAIL: production-registry.json records must remain empty"
  exit 1
fi

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel must remain present"
  exit 1
fi

if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  echo "FAIL: writer scripts must not exist"
  exit 1
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-metadata-pilot-plan-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-metadata-pilot-plan-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-metadata-pilot-plan-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI metadata pilot plan status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-metadata-pilot-plan-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-metadata-pilot-plan-status"
  exit 1
fi

echo "PASS: Metadata pilot execution planning status tests passed."
