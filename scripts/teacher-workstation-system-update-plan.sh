#!/usr/bin/env bash
# Read-only manual update planning checklist. Does not apply updates or mutate state.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Teacher Workstation System Update Plan (Manual Template)'
cat <<'EOF'
Status: read-only planning template only — no automatic application
Mutations: none
Package managers: none
Network calls: none
EOF

[[ -f docs/teacher-workstation-system-updater.md ]] && pass 'system updater doc exists' || fail 'system updater doc missing'

section 'Manual Update Planning Checklist'
cat <<'EOF'
[ ] Run Health Monitor: bin/chief-of-staff --system-health
[ ] Run System Updater check: bin/chief-of-staff --system-update-check
[ ] Review implementation gate: docs/implementation-approval-gate.md
[ ] Confirm mission authorization before any implementation
[ ] Pull latest main: git pull (manual; not run by this command)
[ ] Create feature branch for approved work (manual)
[ ] Run dashboard proof: bin/chief-of-staff --dashboard
[ ] Run phase status: bash scripts/phase-1-status.sh
[ ] Run smoke tests: bash tests/smoke-chief-of-staff-cli.sh
[ ] PR review and merge (manual)
[ ] Branch cleanup and final proof on clean main (manual)
[ ] Non-activation confirmed: no APIs/integrations/automation added
[ ] Document deferred items in build queue if needed
EOF
pass 'update planning checklist emitted'

section 'Blocked in v0 (Requires Separate Approval)'
printf 'Package installs, dependency upgrades, model downloads, Mac changes, widget/shortcut install, apply-approved-updates — all blocked.\n'
pass 'blocked capabilities stated'

section 'Current Local Snapshot'
printf 'Branch: %s\n' "$(git branch --show-current 2>/dev/null || echo unknown)"
printf 'Latest commit: %s\n' "$(git log -1 --oneline 2>/dev/null || echo unknown)"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
