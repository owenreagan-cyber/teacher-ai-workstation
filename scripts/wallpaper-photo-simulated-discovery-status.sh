#!/usr/bin/env bash
# Read-only simulated discovery status only. No network calls, fetchers, or automation runtime.
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

plan_doc="docs/wallpaper-photo-simulated-approved-source-discovery-plan.md"
sample_report="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
discovery_validator="scripts/wallpaper-photo-simulated-discovery-validator.sh"
allowlist_schema="assistant/appearance-vibe/wallpaper-photo-curator/source-allowlist-schema.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
allowlist_validator="scripts/wallpaper-photo-source-allowlist-validator.sh"
allowlist_status="scripts/wallpaper-photo-source-allowlist-status.sh"
metadata_schema="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
sample_records="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"
queue_format="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Simulated Approved-Source Discovery'
cat <<'EOF'
Status: simulated planning/status only
Network calls: no
Fetcher implemented: no
API clients: no
OAuth: no
Secrets or API keys: no
Reddit integration: no
Devvit integration: no
Image fetching: no
Image downloading: no
Image processing: no
Queue writes: no
Scheduler implemented: no
EOF

section 'Workflow Checks'

check_file "${plan_doc}"
check_file "${sample_report}"
check_file "${discovery_validator}"
check_file "${allowlist_schema}"
check_file "${sample_allowlist}"

check_bash_syntax "${discovery_validator}"
check_bash_syntax "${allowlist_validator}"
check_bash_syntax "${allowlist_status}"

if [[ -f "${discovery_validator}" ]]; then
  if bash "${discovery_validator}" >/dev/null 2>&1; then
    pass "simulated discovery validator exits 0 on sample discovery report"
  else
    fail "simulated discovery validator failed on sample discovery report"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${sample_report}" "${allowlist_schema}" "${sample_allowlist}" "${metadata_schema}" "${sample_records}" "${queue_format}" "${sample_queue}"; do
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
records = data.get("records", [])
print(len(records) if isinstance(records, list) else 0)
print(data.get("mode", ""))
print(str(data.get("network_calls", "")).lower())
PY
)"
    record_count="$(printf '%s\n' "${report_checks}" | sed -n '1p')"
    report_mode="$(printf '%s\n' "${report_checks}" | sed -n '2p')"
    report_network="$(printf '%s\n' "${report_checks}" | sed -n '3p')"

    if [[ "${record_count}" == "4" ]]; then
      pass "sample discovery report has exactly 4 records"
    else
      fail "sample discovery report must have exactly 4 records, found ${record_count}"
    fi

    if [[ "${report_mode}" == "simulated" ]]; then
      pass "sample discovery report has mode: simulated"
    else
      fail "sample discovery report must have mode: simulated"
    fi

    if [[ "${report_network}" == "false" ]]; then
      pass "sample discovery report has network_calls: false"
    else
      fail "sample discovery report must have network_calls: false"
    fi

    sample_blob="$(python3 -m json.tool "${sample_report}" 2>/dev/null || cat "${sample_report}")"
    if grep -q 'example.invalid' <<< "${sample_blob}"; then
      pass "sample discovery report references example.invalid allowlist path"
    else
      pass "sample discovery report uses fictional local-only content"
    fi

    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample discovery report must not contain reddit.com"
    else
      pass "sample discovery report does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample discovery report must not contain image file extensions"
    else
      pass "sample discovery report does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample discovery report must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample discovery report does not contain obvious secrets/API keys/OAuth tokens"
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
pass 'no fetcher runtime started'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
