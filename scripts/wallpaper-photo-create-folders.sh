#!/usr/bin/env bash
# Manual folder creation only. Avoids destructive and external commands.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

MODE="dry-run"
ROOT_ARG=""

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

usage() {
  cat <<'EOF'
Usage:
  bash scripts/wallpaper-photo-create-folders.sh [--dry-run]
  bash scripts/wallpaper-photo-create-folders.sh --create [--root ROOT_PATH]

Default mode is dry-run. Use --create only when intentionally creating folders.
EOF
}

APPROVED_RELATIVE_PATHS=(
  'Wallpaper Curator'
  'Wallpaper Curator/Temp Wallpaper Candidates'
  'Wallpaper Curator/Temp Photo Candidates'
  'Wallpaper Curator/Approved Wallpaper Queue'
  'Wallpaper Curator/Approved Photo Queue'
  'Wallpaper Curator/Processed Wallpaper'
  'Wallpaper Curator/Processed Photo Widget'
  'Wallpaper Curator/Metadata'
  'Wallpaper Rotation'
  'Photo Widget Rotation'
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --create)
      MODE="create"
      shift
      ;;
    --root)
      if [[ -z "${2:-}" ]]; then
        fail "missing value for --root"
        usage >&2
        exit 1
      fi
      ROOT_ARG="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      usage >&2
      exit 1
      ;;
  esac
done

resolve_root_path() {
  if [[ -z "${ROOT_ARG}" ]]; then
    printf '%s/Pictures\n' "${HOME}"
    return
  fi

  case "${ROOT_ARG}" in
    ~)
      printf '%s\n' "${HOME}"
      ;;
    ~/*)
      printf '%s/%s\n' "${HOME}" "${ROOT_ARG#~/}"
      ;;
    *)
      printf '%s\n' "${ROOT_ARG}"
      ;;
  esac
}

validate_root_path() {
  local root="$1"

  if [[ -z "${root}" ]]; then
    fail "root path is empty"
    return 1
  fi

  if [[ "${root}" == "/" ]]; then
    fail "root path must not be /"
    return 1
  fi

  if [[ "${root}" == *".."* ]]; then
    fail "root path must not contain .."
    return 1
  fi

  if [[ "${root}" == *';'* || "${root}" == *'|'* || "${root}" == *'&'* || "${root}" == *'`'* ]]; then
    fail "root path must not contain shell metacharacters"
    return 1
  fi

  if [[ "${root}" == *'$('* || "${root}" == *'${'* ]]; then
    fail "root path must not contain command substitution"
    return 1
  fi

  case "${root}" in
    "${HOME}"/*|/Users/*|/tmp/*)
      return 0
      ;;
    *)
      fail "root path must be a user-owned local path under HOME, /Users, or /tmp"
      return 1
      ;;
  esac
}

RESOLVED_ROOT="$(resolve_root_path)"
if ! validate_root_path "${RESOLVED_ROOT}"; then
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

section 'Wallpaper/Photo Manual Folder Creation Helper'
if [[ "${MODE}" == "dry-run" ]]; then
  cat <<'EOF'
Mode: dry-run
Folders created: no
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
else
  cat <<'EOF'
Mode: create
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
fi

printf 'Root: %s\n' "${RESOLVED_ROOT}"

section 'Approved Folders'
for relative_path in "${APPROVED_RELATIVE_PATHS[@]}"; do
  target_dir="${RESOLVED_ROOT}/${relative_path}"

  case "${target_dir}" in
    "${RESOLVED_ROOT}"/*) ;;
    *)
      fail "target escapes approved root: ${target_dir}"
      continue
      ;;
  esac

  if [[ "${MODE}" == "dry-run" ]]; then
    printf 'WOULD CREATE: %s\n' "${target_dir}"
    pass "dry-run path planned: ${relative_path}"
  elif [[ -d "${target_dir}" ]]; then
    printf 'ALREADY PRESENT: %s\n' "${target_dir}"
    pass "folder already present: ${relative_path}"
  else
    mkdir -p "${target_dir}"
    if [[ -d "${target_dir}" ]]; then
      printf 'CREATED: %s\n' "${target_dir}"
      pass "folder created: ${relative_path}"
    else
      fail "folder not created: ${relative_path}"
    fi
  fi
done

if [[ "${MODE}" == "create" ]]; then
  pass "create mode completed without deletion or scanning"
else
  pass "dry-run completed without folder creation"
fi

pass "no network calls attempted"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
