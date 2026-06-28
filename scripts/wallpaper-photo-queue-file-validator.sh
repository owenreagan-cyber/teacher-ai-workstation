#!/usr/bin/env bash
# Dry-run queue file validation only. No network calls, file writes, folder scans, or image handling.
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

default_queue_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json"
queue_file="${1:-${default_queue_file}}"

section 'Wallpaper/Photo Queue File Dry-Run Validator'
cat <<'EOF'
Status: dry-run validation only
Live queues: no
Queue folders created: no
Files created: no
Files deleted: no
Folders scanned: no
Images fetched: no
Images downloaded: no
Images processed: no
Network calls: no
Notifications: no
macOS wallpaper changes: no
Photos changes: no
EOF

if [[ ! -f "${queue_file}" ]]; then
  fail "queue file missing: ${queue_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "queue file exists: ${queue_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for queue file validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${queue_file}" <<'PY'
import json
import re
import sys

queue_file = sys.argv[1]

VALID_QUEUE_TYPES = {"wallpaper", "photo_widget", "mixed"}
VALID_CANDIDATE_TYPES = {"wallpaper", "photo_widget", "both"}
VALID_REVIEW_STATUS = {"unreviewed", "approved", "dismissed", "blocked", "needs_more_info"}
VALID_REVIEW_DECISION = {
    "none",
    "approve_for_processing",
    "dismiss_delete_candidate",
    "block_source",
    "needs_more_info",
}
VALID_CONTENT_RATING = {"safe", "needs_review", "blocked"}
REQUIRED_RECORD_FIELDS = [
    "candidate_id",
    "candidate_type",
    "queue_name",
    "queue_position",
    "queue_added_at",
    "queue_expires_at",
    "review_status",
    "review_decision",
    "source_name",
    "source_url",
    "candidate_url",
    "title",
    "content_rating",
    "nsfw_flag",
    "local_temp_path",
    "processed_output_path",
    "notes",
]
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)", re.I)

results = []

def emit(level, message):
    results.append((level, message))

try:
    with open(queue_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"queue JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read queue file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "queue JSON parses")

records = data.get("records")
if not isinstance(records, list):
    emit("FAIL", "top-level records missing or not an array")
    records = []

max_candidates = data.get("max_candidates")
if not isinstance(max_candidates, int):
    emit("FAIL", "max_candidates missing or not an integer")
elif max_candidates > 20:
    emit("FAIL", "max_candidates exceeds 20")
else:
    emit("PASS", "max_candidates within limit")

queue_type = data.get("queue_type")
if queue_type not in VALID_QUEUE_TYPES:
    emit("FAIL", f"unknown queue_type: {queue_type!r}")
else:
    emit("PASS", f"queue_type valid: {queue_type}")

if isinstance(records, list) and isinstance(max_candidates, int) and len(records) > max_candidates:
    emit("FAIL", f"record count {len(records)} exceeds max_candidates {max_candidates}")
elif isinstance(records, list):
    emit("PASS", f"record count {len(records)} within max_candidates")

for index, record in enumerate(records, start=1):
    label = f"record {index}"
    record_id = record.get("candidate_id", f"record-{index}") if isinstance(record, dict) else f"record-{index}"
    record_label = f"{label} ({record_id})"
    record_failures = []

    if not isinstance(record, dict):
        emit("FAIL", f"{record_label}: not an object")
        continue

    for field in REQUIRED_RECORD_FIELDS:
        if field not in record:
            record_failures.append(f"missing field {field}")

    candidate_type = record.get("candidate_type")
    if candidate_type not in VALID_CANDIDATE_TYPES:
        record_failures.append(f"invalid candidate_type: {candidate_type!r}")

    review_status = record.get("review_status")
    if review_status not in VALID_REVIEW_STATUS:
        record_failures.append(f"invalid review_status: {review_status!r}")

    review_decision = record.get("review_decision")
    if review_decision not in VALID_REVIEW_DECISION:
        record_failures.append(f"invalid review_decision: {review_decision!r}")

    content_rating = record.get("content_rating")
    if content_rating not in VALID_CONTENT_RATING:
        record_failures.append(f"invalid content_rating: {content_rating!r}")

    if record.get("nsfw_flag") is True:
        record_failures.append("nsfw_flag is true")

    for url_field in ("source_url", "candidate_url"):
        url = record.get(url_field, "")
        if not isinstance(url, str):
            record_failures.append(f"{url_field} is not a string")
            continue
        if "example.invalid" not in url:
            record_failures.append(f"{url_field} must use example.invalid")
        if "reddit.com" in url.lower():
            record_failures.append(f"{url_field} contains reddit.com")
        if IMAGE_EXT_RE.search(url):
            record_failures.append(f"{url_field} contains likely image extension")

    for path_field in ("local_temp_path", "processed_output_path"):
        path = record.get(path_field, "")
        if not isinstance(path, str):
            continue
        if path and path.startswith("/"):
            record_failures.append(f"{path_field} must not start with /")
        if ".." in path:
            record_failures.append(f"{path_field} must not contain ..")

    if record_failures:
        emit("FAIL", f"{record_label}: {'; '.join(record_failures)}")
    else:
        emit("PASS", f"{record_label}: valid")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Queue Records Checked'

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

pass 'dry-run validation only'
pass 'no files were created'
pass 'no files were deleted'
pass 'no folders were scanned'
pass 'no images were fetched'
pass 'no images were downloaded'
pass 'no images were processed'
pass 'no network calls were made'
pass 'no macOS wallpaper or Photos changes were made'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
