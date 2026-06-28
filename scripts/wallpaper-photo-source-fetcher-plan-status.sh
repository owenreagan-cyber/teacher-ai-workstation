#!/usr/bin/env bash
# Read-only approved-source fetcher plan status only. No network calls, fetchers, or automation runtime.
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

plan_doc="docs/wallpaper-photo-approved-source-fetcher-plan.md"
metadata_schema="assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json"
sample_records="assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json"
queue_format="assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json"
sample_queue="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"

section 'Wallpaper/Photo Approved-Source Fetcher Plan'
cat <<'EOF'
Status: planning only
Fetcher implemented: no
Network calls: no
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
Launch agents: no
Cron jobs: no
Background jobs: no
Notifications sent: no
macOS wallpaper changes: no
Photos changes: no
EOF

section 'Workflow Checks'

check_file "${plan_doc}"

check_text "${plan_doc}" 'approved source|Approved Source' 'source fetcher plan doc mentions approved source'
check_text "${plan_doc}" 'allowlist|Allowlist' 'source fetcher plan doc mentions allowlist'
check_text "${plan_doc}" 'permission note' 'source fetcher plan doc mentions permission note'
check_text "${plan_doc}" 'license review|license status must be reviewed' 'source fetcher plan doc mentions license review'
check_text "${plan_doc}" 'rate-limit|rate limit' 'source fetcher plan doc mentions rate-limit'
check_text "${plan_doc}" 'terms review|source terms must be reviewed' 'source fetcher plan doc mentions terms review'
check_text "${plan_doc}" 'dry-run discovery|Dry-Run Discovery' 'source fetcher plan doc mentions dry-run discovery'
check_text "${plan_doc}" 'no network calls|does not make network calls' 'source fetcher plan doc mentions no network calls'
check_text "${plan_doc}" 'no API clients|does not add API clients' 'source fetcher plan doc mentions no API clients'
check_text "${plan_doc}" 'no OAuth|does not add OAuth' 'source fetcher plan doc mentions no OAuth'
check_text "${plan_doc}" 'no secrets|does not add secrets' 'source fetcher plan doc mentions no secrets'
check_text "${plan_doc}" 'no API keys|does not add secrets or API keys' 'source fetcher plan doc mentions no API keys'
check_text "${plan_doc}" 'no image fetching|does not fetch images' 'source fetcher plan doc mentions no image fetching'
check_text "${plan_doc}" 'no image downloading|does not download images' 'source fetcher plan doc mentions no image downloading'
check_text "${plan_doc}" 'no image processing|does not process images' 'source fetcher plan doc mentions no image processing'
check_text "${plan_doc}" 'no queue writes|does not write queues' 'source fetcher plan doc mentions no queue writes'
check_text "${plan_doc}" 'no scheduler|does not add a scheduler' 'source fetcher plan doc mentions no scheduler'
check_text "${plan_doc}" 'no launch agents|does not add launch agents' 'source fetcher plan doc mentions no launch agents'
check_text "${plan_doc}" 'no cron jobs|does not add launch agents, cron jobs' 'source fetcher plan doc mentions no cron jobs'
check_text "${plan_doc}" 'no background jobs|does not add launch agents, cron jobs, or background jobs' 'source fetcher plan doc mentions no background jobs'
check_text "${plan_doc}" 'Reddit may be a future|Reddit as a Future Source' 'source fetcher plan doc mentions Reddit as a future source'
check_text "${plan_doc}" 'Devvit may be a future|Devvit as a Future Companion' 'source fetcher plan doc mentions Devvit as a future companion'
check_text "${plan_doc}" 'no Reddit integration|Reddit integration is not implemented' 'source fetcher plan doc mentions no Reddit integration'
check_text "${plan_doc}" 'no Devvit integration|Devvit integration is not implemented' 'source fetcher plan doc mentions no Devvit integration'

check_file "${metadata_schema}"
check_file "${sample_records}"
check_file "${queue_format}"
check_file "${sample_queue}"

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${metadata_schema}" "${sample_records}" "${queue_format}" "${sample_queue}"; do
    if python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    else
      fail "JSON does not parse: ${json_file}"
    fi
  done
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
