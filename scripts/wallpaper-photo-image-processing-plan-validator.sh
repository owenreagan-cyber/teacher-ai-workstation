#!/usr/bin/env bash
# Dry-run image processing plan validation only. No file reads, writes, or image processing.
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

default_plan_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-image-processing-plan.json"
plan_file="${1:-${default_plan_file}}"

section 'Wallpaper/Photo Image Processing Plan Dry-Run Validator'
cat <<'EOF'
Status: simulated processing plan validation only
Image processing implemented: no
File reads: no
File writes: no
Image conversion: no
Image resizing: no
Image cropping: no
Image previews: no
Processed outputs: no
Queue writes: no
Network calls: no
Reddit integration: no
Devvit integration: no
Scheduler implemented: no
Notifications sent: no
EOF

if [[ ! -f "${plan_file}" ]]; then
  fail "image processing plan file missing: ${plan_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "image processing plan file exists: ${plan_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for image processing plan validation"
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

VALID_TARGET_PROFILES = {"wallpaper_landscape", "photo_widget"}
VALID_TARGET_USES = {"wallpaper_rotation", "photo_widget_rotation"}
REQUIRED_INTENT_FIELDS = [
    "output_intent_id",
    "candidate_id",
    "target_profile",
    "target_use",
    "intended_width",
    "intended_height",
    "intended_format",
    "fit_strategy",
    "crop_strategy",
    "would_write_file",
    "would_overwrite_file",
    "would_delete_source",
    "duplicate_risk",
    "watermark_risk",
    "blocked_reason",
    "manual_approval_required",
    "notes",
]
RISK_FIELDS = ("duplicate_risk", "watermark_risk")
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)", re.I)
SECRET_RE = re.compile(
    r"(api[_-]?key|oauth|bearer\s+token|secret|password|credential|access_token|refresh_token)",
    re.I,
)
EXECUTABLE_RE = re.compile(r"\b(convert|magick|sips|ffmpeg|resize|crop)\b", re.I)

results = []

def emit(level, message):
    results.append((level, message))

try:
    with open(plan_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"image processing plan JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read image processing plan file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "image processing plan JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

for flag in ("network_calls", "file_reads", "file_writes", "image_processing"):
    if data.get(flag) is not False:
        emit("FAIL", f"top-level {flag} must be false")
    else:
        emit("PASS", f"top-level {flag} is false")

intents = data.get("output_intents")
if not isinstance(intents, list):
    emit("FAIL", "top-level output_intents missing or not an array")
    intents = []

if plan_file.endswith("sample-image-processing-plan.json") and len(intents) != 4:
    emit("FAIL", f"sample processing plan must contain exactly 4 output intents, found {len(intents)}")
elif plan_file.endswith("sample-image-processing-plan.json"):
    emit("PASS", "sample processing plan contains exactly 4 output intents")

plan_blob = json.dumps(data)
if "reddit.com" in plan_blob.lower():
    emit("FAIL", "processing plan must not contain reddit.com")
else:
    emit("PASS", "processing plan does not contain reddit.com")

if IMAGE_EXT_RE.search(plan_blob):
    emit("FAIL", "processing plan must not contain image file extensions")
else:
    emit("PASS", "processing plan does not contain image file extensions")

if SECRET_RE.search(plan_blob):
    emit("FAIL", "processing plan must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "processing plan does not contain obvious secrets/API keys/OAuth tokens")

profiles_seen = set()
for index, intent in enumerate(intents, start=1):
    label = f"intent {index}"
    intent_id = intent.get("output_intent_id", f"intent-{index}") if isinstance(intent, dict) else f"intent-{index}"
    intent_label = f"{label} ({intent_id})"
    failures = []

    if not isinstance(intent, dict):
        emit("FAIL", f"{intent_label}: not an object")
        continue

    for field in REQUIRED_INTENT_FIELDS:
        if field not in intent:
            failures.append(f"missing field {field}")

    if intent.get("would_write_file") is not False:
        failures.append("would_write_file must be false")
    if intent.get("would_overwrite_file") is not False:
        failures.append("would_overwrite_file must be false")
    if intent.get("would_delete_source") is not False:
        failures.append("would_delete_source must be false")
    if intent.get("manual_approval_required") is not True:
        failures.append("manual_approval_required must be true")

    profile = intent.get("target_profile")
    if profile not in VALID_TARGET_PROFILES:
        failures.append(f"invalid target_profile: {profile!r}")
    else:
        profiles_seen.add(profile)

    use = intent.get("target_use")
    if use not in VALID_TARGET_USES:
        failures.append(f"invalid target_use: {use!r}")

    for dim_field in ("intended_width", "intended_height"):
        value = intent.get(dim_field)
        if not isinstance(value, int) or value <= 0:
            failures.append(f"{dim_field} must be a positive integer")

    for risk_field in RISK_FIELDS:
        value = intent.get(risk_field)
        if not isinstance(value, int) or value < 0 or value > 100:
            failures.append(f"{risk_field} must be an integer between 0 and 100")

    for strategy_field in ("fit_strategy", "crop_strategy"):
        value = intent.get(strategy_field, "")
        if not isinstance(value, str) or not value.startswith("report_only_"):
            failures.append(f"{strategy_field} must be a report-only label")
        elif EXECUTABLE_RE.search(value):
            failures.append(f"{strategy_field} must not contain executable command words")

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

if plan_file.endswith("sample-image-processing-plan.json"):
    if "wallpaper_landscape" in profiles_seen and "photo_widget" in profiles_seen:
        emit("PASS", "sample includes wallpaper and photo-widget output intents")
    else:
        emit("FAIL", "sample must include wallpaper_landscape and photo_widget output intents")

    blocked_dup = any(
        isinstance(i, dict) and i.get("duplicate_risk", 0) >= 70 and i.get("blocked_reason")
        for i in intents
    )
    blocked_wm = any(
        isinstance(i, dict) and i.get("watermark_risk", 0) >= 70 and i.get("blocked_reason")
        for i in intents
    )
    if blocked_dup:
        emit("PASS", "sample includes blocked duplicate-risk example")
    else:
        emit("FAIL", "sample must include blocked duplicate-risk example")
    if blocked_wm:
        emit("PASS", "sample includes blocked watermark-risk example")
    else:
        emit("FAIL", "sample must include blocked watermark-risk example")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Output Intents Checked'

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
pass 'no files were read or written'
pass 'no image processing occurred'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
