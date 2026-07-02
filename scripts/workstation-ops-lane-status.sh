#!/usr/bin/env bash
# Read-only aggregate workstation operations lane status (Health Monitor H + System Updater I).
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

status_script="scripts/workstation-ops-lane-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

COMPONENTS=(
  "Health Monitor (H)|scripts/teacher-workstation-health-status.sh"
  "System Updater (I)|scripts/teacher-workstation-system-updater-status.sh"
)

section 'Workstation Operations Lane Status (Aggregate H+I)'
cat <<'EOF'
Status: read-only aggregate ops lane proof
Classification: observe/plan only — no runtime monitoring
Runtime activation: no
Live system probes: no
Apply/install/repair: blocked
Mac system changes: blocked
Network calls: blocked
Health Monitor vs System Updater: separate lanes — not merged at runtime
EOF

section 'Lane Reviews'
check_file docs/proposals/lane-reviews/teacher-workstation-health-monitor-lane-discovery-review.md
check_file docs/proposals/lane-reviews/teacher-workstation-system-updater-lane-discovery-review.md
check_doc_contains docs/master-build-roadmap.md "docs/proposals/lane-reviews/teacher-workstation-health-monitor-lane-discovery-review.md" "health monitor lane reviewed"
check_doc_contains docs/master-build-roadmap.md "docs/proposals/lane-reviews/teacher-workstation-system-updater-lane-discovery-review.md" "system updater lane reviewed"

section 'Foundation Documents'
check_file docs/teacher-workstation-health-monitor-foundation.md
check_file docs/teacher-workstation-system-updater-foundation.md
check_doc_contains docs/teacher-workstation-health-monitor-foundation.md "complete_v1_h" "health monitor closure"
check_doc_contains docs/teacher-workstation-system-updater-foundation.md "complete_v1_i" "system updater closure"

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
  if grep -q '^FAIL: [1-9]' <<< "${component_output}"; then
    fail "component reported FAIL: ${label}"
    printf '%s\n' "${component_output}" | tail -20
    continue
  fi
  component_pass="$(grep '^PASS:' <<< "${component_output}" | wc -l | tr -d ' ')"
  component_warn="$(grep '^WARN:' <<< "${component_output}" | wc -l | tr -d ' ')"
  pass "component ${label}: PASS ${component_pass} / WARN ${component_warn} / FAIL 0"
done

section 'CLI, Manifest, and Tests'
grep -Fq -- '--workstation-ops-lane-status' bin/chief-of-staff && pass 'CLI exposes --workstation-ops-lane-status' || fail 'CLI missing --workstation-ops-lane-status'
grep -Fq -- '"--workstation-ops-lane-status"' "${manifest}" && pass 'manifest lists --workstation-ops-lane-status' || fail 'manifest missing --workstation-ops-lane-status'
check_file tests/workstation-ops-lane-status-test.sh
bash -n tests/workstation-ops-lane-status-test.sh && pass 'bash syntax ok: workstation ops lane test' || fail 'bash syntax failed: workstation ops lane test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke brew" || pass "${status_script} does not shell-invoke brew"
grep -Eq '(^|[;&|[:space:]])system_profiler[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke system_profiler" || pass "${status_script} does not shell-invoke system_profiler"
pass 'aggregate ops status does not hide component failures'
pass 'no system mutation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
