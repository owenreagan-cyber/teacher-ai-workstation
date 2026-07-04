#!/usr/bin/env bash
# Tests for Curriculum Library foundation status command.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Library foundation status tests..."

status_script="scripts/curriculum-library-foundation-status.sh"
setup_plan="docs/curriculum-library/curriculum-library-setup-plan.md"

for required in \
  "${status_script}" \
  "${setup_plan}" \
  docs/curriculum-library/manual-registry-plan.md \
  docs/curriculum-library/folder-taxonomy.md \
  docs/curriculum-library/canvas-ready-folder-definition.md \
  docs/curriculum-library/file-classification-approval-gate.md \
  assistant/curriculum-library/samples/fake-folder-tree.json \
  assistant/curriculum-library/samples/fake-manual-registry.csv \
  assistant/curriculum-library/samples/fake-classification-suggestion.json; do
  [[ -f "${required}" ]] || { echo "FAIL: required file missing: ${required}"; exit 1; }
done

tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-library-foundation-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || { echo "FAIL: status script exited nonzero"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Real folders on disk: no' "${tmp}" || { echo "FAIL: missing no real folders banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no local library folder creation attempted' "${tmp}" || { echo "FAIL: missing folder creation negative assertion"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-library-foundation-cli.XXXXXX")"
bin/chief-of-staff --curriculum-library-foundation-status >"${cli_tmp}" 2>&1 || { echo "FAIL: CLI exited nonzero"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-library-foundation-status' || { echo "FAIL: --help missing command"; exit 1; }

grep -Fq -- 'fake_local_planning_only' assistant/curriculum-library/samples/fake-folder-tree.json || { echo "FAIL: folder tree missing classification"; exit 1; }
grep -Fq -- '"local_root_created": false' assistant/curriculum-library/samples/fake-folder-tree.json || { echo "FAIL: folder tree must not mark root created"; exit 1; }

grep -Fq -- '--curriculum-library-create)' bin/chief-of-staff 2>/dev/null && { echo "FAIL: CLI must not expose library create command"; exit 1; }

echo "PASS: Curriculum Library foundation status tests complete"
