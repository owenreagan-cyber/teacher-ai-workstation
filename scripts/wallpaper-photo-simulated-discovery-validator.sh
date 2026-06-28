#!/usr/bin/env bash
# Dry-run simulated discovery validation only. No network calls, file writes, or fetching.
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

default_report_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json"
report_file="${1:-${default_report_file}}"
allowlist_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"

section 'Wallpaper/Photo Simulated Discovery Dry-Run Validator'
cat <<'EOF'
Status: simulated validation only
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

if [[ ! -f "${report_file}" ]]; then
  fail "discovery report file missing: ${report_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "discovery report file exists: ${report_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for simulated discovery validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${report_file}" "${allowlist_file}" <<'PY'
import json
import re
import sys

report_file = sys.argv[1]
allowlist_file = sys.argv[2]

EXPECTED_SOURCE_IDS = {
    "fictional-approved-site-001",
    "fictional-local-folder-001",
    "fictional-future-reddit-001",
    "fictional-future-devvit-001",
}
REQUIRED_RECORD_FIELDS = [
    "source_id",
    "source_name",
    "source_type",
    "source_status",
    "discovery_status",
    "candidate_count_estimate",
    "wallpaper_candidate_estimate",
    "photo_widget_candidate_estimate",
    "blocked_reason",
    "network_calls",
    "notes",
]
COUNT_FIELDS = (
    "candidate_count_estimate",
    "wallpaper_candidate_estimate",
    "photo_widget_candidate_estimate",
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
    with open(report_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"discovery report JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read discovery report file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "discovery report JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

if data.get("network_calls") is not False:
    emit("FAIL", "top-level network_calls must be false")
else:
    emit("PASS", "top-level network_calls is false")

records = data.get("records")
if not isinstance(records, list):
    emit("FAIL", "top-level records missing or not an array")
    records = []

if report_file.endswith("sample-discovery-report.json") and len(records) != 4:
    emit("FAIL", f"sample discovery report must contain exactly 4 records, found {len(records)}")
elif report_file.endswith("sample-discovery-report.json"):
    emit("PASS", "sample discovery report contains exactly 4 records")

allowlist_ids = set()
try:
    with open(allowlist_file, "r", encoding="utf-8") as handle:
        allowlist_data = json.load(handle)
    for source in allowlist_data.get("sources", []):
        if isinstance(source, dict) and source.get("source_id"):
            allowlist_ids.add(source["source_id"])
except (OSError, json.JSONDecodeError):
    allowlist_ids = EXPECTED_SOURCE_IDS

report_blob = json.dumps(data)
if "reddit.com" in report_blob.lower():
    emit("FAIL", "discovery report must not contain reddit.com")
else:
    emit("PASS", "discovery report does not contain reddit.com")

if IMAGE_EXT_RE.search(report_blob):
    emit("FAIL", "discovery report must not contain image file extensions")
else:
    emit("PASS", "discovery report does not contain image file extensions")

if SECRET_RE.search(report_blob):
    emit("FAIL", "discovery report must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "discovery report does not contain obvious secrets/API keys/OAuth tokens")

seen_ids = set()
for index, record in enumerate(records, start=1):
    label = f"record {index}"
    source_id = record.get("source_id", f"record-{index}") if isinstance(record, dict) else f"record-{index}"
    record_label = f"{label} ({source_id})"
    failures = []

    if not isinstance(record, dict):
        emit("FAIL", f"{record_label}: not an object")
        continue

    for field in REQUIRED_RECORD_FIELDS:
        if field not in record:
            failures.append(f"missing field {field}")

    if record.get("network_calls") is not False:
        failures.append("network_calls must be false")

    for count_field in COUNT_FIELDS:
        value = record.get(count_field)
        if not isinstance(value, int) or value < 0:
            failures.append(f"{count_field} must be a non-negative integer")

    if source_id not in allowlist_ids:
        failures.append(f"source_id {source_id!r} not found in sample allowlist")

    if source_id in seen_ids:
        failures.append(f"duplicate source_id {source_id!r}")
    seen_ids.add(source_id)

    record_blob = json.dumps(record)
    if "reddit.com" in record_blob.lower():
        failures.append("record must not contain reddit.com")
    if IMAGE_EXT_RE.search(record_blob):
        failures.append("record must not contain image file extension")
    if SECRET_RE.search(record_blob):
        failures.append("record must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{record_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{record_label}: valid")

if report_file.endswith("sample-discovery-report.json") and seen_ids != allowlist_ids:
    missing = sorted(allowlist_ids - seen_ids)
    extra = sorted(seen_ids - allowlist_ids)
    if missing or extra:
        emit("FAIL", f"record source IDs must match sample allowlist; missing={missing}, extra={extra}")
    else:
        emit("PASS", "record source IDs match sample allowlist")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Discovery Records Checked'

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

pass 'dry-run simulated validation only'
pass 'no network calls were made'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
