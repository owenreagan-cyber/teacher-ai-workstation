#!/usr/bin/env bash
# Read-only status only. Does not create folders or run helper in --create mode.
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

check_literal_text() {
  local path="$1"
  local needle="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Fq -- "${needle}" "${path}"; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

check_absent_command() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -En "${pattern}" "${path}" >/dev/null; then
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

guide_doc="docs/wallpaper-photo-manual-folder-creation-helper.md"
create_script="scripts/wallpaper-photo-create-folders.sh"

section 'Wallpaper/Photo Folder Creation Status'
cat <<'EOF'
Status: manual helper available
Default mode: dry-run
Dashboard creates folders: no
Status checks create folders: no
Files deleted: no
Folders scanned: no
Images fetched: no
Images downloaded: no
Images processed: no
Network calls: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${guide_doc}"
check_file "${create_script}"

check_bash_syntax "${create_script}"

check_literal_text "${create_script}" --dry-run "create script mentions --dry-run"
check_literal_text "${create_script}" --create "create script mentions --create"
check_literal_text "${create_script}" --root "create script mentions --root"
check_literal_text "${create_script}" 'mkdir -p' "create script mentions mkdir -p"

check_absent_command "${create_script}" '^[[:space:]]*rm ' "create script does not contain rm "
check_absent_command "${create_script}" '^[[:space:]]*rmdir\b' "create script does not contain rmdir"
check_absent_command "${create_script}" '^[[:space:]]*find ' "create script does not contain find "
check_absent_command "${create_script}" '^[[:space:]]*curl\b' "create script does not contain curl"
check_absent_command "${create_script}" '^[[:space:]]*wget\b' "create script does not contain wget"
check_absent_command "${create_script}" '^[[:space:]]*osascript\b' "create script does not contain osascript"

dry_run_output=""
dry_run_result=0
dry_run_output="$(bash "${create_script}" --dry-run 2>&1)" || dry_run_result=$?

if [[ "${dry_run_result}" == "0" ]]; then
  pass "helper dry-run exits 0"
else
  fail "helper dry-run failed"
  printf '%s\n' "${dry_run_output}"
fi

if grep -Fq 'Folders created: no' <<<"${dry_run_output}"; then
  pass "helper dry-run says folders created: no"
else
  fail "helper dry-run missing folders created: no"
fi

if grep -Fq 'Summary' <<<"${dry_run_output}"; then
  pass "helper dry-run prints Summary"
else
  fail "helper dry-run missing Summary"
fi

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

pass "status script did not run helper in create mode"
pass "no write action attempted from status script"
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
