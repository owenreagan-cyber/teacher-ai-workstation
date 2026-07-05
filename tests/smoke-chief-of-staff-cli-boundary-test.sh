#!/usr/bin/env bash
# Assert smoke-chief-of-staff-cli.sh stays in the fast-smoke tier.
set -euo pipefail

smoke_file="tests/smoke-chief-of-staff-cli.sh"

if [[ ! -f "${smoke_file}" ]]; then
  echo "FAIL: missing ${smoke_file}"
  exit 1
fi

# Executable invocation lines only; comments and boundary-guard lines are ignored.
executable_lines="$(grep -v '^[[:space:]]*#' "${smoke_file}" \
  | grep -E 'bin/chief-of-staff|bash (scripts|tests)/' \
  | grep -v 'Boundary guard')"

forbidden=(
  '--dashboard'
  '--validate-all'
  'whole-system-coherence'
  'teacher-knowledge-vault-m'
  'chief-of-staff-dashboard.sh'
  'validate-all.sh'
  'curriculum-contract-suite-v0-test.sh'
)

for pattern in "${forbidden[@]}"; do
  if printf '%s\n' "${executable_lines}" | grep -q -F -e "${pattern}"; then
    echo "FAIL: smoke file must not reference deep validation: ${pattern}"
    grep -nF "${pattern}" "${smoke_file}" | grep -E 'bin/chief-of-staff|bash (scripts|tests)/' || true
    exit 1
  fi
done

echo "PASS: smoke-chief-of-staff-cli.sh boundary checks"
