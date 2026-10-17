#!/usr/bin/env bash
# Canvas Planner — macOS launcher (the executable inside the .app bundle).
#
# Responsibilities:
#   1. Detect whether the Teacher Workstation backend is already running.
#   2. If not, start it safely (bound to 127.0.0.1:4310).
#   3. Poll health, then open the planner directly.
#
# This is a thin launcher over the existing local system. It does NOT rewrite
# the UI, duplicate Canvas/Pacing logic, expose secrets, or perform Canvas
# writes. It only starts/reuses the backend and opens the local URL.
#
# Usage:
#   CanvasPlannerLauncher [--dry-run]
#
set -u

# ---- Single configurable repo location (overridable via env) --------------
REPO="${TEACHER_WORKSTATION_REPO:-/Users/owen/Projects/teacher-ai-workstation}"

HOST="127.0.0.1"
PORT="4310"
HEALTH_URL="http://${HOST}:${PORT}/api/status"
TARGET_URL="http://${HOST}:${PORT}/#weekly"
STARTUP_TIMEOUT_SECS="15"

LOG_DIR="${REPO}/.local/teacher-workstation/launcher"
LOG_FILE="${LOG_DIR}/launcher.log"

CURL="/usr/bin/curl"
OPEN="/usr/bin/open"
OSASCRIPT="/usr/bin/osascript"

# ---- Resolve python3 robustly (GUI apps do not inherit Homebrew PATH) ------
resolve_python() {
  local p
  for p in "${PYTHON:-}" "python3" "/usr/bin/python3" "/opt/homebrew/bin/python3" "/usr/local/bin/python3"; do
    [ -n "${p}" ] && command -v "${p}" >/dev/null 2>&1 && { printf '%s' "${p}"; return 0; }
  done
  return 1
}

log() {
  mkdir -p "${LOG_DIR}" 2>/dev/null || true
  printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >>"${LOG_FILE}" 2>/dev/null || true
}

# Health check: the endpoint must return JSON containing the "overall" key, so
# an unrelated service squatting on port 4310 is NOT mistaken for the backend.
is_healthy() {
  local body rc
  body="$("${CURL}" -fsS --max-time 3 "${HEALTH_URL}" 2>/dev/null)" && rc=0 || rc=$?
  [ "${rc}" -eq 0 ] && printf '%s' "${body}" | grep -q '"overall"'
}

fail_dialog() {
  local detail="$1"
  log "STARTUP FAILURE: ${detail}"
  if [ -x "${OSASCRIPT}" ]; then
    "${OSASCRIPT}" -e "display dialog \"Teacher Workstation could not start.\\n\\nThe local server did not become ready within ${STARTUP_TIMEOUT_SECS} seconds.\\n\\nDetails: ${detail}\\n\\nSuggested action: Open Terminal and run:\\nbin/teacher-workstation --no-open\" with title \"Canvas Planner\" buttons {\"OK\"} default button \"OK\" with icon caution" >/dev/null 2>&1 || true
  fi
}

dry_run() {
  echo "Canvas Planner launcher — dry run"
  echo "  repo: ${REPO}"
  if [ ! -d "${REPO}" ]; then
    echo "  repo found: NO"
    echo "  status: FAILED (repository not found)"
    return 1
  fi
  echo "  repo found: YES"
  if is_healthy; then
    echo "  server: HEALTHY (reuse existing backend)"
  else
    echo "  server: NOT RUNNING (would start backend)"
  fi
  echo "  target URL: ${TARGET_URL}"
  echo "  app bundle: (validated separately by the installer)"
  echo "  status: OK"
  return 0
}

main() {
  if [ "${1:-}" = "--dry-run" ]; then
    dry_run
    return $?
  fi

  log "launch: repo=${REPO}"

  if [ ! -d "${REPO}" ]; then
    log "REPO NOT FOUND: ${REPO}"
    if [ -x "${OSASCRIPT}" ]; then
      "${OSASCRIPT}" -e "display dialog \"Teacher Workstation repository was not found at:\\n${REPO}\" with title \"Canvas Planner\" buttons {\"OK\"} default button \"OK\" with icon stop" >/dev/null 2>&1 || true
    fi
    echo "ERROR: repo not found at ${REPO}" >&2
    return 2
  fi

  # Step 1: already running?
  if is_healthy; then
    log "backend already running; reusing"
    if [ "${CP_LAUNCHER_NO_OPEN:-0}" != "1" ]; then
      "${OPEN}" "${TARGET_URL}" >/dev/null 2>&1 || true
    fi
    log "opened ${TARGET_URL} (no-open: ${CP_LAUNCHER_NO_OPEN:-0})"
    return 0
  fi

  # Step 2: start backend.
  local py
  py="$(resolve_python)" || { fail_dialog "python3 not found"; return 3; }
  log "starting backend with python=${py}"
  (
    cd "${REPO}" || exit 1
    nohup "${py}" -m scripts.teacher_workstation --no-open >>"${LOG_FILE}" 2>&1 &
  ) >/dev/null 2>&1

  # Step 3: poll health with bounded retries.
  local i
  i=0
  while [ "${i}" -lt "${STARTUP_TIMEOUT_SECS}" ]; do
    sleep 1
    if is_healthy; then
      log "backend ready after $((i + 1))s"
      if [ "${CP_LAUNCHER_NO_OPEN:-0}" != "1" ]; then
        "${OPEN}" "${TARGET_URL}" >/dev/null 2>&1 || true
      fi
      log "opened ${TARGET_URL} (no-open: ${CP_LAUNCHER_NO_OPEN:-0})"
      return 0
    fi
    i=$((i + 1))
  done

  fail_dialog "no health response on http://${HOST}:${PORT}"
  return 4
}

main "$@"
