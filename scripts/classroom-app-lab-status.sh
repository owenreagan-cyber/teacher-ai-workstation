#!/usr/bin/env bash
# Read-only Classroom App Lab status. Prototype rescue planning only — no zip, parse, or execute.
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

section 'Classroom App Lab (Read-Only Prototype Rescue Foundation)'
cat <<'EOF'
Status: read-only planning only
Zip upload: blocked
Zip extraction: blocked
Code parsing: blocked
App execution: blocked
LLM/API analysis: blocked
Automatic Cursor execution: blocked
Automation: no
Network calls: no
EOF

check_file docs/classroom-app-lab-prototype-rescue-foundation.md
check_file docs/classroom-app-lab-non-activation-boundaries.md
check_file docs/classroom-app-lab-readiness-plan.md
check_file docs/classroom-app-lab-fake-prototype-inventory-template.md
check_file docs/classroom-app-lab-vs-lovable-lane-boundary.md
check_file docs/proposals/blocked/classroom-utility-apps-external-ideas.md
check_doc_contains docs/classroom-app-lab-prototype-rescue-foundation.md "complete_v1_cal1" "classroom app lab closure status"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "Zip upload: blocked" "zip upload blocked"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "Zip extraction: blocked" "zip extraction blocked"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "Code parsing: blocked" "code parsing blocked"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "App execution: blocked" "app execution blocked"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "Automatic Cursor execution: blocked" "automatic cursor execution blocked"
check_doc_contains docs/classroom-app-lab-readiness-plan.md "Prototype Rescue" "prototype rescue workflow"
check_doc_contains docs/classroom-app-lab-fake-prototype-inventory-template.md "planning_template_only" "fake prototype inventory template"
check_doc_contains docs/classroom-app-lab-vs-lovable-lane-boundary.md "CAL1" "CAL1 lane boundary"
check_doc_contains docs/classroom-app-lab-vs-lovable-lane-boundary.md "G1" "G1 lane boundary"
check_doc_contains docs/proposals/blocked/classroom-utility-apps-external-ideas.md "ClassPass App" "blocked ClassPass classification"
check_doc_contains docs/long-term-future-programs-roadmap.md "Classroom App Lab" "long-term roadmap classroom app lab"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Classroom App Lab" "roadmap classroom app lab"
check_doc_contains docs/teacher-workstation-capability-map.md "Classroom App Lab" "capability map classroom app lab"
check_doc_contains docs/build-queue.md "Classroom App Lab" "build queue classroom app lab"

section 'Related Program Cross-Links'
check_doc_contains docs/long-term-future-programs-roadmap.md "Classroom App Lab" "long-term roadmap classroom app lab section"
check_doc_contains docs/long-term-future-programs-roadmap.md "zip upload and extraction" "long-term roadmap blocks zip extraction"

section 'Planning Summary'
printf 'Prototype categories: metadata-only concepts documented\n'
printf 'Rescue workflow: planning checklist only\n'
printf 'Runtime analyzer: blocked\n'
pass 'planning summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--classroom-app-lab-status' bin/chief-of-staff && pass 'CLI exposes --classroom-app-lab-status' || fail 'CLI missing --classroom-app-lab-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'
if grep -Fq -- '"--classroom-app-lab-status"' assistant/chief-of-staff/v1/command-surface-manifest.json 2>/dev/null; then
  pass 'manifest lists --classroom-app-lab-status'
else
  fail 'manifest missing --classroom-app-lab-status'
fi

section 'Negative Non-Activation Assertions'
status_script="scripts/classroom-app-lab-status.sh"
if grep -Eq '(^|[;&|[:space:]])(unzip[[:space:]]+-|zipinfo[[:space:]])' "${status_script}" 2>/dev/null; then
  fail 'classroom app lab status script must not shell-invoke archive extraction'
else
  pass 'classroom app lab status script does not shell-invoke archive extraction'
fi
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'classroom app lab status script must not shell-invoke curl'
else
  pass 'classroom app lab status script does not shell-invoke curl'
fi
if grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'classroom app lab status script must not shell-invoke wget'
else
  pass 'classroom app lab status script does not shell-invoke wget'
fi
if grep -Eq '(^|[;&|[:space:]])(brew|npm|pip|apt-get|yum)[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'classroom app lab status script must not shell-invoke package managers'
else
  pass 'classroom app lab status script does not shell-invoke package managers'
fi
pass 'no zip upload attempted'
pass 'no zip extraction attempted'
pass 'no code parsing attempted'
pass 'no app execution attempted'
pass 'no LLM API analysis attempted'
pass 'no automatic Cursor execution attempted'
pass 'no network call attempted'
pass 'no automation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
