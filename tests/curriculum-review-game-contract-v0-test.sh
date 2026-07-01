#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-output-contract-v0-validator.sh"
binding_lookup="scripts/curriculum-binding-v0-lookup.sh"
contract_root="assistant/curriculum-builder/output-contract/v0"

echo "Running Review Game Contract v0 tests..."

if ! bash "${validator}" >/tmp/curriculum-review-game-contract-v0.out 2>&1; then
  echo "FAIL: output contract validator failed"
  cat /tmp/curriculum-review-game-contract-v0.out
  exit 1
fi

grep -q 'canonical review game contract valid' /tmp/curriculum-review-game-contract-v0.out || {
  echo "FAIL: validator missing review game canonical pass message"
  cat /tmp/curriculum-review-game-contract-v0.out
  exit 1
}

grep -q '^FAIL: 0$' /tmp/curriculum-review-game-contract-v0.out || {
  echo "FAIL: output contract validator reported failures"
  cat /tmp/curriculum-review-game-contract-v0.out
  exit 1
}

bash "${binding_lookup}" sample-student-practice-001 >/tmp/curriculum-review-game-binding-lookup.out
grep -q 'sample-contract-review-game-001' /tmp/curriculum-review-game-binding-lookup.out || {
  echo "FAIL: binding lookup missing review game contract"
  cat /tmp/curriculum-review-game-binding-lookup.out
  exit 1
}

tmp_root="$(mktemp -d)"
trap 'rm -rf "${tmp_root}"' EXIT
cp -R "${contract_root}/." "${tmp_root}/"

python3 - "${tmp_root}/contracts/sample-review-game-001.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

data["round_placeholders"][0]["question_placeholder"] = ""
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY

set +e
bash "${validator}" "${tmp_root}" >/tmp/curriculum-review-game-contract-v0-bad.out 2>&1
bad_status=$?
set -e

if [[ "${bad_status}" -eq 0 ]]; then
  echo "FAIL: validator should reject empty question_placeholder"
  cat /tmp/curriculum-review-game-contract-v0-bad.out
  exit 1
fi

grep -q 'question_placeholder must be non-empty string' /tmp/curriculum-review-game-contract-v0-bad.out || {
  echo "FAIL: bad output missing expected question_placeholder error"
  cat /tmp/curriculum-review-game-contract-v0-bad.out
  exit 1
}

echo "PASS: Review Game Contract v0 tests passed."
