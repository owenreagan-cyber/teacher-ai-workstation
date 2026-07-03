#!/usr/bin/env bash
# Tests for markdown frontmatter / manual metadata planning status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running markdown frontmatter planning status tests..."

status_script="scripts/markdown-frontmatter-planning-status.sh"
planning_doc="docs/curriculum-manual-metadata-frontmatter-planning.md"

for required in \
  "${status_script}" \
  "${planning_doc}" \
  docs/proposals/ideas/markdown-frontmatter-planning-note.md \
  docs/proposals/blocked/markdown-frontmatter-runtime-boundaries.md \
  assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning/example-field-ideas-illustration.json; do
  if [[ ! -f "${required}" ]]; then
    echo "FAIL: required file missing: ${required}"
    exit 1
  fi
done

tmp="$(mktemp "${TMPDIR:-/tmp}/frontmatter-planning-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: markdown-frontmatter-planning-status.sh exited nonzero"
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
grep -q 'planning_only' "${tmp}" || {
  echo "FAIL: missing planning-only boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'no frontmatter parsing attempted' "${tmp}" || {
  echo "FAIL: missing negative parsing assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/frontmatter-planning-cli.XXXXXX")"
bin/chief-of-staff --markdown-frontmatter-planning-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --markdown-frontmatter-planning-status exited nonzero"
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

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--markdown-frontmatter-planning-status'; then
  echo "FAIL: --help missing --markdown-frontmatter-planning-status"
  exit 1
fi

if ! grep -Fq -- '"--markdown-frontmatter-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing markdown frontmatter planning status command"
  exit 1
fi

if ! grep -Fq -- 'manual_metadata_frontmatter_planning_only' assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning/example-field-ideas-illustration.json; then
  echo "FAIL: fixture missing planning-only classification"
  exit 1
fi

if grep -rqiE 'https?://' assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning/example-field-ideas-illustration.json 2>/dev/null; then
  echo "FAIL: positive illustration must not contain URLs"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

echo "PASS: Markdown frontmatter planning status tests complete"
