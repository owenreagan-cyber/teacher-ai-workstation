#!/usr/bin/env bash
# Dry-run source allowlist validation only. No network calls, file writes, or fetching.
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

default_allowlist_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json"
allowlist_file="${1:-${default_allowlist_file}}"

section 'Wallpaper/Photo Source Allowlist Dry-Run Validator'
cat <<'EOF'
Status: dry-run validation only
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

if [[ ! -f "${allowlist_file}" ]]; then
  fail "allowlist file missing: ${allowlist_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "allowlist file exists: ${allowlist_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for allowlist validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${allowlist_file}" <<'PY'
import json
import re
import sys

allowlist_file = sys.argv[1]

VALID_SOURCE_TYPES = {
    "fictional_sample",
    "future_approved_site",
    "future_reddit_source",
    "future_local_folder",
    "manual_entry",
    "future_devvit_companion",
}
VALID_STATUSES = {
    "proposed",
    "approved_for_dry_run",
    "approved_for_fetching_later",
    "paused",
    "blocked",
    "needs_more_info",
}
VALID_LICENSE = {
    "fictional_sample",
    "unknown_needs_review",
    "permission_confirmed",
    "public_domain",
    "creative_commons",
    "personal_use_only",
    "not_allowed",
}
REQUIRED_FIELDS = [
    "source_id",
    "source_name",
    "source_type",
    "source_url",
    "allowed_content_types",
    "permission_note",
    "license_review_status",
    "terms_review_note",
    "robots_or_policy_note",
    "rate_limit_note",
    "requires_auth",
    "status",
    "approved_by",
    "approved_at",
    "last_reviewed_at",
    "notes",
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
    with open(allowlist_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"allowlist JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read allowlist file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "allowlist JSON parses")

for field in ("schema_version", "allowlist_name", "sources", "created_at", "updated_at", "notes"):
    if field not in data:
        emit("FAIL", f"missing top-level field: {field}")
    else:
        emit("PASS", f"top-level field present: {field}")

sources = data.get("sources")
if not isinstance(sources, list):
    emit("FAIL", "top-level sources missing or not an array")
    sources = []

if allowlist_file.endswith("sample-source-allowlist.json") and len(sources) != 4:
    emit("FAIL", f"sample allowlist must contain exactly 4 sources, found {len(sources)}")
elif allowlist_file.endswith("sample-source-allowlist.json"):
    emit("PASS", "sample allowlist contains exactly 4 sources")

for index, source in enumerate(sources, start=1):
    label = f"source {index}"
    source_id = source.get("source_id", f"source-{index}") if isinstance(source, dict) else f"source-{index}"
    record_label = f"{label} ({source_id})"
    failures = []

    if not isinstance(source, dict):
        emit("FAIL", f"{record_label}: not an object")
        continue

    for field in REQUIRED_FIELDS:
        if field not in source:
            failures.append(f"missing field {field}")

    source_type = source.get("source_type")
    if source_type not in VALID_SOURCE_TYPES:
        failures.append(f"invalid source_type: {source_type!r}")

    status = source.get("status")
    if status not in VALID_STATUSES:
        failures.append(f"invalid status: {status!r}")

    license_status = source.get("license_review_status")
    if license_status not in VALID_LICENSE:
        failures.append(f"invalid license_review_status: {license_status!r}")

    if not isinstance(source.get("requires_auth"), bool):
        failures.append("requires_auth must be boolean")

    for note_field in ("permission_note", "terms_review_note", "robots_or_policy_note", "rate_limit_note"):
        value = source.get(note_field, "")
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{note_field} must be non-empty")

    if license_status == "unknown_needs_review" and status == "approved_for_fetching_later":
        failures.append("unknown_needs_review cannot be approved_for_fetching_later")

    if license_status == "not_allowed" and status == "approved_for_fetching_later":
        failures.append("not_allowed cannot be approved_for_fetching_later")

    source_url = source.get("source_url", "")
    if not isinstance(source_url, str):
        failures.append("source_url must be a string")
    else:
        if "example.invalid" not in source_url:
            failures.append("source_url must use example.invalid")
        if "reddit.com" in source_url.lower():
            failures.append("source_url must not contain reddit.com")
        if IMAGE_EXT_RE.search(source_url):
            failures.append("source_url must not contain image extension")

    source_blob = json.dumps(source)
    if SECRET_RE.search(source_blob):
        failures.append("source must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{record_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{record_label}: valid")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Sources Checked'

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
pass 'no network calls were made'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
