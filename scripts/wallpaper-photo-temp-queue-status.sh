#!/usr/bin/env bash
# Read-only temp queue rules validation only. No network calls, file writes, or queue runtime.
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

check_absent_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    fail "${label}"
  else
    pass "${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

rules_doc="docs/wallpaper-photo-temp-queue-rules.md"
schema_json="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
samples_json="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

section 'Wallpaper/Photo Temp Queue Rules'
cat <<'EOF'
Status: rules only
Live queues: no
Queue folders created: no
Images fetched: no
Images downloaded: no
Images processed: no
Automatic approval: no
Automatic deletion: no
Folder scanning: no
Network calls: no
Reddit integration: no
Devvit integration: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${rules_doc}"

check_text "${rules_doc}" 'maximum 10 wallpaper candidates' 'temp queue doc mentions max 10 wallpaper candidates'
check_text "${rules_doc}" 'maximum 10 photo-widget candidates|maximum 10 photo-widget' 'temp queue doc mentions max 10 photo-widget candidates'
check_text "${rules_doc}" 'maximum 20 total temporary candidates' 'temp queue doc mentions max 20 total temporary candidates'
check_text "${rules_doc}" 'unreviewed' 'temp queue doc mentions unreviewed'
check_text "${rules_doc}" 'approved' 'temp queue doc mentions approved'
check_text "${rules_doc}" 'dismissed' 'temp queue doc mentions dismissed'
check_text "${rules_doc}" 'blocked' 'temp queue doc mentions blocked'
check_text "${rules_doc}" 'needs_more_info' 'temp queue doc mentions needs_more_info'
check_text "${rules_doc}" 'no automatic approval' 'temp queue doc mentions no automatic approval'
check_text "${rules_doc}" 'no automatic deletion' 'temp queue doc mentions no automatic deletion'
check_text "${rules_doc}" 'stale cleanup requires|stale cleanup requires a separate future approval' 'temp queue doc mentions stale cleanup requires future approval'
check_text "${rules_doc}" 'no image fetching|does not fetch images' 'temp queue doc mentions no image fetching'
check_text "${rules_doc}" 'no image downloading|does not download images' 'temp queue doc mentions no image downloading'
check_text "${rules_doc}" 'no image processing|does not process images' 'temp queue doc mentions no image processing'
check_text "${rules_doc}" 'no folder scanning|does not scan folders' 'temp queue doc mentions no folder scanning'
check_text "${rules_doc}" 'no notifications|does not send notifications' 'temp queue doc mentions no notifications'
check_text "${rules_doc}" 'no Reddit|does not add Reddit' 'temp queue doc mentions no Reddit'
check_text "${rules_doc}" 'no Devvit|no automatic Reddit or Devvit|does not add Reddit or Devvit' 'temp queue doc mentions no Devvit'

check_file "${schema_json}"
check_file "${samples_json}"

if command -v python3 >/dev/null 2>&1; then
  if python3 -m json.tool "${schema_json}" >/dev/null 2>&1; then
    pass 'schema JSON parses'
  else
    fail 'schema JSON does not parse'
  fi

  if python3 -m json.tool "${samples_json}" >/dev/null 2>&1; then
    pass 'sample records JSON parses'
  else
    fail 'sample records JSON does not parse'
  fi

  sample_count="$(python3 -c "import json; print(len(json.load(open('${samples_json}'))['records']))")"
  if [[ "${sample_count}" == "3" ]]; then
    pass 'sample records contain exactly 3 records'
  else
    fail 'sample records count is not 3'
  fi
else
  warn 'python3 not available for JSON parse checks'
fi

check_text "${samples_json}" 'example\.invalid' 'sample records use example.invalid'
check_absent_text "${samples_json}" 'reddit\.com' 'sample records do not contain reddit.com'
check_absent_text "${samples_json}" '\.jpg|\.jpeg|\.png|\.webp|\.gif|\.avif' 'sample records do not contain real image extensions in URLs'

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network calls attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
