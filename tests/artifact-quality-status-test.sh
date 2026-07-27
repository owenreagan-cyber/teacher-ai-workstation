#!/usr/bin/env bash
# Tests for Instructional Artifact Quality status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running artifact quality status tests..."

status_script="scripts/artifact-quality-status.sh"
for required in "${status_script}" docs/instructional-artifact-quality-operator-guide.md; do
  [[ -f "${required}" ]] || { echo "FAIL: missing ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/artifact-quality-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: artifact-quality-status.sh exited nonzero"
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

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/artifact-quality-cli.XXXXXX")"
bin/chief-of-staff --artifact-quality-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --artifact-quality-status exited nonzero"
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

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--artifact-quality-status' || {
  echo "FAIL: --help missing --artifact-quality-status"
  exit 1
}

echo "PASS: artifact quality status tests complete"
