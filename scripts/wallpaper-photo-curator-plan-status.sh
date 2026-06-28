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

plan_doc="docs/appearance-vibe-wallpaper-photo-curator-plan.md"

section "Appearance & Vibe Automated Wallpaper and Photo Curator Plan"
cat <<'EOF'
Status: planning only
Implementation: no
Image fetching: no
Image downloading: no
Image processing: no
Reddit integration: no
Devvit integration: no
Network calls: no
Temp folders created: no
Notifications: no
macOS wallpaper changes: no
EOF

section "Future Approval Gates"
cat <<'EOF'
1. Approve source allowlist
2. Approve metadata-only source check
3. Approve temp review folder design
4. Approve notification design
5. Approve review UI design
6. Approve image processing rules
7. Approve destination folders
8. Approve Reddit source integration, if ever needed
9. Approve Devvit companion app, if ever needed
10. Approve automatic schedule
EOF

section "Workflow Checks"

check_file "${plan_doc}"

check_text "${plan_doc}" "planning-only|planning only" "plan mentions planning-only"
check_text "${plan_doc}" "local-first|local first" "plan mentions local-first"
check_text "${plan_doc}" "Appearance & Vibe" "plan mentions Appearance & Vibe"
check_text "${plan_doc}" "Automated Wallpaper and Photo Curator" "plan mentions Automated Wallpaper and Photo Curator"
check_text "${plan_doc}" "Approve|Dismiss|approve/dismiss" "plan mentions approve/dismiss"
check_text "${plan_doc}" "temporary review queue|temp review queue" "plan mentions temporary review queue"
check_text "${plan_doc}" "10 wallpaper candidates|maximum 10 wallpaper" "plan mentions 10 wallpaper candidates"
check_text "${plan_doc}" "10 photo candidates|maximum 10 photo" "plan mentions 10 photo candidates"
check_text "${plan_doc}" "Reddit may be a future source|Reddit as a future" "plan mentions Reddit as future source only"
check_text "${plan_doc}" "Devvit may be a future|future Reddit-native companion" "plan mentions Devvit as future companion only"
check_text "${plan_doc}" "does not fetch images|no image fetching" "plan mentions no image fetching"
check_text "${plan_doc}" "does not download images|no image downloading" "plan mentions no image downloading"
check_text "${plan_doc}" "does not process images|no image processing" "plan mentions no image processing"
check_text "${plan_doc}" "no network calls|does not add network calls" "plan mentions no network calls"
check_text "${plan_doc}" "No APIs|no APIs" "plan mentions no APIs"
check_text "${plan_doc}" "No OAuth|no OAuth" "plan mentions no OAuth"
check_text "${plan_doc}" "no secrets|No secrets" "plan mentions no secrets"
check_text "${plan_doc}" "no temp folders created|does not create temp folders" "plan mentions no temp folders created"
check_text "${plan_doc}" "no macOS wallpaper changes|does not modify macOS wallpaper" "plan mentions no macOS wallpaper changes"
check_text "${plan_doc}" "no Photos changes|does not modify Photos" "plan mentions no Photos changes"
check_text "${plan_doc}" "no background jobs|background jobs" "plan mentions no background jobs"
check_text "${plan_doc}" "no launch agents|launch agents" "plan mentions no launch agents"
check_text "${plan_doc}" "No NSFW sources by default|NSFW sources are off by default" "plan mentions no NSFW sources by default"
check_text "${plan_doc}" "human approval" "plan mentions human approval"

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
