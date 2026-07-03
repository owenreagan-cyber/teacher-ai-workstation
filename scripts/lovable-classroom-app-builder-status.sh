#!/usr/bin/env bash
# Read-only Lovable Classroom App Builder status. Planning surface only — not connected.
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

section 'Lovable Classroom App Builder (Read-Only Planning Surface)'
cat <<'EOF'
Status: read-only planning only
Lovable API: blocked
External Lovable fetch: blocked
OAuth: blocked
Network calls: blocked
Live app generation: blocked
CAL1 boundary: docs/classroom-app-lab-vs-lovable-lane-boundary.md
AI Tool Routing R0: Lovable row inactive — see --model-routing-status
Automation: no
EOF

check_file docs/lovable-classroom-app-builder-foundation.md
check_file docs/lovable-classroom-app-builder-non-activation-boundaries.md
check_file docs/lovable-classroom-app-builder-readiness-plan.md
check_doc_contains docs/lovable-classroom-app-builder-foundation.md "complete_v1_g1" "lovable closure status"
check_doc_contains docs/lovable-classroom-app-builder-non-activation-boundaries.md "Lovable API: blocked" "lovable api blocked"
check_doc_contains docs/lovable-classroom-app-builder-non-activation-boundaries.md "OAuth: blocked" "lovable oauth blocked"
check_doc_contains docs/lovable-classroom-app-builder-non-activation-boundaries.md "Network calls: blocked" "lovable network blocked"
check_doc_contains docs/lovable-classroom-app-builder-readiness-plan.md "become Lovable" "architecture rule documented"
check_doc_contains assistant/model-routing.md "inactive" "model routing lovable inactive"
check_doc_contains docs/ai-tool-routing-matrix.md "Lovable" "ai tool routing matrix lovable"
check_doc_contains docs/classroom-app-lab-vs-lovable-lane-boundary.md "G1" "cal1 g1 boundary cross-link"
check_doc_contains docs/lovable-classroom-app-builder-mission-approval-gate-checklist.md "approval-gated" "lovable mission approval gate checklist"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Lovable Classroom App Builder" "roadmap lovable program"
check_doc_contains docs/teacher-workstation-capability-map.md "Lovable classroom app builder" "capability map lovable"
check_doc_contains docs/build-queue.md "Lovable" "build queue lovable"

section 'Planning Summary'
printf 'Lovable integration: planning only — not connected\n'
printf 'Chief of Staff role: route/validate/track — not build apps\n'
printf 'Manual browser profile: human-operated only\n'
pass 'planning summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--lovable-status' bin/chief-of-staff && pass 'CLI exposes --lovable-status' || fail 'CLI missing --lovable-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'
if grep -Fq -- '"--lovable-status"' assistant/chief-of-staff/v1/command-surface-manifest.json 2>/dev/null; then
  if grep -A1 '"--lovable-status"' assistant/chief-of-staff/v1/command-surface-manifest.json | grep -Fq '"implemented"'; then
    pass 'manifest lists --lovable-status as implemented'
  else
    fail 'manifest must mark --lovable-status implemented'
  fi
else
  fail 'manifest missing --lovable-status'
fi

section 'Negative Non-Activation Assertions'
status_script="scripts/lovable-classroom-app-builder-status.sh"
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'lovable status script must not shell-invoke curl'
else
  pass 'lovable status script does not shell-invoke curl'
fi
lovable_invocations="$(grep -Ev 'must not reference|does not reference' "${status_script}" || true)"
if grep -Eq 'lovable\.dev' <<< "${lovable_invocations}"; then
  fail 'lovable status script must not reference lovable.dev fetch targets'
else
  pass 'lovable status script does not reference lovable.dev fetch targets'
fi
if grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'lovable status script must not shell-invoke wget'
else
  pass 'lovable status script does not shell-invoke wget'
fi
if grep -Eq '(^|[;&|[:space:]])(brew|npm|pip|apt-get|yum)[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'lovable status script must not shell-invoke package managers'
else
  pass 'lovable status script does not shell-invoke package managers'
fi
pass 'no Lovable API call attempted'
pass 'no OAuth flow attempted'
pass 'no live app generation attempted'
pass 'no network call attempted'
pass 'no automation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
