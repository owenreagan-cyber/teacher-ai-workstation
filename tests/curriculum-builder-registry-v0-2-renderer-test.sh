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

fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
if [[ -f "${fixture}" ]]; then
  before_fixture="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-renderer-fixture-before.XXXXXX")"
  cp "${fixture}" "${before_fixture}"
  bash "${preview}" markdown >/dev/null 2>&1
  if ! cmp -s "${fixture}" "${before_fixture}"; then
    echo "FAIL: render preview mutated fixture registry"
    rm -f "${before_fixture}"
    exit 1
  fi
  rm -f "${before_fixture}"
fi

renderer_dir="assistant/curriculum-builder/samples/registry-v0-2-renderer"
if [[ -d "${renderer_dir}" ]]; then
  before_list="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-renderer-dir-before.XXXXXX")"
  ls -1 "${renderer_dir}" | sort >"${before_list}"
  bash "${preview}" markdown >/dev/null 2>&1
  after_list="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-renderer-dir-after.XXXXXX")"
  ls -1 "${renderer_dir}" | sort >"${after_list}"
  if ! cmp -s "${before_list}" "${after_list}"; then
    echo "FAIL: render preview wrote files under renderer samples directory"
    rm -f "${before_list}" "${after_list}"
    exit 1
  fi
  rm -f "${before_list}" "${after_list}"
fi

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
