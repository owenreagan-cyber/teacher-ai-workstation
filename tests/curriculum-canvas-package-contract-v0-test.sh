#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-output-contract-v0-validator.sh"
binding_lookup="scripts/curriculum-binding-v0-lookup.sh"
contract_root="assistant/curriculum-builder/output-contract/v0"

echo "Running Canvas Package Contract v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-canvas-package-contract-v0.out 2>&1; then
  echo "FAIL: output contract validator failed"
  cat /tmp/curriculum-canvas-package-contract-v0.out
  exit 1
fi

grep -q 'canonical canvas export package contract valid' /tmp/curriculum-canvas-package-contract-v0.out || {
  echo "FAIL: validator missing canvas package canonical pass message"
  cat /tmp/curriculum-canvas-package-contract-v0.out
  exit 1
}

grep -q '^FAIL: 0$' /tmp/curriculum-canvas-package-contract-v0.out || {
  echo "FAIL: output contract validator reported failures"
  cat /tmp/curriculum-canvas-package-contract-v0.out
  exit 1
}

bash "${binding_lookup}" sample-canvas-export-folder-001 >/tmp/curriculum-canvas-package-binding-lookup.out
grep -q 'sample-contract-canvas-package-001' /tmp/curriculum-canvas-package-binding-lookup.out || {
  echo "FAIL: binding lookup missing canvas package contract"
  cat /tmp/curriculum-canvas-package-binding-lookup.out
  exit 1
}

tmp_root="$(mktemp -d)"
trap 'rm -rf "${tmp_root}"' EXIT
cp -R "${contract_root}/." "${tmp_root}/"

python3 - "${tmp_root}/contracts/sample-canvas-package-001.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["module_placeholders"][0]["title_placeholder"] = ""
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_root}" >/tmp/curriculum-canvas-package-contract-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject empty title_placeholder"
  cat /tmp/curriculum-canvas-package-contract-v0-bad.out
  exit 1
fi

grep -q 'title_placeholder must be non-empty string' /tmp/curriculum-canvas-package-contract-v0-bad.out || {
  echo "FAIL: bad output missing expected title_placeholder error"
  cat /tmp/curriculum-canvas-package-contract-v0-bad.out
  exit 1
}

echo "PASS: Canvas Package Contract v0 tests passed."
