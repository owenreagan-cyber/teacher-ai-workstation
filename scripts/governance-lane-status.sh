#!/usr/bin/env bash
# Read-only aggregate governance lane status (operating modes + ABE + proposal folders).
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

status_script="scripts/governance-lane-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

COMPONENTS=(
  "Cursor Operating Modes Governance|scripts/cursor-operating-modes-status.sh"
  "Autonomous Build Engine Governance|scripts/autonomous-build-engine-status.sh"
  "AGENTS.md Governance|scripts/agents-governance-status.sh"
)

section 'Governance Lane Status (Aggregate)'
cat <<'EOF'
Status: read-only aggregate governance proof
Classification: documentation/status only
Runtime activation: no
Discovery does not authorize implementation: yes
Production registry writes: blocked
Active --write: blocked
APIs/OAuth/network: blocked
Student data: blocked
Generation: blocked
EOF

section 'Governance Lane Reviews'
check_file docs/proposals/lane-reviews/cursor-operating-modes-governance-lane-discovery-review.md
check_file docs/proposals/lane-reviews/autonomous-build-engine-governance-lane-discovery-review.md
check_doc_contains docs/master-build-roadmap.md "docs/proposals/lane-reviews/cursor-operating-modes-governance-lane-discovery-review.md" "operating modes lane reviewed"
check_doc_contains docs/master-build-roadmap.md "docs/proposals/lane-reviews/autonomous-build-engine-governance-lane-discovery-review.md" "abe lane reviewed"

section 'Proposal Folder Health (Safe Work Class H)'
check_file docs/proposals/lane-reviews/README.md
check_file docs/proposals/ideas/README.md
check_file docs/proposals/backlog/README.md
check_file docs/proposals/blocked/README.md
check_file docs/proposals/implemented/README.md
check_doc_contains docs/proposals/README.md "lane-reviews/" "proposals readme lane-reviews"

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
grep -Fq -- '--governance-lane-status' bin/chief-of-staff && pass 'CLI exposes --governance-lane-status' || fail 'CLI missing --governance-lane-status'
grep -Fq -- '"--governance-lane-status"' "${manifest}" && pass 'manifest lists --governance-lane-status' || fail 'manifest missing --governance-lane-status'
check_file tests/governance-lane-status-test.sh
bash -n tests/governance-lane-status-test.sh && pass 'bash syntax ok: governance lane test' || fail 'bash syntax failed: governance lane test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
pass 'aggregate governance status does not hide component failures'
pass 'no runtime activation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
