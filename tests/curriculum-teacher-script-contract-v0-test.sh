#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-output-contract-v0-validator.sh"
binding_lookup="scripts/curriculum-binding-v0-lookup.sh"
contract_root="assistant/curriculum-builder/output-contract/v0"
sample="${contract_root}/contracts/sample-teacher-script-001.json"

echo "Running Teacher Script Contract v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-teacher-script-contract-v0.out 2>&1; then
  echo "FAIL: output contract validator failed"
  cat /tmp/curriculum-teacher-script-contract-v0.out
  exit 1
fi

grep -q 'canonical teacher script contract valid' /tmp/curriculum-teacher-script-contract-v0.out || {
  echo "FAIL: validator missing teacher script canonical pass message"
  cat /tmp/curriculum-teacher-script-contract-v0.out
  exit 1
}

grep -q 'canonical direct instruction slide deck contract valid' /tmp/curriculum-teacher-script-contract-v0.out || {
  echo "FAIL: DI slide deck contract no longer validates"
  cat /tmp/curriculum-teacher-script-contract-v0.out
  exit 1
}

grep -q '^FAIL: 0$' /tmp/curriculum-teacher-script-contract-v0.out || {
  echo "FAIL: output contract validator reported failures"
  cat /tmp/curriculum-teacher-script-contract-v0.out
  exit 1
}

bash "${binding_lookup}" sample-sm5-textbook-001 >/tmp/curriculum-teacher-script-binding-lookup.out
grep -q 'sample-contract-teacher-script-001' /tmp/curriculum-teacher-script-binding-lookup.out || {
  echo "FAIL: binding lookup missing teacher script contract"
  cat /tmp/curriculum-teacher-script-binding-lookup.out
  exit 1
}
grep -q 'sample-contract-di-slide-deck-001' /tmp/curriculum-teacher-script-binding-lookup.out || {
  echo "FAIL: binding lookup missing DI slide deck contract"
  cat /tmp/curriculum-teacher-script-binding-lookup.out
  exit 1
}

tmp_root="$(mktemp -d)"
trap 'rm -rf "${tmp_root}"' EXIT
cp -R "${contract_root}/." "${tmp_root}/"

python3 - "${tmp_root}/contracts/sample-teacher-script-001.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["script_sections"][0]["teacher_script"] = ""
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_root}" >/tmp/curriculum-teacher-script-contract-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject empty teacher_script"
  cat /tmp/curriculum-teacher-script-contract-v0-bad.out
  exit 1
fi

grep -q 'teacher_script must be non-empty string' /tmp/curriculum-teacher-script-contract-v0-bad.out || {
  echo "FAIL: bad output missing expected teacher_script error"
  cat /tmp/curriculum-teacher-script-contract-v0-bad.out
  exit 1
}

python3 - "${tmp_root}/contracts/sample-teacher-script-001.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["script_sections"][0]["teacher_script"] = "Teacher script placeholder text only for lesson opener"
data["registry_references"] = ["sample-nonexistent-registry-001"]
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_root}" >/tmp/curriculum-teacher-script-contract-v0-bad-ref.out 2>&1
bad_ref_status=$?
set -e

if [[ "${bad_ref_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject invalid registry reference"
  cat /tmp/curriculum-teacher-script-contract-v0-bad-ref.out
  exit 1
fi

grep -q 'registry reference not found' /tmp/curriculum-teacher-script-contract-v0-bad-ref.out || {
  echo "FAIL: bad output missing expected registry reference error"
  cat /tmp/curriculum-teacher-script-contract-v0-bad-ref.out
  exit 1
}

echo "PASS: Teacher Script Contract v0 tests passed."
