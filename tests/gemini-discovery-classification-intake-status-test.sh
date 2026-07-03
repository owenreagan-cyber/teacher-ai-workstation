#!/usr/bin/env bash
# Tests for Gemini discovery/classification external planning intake status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Gemini discovery/classification intake status tests..."

status_script="scripts/gemini-discovery-classification-intake-status.sh"
filed_memo="docs/external-planning/discovery-classification-memo.md"
intake_doc="docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md"

for required in \
  "${status_script}" \
  "${filed_memo}" \
  "${intake_doc}" \
  docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md \
  assistant/external-planning/intake/gemini-discovery-classification-architecture-summary.json; do
  if [[ ! -f "${required}" ]]; then
    echo "FAIL: required file missing: ${required}"
    exit 1
  fi
done

tmp="$(mktemp "${TMPDIR:-/tmp}/gemini-intake-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: gemini-discovery-classification-intake-status.sh exited nonzero"
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
grep -q 'external_planning_reference_only' "${tmp}" || {
  echo "FAIL: missing external planning boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no runtime discovery execution attempted' "${tmp}" || {
  echo "FAIL: missing negative discovery assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/gemini-intake-cli.XXXXXX")"
bin/chief-of-staff --gemini-discovery-classification-intake-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --gemini-discovery-classification-intake-status exited nonzero"
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

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--gemini-discovery-classification-intake-status'; then
  echo "FAIL: --help missing --gemini-discovery-classification-intake-status"
  exit 1
fi

if ! grep -Fq -- '"--gemini-discovery-classification-intake-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing gemini intake status command"
  exit 1
fi

if ! grep -Fq -- 'external_planning_intake_summary_only' assistant/external-planning/intake/gemini-discovery-classification-architecture-summary.json; then
  echo "FAIL: summary fixture missing classification marker"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

echo "PASS: Gemini discovery/classification intake status tests complete"
