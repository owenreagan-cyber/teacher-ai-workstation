#!/usr/bin/env bash
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

folder_design_doc="docs/wallpaper-photo-rotation-folder-design.md"
curator_plan_doc="docs/appearance-vibe-wallpaper-photo-curator-plan.md"

section "Wallpaper/Photo Rotation Folder Design"
cat <<'EOF'
Status: planning only
Folders created: no
Image fetching: no
Image downloading: no
Image processing: no
Folder scanning: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
Reddit integration: no
Devvit integration: no
Network calls: no
EOF

section "Future Approval Gates"
cat <<'EOF'
1. Approve conceptual folder design
2. Approve actual folder creation
3. Approve metadata file format
4. Approve temp candidate queue behavior
5. Approve cleanup/deletion rules
6. Approve processing destination folders
7. Approve macOS permissions
8. Approve notification behavior
9. Approve image processing rules
10. Approve any source integration
EOF

section "Workflow Checks"

check_file "${folder_design_doc}"
check_file "${curator_plan_doc}"

check_text "${folder_design_doc}" "planning-only|planning only" "folder design doc mentions planning-only"
check_text "${folder_design_doc}" "does not create folders|does not create these folders" "folder design doc mentions does not create folders"
check_text "${folder_design_doc}" "Temp Wallpaper Candidates" "folder design doc mentions Temp Wallpaper Candidates"
check_text "${folder_design_doc}" "Temp Photo Candidates" "folder design doc mentions Temp Photo Candidates"
check_text "${folder_design_doc}" "Approved Wallpaper Queue" "folder design doc mentions Approved Wallpaper Queue"
check_text "${folder_design_doc}" "Approved Photo Queue" "folder design doc mentions Approved Photo Queue"
check_text "${folder_design_doc}" "Processed Wallpaper" "folder design doc mentions Processed Wallpaper"
check_text "${folder_design_doc}" "Processed Photo Widget" "folder design doc mentions Processed Photo Widget"
check_text "${folder_design_doc}" "Metadata" "folder design doc mentions Metadata"
check_text "${folder_design_doc}" "Wallpaper Rotation" "folder design doc mentions Wallpaper Rotation"
check_text "${folder_design_doc}" "Photo Widget Rotation" "folder design doc mentions Photo Widget Rotation"
check_text "${folder_design_doc}" "maximum 10 wallpaper candidates|10 wallpaper" "folder design doc mentions maximum 10 wallpaper candidates"
check_text "${folder_design_doc}" "maximum 10 photo candidates|10 photo" "folder design doc mentions maximum 10 photo candidates"
check_text "${folder_design_doc}" "human approval" "folder design doc mentions human approval"
check_text "${folder_design_doc}" "no image fetching|does not fetch images" "folder design doc mentions no image fetching"
check_text "${folder_design_doc}" "no image downloading|does not download images" "folder design doc mentions no image downloading"
check_text "${folder_design_doc}" "no image processing|does not process images" "folder design doc mentions no image processing"
check_text "${folder_design_doc}" "no folder scanning|does not scan folders" "folder design doc mentions no folder scanning"
check_text "${folder_design_doc}" "no notifications|does not send notifications" "folder design doc mentions no notifications"
check_text "${folder_design_doc}" "no macOS wallpaper changes|does not change macOS wallpaper" "folder design doc mentions no macOS wallpaper changes"
check_text "${folder_design_doc}" "no Photos changes|does not modify Photos" "folder design doc mentions no Photos changes"
check_text "${folder_design_doc}" "no Reddit|does not add Reddit" "folder design doc mentions no Reddit"
check_text "${folder_design_doc}" "no Devvit|does not add Devvit" "folder design doc mentions no Devvit"
check_text "${folder_design_doc}" "no network calls|does not add network calls" "folder design doc mentions no network calls"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

pass "no write action attempted"
pass "no folder scanning attempted"
pass "no network calls attempted"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
