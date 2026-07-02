#!/usr/bin/env bash
# Read-only approval queue surfacing from repo-local planning docs.
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

section 'Chief of Staff Approval Queue (Read-Only)'
cat <<'EOF'
Status: reporting only — Chief of Staff does not bypass gates
Task creation: no
Network calls: no
EOF

[[ -f docs/chief-of-staff-approval-blocker-queues.md ]] && pass 'approval/blocker queue doc exists' || fail 'queue doc missing'
[[ -f docs/implementation-approval-gate.md ]] && pass 'implementation gate doc exists' || fail 'implementation gate doc missing'

section 'Default Gate'
printf 'Implementation approval: NOT approved by default\n'
grep -Fq 'Implementation approval status: not approved' docs/implementation-approval-gate.md && pass 'default gate documented' || warn 'default gate wording missing'

section 'Approval Queue Categories (Planning)'
cat <<'EOF'
- New implementation track intake (docs/implementation-approval-gate.md)
- Real registry records (Curriculum Builder; no student data)
- Renderers and generation surfaces
- Canvas LLM stop marker supersession
- Drive/Gmail/Canvas API/OAuth connectors
- Mac wallpaper/widget/shortcut install missions
- Local LLM install/model downloads
- Lovable / cloud API connection
- 3D Builder CAD/slicing/printing activation
- Health Monitor repair or System Updater apply
- Automation/background jobs
EOF
pass 'approval queue categories emitted'

section 'Owen Decision Required'
printf 'Chief of Staff reports queue items only. Owen approves missions explicitly.\n'
pass 'approval boundary stated'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
