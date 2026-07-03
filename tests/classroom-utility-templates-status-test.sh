#!/usr/bin/env bash
# Tests for Classroom Utility per-app mission templates status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Classroom Utility templates status tests..."

status_script="scripts/classroom-utility-templates-status.sh"
mission_template="docs/classroom-utility-per-app-mission-template.md"

for required in \
  "${status_script}" \
  "${mission_template}" \
  docs/classroom-utility-app-candidate-matrix.md \
  docs/classroom-utility-student-data-boundaries.md \
  docs/classroom-utility-templates/classpass-planning-template.md \
  assistant/classroom-utilities/samples/planning/example-classpass-labels-001.json; do
  if [[ ! -f "${required}" ]]; then
    echo "FAIL: required file missing: ${required}"
    exit 1
  fi
done

tmp="$(mktemp "${TMPDIR:-/tmp}/classroom-utility-templates-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: classroom-utility-templates-status.sh exited nonzero"
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
grep -q 'no runtime classroom app execution attempted' "${tmp}" || {
  echo "FAIL: missing negative runtime assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/classroom-utility-templates-cli.XXXXXX")"
bin/chief-of-staff --classroom-utility-templates-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --classroom-utility-templates-status exited nonzero"
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

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--classroom-utility-templates-status'; then
  echo "FAIL: --help missing --classroom-utility-templates-status"
  exit 1
fi

if ! grep -Fq -- '"--classroom-utility-templates-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing classroom utility templates status command"
  exit 1
fi

if ! grep -Fq -- 'fake_local_planning_only' assistant/classroom-utilities/samples/planning/example-classpass-labels-001.json; then
  echo "FAIL: fixture missing fake_local_planning_only classification"
  exit 1
fi

if grep -rqiE 'https?://' assistant/classroom-utilities/samples/planning/ --include='example-*.json' 2>/dev/null; then
  echo "FAIL: positive planning fixtures must not contain URLs"
  exit 1
fi

grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && {
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
}

echo "PASS: Classroom Utility templates status tests complete"
