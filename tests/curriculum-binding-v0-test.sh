#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-binding-v0-validator.sh"
lookup="scripts/curriculum-binding-v0-lookup.sh"
binding_root="assistant/curriculum-builder/binding/v0"
contract_root="assistant/curriculum-builder/output-contract/v0"

echo "Running Curriculum Binding v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-binding-v0-canonical.out 2>&1; then
  echo "FAIL: canonical binding validation failed"
  cat /tmp/curriculum-binding-v0-canonical.out
  exit 1
fi

grep -q '^FAIL: 0$' /tmp/curriculum-binding-v0-canonical.out || {
  echo "FAIL: canonical binding validation reported failures"
  cat /tmp/curriculum-binding-v0-canonical.out
  exit 1
}

grep -q 'sample-contract-di-slide-deck-001' /tmp/curriculum-binding-v0-canonical.out || {
  echo "FAIL: binding validator missing canonical contract reference"
  cat /tmp/curriculum-binding-v0-canonical.out
  exit 1
}

bash "${lookup}" sample-sm5-textbook-001 >/tmp/curriculum-binding-v0-lookup.out
grep -q 'sample-contract-di-slide-deck-001' /tmp/curriculum-binding-v0-lookup.out || {
  echo "FAIL: binding lookup missing expected contract reference"
  cat /tmp/curriculum-binding-v0-lookup.out
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

tmp_manifest="$(mktemp)"
trap 'rm -rf "${tmp_root}" "${tmp_manifest}"' EXIT
python3 - "${binding_root}/binding-manifest.json" "${tmp_root}" "${tmp_manifest}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)

manifest["contract_root"] = sys.argv[2]
manifest["contract_manifest"] = f"{sys.argv[2]}/placeholder-manifest.json"
with open(sys.argv[3], "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)
    handle.write("\n")
PY

tmp_binding="$(mktemp -d)"
cp "${tmp_manifest}" "${tmp_binding}/binding-manifest.json"

set +e
bash "${validator}" "${tmp_binding}" >/tmp/curriculum-binding-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: binding validator should reject invalid registry reference"
  cat /tmp/curriculum-binding-v0-bad.out
  exit 1
fi

grep -q 'registry reference not found' /tmp/curriculum-binding-v0-bad.out || {
  echo "FAIL: bad binding output missing expected registry reference error"
  cat /tmp/curriculum-binding-v0-bad.out
  exit 1
}

if grep -qiE 'https?://' /tmp/curriculum-binding-v0-canonical.out; then
  echo "FAIL: binding validator output must not perform network resolution"
  exit 1
fi

bin/chief-of-staff --curriculum-binding-v0-status >/tmp/curriculum-binding-v0-status.out
grep -q '^FAIL: 0$' /tmp/curriculum-binding-v0-status.out || {
  echo "FAIL: chief-of-staff binding v0 status reported failures"
  cat /tmp/curriculum-binding-v0-status.out
  exit 1
}

bin/chief-of-staff --curriculum-binding-v0-validate >/tmp/curriculum-binding-v0-validate.out
grep -q '^FAIL: 0$' /tmp/curriculum-binding-v0-validate.out || {
  echo "FAIL: chief-of-staff binding v0 validate reported failures"
  cat /tmp/curriculum-binding-v0-validate.out
  exit 1
}

bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-textbook-001 >/tmp/curriculum-binding-v0-cos-lookup.out
grep -q 'sample-contract-di-slide-deck-001' /tmp/curriculum-binding-v0-cos-lookup.out || {
  echo "FAIL: chief-of-staff binding v0 lookup missing expected contract"
  cat /tmp/curriculum-binding-v0-cos-lookup.out
  exit 1
}

echo "PASS: Curriculum Binding v0 tests passed."
