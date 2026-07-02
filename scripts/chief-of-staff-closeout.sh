#!/usr/bin/env bash
# Read-only deterministic closeout checklist. Does not mutate git, branches, or system state.
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

section 'Chief of Staff Closeout (Read-Only Checklist)'
cat <<'EOF'
Status: closeout template only — no automation
Mutations: none (does not merge PRs, delete branches, or push)
Network calls: no
EOF

[[ -f docs/chief-of-staff-closeout-workflow.md ]] && pass 'closeout workflow doc exists' || fail 'closeout workflow doc missing'

section 'Closeout Checklist'
cat <<'EOF'
[ ] Dashboard proof: bin/chief-of-staff --dashboard
[ ] Phase status: bash scripts/phase-1-status.sh
[ ] Cursor workflow: bash scripts/cursor-workflow-status.sh
[ ] Smoke CLI: bash tests/smoke-chief-of-staff-cli.sh
[ ] Operating commands: bash tests/chief-of-staff-v1-operating-test.sh
[ ] PR reviewed (if applicable): gh pr view
[ ] Merge commit recorded on main (if applicable): git log -1
[ ] Local main clean: git status
[ ] Feature branches deleted: git branch -a
[ ] Branches pruned: git fetch --prune
[ ] Non-activation confirmed: no APIs/integrations/automation added
[ ] Next mission noted: docs/build-queue.md / docs/master-build-roadmap.md
EOF
pass 'closeout checklist emitted'

section 'Current Local Snapshot'
branch="$(git branch --show-current 2>/dev/null || echo unknown)"
printf 'Current branch: %s\n' "${branch}"
if git diff --quiet && git diff --cached --quiet 2>/dev/null; then
  pass 'working tree currently clean'
else
  warn 'working tree currently has uncommitted changes'
fi
printf 'Latest commit: %s\n' "$(git log -1 --oneline 2>/dev/null || echo unknown)"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
