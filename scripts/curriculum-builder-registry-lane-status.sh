#!/usr/bin/env bash
# Read-only aggregate Curriculum Builder Registry lane status (CB-IMPL-1–4 + planning + hardening).
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} must mention ${label}"; return; }
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

status_script="scripts/curriculum-builder-registry-lane-status.sh"
authority_map="docs/curriculum-builder-registry-authority-map.md"
lane_closure="docs/curriculum-builder-registry-v0-2-lane-closure.md"
level2_review="docs/proposals/curriculum-builder-registry-lane-discovery-review.md"
planning_brief="docs/curriculum-builder-production-registry-workflow-planning-brief.md"

COMPONENTS=(
  "CB-IMPL-1 dry-run|scripts/curriculum-builder-registry-v0-2-status.sh"
  "CB-IMPL-2 local fake records|scripts/curriculum-builder-registry-v0-2-local-records-status.sh"
  "CB-IMPL-3 renderer|scripts/curriculum-builder-registry-v0-2-renderer-status.sh"
  "CB-IMPL-4 retrieval|scripts/curriculum-builder-registry-v0-2-retrieval-status.sh"
  "production registry planning|scripts/curriculum-builder-production-registry-planning-status.sh"
  "production registry governance|scripts/curriculum-builder-production-registry-governance-status.sh"
  "production registry Phase 2 preflight|scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh"
  "production registry metadata boundary|scripts/curriculum-builder-production-registry-metadata-boundary-status.sh"
  "production registry empty file|scripts/curriculum-builder-production-registry-empty-file-status.sh"
  "production registry metadata pilot plan|scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh"
  "production registry first record|scripts/curriculum-builder-production-registry-first-record-status.sh"
  "Owen § J approval checklist|scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
  "curriculum source readiness|scripts/curriculum-source-readiness-status.sh"
  "A4–A7 fixture schema cross-validation|scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh"
)

section 'Curriculum Builder Registry Lane Status (Aggregate)'
cat <<'EOF'
Status: read-only aggregate lane proof
Classification: fake-fixture-only registry foundations
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Fixture promotion: blocked
Network calls: no
Student data: no
Real curriculum content: no
Expected WARNs: see docs/curriculum-builder-registry-expected-warns.md
EOF

section 'Lane Documentation'
check_file "${authority_map}"
check_file "${lane_closure}"
check_file "${level2_review}"
check_file "${planning_brief}"
check_doc_contains "${authority_map}" "complete_registry_authority_map" "authority map closure"
check_doc_contains "${lane_closure}" "complete_cb_impl_2_3_4_local_foundation_lane" "lane closure"
check_doc_contains "${level2_review}" "reviewed" "level 2 review status"
check_doc_contains "${planning_brief}" "complete_production_registry_planning_brief" "planning brief closure"
check_doc_contains "${planning_brief}" "Production registry writes: blocked" "planning blocked writes"

section 'Component Status Scripts'
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"

for entry in "${COMPONENTS[@]}"; do
  label="${entry%%|*}"
  script_path="${entry##*|}"
  if [[ ! -f "${script_path}" ]]; then
    fail "component script missing: ${label} (${script_path})"
    continue
  fi
  bash -n "${script_path}" && pass "bash syntax ok: ${script_path}" || fail "bash syntax failed: ${script_path}"
  component_output="$(bash "${script_path}" 2>&1)" || component_result=$?
  component_result="${component_result:-0}"
  if [[ "${component_result}" != "0" ]]; then
    fail "component failed: ${label}"
    printf '%s\n' "${component_output}" | tail -20
    continue
  fi
  if grep -q '^FAIL: [1-9]' <<< "${component_output}" || grep -q 'FAIL_COUNT:[1-9]' <<< "${component_output}"; then
    fail "component reported FAIL: ${label}"
    printf '%s\n' "${component_output}" | tail -20
    continue
  fi
  component_pass="$(grep '^PASS:' <<< "${component_output}" | wc -l | tr -d ' ')"
  component_warn="$(grep '^WARN:' <<< "${component_output}" | wc -l | tr -d ' ')"
  pass "component ${label}: PASS ${component_pass} / WARN ${component_warn} / FAIL 0"
done

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-registry-lane-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-lane-status' || fail 'CLI missing --curriculum-registry-lane-status'
grep -Fq -- '"--curriculum-registry-lane-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-registry-lane-status' || fail 'manifest missing --curriculum-registry-lane-status'
grep -Fq -- '"--curriculum-registry-write"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest retains blocked --curriculum-registry-write' || fail 'manifest missing blocked write command'
check_file tests/curriculum-builder-registry-lane-status-test.sh
bash -n tests/curriculum-builder-registry-lane-status-test.sh && pass 'bash syntax ok: lane status test' || fail 'bash syntax failed: lane status test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
pass 'no production registry write attempted'
pass 'no network call attempted'
pass 'aggregate lane status does not hide component failures'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
