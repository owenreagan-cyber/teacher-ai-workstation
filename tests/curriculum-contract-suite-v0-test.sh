#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

validator="scripts/curriculum-output-contract-v0-validator.sh"
binding_validator="scripts/curriculum-binding-v0-validator.sh"
binding_lookup="scripts/curriculum-binding-v0-lookup.sh"

expected_contracts=(
  sample-contract-di-slide-deck-001
  sample-contract-teacher-script-001
  sample-contract-worksheet-001
  sample-contract-review-game-001
  sample-contract-canvas-package-001
)

expected_pass_messages=(
  "canonical direct instruction slide deck contract valid"
  "canonical teacher script contract valid"
  "canonical worksheet contract valid"
  "canonical review game contract valid"
  "canonical canvas export package contract valid"
)

echo "Running Curriculum Contract Suite v0 tests..."

for test_script in \
  tests/curriculum-output-contract-v0-test.sh \
  tests/curriculum-teacher-script-contract-v0-test.sh \
  tests/curriculum-worksheet-contract-v0-test.sh \
  tests/curriculum-review-game-contract-v0-test.sh \
  tests/curriculum-canvas-package-contract-v0-test.sh \
  tests/curriculum-binding-v0-test.sh \
  tests/curriculum-registry-v0-test.sh; do
  bash "${test_script}" >/dev/null
done

bash "${validator}" >/tmp/curriculum-contract-suite-validator.out
grep -q '^FAIL: 0$' /tmp/curriculum-contract-suite-validator.out || {
  echo "FAIL: output contract validator reported failures"
  cat /tmp/curriculum-contract-suite-validator.out
  exit 1
}

for message in "${expected_pass_messages[@]}"; do
  grep -q "${message}" /tmp/curriculum-contract-suite-validator.out || {
    echo "FAIL: validator missing pass message: ${message}"
    cat /tmp/curriculum-contract-suite-validator.out
    exit 1
  }
done

bash "${binding_validator}" >/tmp/curriculum-contract-suite-binding.out
grep -q '^FAIL: 0$' /tmp/curriculum-contract-suite-binding.out || {
  echo "FAIL: binding validator reported failures"
  cat /tmp/curriculum-contract-suite-binding.out
  exit 1
}

grep -q 'validated 5 contracts against 7 registry records' /tmp/curriculum-contract-suite-binding.out || {
  echo "FAIL: binding validator missing five-contract validation proof"
  cat /tmp/curriculum-contract-suite-binding.out
  exit 1
}

bash "${binding_lookup}" >/tmp/curriculum-contract-suite-lookup.out
for contract_id in "${expected_contracts[@]}"; do
  grep -q "${contract_id}" /tmp/curriculum-contract-suite-lookup.out || {
    echo "FAIL: binding lookup missing contract ${contract_id}"
    cat /tmp/curriculum-contract-suite-lookup.out
    exit 1
  }
done

echo "PASS: Curriculum Contract Suite v0 tests passed."
