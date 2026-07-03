#!/usr/bin/env bash
# Tests for production registry first-record status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running production registry first-record status tests..."

status_script="scripts/curriculum-builder-production-registry-first-record-status.sh"
validator="scripts/curriculum-builder-production-registry-first-record-validate.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
pre_write_snapshot="assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
APPROVED_ID="resource-math-lesson-108-presentation"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-first-record-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: first-record status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: first-record status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'first_record_complete' "${tmp}" || {
  echo "FAIL: missing first record complete banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Records count: exactly 1' "${tmp}" || {
  echo "FAIL: missing records count banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'production-registry.json validates as one approved record' "${tmp}" || {
  echo "FAIL: missing one-record validation check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'records count is exactly 1' "${tmp}" || {
  echo "FAIL: missing record count check"
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
grep -Fq 'no second production record authorized' "${tmp}" || {
  echo "FAIL: missing no second record assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'audit diff narrative: 0 to 1 record' "${tmp}" || {
  echo "FAIL: missing audit diff narrative check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'first-record validator negative tests pass' "${tmp}" || {
  echo "FAIL: missing negative validator test check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'doc mentions sentinel not zero-records-only' "${tmp}" || {
  echo "FAIL: missing sentinel semantics check"
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
assert len(d.get('records', [])) == 1
assert d['records'][0]['id'] == '${APPROVED_ID}'
assert d['records'][0]['review_state'] == 'approved'
assert d['records'][0]['audience'] == 'teacher_facing'
assert d['records'][0]['source_reference']['source_type'] == 'manual_label'
"; then
  echo "FAIL: production-registry.json must contain exactly one approved record"
  exit 1
fi

if [[ ! -f "${pre_write_snapshot}" ]]; then
  echo "FAIL: pre-write snapshot must exist"
  exit 1
fi

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel must remain present"
  exit 1
fi

val_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-first-record-val.XXXXXX")"
bash "${validator}" "${production_registry_path}" >"${val_tmp}" 2>&1 || {
  echo "FAIL: validator exited nonzero"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
grep -q 'first production registry record validation succeeded' "${val_tmp}" || {
  echo "FAIL: validator did not succeed"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
rm -f "${val_tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-first-record-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-first-record-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-first-record-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI first-record status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-first-record-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-first-record-status"
  exit 1
fi

echo "PASS: Production registry first-record status tests passed."
