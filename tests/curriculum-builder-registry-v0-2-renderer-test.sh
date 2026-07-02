#!/usr/bin/env bash
# Tests for Curriculum Builder Registry v0.2 renderer foundation (CB-IMPL-3).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry v0.2 renderer tests..."

preview="scripts/curriculum-builder-registry-v0-2-render-preview.sh"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-renderer.XXXXXX")"
bash "${preview}" markdown >"${tmp}" 2>&1 || {
  echo "FAIL: render preview exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'metadata preview only' "${tmp}" || { echo "FAIL: missing preview boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'example-resource-001' "${tmp}" || { echo "FAIL: missing fake record in preview"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no content generated' "${tmp}" || { echo "FAIL: missing no-generation footer"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-renderer-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-renderer-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-registry-renderer-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: renderer status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q 'no lesson generation attempted' "${cli_tmp}" || { echo "FAIL: missing negative generation assertion"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

echo "PASS: Curriculum Builder Registry v0.2 renderer tests passed."
