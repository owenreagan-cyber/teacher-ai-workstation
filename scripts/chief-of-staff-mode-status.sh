#!/usr/bin/env bash
# Read-only operating mode concepts. Does not change Mac settings or system state.
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

section 'Chief of Staff Mode Status (Conceptual)'
cat <<'EOF'
Status: descriptive/status concepts only
Mac changes: no
Automation: no
Wallpaper/widgets/shortcuts: no changes
EOF

[[ -f docs/chief-of-staff-mode-status.md ]] && pass 'mode status doc exists' || fail 'mode status doc missing'

section 'Operating Modes (Planning)'
cat <<'EOF'
| Mode | Purpose | Active switching |
| --- | --- | --- |
| Planning Mode | Lesson/weekly planning focus | conceptual only |
| Development Mode | Repo/engineering missions (Cursor) | conceptual only |
| Curriculum Mode | Curriculum Builder foundations | conceptual only |
| Lesson Planning Mode | Lesson planning scaffold review | conceptual only |
| Teaching Mode | Classroom delivery focus | conceptual only |
| Canvas Prep Mode | Frozen Canvas export planning | conceptual only |
| Review Mode | Grading/review workflows | conceptual only |
| Closeout Mode | End-of-day proof and handoff | conceptual only |
EOF
pass 'mode table emitted'

section 'Current Context Hints (Deterministic)'
if [[ -f docs/master-build-roadmap.md ]] && grep -Fq 'Health Monitor' docs/master-build-roadmap.md; then
  printf 'Suggested post-Program-B focus: Health Monitor read-only foundation (see roadmap)\n'
  pass 'roadmap hint emitted'
fi
printf 'Chief of Staff does not switch modes automatically.\n'
pass 'mode boundary stated'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
