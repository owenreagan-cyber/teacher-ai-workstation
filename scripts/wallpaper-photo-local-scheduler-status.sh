#!/usr/bin/env bash
# Read-only local scheduler plan status only. No network calls, schedulers, or automation runtime.
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

plan_doc="docs/wallpaper-photo-local-automation-scheduler-plan.md"
metadata_schema="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
sample_records="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"
queue_format="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Local Automation Scheduler Plan'
cat <<'EOF'
Status: planning only
Scheduler implemented: no
Launch agents: no
Cron jobs: no
Background jobs: no
Unattended runs: no
Notifications sent: no
Live processing: no
Image conversion: no
Image resizing: no
Image cropping: no
Image previews: no
Processed outputs created: no
Queue writes: no
Files deleted: no
Folder scanning: no
Network calls: no
Reddit integration: no
Devvit integration: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${plan_doc}"

check_text "${plan_doc}" 'manual only' 'scheduler doc mentions manual only'
check_text "${plan_doc}" 'daily dry-run' 'scheduler doc mentions daily dry-run'
check_text "${plan_doc}" 'weekly dry-run' 'scheduler doc mentions weekly dry-run'
check_text "${plan_doc}" 'dry-run first|Dry-Run First' 'scheduler doc mentions dry-run first'
check_text "${plan_doc}" 'preflight checks|Preflight Checks' 'scheduler doc mentions preflight checks'
check_text "${plan_doc}" 'pause scheduling' 'scheduler doc mentions pause scheduling'
check_text "${plan_doc}" 'disable scheduling' 'scheduler doc mentions disable scheduling'
check_text "${plan_doc}" 'notifications are design-only' 'scheduler doc mentions notifications are design-only'
check_text "${plan_doc}" 'no automatic scheduling' 'scheduler doc mentions no automatic scheduling'
check_text "${plan_doc}" 'no launch agents' 'scheduler doc mentions no launch agents'
check_text "${plan_doc}" 'no cron jobs' 'scheduler doc mentions no cron jobs'
check_text "${plan_doc}" 'no background jobs' 'scheduler doc mentions no background jobs'
check_text "${plan_doc}" 'no unattended source fetching' 'scheduler doc mentions no unattended source fetching'
check_text "${plan_doc}" 'no unattended image downloading' 'scheduler doc mentions no unattended image downloading'
check_text "${plan_doc}" 'no unattended image processing' 'scheduler doc mentions no unattended image processing'
check_text "${plan_doc}" 'no unattended deletion' 'scheduler doc mentions no unattended deletion'
check_text "${plan_doc}" 'no unattended queue writes' 'scheduler doc mentions no unattended queue writes'
check_text "${plan_doc}" 'no unattended wallpaper changes' 'scheduler doc mentions no unattended wallpaper changes'
check_text "${plan_doc}" 'no unattended Photos changes' 'scheduler doc mentions no unattended Photos changes'
check_text "${plan_doc}" 'no image fetching|does not fetch images' 'scheduler doc mentions no image fetching'
check_text "${plan_doc}" 'no image downloading|does not download images' 'scheduler doc mentions no image downloading'
check_text "${plan_doc}" 'no image processing|does not process images' 'scheduler doc mentions no image processing'
check_text "${plan_doc}" 'no file deletion|does not delete files' 'scheduler doc mentions no file deletion'
check_text "${plan_doc}" 'no folder scanning|does not scan folders' 'scheduler doc mentions no folder scanning'
check_text "${plan_doc}" 'no notifications|does not send notifications' 'scheduler doc mentions no notifications'
check_text "${plan_doc}" 'no macOS wallpaper changes|does not change macOS wallpaper' 'scheduler doc mentions no macOS wallpaper changes'
check_text "${plan_doc}" 'no Photos changes|does not modify Photos' 'scheduler doc mentions no Photos changes'
check_text "${plan_doc}" 'no Reddit|does not add Reddit|automatic Reddit' 'scheduler doc mentions no Reddit'
check_text "${plan_doc}" 'no Devvit|does not add Reddit or Devvit|automatic Reddit or Devvit' 'scheduler doc mentions no Devvit'

check_file "${metadata_schema}"
check_file "${sample_records}"
check_file "${queue_format}"
check_file "${sample_queue}"

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${metadata_schema}" "${sample_records}" "${queue_format}" "${sample_queue}"; do
    if python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    else
      fail "JSON does not parse: ${json_file}"
    fi
  done
else
  warn 'python3 not available for JSON parse checks'
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network calls attempted'
pass 'no scheduler runtime started'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
