#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
expected='[local-script-tool] placeholder: tool ran successfully'
actual="$(bash "${script_dir}/tool.sh")"

if [[ "${actual}" != "${expected}" ]]; then
  printf 'Expected: %s\n' "${expected}" >&2
  printf 'Actual: %s\n' "${actual}" >&2
  exit 1
fi

printf '[local-script-tool] test passed\n'
