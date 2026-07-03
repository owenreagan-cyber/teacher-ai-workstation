#!/usr/bin/env bash
# Read-only System Updater status. Plans and checks only — no apply/install/network.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Teacher Workstation System Updater (Read-Only Planning)'
cat <<'EOF'
Status: read-only update planning only
Check-only: yes
Install/apply: no
Apply/install/repair: no
Package managers: no
Network calls: no
Automation: no
Health Monitor: separate (Program H) — observe-only; not invoked for repair
EOF

check_file docs/teacher-workstation-system-updater.md
check_file docs/teacher-workstation-system-updater-foundation.md
check_doc_contains docs/teacher-workstation-system-updater.md "recommends and plans only" "read-only planning boundary"
check_doc_contains docs/teacher-workstation-system-updater.md "Health Monitor" "health monitor separation"
check_doc_contains docs/teacher-workstation-system-updater.md "Network calls: no" "no network boundary"
check_doc_contains docs/teacher-workstation-system-updater.md "package manager" "no package manager boundary"
check_doc_contains docs/teacher-workstation-system-updater-foundation.md "complete_v1_i" "system updater closure status"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Teacher Workstation System Updater" "roadmap system updater"
check_doc_contains docs/teacher-workstation-capability-map.md "System Updater" "capability map system updater"
check_doc_contains docs/build-queue.md "System Updater" "build queue system updater"

section 'Repo Update Planning (Informational)'
[[ -f bin/chief-of-staff ]] && pass 'chief-of-staff CLI exists' || fail 'chief-of-staff CLI missing'
branch="$(git branch --show-current 2>/dev/null || echo unknown)"
printf 'Current branch: %s\n' "${branch}"
if git diff --quiet && git diff --cached --quiet 2>/dev/null; then
  pass 'working tree clean'
else
  warn 'working tree has uncommitted changes'
fi

section 'CLI and Script Surfaces'
check_file scripts/teacher-workstation-system-update-plan.sh
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--system-update-check' bin/chief-of-staff && pass 'CLI exposes --system-update-check' || fail 'CLI missing --system-update-check'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--system-update-plan' bin/chief-of-staff && pass 'CLI exposes --system-update-plan' || fail 'CLI missing --system-update-plan'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'

section 'Negative Non-Activation Assertions'
status_script="scripts/teacher-workstation-system-updater-status.sh"
plan_script="scripts/teacher-workstation-system-update-plan.sh"
for script_path in "${status_script}" "${plan_script}"; do
  script_invocations="$(grep -Ev 'must not shell-invoke|does not shell-invoke' "${script_path}" || true)"
  grep -Eq '(^|[;&|[:space:]])brew[[:space:]]+(install|upgrade)' <<< "${script_invocations}" && fail "${script_path} must not shell-invoke brew install" || pass "${script_path} does not shell-invoke brew install"
  grep -Eq '(^|[;&|[:space:]])npm[[:space:]]+(install|ci)' <<< "${script_invocations}" && fail "${script_path} must not shell-invoke npm install" || pass "${script_path} does not shell-invoke npm install"
  grep -Eq '(^|[;&|[:space:]])softwareupdate[[:space:]]+--install' <<< "${script_invocations}" && fail "${script_path} must not shell-invoke softwareupdate --install" || pass "${script_path} does not shell-invoke softwareupdate --install"
done
script_invocations="$(grep -Ev 'must not shell-invoke|does not shell-invoke' "${status_script}" || true)"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' <<< "${script_invocations}" && fail 'updater status script must not shell-invoke curl' || pass 'updater status script does not shell-invoke curl'

section 'Non-Activation Health'
pass 'no apply attempted'
pass 'no install attempted'
pass 'no package manager invoked'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
