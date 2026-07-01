#!/usr/bin/env bash
# Read-only rotation handoff safety status only. No file moves, network calls, or file operations.
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

check_doc_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "${file}" ]]; then
    fail "cannot check missing doc: ${file}"
    return
  fi
  if grep -Fq "${phrase}" "${file}"; then
    pass "doc mentions ${label}"
  else
    fail "${file} must mention ${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

audit_doc="docs/wallpaper-photo-rotation-handoff-safety-audit.md"
phase_1_audit_doc="docs/phase-1-chief-of-staff-status-audit.md"
curator_plan_doc="docs/appearance-vibe-wallpaper-photo-curator-plan.md"
sample_report="assistant/appearance-vibe/wallpaper-photo-curator/sample-rotation-handoff-readiness-report.json"
report_validator="scripts/wallpaper-photo-rotation-handoff-validator.sh"
sample_notification="assistant/appearance-vibe/wallpaper-photo-curator/sample-notification-plan.json"
sample_scheduler="assistant/appearance-vibe/wallpaper-photo-curator/sample-scheduler-run-plan.json"
sample_processing="assistant/appearance-vibe/wallpaper-photo-curator/sample-image-processing-plan.json"
sample_ui_state="assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json"
sample_discovery="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
sample_metadata="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

section 'Wallpaper/Photo Rotation Handoff and Safety Audit'
cat <<'EOF'
Status: planning/status/sample handoff audit only
Handoff enabled: no
File moves: no
File copies: no
File deletions: no
Folder scans: no
Queue writes: no
Wallpaper changes: no
Photos changes: no
Network calls: no
Image processing: no
Scheduler implemented: no
Notifications sent: no
Reddit integration: no
Devvit integration: no
EOF

section 'Workflow Checks'

check_file "${audit_doc}"
check_file "${sample_report}"
check_file "${report_validator}"
check_file "${sample_notification}"
check_file "${sample_scheduler}"
check_file "${sample_processing}"
check_file "${sample_ui_state}"
check_file "${sample_discovery}"
check_file "${sample_allowlist}"
check_file "${sample_queue}"
check_file "${sample_metadata}"

check_bash_syntax "${report_validator}"

if [[ -f "${report_validator}" ]]; then
  if bash "${report_validator}" >/dev/null 2>&1; then
    pass "rotation handoff validator exits 0 on sample readiness report"
  else
    fail "rotation handoff validator failed on sample readiness report"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${sample_report}" "${sample_notification}" "${sample_scheduler}" "${sample_processing}" "${sample_ui_state}" "${sample_discovery}" "${sample_allowlist}" "${sample_queue}" "${sample_metadata}"; do
    if [[ -f "${json_file}" ]] && python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    elif [[ -f "${json_file}" ]]; then
      fail "JSON does not parse: ${json_file}"
    fi
  done

  if [[ -f "${sample_report}" ]]; then
    report_checks="$(python3 - "${sample_report}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("mode", ""))
print(str(data.get("handoff_enabled", "")).lower())
print(str(data.get("file_moves", "")).lower())
print(str(data.get("file_copies", "")).lower())
print(str(data.get("file_deletions", "")).lower())
print(str(data.get("folder_scans", "")).lower())
print(str(data.get("queue_writes", "")).lower())
print(str(data.get("wallpaper_changes", "")).lower())
print(str(data.get("photos_changes", "")).lower())
print(str(data.get("network_calls", "")).lower())
PY
)"
    report_mode="$(printf '%s\n' "${report_checks}" | sed -n '1p')"
    report_handoff="$(printf '%s\n' "${report_checks}" | sed -n '2p')"
    report_moves="$(printf '%s\n' "${report_checks}" | sed -n '3p')"
    report_copies="$(printf '%s\n' "${report_checks}" | sed -n '4p')"
    report_deletions="$(printf '%s\n' "${report_checks}" | sed -n '5p')"
    report_scans="$(printf '%s\n' "${report_checks}" | sed -n '6p')"
    report_queue="$(printf '%s\n' "${report_checks}" | sed -n '7p')"
    report_wallpaper="$(printf '%s\n' "${report_checks}" | sed -n '8p')"
    report_photos="$(printf '%s\n' "${report_checks}" | sed -n '9p')"
    report_network="$(printf '%s\n' "${report_checks}" | sed -n '10p')"

    if [[ "${report_mode}" == "simulated" ]]; then
      pass "sample readiness report has mode: simulated"
    else
      fail "sample readiness report must have mode: simulated"
    fi

    for label_value_pair in \
      "handoff_enabled:${report_handoff}" \
      "file_moves:${report_moves}" \
      "file_copies:${report_copies}" \
      "file_deletions:${report_deletions}" \
      "folder_scans:${report_scans}" \
      "queue_writes:${report_queue}" \
      "wallpaper_changes:${report_wallpaper}" \
      "photos_changes:${report_photos}" \
      "network_calls:${report_network}"; do
      label="${label_value_pair%%:*}"
      value="${label_value_pair#*:}"
      if [[ "${value}" == "false" ]]; then
        pass "sample readiness report has ${label}: false"
      else
        fail "sample readiness report must have ${label}: false"
      fi
    done

    sample_blob="$(python3 -m json.tool "${sample_report}" 2>/dev/null || cat "${sample_report}")"
    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample readiness report must not contain reddit.com"
    else
      pass "sample readiness report does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample readiness report must not contain image file extensions"
    else
      pass "sample readiness report does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample readiness report must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample readiness report does not contain obvious secrets/API keys/OAuth tokens"
    fi
  fi
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Appearance & Vibe Status Audit Closeout Checks'

check_doc_contains "${phase_1_audit_doc}" "Appearance & Vibe Wallpaper/Vibe Status Audit" "Appearance & Vibe Wallpaper/Vibe Status Audit section"
check_doc_contains "${phase_1_audit_doc}" "no live wallpaper app" "no live wallpaper app"
check_doc_contains "${phase_1_audit_doc}" "live wallpaper/photo curator implementation has not started" "live wallpaper/photo curator implementation has not started"
check_doc_contains "${phase_1_audit_doc}" "script-scaffolded/manual where applicable, not automated" "widgets/shortcuts/appearance modes remain manual or scaffolded"
check_doc_contains "${phase_1_audit_doc}" "no live integration is active" "no live integration is active"

if [[ -f "${curator_plan_doc}" ]]; then
  check_doc_contains "${curator_plan_doc}" "foundation stack complete for now; live wallpaper/photo curator implementation not started" "curator plan foundation-stack closeout posture"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no handoff occurred'
pass 'no file move, copy, or delete attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
