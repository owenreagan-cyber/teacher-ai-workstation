#!/usr/bin/env bash
# Read-only scheduler foundation status only. No scheduler install, network calls, or file operations.
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

foundation_doc="docs/wallpaper-photo-scheduler-foundation.md"
sample_plan="assistant/appearance-vibe/wallpaper-photo-curator/sample-scheduler-run-plan.json"
plan_validator="scripts/wallpaper-photo-scheduler-run-plan-validator.sh"
sample_processing="assistant/appearance-vibe/wallpaper-photo-curator/sample-image-processing-plan.json"
sample_ui_state="assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json"
sample_discovery="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
sample_metadata="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

section 'Wallpaper/Photo Scheduler Foundation'
cat <<'EOF'
Status: planning/status/sample scheduler plan only
Scheduler implemented: no
Launch agents: no
Cron jobs: no
Background jobs: no
Unattended runs: no
Notifications sent: no
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
check_file "${sample_processing}"
check_file "${sample_ui_state}"
check_file "${sample_discovery}"
check_file "${sample_allowlist}"
check_file "${sample_queue}"
check_file "${sample_metadata}"

check_bash_syntax "${plan_validator}"

if [[ -f "${plan_validator}" ]]; then
  if bash "${plan_validator}" >/dev/null 2>&1; then
    pass "scheduler run plan validator exits 0 on sample scheduler run plan"
  else
    fail "scheduler run plan validator failed on sample scheduler run plan"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${sample_plan}" "${sample_processing}" "${sample_ui_state}" "${sample_discovery}" "${sample_allowlist}" "${sample_queue}" "${sample_metadata}"; do
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
intents = data.get("run_intents", [])
print(len(intents) if isinstance(intents, list) else 0)
print(data.get("mode", ""))
print(str(data.get("scheduler_enabled", "")).lower())
print(str(data.get("scheduler_paused", "")).lower())
print(str(data.get("manual_run_required", "")).lower())
print(str(data.get("network_calls", "")).lower())
print(str(data.get("queue_writes", "")).lower())
print(str(data.get("notifications_sent", "")).lower())
print(str(data.get("background_jobs", "")).lower())
print(str(data.get("launch_agents", "")).lower())
print(str(data.get("cron_jobs", "")).lower())
PY
)"
    intent_count="$(printf '%s\n' "${plan_checks}" | sed -n '1p')"
    plan_mode="$(printf '%s\n' "${plan_checks}" | sed -n '2p')"
    plan_enabled="$(printf '%s\n' "${plan_checks}" | sed -n '3p')"
    plan_paused="$(printf '%s\n' "${plan_checks}" | sed -n '4p')"
    plan_manual="$(printf '%s\n' "${plan_checks}" | sed -n '5p')"
    plan_network="$(printf '%s\n' "${plan_checks}" | sed -n '6p')"
    plan_queue="$(printf '%s\n' "${plan_checks}" | sed -n '7p')"
    plan_notifications="$(printf '%s\n' "${plan_checks}" | sed -n '8p')"
    plan_background="$(printf '%s\n' "${plan_checks}" | sed -n '9p')"
    plan_launch="$(printf '%s\n' "${plan_checks}" | sed -n '10p')"
    plan_cron="$(printf '%s\n' "${plan_checks}" | sed -n '11p')"

    if [[ "${intent_count}" == "4" ]]; then
      pass "sample scheduler run plan has exactly 4 run intents"
    else
      fail "sample scheduler run plan must have exactly 4 run intents, found ${intent_count}"
    fi

    if [[ "${plan_mode}" == "simulated" ]]; then
      pass "sample scheduler run plan has mode: simulated"
    else
      fail "sample scheduler run plan must have mode: simulated"
    fi

    if [[ "${plan_enabled}" == "false" ]]; then
      pass "sample scheduler run plan has scheduler_enabled: false"
    else
      fail "sample scheduler run plan must have scheduler_enabled: false"
    fi

    if [[ "${plan_paused}" == "true" ]]; then
      pass "sample scheduler run plan has scheduler_paused: true"
    else
      fail "sample scheduler run plan must have scheduler_paused: true"
    fi

    if [[ "${plan_manual}" == "true" ]]; then
      pass "sample scheduler run plan has manual_run_required: true"
    else
      fail "sample scheduler run plan must have manual_run_required: true"
    fi

    for label_value_pair in \
      "network_calls:${plan_network}" \
      "queue_writes:${plan_queue}" \
      "notifications_sent:${plan_notifications}" \
      "background_jobs:${plan_background}" \
      "launch_agents:${plan_launch}" \
      "cron_jobs:${plan_cron}"; do
      label="${label_value_pair%%:*}"
      value="${label_value_pair#*:}"
      if [[ "${value}" == "false" ]]; then
        pass "sample scheduler run plan has ${label}: false"
      else
        fail "sample scheduler run plan must have ${label}: false"
      fi
    done

    sample_blob="$(python3 -m json.tool "${sample_plan}" 2>/dev/null || cat "${sample_plan}")"
    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample scheduler run plan must not contain reddit.com"
    else
      pass "sample scheduler run plan does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample scheduler run plan must not contain image file extensions"
    else
      pass "sample scheduler run plan does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample scheduler run plan must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample scheduler run plan does not contain obvious secrets/API keys/OAuth tokens"
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
pass 'no scheduler install attempted'
pass 'no unattended run attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
