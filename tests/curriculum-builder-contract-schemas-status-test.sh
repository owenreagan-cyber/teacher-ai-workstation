#!/usr/bin/env bash
# Lightweight tests for Curriculum Builder metadata contract schemas (Programs A4–A7).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder contract schemas status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-contract-schemas-status.XXXXXX")"
bash scripts/curriculum-builder-contract-schemas-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: curriculum-builder-contract-schemas-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: curriculum-builder-contract-schemas-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'read-only planning only' "${tmp}" || {
  echo "FAIL: missing read-only planning boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no network call attempted' "${tmp}" || {
  echo "FAIL: missing negative network assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'contract schemas status script does not shell-invoke curl' "${tmp}" || {
  echo "FAIL: missing negative curl assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no lesson generation attempted' "${tmp}" || {
  echo "FAIL: missing negative lesson generation assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'contract schemas status script does not shell-invoke find' "${tmp}" || {
  echo "FAIL: missing negative folder scan assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-contract-schemas-cli.XXXXXX")"
bin/chief-of-staff --curriculum-contracts-status >"${tmp}" 2>&1 || {
  echo "FAIL: --curriculum-contracts-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --curriculum-contracts-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-contract-schemas-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--curriculum-contracts-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --curriculum-contracts-status"
  cat "${cmds_tmp}"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

help_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-contract-schemas-help.XXXXXX")"
bin/chief-of-staff --help >"${help_tmp}" 2>&1 || true
if ! grep -Fq -- '--curriculum-contracts-status' "${help_tmp}"; then
  echo "FAIL: --help does not list --curriculum-contracts-status"
  cat "${help_tmp}"
  rm -f "${help_tmp}"
  exit 1
fi
rm -f "${help_tmp}"

echo "PASS: Curriculum Builder contract schemas status tests passed."
