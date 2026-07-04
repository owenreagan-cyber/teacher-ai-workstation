#!/usr/bin/env bash
# Tests for Owen architecture decision packets status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Owen architecture decision packets status tests..."

status_script="scripts/owen-architecture-decision-packets-status.sh"
index_doc="docs/owen-architecture-decision-packets.md"

for required in \
  "${status_script}" \
  "${index_doc}" \
  docs/proposals/blocked/production-registry-options-decision-packet.md \
  docs/proposals/blocked/manual-text-asset-directory-layout-decision-packet.md \
  docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md \
  docs/proposals/blocked/external-builder-trial-decision-packet.md \
  docs/proposals/blocked/local-llm-ollama-decision-packet.md \
  docs/proposals/blocked/drive-nas-icloud-canvas-integration-posture-decision-packet.md; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/owen-decision-packets-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Chief of Staff chooses options for Owen: no' "${tmp}" || { echo "FAIL: missing CoS no-choose banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/owen-decision-packets-cli.XXXXXX")"
bin/chief-of-staff --owen-architecture-decision-packets-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--owen-architecture-decision-packets-status' || { echo "FAIL: --help missing command"; exit 1; }
grep -Fq -- '"--owen-architecture-decision-packets-status"' assistant/chief-of-staff/v1/command-surface-manifest.json || { echo "FAIL: manifest missing command"; exit 1; }

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && { echo "FAIL: --write handler must not exist"; exit 1; }

echo "PASS: Owen architecture decision packets status tests complete"
