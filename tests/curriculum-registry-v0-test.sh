#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

registry_file="assistant/curriculum-builder/registry/v0/registry.json"
validator="scripts/curriculum-registry-v0-validator.sh"

echo "Running Curriculum Registry v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-registry-v0-canonical.out 2>&1; then
  echo "FAIL: canonical registry validation failed"
  cat /tmp/curriculum-registry-v0-canonical.out
  exit 1
fi

grep -q '^FAIL: 0$' /tmp/curriculum-registry-v0-canonical.out || {
  echo "FAIL: canonical registry validation reported failures"
  cat /tmp/curriculum-registry-v0-canonical.out
  exit 1
}

tmp_bad="$(mktemp)"
trap 'rm -f "${tmp_bad}"' EXIT
python3 - "${registry_file}" "${tmp_bad}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["records"][0]["registry_id"] = "invalid-id"
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_bad}" >/tmp/curriculum-registry-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject invalid registry_id"
  cat /tmp/curriculum-registry-v0-bad.out
  exit 1
fi

grep -q 'registry_id invalid' /tmp/curriculum-registry-v0-bad.out || {
  echo "FAIL: bad registry output missing expected registry_id error"
  cat /tmp/curriculum-registry-v0-bad.out
  exit 1
}

bin/chief-of-staff --curriculum-registry-v0-status >/tmp/curriculum-registry-v0-status.out
grep -q '^FAIL: 0$' /tmp/curriculum-registry-v0-status.out || {
  echo "FAIL: chief-of-staff registry v0 status reported failures"
  cat /tmp/curriculum-registry-v0-status.out
  exit 1
}

bin/chief-of-staff --curriculum-registry-v0-validate >/tmp/curriculum-registry-v0-validate.out
grep -q '^FAIL: 0$' /tmp/curriculum-registry-v0-validate.out || {
  echo "FAIL: chief-of-staff registry v0 validate reported failures"
  cat /tmp/curriculum-registry-v0-validate.out
  exit 1
}

echo "PASS: Curriculum Registry v0 tests passed."
