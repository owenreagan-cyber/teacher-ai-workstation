#!/usr/bin/env bash
# Registry v0.2 manual entry dry-run validator. Fake candidates only — no registry writes.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

default_candidate="assistant/curriculum-builder/samples/registry-v0-2-dry-run/example-candidate-valid.json"
candidate_file="${1:-${default_candidate}}"

section 'Curriculum Registry v0.2 Manual Entry Dry-Run'
cat <<'EOF'
Status: dry-run validation only
Registry writes: no
Active --write: no
Network calls: no
Student data: no
Real curriculum content: no
EOF

if [[ ! -f "${candidate_file}" ]]; then
  fail "candidate file missing: ${candidate_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "candidate file exists: ${candidate_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for dry-run validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${candidate_file}" <<'PY'
import json
import re
import sys

candidate_file = sys.argv[1]

RESOURCE_TYPES = {
    "textbook", "worksheet", "study_guide", "slides", "test", "answer_key",
    "pacing_link", "canvas_export", "folder_index",
}
SOURCE_SYSTEMS = {
    "google_drive", "nas", "icloud", "local_folder", "canvas_export", "manual_reference",
}
REVIEW_STATUSES = {
    "approved_placeholder", "not_started", "in_review", "deferred_placeholder",
}
REQUIRED_ENTRY_FIELDS = [
    "resource_id", "title", "resource_type", "subject", "grade_band", "course",
    "unit", "lesson", "topic", "source_reference_id", "source_reference",
    "source_system", "teacher_only", "student_facing_allowed", "review_status", "notes",
]
ID_PATTERN = re.compile(r"^example-[a-z0-9-]+$")
PLACEHOLDER_REF = re.compile(
    r"^(placeholder://|gdrive://placeholder/|nas://placeholder/|icloud://placeholder/|local://placeholder/)"
)
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
STUDENT_PATTERN = re.compile(r"\b(student name|real student|pupil name)\b", re.IGNORECASE)

errors = []
warnings = []

with open(candidate_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        sys.exit(0)

if data.get("dry_run_version") != "0.2.0":
    errors.append("dry_run_version must be 0.2.0")
if data.get("dry_run_mode") != "manual_entry_candidate":
    errors.append("dry_run_mode must be manual_entry_candidate")
for flag in ("metadata_only", "read_only", "no_registry_write"):
    if data.get(flag) is not True:
        errors.append(f"{flag} must be true")
if data.get("would_write") is not False:
    errors.append("would_write must be false")

entry = data.get("candidate_entry")
if not isinstance(entry, dict):
    errors.append("candidate_entry must be an object")
    entry = {}

for field in REQUIRED_ENTRY_FIELDS:
    if field not in entry:
        errors.append(f"candidate_entry missing field: {field}")

extra = set(entry.keys()) - set(REQUIRED_ENTRY_FIELDS)
if extra:
    errors.append(f"candidate_entry unexpected fields: {sorted(extra)}")

resource_id = entry.get("resource_id", "")
if not isinstance(resource_id, str) or not ID_PATTERN.match(resource_id):
    errors.append(f"resource_id invalid: {resource_id!r}")

source_ref_id = entry.get("source_reference_id", "")
if not isinstance(source_ref_id, str) or not ID_PATTERN.match(source_ref_id):
    errors.append(f"source_reference_id invalid: {source_ref_id!r}")

resource_type = entry.get("resource_type")
if resource_type not in RESOURCE_TYPES:
    errors.append(f"invalid resource_type: {resource_type!r}")

source_system = entry.get("source_system")
if source_system not in SOURCE_SYSTEMS:
    errors.append(f"invalid source_system: {source_system!r}")

review_status = entry.get("review_status")
if review_status not in REVIEW_STATUSES:
    errors.append(f"invalid review_status: {review_status!r}")

source_reference = entry.get("source_reference", "")
if not isinstance(source_reference, str) or not PLACEHOLDER_REF.match(source_reference):
    errors.append("source_reference must use allowed placeholder URI scheme")
if isinstance(source_reference, str) and HTTP_PATTERN.search(source_reference):
    errors.append("source_reference must not contain http(s) URLs")

for field in ("title", "subject", "grade_band", "course", "unit", "lesson", "topic", "notes"):
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be non-empty string")
    elif isinstance(value, str) and STUDENT_PATTERN.search(value):
        errors.append(f"{field} must not contain student-identifying placeholder violations")

for bool_field in ("teacher_only", "student_facing_allowed"):
    if not isinstance(entry.get(bool_field), bool):
        errors.append(f"{bool_field} must be boolean")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
    sys.exit(0)

if warnings:
    for w in warnings:
        print(f"WARN: {w}")

print("PASS: dry-run candidate validation succeeded")
print("dry-run only: would_write=false")
print("no_registry_write: true")
print(f"FAIL_COUNT:0")
PY
)"

while IFS= read -r line; do
  case "${line}" in
    PASS:*) pass "${line#PASS: }" ;;
    WARN:*) warn "${line#WARN: }" ;;
    FAIL:*) fail "${line#FAIL: }" ;;
    dry-run\ only:*) pass "${line}" ;;
    no_registry_write:*) pass "${line}" ;;
  esac
done <<< "${validation_output}"

if grep -q '^FAIL:' <<< "${validation_output}" || grep -q 'FAIL_COUNT:[1-9]' <<< "${validation_output}"; then
  :
elif grep -q 'PASS: dry-run candidate validation succeeded' <<< "${validation_output}"; then
  pass "dry-run validator completed"
else
  fail "dry-run validator did not report success"
  printf '%s\n' "${validation_output}"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
