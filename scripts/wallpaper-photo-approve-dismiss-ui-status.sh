#!/usr/bin/env bash
# Read-only Approve/Dismiss UI design status only. No network calls, UI runtime, or queue writes.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "cannot syntax check missing file: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

design_doc="docs/wallpaper-photo-approve-dismiss-ui-design.md"
schema_json="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Approve/Dismiss UI Design'
cat <<'EOF'
Status: design only
Live UI: no
Queue writes: no
Queue folders created: no
Real images: no
Real image URLs: no
Network calls: no
Reddit integration: no
Devvit integration: no
Image fetching: no
Image downloading: no
Image processing: no
File deletion: no
Folder scanning: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${design_doc}"

check_text "${design_doc}" 'Approve' 'UI design doc mentions Approve'
check_text "${design_doc}" 'Dismiss' 'UI design doc mentions Dismiss'
check_text "${design_doc}" 'Block' 'UI design doc mentions Block'
check_text "${design_doc}" 'Needs More Info' 'UI design doc mentions Needs More Info'
check_text "${design_doc}" 'candidate list' 'UI design doc mentions candidate list'
check_text "${design_doc}" 'candidate detail' 'UI design doc mentions candidate detail'
check_text "${design_doc}" 'metadata summary' 'UI design doc mentions metadata summary'
check_text "${design_doc}" 'source and permission summary' 'UI design doc mentions source and permission summary'
check_text "${design_doc}" 'safety warnings' 'UI design doc mentions safety warnings'
check_text "${design_doc}" 'no live UI|does not implement a live UI|does not implement.*live UI' 'UI design doc mentions no live UI'
check_text "${design_doc}" 'no image fetching|does not fetch images' 'UI design doc mentions no image fetching'
check_text "${design_doc}" 'no image downloading|does not download images' 'UI design doc mentions no image downloading'
check_text "${design_doc}" 'no image processing|does not process images' 'UI design doc mentions no image processing'
check_text "${design_doc}" 'no queue writes|does not write queue decisions' 'UI design doc mentions no queue writes'
check_text "${design_doc}" 'no file deletion|does not delete files' 'UI design doc mentions no file deletion'
check_text "${design_doc}" 'no folder scanning|does not scan folders' 'UI design doc mentions no folder scanning'
check_text "${design_doc}" 'no notifications|does not send notifications' 'UI design doc mentions no notifications'
check_text "${design_doc}" 'no macOS wallpaper changes|does not change macOS wallpaper' 'UI design doc mentions no macOS wallpaper changes'
check_text "${design_doc}" 'no Photos changes|does not modify Photos' 'UI design doc mentions no Photos changes'
check_text "${design_doc}" 'no Reddit|does not add Reddit' 'UI design doc mentions no Reddit'
check_text "${design_doc}" 'no Devvit|does not add Reddit or Devvit|does not add Devvit' 'UI design doc mentions no Devvit'

check_file "${schema_json}"
check_file "${sample_queue}"

if command -v python3 >/dev/null 2>&1; then
  if python3 -m json.tool "${schema_json}" >/dev/null 2>&1; then
    pass 'queue file format JSON parses'
  else
    fail 'queue file format JSON does not parse'
  fi

  if python3 -m json.tool "${sample_queue}" >/dev/null 2>&1; then
    pass 'sample queue JSON parses'
  else
    fail 'sample queue JSON does not parse'
  fi
else
  warn 'python3 not available for JSON parse checks'
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network calls attempted'
pass 'no UI runtime started'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
