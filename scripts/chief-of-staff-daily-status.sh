#!/usr/bin/env bash
# Read-only deterministic daily operating summary. No LLM, network, or automation.
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

section 'Chief of Staff Daily Status (Deterministic)'
cat <<'EOF'
Status: read-only daily operations aggregate only
LLM inference: no
Scheduling/notifications: no
Network calls: no
EOF

[[ -f docs/chief-of-staff-daily-operations.md ]] && pass 'daily operations doc exists' || fail 'daily operations doc missing'
[[ -f docs/build-queue.md ]] && pass 'build queue doc exists' || fail 'build queue doc missing'
[[ -f assistant/memory/active-priorities.md ]] && pass 'active priorities doc exists' || fail 'active priorities doc missing'
[[ -f docs/implementation-approval-gate.md ]] && pass 'implementation gate doc exists' || fail 'implementation gate doc missing'

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
if git diff --quiet && git diff --cached --quiet 2>/dev/null; then
  pass 'working tree clean'
  tree_state="clean"
else
  warn 'working tree has uncommitted changes'
  tree_state="dirty"
fi
printf 'Git branch: %s\n' "${branch}"
printf 'Working tree: %s\n' "${tree_state}"

major_program="$(awk -F'Recommended next major program: ' '/Recommended next major program:/ { split($2,a,"."); print a[1]; exit }' docs/build-queue.md)"
[[ -n "${major_program}" ]] && pass 'major program parsed' || warn 'major program not parsed'
printf 'Recommended major program: %s\n' "${major_program:-(see docs/build-queue.md)}"

roadmap_mission="$(awk '
  /^## 10\. Immediate Next Recommended Mission$/ { in_section = 1; next }
  in_section && /^## / { exit }
  in_section && /^[*][*]/ { gsub(/^\*\*|\*\*$/, ""); print; exit }
' docs/master-build-roadmap.md)"
printf 'Roadmap immediate mission: %s\n' "${roadmap_mission:-(see docs/master-build-roadmap.md)}"

if grep -Fq 'not approved by default' docs/implementation-approval-gate.md; then
  pass 'implementation gate boundary present'
  printf 'Implementation gate: not approved by default\n'
else
  warn 'implementation gate boundary unclear'
fi

if [[ -f docs/canvas-llm-stop-marker-curriculum-builder-return.md ]] && grep -Fq 'stop marker' docs/canvas-llm-stop-marker-curriculum-builder-return.md; then
  pass 'canvas stop marker documented'
  printf 'Canvas LLM: frozen (stop marker active)\n'
else
  warn 'canvas stop marker doc unclear'
fi

if [[ -f docs/chief-of-staff-v1-program-b-closure.md ]]; then
  pass 'program b closure doc exists'
  printf 'Program B: see docs/chief-of-staff-v1-program-b-closure.md\n'
else
  warn 'program b closure doc missing'
fi

section 'Pointers'
printf 'Next-action detail: bin/chief-of-staff --next-action\n'
printf 'Command surface: bin/chief-of-staff --commands\n'
printf 'Full dashboard: bin/chief-of-staff --dashboard\n'
printf 'Closeout checklist: bin/chief-of-staff --closeout\n'
pass 'daily status pointers emitted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
