#!/usr/bin/env bash
# Read-only metadata validation only. No network calls, file writes, or image handling.
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

schema_doc="docs/wallpaper-photo-metadata-schema.md"
curator_readme="assistant/appearance-vibe/wallpaper-photo-curator/README.md"
schema_json="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
samples_json="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

REQUIRED_FIELDS=(
  schema_version
  candidate_id
  candidate_type
  source_type
  source_name
  source_url
  candidate_url
  title
  creator_name
  license_status
  permission_note
  content_rating
  nsfw_flag
  width
  height
  aspect_ratio
  file_format
  file_size_bytes
  wallpaper_fit_score
  photo_widget_fit_score
  duplicate_risk
  watermark_risk
  review_status
  review_decision
  reviewed_by
  reviewed_at
  local_temp_path
  processed_output_path
  created_at
  updated_at
  notes
)

section 'Wallpaper/Photo Metadata Schema'
cat <<'EOF'
Status: schema and safe samples only
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

check_file "${schema_doc}"
check_file "${curator_readme}"
check_file "${schema_json}"
check_file "${samples_json}"

if command -v python3 >/dev/null 2>&1; then
  if python3 -m json.tool "${schema_json}" >/dev/null 2>&1; then
    pass "schema JSON parses"
  else
    fail "schema JSON does not parse"
  fi

  if python3 -m json.tool "${samples_json}" >/dev/null 2>&1; then
    pass "sample records JSON parses"
  else
    fail "sample records JSON does not parse"
  fi

  sample_count="$(python3 -c "import json; print(len(json.load(open('${samples_json}'))['records']))")"
  if [[ "${sample_count}" == "3" ]]; then
    pass "sample records contain exactly 3 records"
  else
    fail "sample records count is not 3"
  fi
else
  warn "python3 not available for JSON parse checks"
fi

check_text "${schema_json}" 'additionalProperties' "schema mentions additionalProperties"

for field in "${REQUIRED_FIELDS[@]}"; do
  check_text "${schema_json}" "\"${field}\"" "schema mentions required field ${field}"
done

check_absent_text "${samples_json}" 'reddit\.com' "sample records do not contain reddit.com"
check_absent_text "${samples_json}" 'devvit' "sample records do not contain devvit"
check_absent_text "${samples_json}" 'http://' "sample records do not contain http://"
check_text "${samples_json}" 'example\.invalid' "sample records use example.invalid"
check_absent_text "${samples_json}" 'nsfw_flag": true' "sample records do not contain nsfw_flag true"
check_absent_text "${samples_json}" '\.jpg|\.jpeg|\.png|\.webp|\.gif|\.avif' "sample records do not contain real image extensions in URLs"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

pass "no write action attempted"
pass "no folder scanning attempted"
pass "no network calls attempted"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
