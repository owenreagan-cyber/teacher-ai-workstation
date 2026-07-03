#!/usr/bin/env bash
# Lightweight tests for AI Tool Routing read-only operational surface.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running AI Tool Routing status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/ai-tool-routing-status.XXXXXX")"
bash scripts/ai-tool-routing-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: ai-tool-routing-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: ai-tool-routing-status.sh reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Routing matrix version: 2026-07-02-v1' "${tmp}" || {
  echo "FAIL: missing routing matrix version stamp"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Local LLM D1' "${tmp}" || {
  echo "FAIL: missing R0+D1 cross-link banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'does not reference cloud API endpoint invocation' "${tmp}" || {
  echo "FAIL: missing negative API endpoint assertion"
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
grep -q 'routing status script does not shell-invoke ollama' "${tmp}" || {
  echo "FAIL: missing negative ollama assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/ai-tool-routing-cli.XXXXXX")"
bin/chief-of-staff --model-routing-status >"${tmp}" 2>&1 || {
  echo "FAIL: --model-routing-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --model-routing-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: AI Tool Routing status tests passed."
