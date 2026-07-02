#!/usr/bin/env bash
# Read-only blocker queue surfacing from repo-local planning docs.
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

section 'Chief of Staff Blocker Queue (Read-Only)'
cat <<'EOF'
Status: reporting only — blockers are not auto-cleared
Network calls: no
Automation: no
EOF

[[ -f docs/chief-of-staff-approval-blocker-queues.md ]] && pass 'approval/blocker queue doc exists' || fail 'queue doc missing'

section 'Active Blockers'
blockers=0
if [[ -f docs/canvas-llm-stop-marker-curriculum-builder-return.md ]]; then
  printf '[blocker] Canvas LLM runtime — stop marker active\n'
  pass 'canvas blocker listed'
  blockers=$((blockers + 1))
fi
printf '[blocker] Implementation default — no track approved without intake\n'
pass 'implementation gate blocker listed'
blockers=$((blockers + 1))
printf '[blocker] Lovable integration — planning only (Program G1)\n'
printf '[blocker] Cloud AI APIs — no routing active\n'
printf '[blocker] Local LLM inference/install — approval-gated (Program D)\n'
printf '[blocker] Mac system changes/widgets/shortcuts — approval-gated\n'
printf '[blocker] 3D CAD/slicing/printing — approval-gated (Program J)\n'
printf '[blocker] Drive/Gmail/Canvas API/OAuth — last-stage integrations\n'
pass 'static blocker categories emitted'

section 'Escalation'
printf 'See docs/engineering-constitution.md for escalation conditions.\n'
pass 'escalation pointer emitted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
