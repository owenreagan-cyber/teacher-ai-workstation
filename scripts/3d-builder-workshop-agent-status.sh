#!/usr/bin/env bash
# Read-only 3D Builder Workshop Agent status. Planning surface only — no CAD/export/print.
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

section '3D Builder Workshop Agent (Read-Only Planning Surface)'
cat <<'EOF'
Status: read-only planning only
CAD generation: blocked
STL/3MF export: blocked
Slicer integration: blocked
Printer integration: blocked
Automation: no
Network calls: no
EOF

check_file docs/3d-builder-workshop-agent-foundation.md
check_file docs/3d-builder-workshop-agent-roadmap.md
check_file docs/3d-builder-workshop-agent-non-activation-boundaries.md
check_doc_contains docs/3d-builder-workshop-agent-foundation.md "complete_v1_j1" "3d builder closure status"
check_doc_contains docs/3d-builder-workshop-agent-non-activation-boundaries.md "CAD generation: blocked" "cad generation blocked"
check_doc_contains docs/3d-builder-workshop-agent-roadmap.md "planning only" "roadmap planning only"
check_doc_contains docs/master-build-roadmap.md "3D Builder Workshop Agent" "master roadmap 3d builder"
check_doc_contains docs/teacher-workstation-capability-map.md "3D Builder Workshop Agent" "capability map 3d builder"

section 'CLI and Manifest'
grep -Fq -- '--3d-builder-status' bin/chief-of-staff && pass 'CLI exposes --3d-builder-status' || fail 'CLI missing --3d-builder-status'
grep -Fq -- '"--3d-builder-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --3d-builder-status' || fail 'manifest missing --3d-builder-status'

section 'Negative Non-Activation Assertions'
status_script="scripts/3d-builder-workshop-agent-status.sh"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail '3d builder status script must not shell-invoke curl' || pass '3d builder status script does not shell-invoke curl'
pass 'no CAD generation attempted'
pass 'no STL export attempted'
pass 'no slicer integration attempted'
pass 'no printer integration attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
