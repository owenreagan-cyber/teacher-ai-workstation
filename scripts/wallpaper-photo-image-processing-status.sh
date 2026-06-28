#!/usr/bin/env bash
# Read-only image processing rules status only. No network calls, image tools, or processing runtime.
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

rules_doc="docs/wallpaper-photo-image-processing-rules.md"
metadata_schema="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
sample_records="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"
queue_format="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Image Processing Rules'
cat <<'EOF'
Status: rules only
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
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${rules_doc}"

check_text "${rules_doc}" '16:9' 'image processing doc mentions 16:9'
check_text "${rules_doc}" '1920' 'image processing doc mentions 1920'
check_text "${rules_doc}" '1080' 'image processing doc mentions 1080'
check_text "${rules_doc}" '3840x2160' 'image processing doc mentions 3840x2160'
check_text "${rules_doc}" '1024' 'image processing doc mentions 1024'
check_text "${rules_doc}" 'jpg' 'image processing doc mentions jpg'
check_text "${rules_doc}" 'png' 'image processing doc mentions png'
check_text "${rules_doc}" 'aspect ratio' 'image processing doc mentions aspect ratio'
check_text "${rules_doc}" 'crop' 'image processing doc mentions crop'
check_text "${rules_doc}" 'fit' 'image processing doc mentions fit'
check_text "${rules_doc}" 'duplicate_risk' 'image processing doc mentions duplicate_risk'
check_text "${rules_doc}" 'watermark_risk' 'image processing doc mentions watermark_risk'
check_text "${rules_doc}" 'license_status' 'image processing doc mentions license_status'
check_text "${rules_doc}" 'permission_note' 'image processing doc mentions permission_note'
check_text "${rules_doc}" 'content_rating' 'image processing doc mentions content_rating'
check_text "${rules_doc}" 'nsfw_flag' 'image processing doc mentions nsfw_flag'
check_text "${rules_doc}" 'no automatic processing' 'image processing doc mentions no automatic processing'
check_text "${rules_doc}" 'no automatic conversion' 'image processing doc mentions no automatic conversion'
check_text "${rules_doc}" 'no automatic resizing' 'image processing doc mentions no automatic resizing'
check_text "${rules_doc}" 'no automatic cropping' 'image processing doc mentions no automatic cropping'
check_text "${rules_doc}" 'no image fetching|does not fetch images' 'image processing doc mentions no image fetching'
check_text "${rules_doc}" 'no image downloading|does not download images' 'image processing doc mentions no image downloading'
check_text "${rules_doc}" 'no file deletion|does not delete files' 'image processing doc mentions no file deletion'
check_text "${rules_doc}" 'no folder scanning|does not scan folders' 'image processing doc mentions no folder scanning'
check_text "${rules_doc}" 'no notifications|does not send notifications' 'image processing doc mentions no notifications'
check_text "${rules_doc}" 'no macOS wallpaper changes|does not change macOS wallpaper' 'image processing doc mentions no macOS wallpaper changes'
check_text "${rules_doc}" 'no Photos changes|does not modify Photos' 'image processing doc mentions no Photos changes'
check_text "${rules_doc}" 'no Reddit|does not add Reddit|automatic Reddit' 'image processing doc mentions no Reddit'
check_text "${rules_doc}" 'no Devvit|does not add Reddit or Devvit|automatic Reddit or Devvit' 'image processing doc mentions no Devvit'

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
pass 'no image processing attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
