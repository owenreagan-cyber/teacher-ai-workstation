#!/usr/bin/env bash
# Tests for Curriculum Builder Registry v0.2 retrieval hooks (CB-IMPL-4).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry v0.2 retrieval tests..."

retrieval="scripts/curriculum-builder-registry-v0-2-retrieval-check.sh"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-retrieval.XXXXXX")"
bash "${retrieval}" >"${tmp}" 2>&1 || {
  echo "FAIL: retrieval check exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'MATCH:' "${tmp}" || { echo "FAIL: retrieval missing matches"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'local fake-record retrieval only' "${tmp}" || { echo "FAIL: missing retrieval boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

filter_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-retrieval-filter.XXXXXX")"
bash "${retrieval}" --subject "Example Math Course" >"${filter_tmp}" 2>&1 || {
  echo "FAIL: filtered retrieval exited nonzero"
  cat "${filter_tmp}"
  rm -f "${filter_tmp}"
  exit 1
}
grep -q 'example-resource-001' "${filter_tmp}" || { echo "FAIL: filter missing expected record"; cat "${filter_tmp}"; rm -f "${filter_tmp}"; exit 1; }
if grep -q 'example-resource-002' "${filter_tmp}" && ! grep -q 'WARN: no matching' "${filter_tmp}"; then
  echo "FAIL: filter returned wrong record"
  cat "${filter_tmp}"
  rm -f "${filter_tmp}"
  exit 1
fi
rm -f "${filter_tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-retrieval-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-retrieval-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-registry-retrieval-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: retrieval status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q 'no embeddings or RAG attempted' "${cli_tmp}" || { echo "FAIL: missing negative RAG assertion"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
if [[ -f "${fixture}" ]]; then
  before_fixture="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-retrieval-fixture-before.XXXXXX")"
  cp "${fixture}" "${before_fixture}"
  bash "${retrieval}" >/dev/null 2>&1
  bash "${retrieval}" --subject "Example Math Course" >/dev/null 2>&1
  if ! cmp -s "${fixture}" "${before_fixture}"; then
    echo "FAIL: retrieval check mutated fixture registry"
    rm -f "${before_fixture}"
    exit 1
  fi
  rm -f "${before_fixture}"
fi

echo "PASS: Curriculum Builder Registry v0.2 retrieval tests passed."
