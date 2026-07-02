#!/usr/bin/env bash
# Tests for Curriculum Builder production registry workflow planning status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder production registry planning status tests..."

status_script="scripts/curriculum-builder-production-registry-planning-status.sh"
planning_brief="docs/curriculum-builder-production-registry-workflow-planning-brief.md"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-prod-registry-planning.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: planning status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: planning status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'planning_only' "${tmp}" || { echo "FAIL: missing planning_only boundary"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Production registry writes: blocked' "${tmp}" || { echo "FAIL: missing blocked writes"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'ChatGPT review recommended before implementation prompt: yes' "${tmp}" || {
  echo "FAIL: missing ChatGPT review gate banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-prod-registry-live-before.XXXXXX")"
  cp assistant/curriculum-builder/registry/v0/registry.json "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${before}"; then
    echo "FAIL: planning status script mutated live registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

if grep -Fq -- '--write)' "${status_script}" 2>/dev/null; then
  if ! grep -Fq "grep -Fq -- '--write)'" "${status_script}" 2>/dev/null; then
    echo "FAIL: planning status script implements --write flag"
    exit 1
  fi
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-prod-registry-planning-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-planning-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-planning-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI planning status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-planning-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-planning-status"
  exit 1
fi

if ! grep -Fq -- '"--curriculum-production-registry-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing planning status command"
  exit 1
fi

if ! grep -Fq -- '"--curriculum-registry-write"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: blocked --curriculum-registry-write missing from manifest"
  exit 1
fi

grep -q 'complete_production_registry_planning_brief' "${planning_brief}" || {
  echo "FAIL: planning brief missing closure status"
  exit 1
}

echo "PASS: Curriculum Builder production registry planning status tests passed."
