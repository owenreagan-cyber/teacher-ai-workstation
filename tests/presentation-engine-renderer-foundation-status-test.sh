#!/usr/bin/env bash
# Tests for Presentation Engine renderer-foundation planning status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Presentation Engine renderer foundation status tests..."

status_script="scripts/presentation-engine-renderer-foundation-status.sh"
foundation_doc="docs/presentation-engine-renderer-foundation.md"
interface_doc="docs/presentation-engine-static-renderer-interface-plan.md"
boundary_doc="docs/presentation-engine-blocked-runtime-boundaries.md"
plan_fixture="assistant/presentation-engine/samples/renderer-planning/example-presentation-plan-001.json"

for required in "${status_script}" "${foundation_doc}" "${interface_doc}" "${boundary_doc}" "${plan_fixture}"; do
  if [[ ! -f "${required}" ]]; then
    echo "FAIL: required file missing: ${required}"
    exit 1
  fi
done

tmp="$(mktemp "${TMPDIR:-/tmp}/presentation-engine-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: presentation-engine-renderer-foundation-status.sh exited nonzero"
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
grep -q 'documentation/status/fixture planning only' "${tmp}" || {
  echo "FAIL: missing planning-only boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no rendering attempted' "${tmp}" || {
  echo "FAIL: missing negative rendering assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/presentation-engine-cli.XXXXXX")"
bin/chief-of-staff --presentation-engine-renderer-foundation-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --presentation-engine-renderer-foundation-status exited nonzero"
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

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--presentation-engine-renderer-foundation-status'; then
  echo "FAIL: --help missing --presentation-engine-renderer-foundation-status"
  exit 1
fi

cmds_tmp="$(mktemp "${TMPDIR:-/tmp}/presentation-engine-commands.XXXXXX")"
bin/chief-of-staff --commands >"${cmds_tmp}" 2>&1 || true
if ! grep -Fq -- '--presentation-engine-renderer-foundation-status' "${cmds_tmp}"; then
  echo "FAIL: --commands does not list --presentation-engine-renderer-foundation-status"
  rm -f "${cmds_tmp}"
  exit 1
fi
rm -f "${cmds_tmp}"

if ! grep -Fq -- '"--presentation-engine-renderer-foundation-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing presentation engine status command"
  exit 1
fi

if ! grep -Fq -- 'fake_local_planning_only' "${plan_fixture}"; then
  echo "FAIL: plan fixture missing fake_local_planning_only classification"
  exit 1
fi

if ! grep -Fq -- 'Runtime rendering' "${boundary_doc}"; then
  echo "FAIL: boundary doc missing runtime rendering blocked language"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

# Positive fixtures must not contain URLs (exclude negative fixture directory)
if grep -rqiE 'https?://' assistant/presentation-engine/samples/renderer-planning/ \
  --include='*.json' \
  --exclude-dir=negative 2>/dev/null; then
  echo "FAIL: positive planning fixtures must not contain URLs"
  exit 1
fi

echo "PASS: Presentation Engine renderer foundation status tests complete"
