#!/usr/bin/env bash
# Read-only review UI prototype status only. No network calls, UI runtime, or image rendering.
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

plan_doc="docs/wallpaper-photo-live-local-review-ui-prototype-plan.md"
sample_ui_state="assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json"
ui_state_validator="scripts/wallpaper-photo-review-ui-state-validator.sh"
sample_discovery="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
sample_metadata="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"

section 'Wallpaper/Photo Live Local Review UI Prototype Plan'
cat <<'EOF'
Status: planning/status/sample UI state only
Live UI implemented: no
Server started: no
Image rendering: no
Image previews: no
Queue writes: no
Network calls: no
Reddit integration: no
Devvit integration: no
Scheduler implemented: no
Notifications sent: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${plan_doc}"
check_file "${sample_ui_state}"
check_file "${ui_state_validator}"
check_file "${sample_discovery}"
check_file "${sample_allowlist}"
check_file "${sample_queue}"
check_file "${sample_metadata}"

check_bash_syntax "${ui_state_validator}"

if [[ -f "${ui_state_validator}" ]]; then
  if bash "${ui_state_validator}" >/dev/null 2>&1; then
    pass "review UI state validator exits 0 on sample review UI state"
  else
    fail "review UI state validator failed on sample review UI state"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${sample_ui_state}" "${sample_discovery}" "${sample_allowlist}" "${sample_queue}" "${sample_metadata}"; do
    if [[ -f "${json_file}" ]] && python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    elif [[ -f "${json_file}" ]]; then
      fail "JSON does not parse: ${json_file}"
    fi
  done

  if [[ -f "${sample_ui_state}" ]]; then
    ui_checks="$(python3 - "${sample_ui_state}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
cards = data.get("candidate_cards", [])
preview_statuses = []
if isinstance(cards, list):
    for card in cards:
        if isinstance(card, dict):
            preview_statuses.append(card.get("image_preview_status", ""))
print(len(cards) if isinstance(cards, list) else 0)
print(data.get("mode", ""))
print(str(data.get("network_calls", "")).lower())
print("not_rendered" if preview_statuses and all(status == "not_rendered" for status in preview_statuses) else "invalid")
PY
)"
    card_count="$(printf '%s\n' "${ui_checks}" | sed -n '1p')"
    ui_mode="$(printf '%s\n' "${ui_checks}" | sed -n '2p')"
    ui_network="$(printf '%s\n' "${ui_checks}" | sed -n '3p')"
    preview_check="$(printf '%s\n' "${ui_checks}" | sed -n '4p')"

    if [[ "${card_count}" == "4" ]]; then
      pass "sample review UI state has exactly 4 candidate cards"
    else
      fail "sample review UI state must have exactly 4 candidate cards, found ${card_count}"
    fi

    if [[ "${ui_mode}" == "simulated" ]]; then
      pass "sample review UI state has mode: simulated"
    else
      fail "sample review UI state must have mode: simulated"
    fi

    if [[ "${ui_network}" == "false" ]]; then
      pass "sample review UI state has network_calls: false"
    else
      fail "sample review UI state must have network_calls: false"
    fi

    if [[ "${preview_check}" == "not_rendered" ]]; then
      pass "sample review UI state has image_preview_status: not_rendered"
    else
      fail "sample review UI state must have image_preview_status: not_rendered on all cards"
    fi

    sample_blob="$(python3 -m json.tool "${sample_ui_state}" 2>/dev/null || cat "${sample_ui_state}")"
    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample review UI state must not contain reddit.com"
    else
      pass "sample review UI state does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample review UI state must not contain image file extensions"
    else
      pass "sample review UI state does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample review UI state must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample review UI state does not contain obvious secrets/API keys/OAuth tokens"
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
pass 'no network calls attempted'
pass 'no UI runtime started'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
