#!/usr/bin/env bash
# Dry-run notification plan validation only. No notifications sent, network calls, or file operations.
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

default_plan_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-notification-plan.json"
plan_file="${1:-${default_plan_file}}"

section 'Wallpaper/Photo Notification Plan Dry-Run Validator'
cat <<'EOF'
Status: simulated notification plan validation only
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
Image processing: no
Queue writes: no
Reddit integration: no
Devvit integration: no
EOF

if [[ ! -f "${plan_file}" ]]; then
  fail "notification plan file missing: ${plan_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "notification plan file exists: ${plan_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for notification plan validation"
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

VALID_TYPES = {
    "review_ready",
    "dry_run_complete",
    "safety_blocked",
    "scheduler_paused",
    "manual_attention_needed",
    "disabled",
}
VALID_ACTION_LABELS = {
    "open_review_ui_simulated",
    "view_safety_summary",
    "keep_disabled",
    "needs_more_info",
}
REQUIRED_PREVIEW_FIELDS = [
    "notification_id",
    "notification_type",
    "mode",
    "would_send_notification",
    "candidate_count",
    "wallpaper_candidate_count",
    "photo_widget_candidate_count",
    "blocked_candidate_count",
    "needs_review_count",
    "source_count",
    "message_title",
    "message_body",
    "action_labels",
    "blocked_actions",
    "manual_approval_required",
    "notes",
]
COUNT_FIELDS = [
    "candidate_count",
    "wallpaper_candidate_count",
    "photo_widget_candidate_count",
    "blocked_candidate_count",
    "needs_review_count",
    "source_count",
]
TOP_FALSE_FLAGS = [
    "network_calls",
    "scheduler_enabled",
    "queue_writes",
    "image_processing",
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
    emit("FAIL", f"notification plan JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read notification plan file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "notification plan JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

if data.get("notifications_enabled") is not False:
    emit("FAIL", "top-level notifications_enabled must be false")
else:
    emit("PASS", "top-level notifications_enabled is false")

if data.get("notifications_sent") is not False:
    emit("FAIL", "top-level notifications_sent must be false")
else:
    emit("PASS", "top-level notifications_sent is false")

if data.get("notification_mechanism") != "none":
    emit("FAIL", "top-level notification_mechanism must be none")
else:
    emit("PASS", "top-level notification_mechanism is none")

for flag in TOP_FALSE_FLAGS:
    if data.get(flag) is not False:
        emit("FAIL", f"top-level {flag} must be false")
    else:
        emit("PASS", f"top-level {flag} is false")

previews = data.get("notification_previews")
if not isinstance(previews, list):
    emit("FAIL", "top-level notification_previews missing or not an array")
    previews = []

if plan_file.endswith("sample-notification-plan.json") and len(previews) != 4:
    emit("FAIL", f"sample notification plan must contain exactly 4 notification previews, found {len(previews)}")
elif plan_file.endswith("sample-notification-plan.json"):
    emit("PASS", "sample notification plan contains exactly 4 notification previews")

plan_blob = json.dumps(data)
if "reddit.com" in plan_blob.lower():
    emit("FAIL", "notification plan must not contain reddit.com")
else:
    emit("PASS", "notification plan does not contain reddit.com")

if IMAGE_EXT_RE.search(plan_blob):
    emit("FAIL", "notification plan must not contain image file extensions")
else:
    emit("PASS", "notification plan does not contain image file extensions")

if SECRET_RE.search(plan_blob):
    emit("FAIL", "notification plan must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "notification plan does not contain obvious secrets/API keys/OAuth tokens")

types_seen = set()
for index, preview in enumerate(previews, start=1):
    label = f"preview {index}"
    notification_id = preview.get("notification_id", f"preview-{index}") if isinstance(preview, dict) else f"preview-{index}"
    preview_label = f"{label} ({notification_id})"
    failures = []

    if not isinstance(preview, dict):
        emit("FAIL", f"{preview_label}: not an object")
        continue

    for field in REQUIRED_PREVIEW_FIELDS:
        if field not in preview:
            failures.append(f"missing field {field}")

    if preview.get("mode") != "simulated":
        failures.append("mode must be simulated")

    notification_type = preview.get("notification_type")
    if notification_type not in VALID_TYPES:
        failures.append(f"invalid notification_type: {notification_type!r}")
    else:
        types_seen.add(notification_type)

    if preview.get("would_send_notification") is not False:
        failures.append("would_send_notification must be false")
    if preview.get("manual_approval_required") is not True:
        failures.append("manual_approval_required must be true")

    for field in COUNT_FIELDS:
        value = preview.get(field)
        if not isinstance(value, int) or value < 0:
            failures.append(f"{field} must be a numeric value >= 0")

    action_labels = preview.get("action_labels")
    if not isinstance(action_labels, list) or not action_labels:
        failures.append("action_labels must be a non-empty array")
    else:
        for action in action_labels:
            if action not in VALID_ACTION_LABELS:
                failures.append(f"invalid action label: {action!r}")

    blocked_actions = preview.get("blocked_actions")
    if not isinstance(blocked_actions, list) or not blocked_actions:
        failures.append("blocked_actions must be a non-empty array")

    preview_blob = json.dumps(preview)
    if "reddit.com" in preview_blob.lower():
        failures.append("preview must not contain reddit.com")
    if IMAGE_EXT_RE.search(preview_blob):
        failures.append("preview must not contain image file extension")
    if SECRET_RE.search(preview_blob):
        failures.append("preview must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{preview_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{preview_label}: valid")

if plan_file.endswith("sample-notification-plan.json"):
    if "review_ready" in types_seen:
        emit("PASS", "sample includes review_ready example")
    else:
        emit("FAIL", "sample must include review_ready example")
    if "dry_run_complete" in types_seen:
        emit("PASS", "sample includes dry_run_complete example")
    else:
        emit("FAIL", "sample must include dry_run_complete example")
    if "safety_blocked" in types_seen:
        emit("PASS", "sample includes safety_blocked example")
    else:
        emit("FAIL", "sample must include safety_blocked example")
    disabled_or_paused = types_seen & {"disabled", "scheduler_paused"}
    if disabled_or_paused:
        emit("PASS", "sample includes disabled or scheduler_paused example")
    else:
        emit("FAIL", "sample must include disabled or scheduler_paused example")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Notification Previews Checked'

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
pass 'no notification was sent'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
