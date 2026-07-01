#!/usr/bin/env bash
# Read-only Curriculum Registry v0 validation only. No network calls, writes, or ingestion.
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

default_registry_file="assistant/curriculum-builder/registry/v0/registry.json"
registry_file="${1:-${default_registry_file}}"

section 'Curriculum Registry v0 Read-Only Validator'
cat <<'EOF'
Status: read-only validation only
Network calls: no
Drive scanning: no
NAS scanning: no
Folder crawling: no
OCR: no
Embeddings: no
Vector database: no
RAG: no
Lesson generation: no
Canvas API: no
Google Drive API: no
OAuth: no
Student data: no
Registry writes: no
EOF

if [[ ! -f "${registry_file}" ]]; then
  fail "registry file missing: ${registry_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "registry file exists: ${registry_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for registry validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${registry_file}" <<'PY'
import json
import re
import sys

registry_file = sys.argv[1]

RESOURCE_TYPES = {
    "textbook", "worksheet", "study_guide", "slides", "test", "answer_key",
    "pacing_link", "canvas_export", "folder_index",
}
SOURCE_SYSTEMS = {
    "google_drive", "nas", "icloud", "local_folder", "canvas_export",
}
SOURCE_REFERENCE_TYPES = {"placeholder_uri"}
REVIEW_STATUSES = {
    "not_reviewed", "metadata_only", "teacher_reviewed", "needs_update",
    "needs_review", "reviewed_placeholder", "retired",
}
APPROVAL_STATUSES = {
    "not_approved", "placeholder_approved", "blocked_placeholder",
    "approved", "rejected",
}
STUDENT_FACING = {"true", "false", "unknown"}
REQUIRED_RECORD_FIELDS = [
    "registry_id", "title", "resource_type", "source_system", "source_reference",
    "source_reference_type", "subject", "grade_band", "course", "unit", "lesson",
    "pacing_reference", "teacher_only", "student_facing_allowed", "review_status",
    "approval_status", "local_first_safety_flags", "notes", "created_by_manual_entry",
    "activation_status",
]
REQUIRED_SAFETY_FLAGS = {
    "metadata_only", "no_student_data", "not_indexed", "not_scanned",
    "manual_entry", "placeholder_only", "no_external_resolution", "planning_only",
}
RESERVED_BLOCKED_FIELDS = {
    "parsed_text_status", "ocr_status", "embedding_status", "ai_summary_status",
    "auto_classification_status", "api_sync_status",
}
ID_PATTERN = re.compile(r"^sample-[a-z0-9-]+$")
REF_PATTERN = re.compile(r"^(gdrive|nas|local|icloud)://placeholder/")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
STUDENT_NAME_PATTERN = re.compile(
    r"\b(student name|real student|pupil name)\b", re.IGNORECASE
)

errors = []
warnings = []

with open(registry_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        sys.exit(0)

if not isinstance(data, dict):
    errors.append("registry root must be an object")

version = data.get("registry_version")
if version != "0.1.0":
    errors.append(f"registry_version must be 0.1.0 (got {version!r})")

if data.get("registry_status") != "active_v0":
    errors.append("registry_status must be active_v0")

if data.get("metadata_only") is not True:
    errors.append("metadata_only must be true")

if data.get("read_only") is not True:
    errors.append("read_only must be true")

records = data.get("records")
if not isinstance(records, list):
    errors.append("records must be an array")
    records = []

if len(records) != 7:
    errors.append(f"registry v0 requires exactly 7 fictional records (got {len(records)})")

seen_ids = set()
for index, record in enumerate(records):
    label = f"records[{index}]"
    if not isinstance(record, dict):
        errors.append(f"{label} must be an object")
        continue

    for field in REQUIRED_RECORD_FIELDS:
        if field not in record:
            errors.append(f"{label} missing required field: {field}")

    extra = set(record.keys()) - set(REQUIRED_RECORD_FIELDS)
    if extra:
        errors.append(f"{label} has unexpected fields: {sorted(extra)}")

    blocked = set(record.keys()) & RESERVED_BLOCKED_FIELDS
    if blocked:
        errors.append(f"{label} contains reserved blocked fields: {sorted(blocked)}")

    registry_id = record.get("registry_id", "")
    if not isinstance(registry_id, str) or not ID_PATTERN.match(registry_id):
        errors.append(f"{label} registry_id invalid: {registry_id!r}")
    elif registry_id in seen_ids:
        errors.append(f"{label} duplicate registry_id: {registry_id}")
    else:
        seen_ids.add(registry_id)

    title = record.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{label} title must be non-empty string")
    elif "placeholder" not in title.lower():
        warnings.append(f"{label} title should contain Placeholder for v0 fictional data")

    resource_type = record.get("resource_type")
    if resource_type not in RESOURCE_TYPES:
        errors.append(f"{label} invalid resource_type: {resource_type!r}")

    source_system = record.get("source_system")
    if source_system not in SOURCE_SYSTEMS:
        errors.append(f"{label} invalid source_system: {source_system!r}")

    source_reference = record.get("source_reference", "")
    if not isinstance(source_reference, str) or not REF_PATTERN.match(source_reference):
        errors.append(f"{label} source_reference must use placeholder URI scheme")
    if isinstance(source_reference, str) and HTTP_PATTERN.search(source_reference):
        errors.append(f"{label} source_reference must not contain http(s) URLs")

    source_reference_type = record.get("source_reference_type")
    if source_reference_type not in SOURCE_REFERENCE_TYPES:
        errors.append(f"{label} invalid source_reference_type: {source_reference_type!r}")

    for text_field in ("subject", "grade_band", "course", "unit", "lesson", "pacing_reference", "notes"):
        value = record.get(text_field)
        if not isinstance(value, str):
            errors.append(f"{label} {text_field} must be a string")

    teacher_only = record.get("teacher_only")
    if not isinstance(teacher_only, bool):
        errors.append(f"{label} teacher_only must be boolean")

    student_facing = record.get("student_facing_allowed")
    if student_facing not in STUDENT_FACING:
        errors.append(f"{label} invalid student_facing_allowed: {student_facing!r}")
    if teacher_only is True and student_facing == "true":
        errors.append(f"{label} teacher_only true cannot pair with student_facing_allowed true")

    review_status = record.get("review_status")
    if review_status not in REVIEW_STATUSES:
        errors.append(f"{label} invalid review_status: {review_status!r}")

    approval_status = record.get("approval_status")
    if approval_status not in APPROVAL_STATUSES:
        errors.append(f"{label} invalid approval_status: {approval_status!r}")

    flags = record.get("local_first_safety_flags")
    if not isinstance(flags, list) or not all(isinstance(item, str) for item in flags):
        errors.append(f"{label} local_first_safety_flags must be string array")
    else:
        flag_set = set(flags)
        missing_flags = REQUIRED_SAFETY_FLAGS - flag_set
        if missing_flags:
            errors.append(
                f"{label} missing required safety flags: {sorted(missing_flags)}"
            )

    if record.get("created_by_manual_entry") is not True:
        errors.append(f"{label} created_by_manual_entry must be true")

    if record.get("activation_status") != "registry_v0":
        errors.append(f"{label} activation_status must be registry_v0")

    combined_text = " ".join(
        str(record.get(field, "")) for field in ("title", "notes", "source_reference")
    )
    if STUDENT_NAME_PATTERN.search(combined_text):
        errors.append(f"{label} appears to contain student-identifying text")

for warning in warnings:
    print(f"WARN: {warning}")

for error in errors:
    print(f"FAIL: {error}")

if not errors:
    print("PASS: registry envelope valid")
    print("PASS: all records pass v0 manual metadata validation")
    print(f"PASS: validated {len(records)} registry records")
PY
)" || true

while IFS= read -r line; do
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
      if [[ -n "${line}" ]]; then
        printf '%s\n' "${line}"
      fi
      ;;
  esac
done <<< "${validation_output}"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
