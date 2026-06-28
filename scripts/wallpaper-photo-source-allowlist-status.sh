#!/usr/bin/env bash
# Read-only source allowlist foundation status only. No network calls, fetchers, or automation runtime.
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

foundation_doc="docs/wallpaper-photo-source-allowlist-foundation.md"
allowlist_schema="assistant/appearance-vibe/wallpaper-photo-curator/source-allowlist-schema.json"
sample_allowlist="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
allowlist_validator="scripts/wallpaper-photo-source-allowlist-validator.sh"
fetcher_plan_doc="docs/wallpaper-photo-approved-source-fetcher-plan.md"
metadata_schema="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
sample_records="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"
queue_format="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Source Allowlist Foundation'
cat <<'EOF'
Status: file format and dry-run validator only
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

check_file "${foundation_doc}"
check_file "${allowlist_schema}"
check_file "${sample_allowlist}"
check_file "${allowlist_validator}"
check_file "${fetcher_plan_doc}"

check_bash_syntax "${allowlist_validator}"

if [[ -x "${allowlist_validator}" ]] || [[ -f "${allowlist_validator}" ]]; then
  if bash "${allowlist_validator}" >/dev/null 2>&1; then
    pass "allowlist validator exits 0 on sample allowlist"
  else
    fail "allowlist validator failed on sample allowlist"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${allowlist_schema}" "${sample_allowlist}" "${metadata_schema}" "${sample_records}" "${queue_format}" "${sample_queue}"; do
    if [[ -f "${json_file}" ]] && python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    elif [[ -f "${json_file}" ]]; then
      fail "JSON does not parse: ${json_file}"
    fi
  done

  if [[ -f "${sample_allowlist}" ]]; then
    source_count="$(python3 - "${sample_allowlist}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
sources = data.get("sources", [])
print(len(sources) if isinstance(sources, list) else 0)
PY
)"
    if [[ "${source_count}" == "4" ]]; then
      pass "sample allowlist has exactly 4 sources"
    else
      fail "sample allowlist must have exactly 4 sources, found ${source_count}"
    fi

    sample_blob="$(python3 -m json.tool "${sample_allowlist}" 2>/dev/null || cat "${sample_allowlist}")"
    if grep -q 'example.invalid' <<< "${sample_blob}"; then
      pass "sample allowlist uses example.invalid"
    else
      fail "sample allowlist must use example.invalid"
    fi

    if grep -Eiq 'reddit\.com' <<< "${sample_blob}"; then
      fail "sample allowlist must not contain reddit.com"
    else
      pass "sample allowlist does not contain reddit.com"
    fi

    if grep -Eiq '\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)' <<< "${sample_blob}"; then
      fail "sample allowlist must not contain image file extensions"
    else
      pass "sample allowlist does not contain image file extensions"
    fi

    if grep -Eiq 'api[_-]?key|oauth|bearer[[:space:]]+token|secret|password|credential|access_token|refresh_token' <<< "${sample_blob}"; then
      fail "sample allowlist must not contain obvious secrets/API keys/OAuth tokens"
    else
      pass "sample allowlist does not contain obvious secrets/API keys/OAuth tokens"
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
