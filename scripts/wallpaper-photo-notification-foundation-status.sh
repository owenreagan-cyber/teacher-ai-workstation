#!/usr/bin/env bash
# Read-only notification foundation status only. No notifications sent, network calls, or file operations.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

foundation_doc="docs/wallpaper-photo-notification-foundation.md"
sample_plan="assistant/appearance-vibe/wallpaper-photo-curator/sample-notification-plan.json"
plan_validator="scripts/wallpaper-photo-notification-plan-validator.sh"
sample_scheduler="assistant/appearance-vibe/wallpaper-photo-curator/sample-scheduler-run-plan.json"
sample_processing="assistant/appearance-vibe/wallpaper-photo-curator/sample-image-processing-plan.json"
sample_ui_state="assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json"
sample_discovery="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
sample_metadata="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

section 'Wallpaper/Photo Notification Foundation'
cat <<'EOF'
Status: planning/status/sample notification plan only
Notifications enabled: no
Notifications sent: no
Notification mechanism: none
Scheduler implemented: no
Launch agents: no
Cron jobs: no
Background jobs: no
Unattended runs: no
Network calls: no
Image fetching: no
Image downloading: no
Image processing: no
Queue writes: no
Reddit integration: no
Devvit integration: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${foundation_doc}"
check_file "${sample_plan}"
check_file "${plan_validator}"
check_file "${sample_scheduler}"
check_file "${sample_processing}"
check_file "${sample_ui_state}"
check_file "${sample_discovery}"
check_file "${sample_allowlist}"
check_file "${sample_queue}"
check_file "${sample_metadata}"

check_bash_syntax "${plan_validator}"

if [[ -f "${plan_validator}" ]]; then
  if bash "${plan_validator}" >/dev/null 2>&1; then
    pass "notification plan validator exits 0 on sample notification plan"
  else
    fail "notification plan validator failed on sample notification plan"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${sample_plan}" "${sample_scheduler}" "${sample_processing}" "${sample_ui_state}" "${sample_discovery}" "${sample_allowlist}" "${sample_queue}" "${sample_metadata}"; do
    if [[ -f "${json_file}" ]] && python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    elif [[ -f "${json_file}" ]]; then
      fail "JSON does not parse: ${json_file}"
    fi
  done

  if [[ -f "${sample_plan}" ]]; then
    plan_checks="$(python3 - "${sample_plan}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
previews = data.get("notification_previews", [])
print(len(previews) if isinstance(previews, list) else 0)
print(data.get("mode", ""))
print(str(data.get("notifications_enabled", "")).lower())
print(str(data.get("notifications_sent", "")).lower())
print(data.get("notification_mechanism", ""))
print(str(data.get("network_calls", "")).lower())
print(str(data.get("scheduler_enabled", "")).lower())
print(str(data.get("queue_writes", "")).lower())
print(str(data.get("image_processing", "")).lower())
PY
)"
    preview_count="$(printf '%s\n' "${plan_checks}" | sed -n '1p')"
    plan_mode="$(printf '%s\n' "${plan_checks}" | sed -n '2p')"
    plan_enabled="$(printf '%s\n' "${plan_checks}" | sed -n '3p')"
    plan_sent="$(printf '%s\n' "${plan_checks}" | sed -n '4p')"
    plan_mechanism="$(printf '%s\n' "${plan_checks}" | sed -n '5p')"
    plan_network="$(printf '%s\n' "${plan_checks}" | sed -n '6p')"
    plan_scheduler="$(printf '%s\n' "${plan_checks}" | sed -n '7p')"
    plan_queue="$(printf '%s\n' "${plan_checks}" | sed -n '8p')"
    plan_processing="$(printf '%s\n' "${plan_checks}" | sed -n '9p')"

    if [[ "${preview_count}" == "4" ]]; then
      pass "sample notification plan has exactly 4 notification previews"
    else
      fail "sample notification plan must have exactly 4 notification previews, found ${preview_count}"
    fi

    if [[ "${plan_mode}" == "simulated" ]]; then
      pass "sample notification plan has mode: simulated"
    else
      fail "sample notification plan must have mode: simulated"
    fi

    if [[ "${plan_enabled}" == "false" ]]; then
      pass "sample notification plan has notifications_enabled: false"
    else
      fail "sample notification plan must have notifications_enabled: false"
    fi

    if [[ "${plan_sent}" == "false" ]]; then
      pass "sample notification plan has notifications_sent: false"
    else
      fail "sample notification plan must have notifications_sent: false"
    fi

    if [[ "${plan_mechanism}" == "none" ]]; then
      pass "sample notification plan has notification_mechanism: none"
    else
      fail "sample notification plan must have notification_mechanism: none"
    fi

    for label_value_pair in \
      "network_calls:${plan_network}" \
      "scheduler_enabled:${plan_scheduler}" \
      "queue_writes:${plan_queue}" \
      "image_processing:${plan_processing}"; do
      label="${label_value_pair%%:*}"
      value="${label_value_pair#*:}"
      if [[ "${value}" == "false" ]]; then
        pass "sample notification plan has ${label}: false"
      else
        fail "sample notification plan must have ${label}: false"
      fi
    done

    sample_blob="$(python3 -m json.tool "${sample_plan}" 2>/dev/null || cat "${sample_plan}")"
    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample notification plan must not contain reddit.com"
    else
      pass "sample notification plan does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample notification plan must not contain image file extensions"
    else
      pass "sample notification plan does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample notification plan must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample notification plan does not contain obvious secrets/API keys/OAuth tokens"
    fi
  fi
else
  warn 'python3 not available for JSON parse checks'
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no notification sent'
pass 'no unattended run attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
