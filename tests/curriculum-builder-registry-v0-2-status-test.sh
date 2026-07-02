#!/usr/bin/env bash
# Lightweight tests for Curriculum Builder Registry v0.2 dry-run status and CLI.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry v0.2 status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-status.XXXXXX")"
bash scripts/curriculum-builder-registry-v0-2-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: curriculum-builder-registry-v0-2-status.sh exited nonzero"
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
grep -q 'dry-run validation only' "${tmp}" || {
  echo "FAIL: missing dry-run boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'PASS does not authorize promotion: yes' "${tmp}" || {
  echo "FAIL: missing PASS does not authorize promotion banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no registry write attempted' "${tmp}" || {
  echo "FAIL: missing negative registry write assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'dry-run validator has no --write flag' "${tmp}" || {
  echo "FAIL: missing --write negative assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-dry-run-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-registry-dry-run-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--curriculum-registry-dry-run-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --curriculum-registry-dry-run-status"
  cat "${cmds_tmp}"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

help_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-help.XXXXXX")"
bin/chief-of-staff --help >"${help_tmp}" 2>&1 || true
if ! grep -Fq -- '--curriculum-registry-dry-run-status' "${help_tmp}"; then
  echo "FAIL: --help does not list --curriculum-registry-dry-run-status"
  cat "${help_tmp}"
  rm -f "${help_tmp}"
  exit 1
fi
rm -f "${help_tmp}"

echo "PASS: Curriculum Builder Registry v0.2 status tests passed."
