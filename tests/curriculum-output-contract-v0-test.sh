#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-output-contract-v0-validator.sh"
contract_root="assistant/curriculum-builder/output-contract/v0"
canonical="${contract_root}/contracts/sample-di-slide-deck-001.json"

echo "Running Curriculum Output Contract v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-output-contract-v0-canonical.out 2>&1; then
  echo "FAIL: canonical contract validation failed"
  cat /tmp/curriculum-output-contract-v0-canonical.out
  exit 1
fi

grep -q '^FAIL: 0$' /tmp/curriculum-output-contract-v0-canonical.out || {
  echo "FAIL: canonical contract validation reported failures"
  cat /tmp/curriculum-output-contract-v0-canonical.out
  exit 1
}

tmp_root="$(mktemp -d)"
trap 'rm -rf "${tmp_root}"' EXIT
cp -R "${contract_root}/." "${tmp_root}/"

python3 - "${tmp_root}/contracts/sample-di-slide-deck-001.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["registry_references"] = ["sample-nonexistent-registry-001"]
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_root}" >/tmp/curriculum-output-contract-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject invalid registry reference"
  cat /tmp/curriculum-output-contract-v0-bad.out
  exit 1
fi

grep -q 'registry reference not found' /tmp/curriculum-output-contract-v0-bad.out || {
  echo "FAIL: bad contract output missing expected registry reference error"
  cat /tmp/curriculum-output-contract-v0-bad.out
  exit 1
}

bin/chief-of-staff --curriculum-output-contract-v0-status >/tmp/curriculum-output-contract-v0-status.out
grep -q '^FAIL: 0$' /tmp/curriculum-output-contract-v0-status.out || {
  echo "FAIL: chief-of-staff output contract v0 status reported failures"
  cat /tmp/curriculum-output-contract-v0-status.out
  exit 1
}

bin/chief-of-staff --curriculum-output-contract-v0-validate >/tmp/curriculum-output-contract-v0-validate.out
grep -q '^FAIL: 0$' /tmp/curriculum-output-contract-v0-validate.out || {
  echo "FAIL: chief-of-staff output contract v0 validate reported failures"
  cat /tmp/curriculum-output-contract-v0-validate.out
  exit 1
}

echo "PASS: Curriculum Output Contract v0 tests passed."
