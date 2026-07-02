#!/usr/bin/env bash
# Backlog non-mutation guardrail tests (renderer, retrieval, promotion, write flags).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running backlog non-mutation guardrail tests..."

promotion_spec="docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md"
if [[ ! -f "${promotion_spec}" ]]; then
  echo "FAIL: dry-run promotion planning spec missing"
  exit 1
fi
grep -q 'Fixture promotion: blocked' "${promotion_spec}" || {
  echo "FAIL: promotion spec must state fixture promotion blocked"
  exit 1
}
grep -q 'Automatic promotion: blocked' "${promotion_spec}" || {
  echo "FAIL: promotion spec must state automatic promotion blocked"
  exit 1
}

if grep -Fq -- '--curriculum-registry-promote' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: chief-of-staff must not expose --curriculum-registry-promote"
  exit 1
fi
if grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: chief-of-staff must not implement --curriculum-registry-write handler"
  exit 1
fi

planning_tmp="$(mktemp "${TMPDIR:-/tmp}/backlog-guardrails-planning.XXXXXX")"
bash scripts/curriculum-builder-production-registry-planning-status.sh >"${planning_tmp}" 2>&1 || {
  echo "FAIL: production planning status exited nonzero"
  cat "${planning_tmp}"
  rm -f "${planning_tmp}"
  exit 1
}
grep -q 'Runtime activation: no' "${planning_tmp}" || {
  echo "FAIL: planning status missing runtime activation banner"
  cat "${planning_tmp}"
  rm -f "${planning_tmp}"
  exit 1
}
grep -q 'Production registry writes: blocked' "${planning_tmp}" || {
  echo "FAIL: planning status missing blocked writes banner"
  cat "${planning_tmp}"
  rm -f "${planning_tmp}"
  exit 1
}
rm -f "${planning_tmp}"

lane_tmp="$(mktemp "${TMPDIR:-/tmp}/backlog-guardrails-lane.XXXXXX")"
bash scripts/curriculum-builder-registry-lane-status.sh >"${lane_tmp}" 2>&1 || {
  echo "FAIL: registry lane status exited nonzero"
  cat "${lane_tmp}"
  rm -f "${lane_tmp}"
  exit 1
}
grep -q 'aggregate lane status does not hide component failures' "${lane_tmp}" || {
  echo "FAIL: registry lane status missing non-hiding assertion"
  cat "${lane_tmp}"
  rm -f "${lane_tmp}"
  exit 1
}
rm -f "${lane_tmp}"

echo "PASS: backlog non-mutation guardrail tests passed."
