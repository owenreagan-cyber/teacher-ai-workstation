#!/usr/bin/env bash
# Tests for production registry empty-file status (historical milestone).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running production registry empty-file status tests..."

status_script="scripts/curriculum-builder-production-registry-empty-file-status.sh"
validator="scripts/curriculum-builder-production-registry-empty-file-validate.sh"
pre_write_snapshot="assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-empty-file-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: empty-file status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: empty-file status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'empty_file_historical_complete' "${tmp}" || {
  echo "FAIL: missing empty file historical complete banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'PASS does not authorize write tooling: yes' "${tmp}" || {
  echo "FAIL: missing non-write-tooling banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'pre-write snapshot validates as empty shell' "${tmp}" || {
  echo "FAIL: missing pre-write snapshot validation check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'CLI exposes first-record status successor' "${tmp}" || {
  echo "FAIL: missing first-record successor check"
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
rm -f "${tmp}"

if [[ ! -f "${pre_write_snapshot}" ]]; then
  echo "FAIL: pre-write snapshot must exist"
  exit 1
fi

if ! python3 -c "
import json
with open('${pre_write_snapshot}') as f:
    d = json.load(f)
assert d.get('records') == []
"; then
  echo "FAIL: pre-write snapshot must be valid empty shell"
  exit 1
fi

if [[ ! -f "${sentinel}" ]]; then
  echo "FAIL: BLOCKED-NO-WRITES.sentinel must remain present"
  exit 1
fi

val_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-empty-file-val.XXXXXX")"
bash "${validator}" "${pre_write_snapshot}" >"${val_tmp}" 2>&1 || {
  echo "FAIL: validator exited nonzero on pre-write snapshot"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
grep -q 'empty shell validation succeeded' "${val_tmp}" || {
  echo "FAIL: validator did not succeed on pre-write snapshot"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
rm -f "${val_tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-empty-file-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-empty-file-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-empty-file-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI empty-file status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-empty-file-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-empty-file-status"
  exit 1
fi

echo "PASS: Production registry empty-file status tests passed."
