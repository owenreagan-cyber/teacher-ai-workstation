#!/usr/bin/env bash
# Read-only Mac Workstation Experience status. Planning visibility only — no Mac mutations.
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

section 'Mac Workstation Experience (Read-Only Planning Foundation)'
cat <<'EOF'
Status: read-only planning only
Planning-only: yes (Program E1 — no Mac mutations)
Mac system changes: blocked
Wallpaper apply: blocked
Widget install: blocked
Widget/Shortcut lane (F1): see --widget-shortcut-status
Wallpaper/photo lane: separate planning stack — not live curator
Automation: no
Network calls: no
EOF

check_file docs/mac-workstation-experience-foundation.md
check_file docs/mac-workstation-non-activation-boundaries.md
check_file docs/mac-workstation-readiness-plan.md
check_file docs/chief-of-staff-mode-status.md
check_doc_contains docs/mac-workstation-experience-foundation.md "complete_v1_e1" "mac workstation closure status"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Mac system changes: blocked" "mac system changes blocked"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Wallpaper apply: blocked" "wallpaper apply blocked"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Widget install: blocked" "widget install blocked"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Automation: no" "no automation boundary"
check_doc_contains docs/mac-workstation-readiness-plan.md "read-only planning" "readiness read-only boundary"
check_doc_contains docs/chief-of-staff-mode-status.md "Mac changes: no" "mode status mac boundary"
check_doc_contains docs/widget-shortcut-builder-catalog-foundation.md "complete_v1_f1" "f1 widget shortcut cross-link"
check_doc_contains docs/mac-workstation-experience-foundation.md "Wallpaper" "mac wallpaper lane reference"
check_file docs/mac-workstation-e1-vs-wallpaper-lane-map.md
check_doc_contains docs/mac-workstation-e1-vs-wallpaper-lane-map.md "planning-only" "e1 wallpaper lane map"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Mac Workstation Experience" "roadmap mac workstation"
check_doc_contains docs/teacher-workstation-capability-map.md "Mac teacher modes" "capability map mac modes"
check_doc_contains docs/build-queue.md "Mac Workstation" "build queue mac workstation"

section 'Planning Summary'
printf 'Teacher modes: documented (see --mode-status for concepts)\n'
printf 'Wallpaper curator: parked planning only\n'
printf 'Vibe Panel: planning only\n'
pass 'planning summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--mac-workstation-status' bin/chief-of-staff && pass 'CLI exposes --mac-workstation-status' || fail 'CLI missing --mac-workstation-status'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--mode-status' bin/chief-of-staff && pass 'CLI exposes --mode-status (B5)' || fail 'CLI missing --mode-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'

section 'Negative Non-Activation Assertions'
if grep -Eq '(^|[;&|[:space:]])osascript[[:space:]]' scripts/mac-workstation-experience-status.sh 2>/dev/null; then
  fail 'mac status script must not shell-invoke osascript'
else
  pass 'mac status script does not shell-invoke osascript'
fi
if grep -Eq '(^|[;&|[:space:]])defaults[[:space:]]+write' scripts/mac-workstation-experience-status.sh 2>/dev/null; then
  fail 'mac status script must not shell-invoke prefs defaults'
else
  pass 'mac status script does not shell-invoke prefs defaults'
fi
if grep -Eq '(^|[;&|[:space:]])PlistBuddy[[:space:]]' scripts/mac-workstation-experience-status.sh 2>/dev/null; then
  fail 'mac status script must not shell-invoke PlistBuddy'
else
  pass 'mac status script does not shell-invoke PlistBuddy'
fi
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' scripts/mac-workstation-experience-status.sh 2>/dev/null; then
  fail 'mac status script must not shell-invoke curl'
else
  pass 'mac status script does not shell-invoke curl'
fi
pass 'no wallpaper apply attempted'
pass 'no widget install attempted'
pass 'no Mac system mutation attempted'
pass 'no network call attempted'
pass 'no automation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
