#!/usr/bin/env bash
# Dry-run review UI state validation only. No network calls, UI runtime, or image rendering.
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

default_ui_state_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json"
ui_state_file="${1:-${default_ui_state_file}}"

section 'Wallpaper/Photo Review UI State Dry-Run Validator'
cat <<'EOF'
Status: simulated UI state validation only
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
EOF

if [[ ! -f "${ui_state_file}" ]]; then
  fail "review UI state file missing: ${ui_state_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "review UI state file exists: ${ui_state_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for review UI state validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${ui_state_file}" <<'PY'
import json
import re
import sys

ui_state_file = sys.argv[1]

VALID_ACTIONS = {
    "approve_simulated",
    "dismiss_simulated",
    "needs_more_info",
    "open_metadata_details",
    "open_source_details",
    "open_processing_rules",
}
REQUIRED_CARD_FIELDS = [
    "candidate_id",
    "candidate_type",
    "source_id",
    "source_name",
    "source_type",
    "review_status",
    "review_decision",
    "content_rating",
    "nsfw_flag",
    "license_status",
    "permission_note",
    "wallpaper_fit_score",
    "photo_widget_fit_score",
    "duplicate_risk",
    "watermark_risk",
    "image_preview_status",
    "actions_available",
    "blocked_actions",
    "notes",
]
SCORE_FIELDS = (
    "wallpaper_fit_score",
    "photo_widget_fit_score",
    "duplicate_risk",
    "watermark_risk",
)
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)", re.I)
SECRET_RE = re.compile(
    r"(api[_-]?key|oauth|bearer\s+token|secret|password|credential|access_token|refresh_token)",
    re.I,
)

results = []

def emit(level, message):
    results.append((level, message))

try:
    with open(ui_state_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"review UI state JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read review UI state file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "review UI state JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

if data.get("network_calls") is not False:
    emit("FAIL", "top-level network_calls must be false")
else:
    emit("PASS", "top-level network_calls is false")

cards = data.get("candidate_cards")
if not isinstance(cards, list):
    emit("FAIL", "top-level candidate_cards missing or not an array")
    cards = []

if ui_state_file.endswith("sample-review-ui-state.json") and len(cards) != 4:
    emit("FAIL", f"sample review UI state must contain exactly 4 candidate cards, found {len(cards)}")
elif ui_state_file.endswith("sample-review-ui-state.json"):
    emit("PASS", "sample review UI state contains exactly 4 candidate cards")

state_blob = json.dumps(data)
if "reddit.com" in state_blob.lower():
    emit("FAIL", "review UI state must not contain reddit.com")
else:
    emit("PASS", "review UI state does not contain reddit.com")

if IMAGE_EXT_RE.search(state_blob):
    emit("FAIL", "review UI state must not contain image file extensions")
else:
    emit("PASS", "review UI state does not contain image file extensions")

if SECRET_RE.search(state_blob):
    emit("FAIL", "review UI state must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "review UI state does not contain obvious secrets/API keys/OAuth tokens")

top_blocked = data.get("blocked_actions", [])
if isinstance(top_blocked, list):
    blocked_blob = " ".join(str(item) for item in top_blocked).lower()
    if "queue" in blocked_blob and "write" in blocked_blob.replace("_", " "):
        emit("PASS", "top-level blocked_actions includes no queue writes")
    elif any("no_queue_writes" in str(item) for item in top_blocked):
        emit("PASS", "top-level blocked_actions includes no queue writes")
    else:
        emit("FAIL", "top-level blocked_actions must include no queue writes")
    if any("image_rendering" in str(item) or "no_image_rendering" in str(item) for item in top_blocked):
        emit("PASS", "top-level blocked_actions includes no image rendering")
    else:
        emit("FAIL", "top-level blocked_actions must include no image rendering")

for index, card in enumerate(cards, start=1):
    label = f"card {index}"
    candidate_id = card.get("candidate_id", f"card-{index}") if isinstance(card, dict) else f"card-{index}"
    card_label = f"{label} ({candidate_id})"
    failures = []

    if not isinstance(card, dict):
        emit("FAIL", f"{card_label}: not an object")
        continue

    for field in REQUIRED_CARD_FIELDS:
        if field not in card:
            failures.append(f"missing field {field}")

    if card.get("image_preview_status") != "not_rendered":
        failures.append("image_preview_status must be not_rendered")

    if card.get("review_decision") != "none":
        failures.append("review_decision must be none")

    if card.get("content_rating") != "safe":
        failures.append("content_rating must be safe")

    if card.get("nsfw_flag") is not False:
        failures.append("nsfw_flag must be false")

    for score_field in SCORE_FIELDS:
        value = card.get(score_field)
        if not isinstance(value, int) or value < 0 or value > 100:
            failures.append(f"{score_field} must be an integer between 0 and 100")

    actions = card.get("actions_available", [])
    if not isinstance(actions, list):
        failures.append("actions_available must be an array")
    else:
        for action in actions:
            if action not in VALID_ACTIONS:
                failures.append(f"invalid action label: {action!r}")

    card_blocked = card.get("blocked_actions", [])
    if not isinstance(card_blocked, list):
        failures.append("blocked_actions must be an array")
    else:
        blocked_text = " ".join(str(item) for item in card_blocked).lower()
        if "no_queue_writes" not in blocked_text and "queue" not in blocked_text:
            failures.append("blocked_actions must include no queue writes")
        if "no_image_rendering" not in blocked_text and "image_rendering" not in blocked_text:
            failures.append("blocked_actions must include no image rendering")

    card_blob = json.dumps(card)
    if "reddit.com" in card_blob.lower():
        failures.append("card must not contain reddit.com")
    if IMAGE_EXT_RE.search(card_blob):
        failures.append("card must not contain image file extension")
    if SECRET_RE.search(card_blob):
        failures.append("card must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{card_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{card_label}: valid")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Candidate Cards Checked'

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
pass 'no network calls were made'
pass 'no UI was started'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
