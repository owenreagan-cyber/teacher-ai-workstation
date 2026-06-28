#!/usr/bin/env bash
# Dry-run scheduler run plan validation only. No scheduler install, network calls, or file operations.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

default_plan_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-scheduler-run-plan.json"
plan_file="${1:-${default_plan_file}}"

section 'Wallpaper/Photo Scheduler Run Plan Dry-Run Validator'
cat <<'EOF'
Status: simulated scheduler run plan validation only
Scheduler implemented: no
Launch agents: no
Cron jobs: no
Background jobs: no
Unattended runs: no
Notifications sent: no
Network calls: no
Image fetching: no
Image processing: no
Queue writes: no
Reddit integration: no
Devvit integration: no
EOF

if [[ ! -f "${plan_file}" ]]; then
  fail "scheduler run plan file missing: ${plan_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "scheduler run plan file exists: ${plan_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for scheduler run plan validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${plan_file}" <<'PY'
import json
import re
import sys

plan_file = sys.argv[1]

VALID_CADENCE = {
    "manual_only",
    "daily_dry_run",
    "weekly_dry_run",
    "on_demand_only",
    "paused",
    "disabled",
}
REQUIRED_INTENT_FIELDS = [
    "run_intent_id",
    "mode",
    "cadence",
    "scheduler_enabled",
    "scheduler_paused",
    "manual_run_required",
    "would_install_launch_agent",
    "would_install_cron_job",
    "would_start_background_job",
    "would_send_notification",
    "would_make_network_calls",
    "would_fetch_images",
    "would_process_images",
    "would_write_queues",
    "would_change_wallpaper",
    "would_modify_photos",
    "preflight_checks",
    "blocked_reason",
    "manual_approval_required",
    "notes",
]
WOULD_FIELDS = [
    "would_install_launch_agent",
    "would_install_cron_job",
    "would_start_background_job",
    "would_send_notification",
    "would_make_network_calls",
    "would_fetch_images",
    "would_process_images",
    "would_write_queues",
    "would_change_wallpaper",
    "would_modify_photos",
]
TOP_FALSE_FLAGS = [
    "network_calls",
    "file_reads",
    "file_writes",
    "queue_writes",
    "notifications_sent",
    "background_jobs",
    "launch_agents",
    "cron_jobs",
]
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)", re.I)
SECRET_RE = re.compile(
    r"(api[_-]?key|oauth|bearer\s+token|secret|password|credential|access_token|refresh_token)",
    re.I,
)

results = []

def emit(level, message):
    results.append((level, message))

try:
    with open(plan_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"scheduler run plan JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read scheduler run plan file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "scheduler run plan JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

if data.get("scheduler_enabled") is not False:
    emit("FAIL", "top-level scheduler_enabled must be false")
else:
    emit("PASS", "top-level scheduler_enabled is false")

if data.get("scheduler_paused") is not True:
    emit("FAIL", "top-level scheduler_paused must be true")
else:
    emit("PASS", "top-level scheduler_paused is true")

if data.get("manual_run_required") is not True:
    emit("FAIL", "top-level manual_run_required must be true")
else:
    emit("PASS", "top-level manual_run_required is true")

for flag in TOP_FALSE_FLAGS:
    if data.get(flag) is not False:
        emit("FAIL", f"top-level {flag} must be false")
    else:
        emit("PASS", f"top-level {flag} is false")

intents = data.get("run_intents")
if not isinstance(intents, list):
    emit("FAIL", "top-level run_intents missing or not an array")
    intents = []

if plan_file.endswith("sample-scheduler-run-plan.json") and len(intents) != 4:
    emit("FAIL", f"sample scheduler run plan must contain exactly 4 run intents, found {len(intents)}")
elif plan_file.endswith("sample-scheduler-run-plan.json"):
    emit("PASS", "sample scheduler run plan contains exactly 4 run intents")

plan_blob = json.dumps(data)
if "reddit.com" in plan_blob.lower():
    emit("FAIL", "scheduler run plan must not contain reddit.com")
else:
    emit("PASS", "scheduler run plan does not contain reddit.com")

if IMAGE_EXT_RE.search(plan_blob):
    emit("FAIL", "scheduler run plan must not contain image file extensions")
else:
    emit("PASS", "scheduler run plan does not contain image file extensions")

if SECRET_RE.search(plan_blob):
    emit("FAIL", "scheduler run plan must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "scheduler run plan does not contain obvious secrets/API keys/OAuth tokens")

cadences_seen = set()
for index, intent in enumerate(intents, start=1):
    label = f"intent {index}"
    intent_id = intent.get("run_intent_id", f"intent-{index}") if isinstance(intent, dict) else f"intent-{index}"
    intent_label = f"{label} ({intent_id})"
    failures = []

    if not isinstance(intent, dict):
        emit("FAIL", f"{intent_label}: not an object")
        continue

    for field in REQUIRED_INTENT_FIELDS:
        if field not in intent:
            failures.append(f"missing field {field}")

    if intent.get("mode") != "simulated":
        failures.append("mode must be simulated")

    cadence = intent.get("cadence")
    if cadence not in VALID_CADENCE:
        failures.append(f"invalid cadence: {cadence!r}")
    else:
        cadences_seen.add(cadence)

    if intent.get("scheduler_enabled") is not False:
        failures.append("scheduler_enabled must be false")
    if intent.get("scheduler_paused") is not True:
        failures.append("scheduler_paused must be true")
    if intent.get("manual_run_required") is not True:
        failures.append("manual_run_required must be true")
    if intent.get("manual_approval_required") is not True:
        failures.append("manual_approval_required must be true")

    for field in WOULD_FIELDS:
        if intent.get(field) is not False:
            failures.append(f"{field} must be false")

    preflight = intent.get("preflight_checks")
    if not isinstance(preflight, list) or not preflight:
        failures.append("preflight_checks must be a non-empty array")

    intent_blob = json.dumps(intent)
    if "reddit.com" in intent_blob.lower():
        failures.append("intent must not contain reddit.com")
    if IMAGE_EXT_RE.search(intent_blob):
        failures.append("intent must not contain image file extension")
    if SECRET_RE.search(intent_blob):
        failures.append("intent must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{intent_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{intent_label}: valid")

if plan_file.endswith("sample-scheduler-run-plan.json"):
    required_cadences = {"manual_only", "daily_dry_run", "weekly_dry_run"}
    disabled_or_paused = cadences_seen & {"disabled", "paused"}
    if required_cadences.issubset(cadences_seen):
        emit("PASS", "sample includes manual_only, daily_dry_run, and weekly_dry_run examples")
    else:
        emit("FAIL", "sample must include manual_only, daily_dry_run, and weekly_dry_run examples")
    if disabled_or_paused:
        emit("PASS", "sample includes disabled or paused example")
    else:
        emit("FAIL", "sample must include disabled or paused example")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Run Intents Checked'

while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  case "${line}" in
    PASS:*)
      pass "${line#PASS: }"
      ;;
    WARN:*)
      warn "${line#WARN: }"
      ;;
    FAIL:*)
      fail "${line#FAIL: }"
      ;;
    *)
      printf '%s\n' "${line}"
      ;;
  esac
done <<< "${validation_output}"

pass 'simulated/local-only validation only'
pass 'no scheduler was installed'
pass 'no unattended run exists'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
