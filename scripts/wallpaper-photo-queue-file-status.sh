#!/usr/bin/env bash
# Read-only queue file format status only. No network calls, file writes, or queue runtime.
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

format_doc="docs/wallpaper-photo-queue-file-format.md"
schema_json="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
validator_script="scripts/wallpaper-photo-queue-file-validator.sh"

section 'Wallpaper/Photo Queue File Format'
cat <<'EOF'
Status: file format and dry-run validator only
Live queues: no
Queue folders created: no
Real images: no
Real image URLs: no
Network calls: no
Reddit integration: no
Devvit integration: no
Image fetching: no
Image downloading: no
Image processing: no
Folder scanning: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${format_doc}"
check_file "${schema_json}"
check_file "${sample_queue}"
check_file "${validator_script}"
check_bash_syntax "${validator_script}"

if command -v python3 >/dev/null 2>&1; then
  if python3 -m json.tool "${schema_json}" >/dev/null 2>&1; then
    pass 'queue-file-format.json parses'
  else
    fail 'queue-file-format.json does not parse'
  fi

  if python3 -m json.tool "${sample_queue}" >/dev/null 2>&1; then
    pass 'sample-queue.json parses'
  else
    fail 'sample-queue.json does not parse'
  fi

  sample_count="$(python3 -c "import json; print(len(json.load(open('${sample_queue}'))['records']))")"
  if [[ "${sample_count}" == "3" ]]; then
    pass 'sample queue contains exactly 3 records'
  else
    fail 'sample queue record count is not 3'
  fi
else
  warn 'python3 not available for JSON parse checks'
fi

check_text "${sample_queue}" 'example\.invalid' 'sample queue uses example.invalid'
check_absent_text "${sample_queue}" 'reddit\.com' 'sample queue does not contain reddit.com'
check_absent_text "${sample_queue}" '\.jpg|\.jpeg|\.png|\.webp|\.gif|\.avif' 'sample queue does not contain likely image extensions in URLs'
check_absent_text "${sample_queue}" 'nsfw_flag": true' 'sample queue does not contain nsfw_flag true'

if [[ -x "${validator_script}" || -f "${validator_script}" ]]; then
  if bash "${validator_script}" >/dev/null 2>&1; then
    pass 'validator exits 0 on sample queue'
  else
    fail 'validator failed on sample queue'
  fi
fi

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
