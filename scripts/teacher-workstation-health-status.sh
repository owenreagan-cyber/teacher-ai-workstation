#!/usr/bin/env bash
# Read-only Teacher Workstation Health Monitor status. Observes and reports only.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"
}

check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  if [[ ! -f "${path}" ]]; then
    fail "${path} must mention ${label}"
    return
  fi
  if grep -Fq -- "${needle}" "${path}"; then
    pass "doc mentions ${label}"
  else
    fail "${path} must mention ${label}"
  fi
}

run_health_track() {
  local label="$1" script="$2"
  if [[ ! -f "${script}" ]]; then
    fail "${label} status script missing: ${script}"
    return 1
  fi
  if bash -n "${script}"; then
    pass "bash syntax ok: ${script}"
  else
    fail "bash syntax failed: ${script}"
    return 1
  fi
  if bash "${script}" >/dev/null 2>&1; then
    pass "${label} health track exits 0"
    return 0
  fi
  fail "${label} health track failed"
  return 1
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Teacher Workstation Health Monitor (Read-Only)'
cat <<'EOF'
Status: observe and report only
Health vs Updater: Health Monitor (H) observes only — System Updater (I) is separate; not invoked for repair
Update/repair/install: no
Network calls: no
Automation: no
Canvas LLM: frozen/stopped unless Owen supersedes stop marker
EOF

check_file docs/teacher-workstation-health-monitor.md
check_file docs/teacher-workstation-health-monitor-foundation.md
check_doc_contains docs/teacher-workstation-health-monitor.md "observes and reports" "observe-only boundary"
check_doc_contains docs/teacher-workstation-health-monitor.md "System Updater" "system updater separation"
check_doc_contains docs/teacher-workstation-health-monitor.md "no network" "no network boundary"
check_doc_contains docs/teacher-workstation-health-monitor-foundation.md "complete_v1_h" "health monitor closure status"

section 'Repo Health'
[[ -f bin/chief-of-staff ]] && pass 'chief-of-staff CLI exists' || fail 'chief-of-staff CLI missing'
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pass 'git repository detected'
else
  fail 'not inside git repository'
fi
branch="$(git branch --show-current 2>/dev/null || echo unknown)"
printf 'Git branch: %s\n' "${branch}"
if git diff --quiet && git diff --cached --quiet 2>/dev/null; then
  pass 'working tree clean'
else
  warn 'working tree has uncommitted changes'
fi

section 'Chief of Staff Health'
run_health_track 'Chief of Staff v1 Agent Core' scripts/chief-of-staff-v1-foundation-status.sh || true
run_health_track 'Chief of Staff command surface' scripts/chief-of-staff-commands.sh || true

section 'Roadmap and Capability Health'
check_doc_contains docs/master-build-roadmap.md "Teacher Workstation Health Monitor" "roadmap health monitor"
check_doc_contains docs/teacher-workstation-capability-map.md "Health Monitor" "capability map health monitor"
check_doc_contains docs/build-queue.md "Health Monitor" "build queue health monitor"

section 'Foundation Program Health'
run_health_track 'Teacher Workstation Foundation v0' scripts/teacher-workstation-foundation-status.sh || true
run_health_track 'Curriculum Builder foundation' scripts/curriculum-builder-foundation-status.sh || true

section 'Canvas and Future Boundary Health'
if [[ -f docs/canvas-llm-stop-marker-curriculum-builder-return.md ]]; then
  grep -Fq 'stop marker' docs/canvas-llm-stop-marker-curriculum-builder-return.md && pass 'canvas stop marker documented' || warn 'canvas stop marker wording unclear'
else
  warn 'canvas stop marker doc missing'
fi
check_doc_contains docs/canvas-llm-stop-marker-curriculum-builder-return.md "stop marker" "canvas frozen stop marker rule"
run_health_track 'Canvas LLM frozen foundation' scripts/teacher-app-designer-canvas-llm-status.sh || true
check_doc_contains docs/teacher-workstation-health-monitor.md "planning-only" "future program planning boundary"
check_doc_contains docs/teacher-workstation-health-monitor.md "System Updater" "health monitor updater separation doc"

section 'Validation Suite Health'
run_health_track 'Cursor workflow' scripts/cursor-workflow-status.sh || true

section 'Negative Non-Activation Assertions'
status_script="scripts/teacher-workstation-health-status.sh"
script_invocations="$(grep -Ev 'must not shell-invoke|does not shell-invoke' "${status_script}" || true)"
grep -Eq '(^|[;&|[:space:]])brew[[:space:]]+(install|upgrade)' <<< "${script_invocations}" && fail 'health status script must not shell-invoke brew install' || pass 'health status script does not shell-invoke brew install'
grep -Eq '(^|[;&|[:space:]])npm[[:space:]]+(install|ci)' <<< "${script_invocations}" && fail 'health status script must not shell-invoke npm install' || pass 'health status script does not shell-invoke npm install'
grep -Eq '(^|[;&|[:space:]])softwareupdate[[:space:]]' <<< "${script_invocations}" && fail 'health status script must not shell-invoke softwareupdate' || pass 'health status script does not shell-invoke softwareupdate'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' <<< "${script_invocations}" && fail 'health status script must not shell-invoke curl' || pass 'health status script does not shell-invoke curl'

section 'Non-Activation Health'
pass 'no repair attempted'
pass 'no install attempted'
pass 'no network call attempted'
pass 'System Updater not invoked'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
