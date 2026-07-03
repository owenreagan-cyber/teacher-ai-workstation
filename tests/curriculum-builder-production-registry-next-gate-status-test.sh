#!/usr/bin/env bash
# Tests for production registry next-gate decision prep status.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running production registry next-gate status tests..."

status_script="scripts/curriculum-builder-production-registry-next-gate-status.sh"
decision_packet="docs/curriculum-builder-production-registry-next-gate-decision-packet.md"
writer_boundary="docs/curriculum-builder-production-registry-writer-tooling-design-boundary.md"
second_record_plan="docs/curriculum-builder-production-registry-second-record-worksheet-plan.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
APPROVED_ID="resource-math-lesson-108-presentation"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-next-gate-status.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: next-gate status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: next-gate status reported failures"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'next_gate_decision_prep_complete' "${tmp}" || {
  echo "FAIL: missing decision prep complete banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Next gates: blocked pending Owen decision' "${tmp}" || {
  echo "FAIL: missing blocked gates banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'Parked state: allowed' "${tmp}" || {
  echo "FAIL: missing parked state allowed banner"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'records count remains exactly 1' "${tmp}" || {
  echo "FAIL: missing record count check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'BLOCKED-NO-WRITES.sentinel remains intact' "${tmp}" || {
  echo "FAIL: missing sentinel intact check"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -Fq 'no second production record authorized' "${tmp}" || {
  echo "FAIL: missing no second record assertion"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

[[ -f "${decision_packet}" ]] || { echo "FAIL: decision packet missing"; exit 1; }
grep -Fq 'next_gate_decision_packet_complete' "${decision_packet}" || {
  echo "FAIL: decision packet must use planning closure status"
  exit 1
}
grep -Fq 'no gate approved' "${decision_packet}" || {
  echo "FAIL: decision packet must state no gate approved"
  exit 1
}

[[ -f "${writer_boundary}" ]] || { echo "FAIL: writer boundary doc missing"; exit 1; }
grep -Fq 'writer_tooling_design_boundary_planning_only' "${writer_boundary}" || {
  echo "FAIL: writer boundary must be planning only"
  exit 1
}
grep -Fq 'planning-only' "${writer_boundary}" || {
  echo "FAIL: writer boundary must use planning-only language"
  exit 1
}

[[ -f "${second_record_plan}" ]] || { echo "FAIL: second record worksheet plan missing"; exit 1; }
grep -Fq 'second_record_worksheet_planning_only' "${second_record_plan}" || {
  echo "FAIL: second record plan must be planning only"
  exit 1
}
grep -Fq '<placeholder>' "${second_record_plan}" || {
  echo "FAIL: second record worksheet must remain template placeholders"
  exit 1
}

if ! python3 -c "
import json
with open('${production_registry_path}') as f:
    d = json.load(f)
assert len(d.get('records', [])) == 1
assert d['records'][0]['id'] == '${APPROVED_ID}'
"; then
  echo "FAIL: production registry must still have exactly one approved record"
  exit 1
fi

[[ -f "${sentinel}" ]] || { echo "FAIL: sentinel must remain present"; exit 1; }

if [[ -f scripts/curriculum-registry-write.sh ]] || [[ -f scripts/curriculum-production-registry-write.sh ]]; then
  echo "FAIL: writer scripts must not exist"
  exit 1
fi

if grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-next-gate-cli.XXXXXX")"
bin/chief-of-staff --curriculum-production-registry-next-gate-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-production-registry-next-gate-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || {
  echo "FAIL: CLI next-gate status reported failures"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-production-registry-next-gate-status'; then
  echo "FAIL: --help missing --curriculum-production-registry-next-gate-status"
  exit 1
fi

echo "PASS: Production registry next-gate status tests passed."
