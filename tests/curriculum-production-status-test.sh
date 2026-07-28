#!/usr/bin/env bash
# Tests for Curriculum Production Engine status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running curriculum production status tests..."

status_script="scripts/curriculum-production-status.sh"
for required in \
  "${status_script}" \
  docs/curriculum-production-engine-foundation.md \
  configs/curriculum-production/instructional-sequences.yaml; do
  [[ -f "${required}" ]] || { echo "FAIL: missing ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-production-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: curriculum-production-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: status script reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-production-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-status' || {
  echo "FAIL: --help missing --curriculum-production-status"
  exit 1
}

echo "PASS: curriculum production status tests complete"
