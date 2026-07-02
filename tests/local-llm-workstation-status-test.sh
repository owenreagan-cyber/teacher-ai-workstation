#!/usr/bin/env bash
# Lightweight tests for Local LLM/Ollama read-only status foundation (Program D1).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Local LLM workstation status tests..."

tmp="$(mktemp "${TMPDIR:-/tmp}/local-llm-workstation-status.XXXXXX")"
bash scripts/local-llm-workstation-status.sh >"${tmp}" 2>&1 || {
  echo "FAIL: local-llm-workstation-status.sh exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: local-llm-workstation-status.sh reported failures"
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
grep -q 'local llm status script does not shell-invoke ollama' "${tmp}" || {
  echo "FAIL: missing negative ollama assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no localhost port check attempted' "${tmp}" || {
  echo "FAIL: missing negative port-check assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

tmp="$(mktemp "${TMPDIR:-/tmp}/local-llm-workstation-cli.XXXXXX")"
bin/chief-of-staff --local-llm-workstation-status >"${tmp}" 2>&1 || {
  echo "FAIL: --local-llm-workstation-status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: --local-llm-workstation-status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

echo "PASS: Local LLM workstation status tests passed."
