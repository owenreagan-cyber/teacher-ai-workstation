#!/usr/bin/env bash
# Fake curriculum source inventory validator. Planning-only — no real ingestion.
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

default_inventory="assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json"
inventory_file="${1:-${default_inventory}}"

section 'Curriculum Source Readiness Fake Inventory Validation'
cat <<'EOF'
Status: fake fixture validation only
Real curriculum ingestion: no
Production registry writes: no
Active user-facing --write: no
Network calls: no
Student data: no
Real curriculum content: no
EOF

if [[ ! -f "${inventory_file}" ]]; then
  fail "inventory file missing: ${inventory_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "inventory file exists: ${inventory_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for curriculum source readiness validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${inventory_file}" <<'PY'
import json
import re
import sys

inventory_file = sys.argv[1]

SOURCE_ID = re.compile(r"^fake-source-[0-9]{3}$")
HTTP = re.compile(r"https?://", re.IGNORECASE)
DRIVE = re.compile(r"drive\.google\.com", re.IGNORECASE)
ABS_PATH = re.compile(r"(^|[\s\"'])(/Users/|/home/|C:\\\\|D:\\\\)")
STUDENT_FIELD = re.compile(r"student_name|student_id|pupil_name|roster", re.IGNORECASE)
STUDENT_TEXT = re.compile(r"\b(real student|student name)\b", re.IGNORECASE)

SOURCE_TYPES = {
    "teacher_created_placeholder", "manual_reference_placeholder",
    "folder_index_placeholder", "canvas_export_placeholder", "draft_fake_fixture",
}
REVIEW_STATES = {
    "draft_fake_fixture", "not_started", "in_review_placeholder", "approved_placeholder",
}
REQUIRED_SOURCE_FIELDS = [
    "source_id", "grade_band", "subject", "unit_label", "lesson_label",
    "source_type", "review_state", "content_ingestion_allowed",
    "student_data_allowed", "real_curriculum_content_allowed",
    "fake_fixture_only", "production_write_allowed", "notes",
]
ALLOWED_SOURCE_FIELDS = set(REQUIRED_SOURCE_FIELDS)

errors = []

with open(inventory_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        print("FAIL_COUNT:1")
        sys.exit(0)

if data.get("inventory_version") != "0.1.0":
    errors.append("inventory_version must be 0.1.0")
if data.get("inventory_mode") != "fake_fixture_only":
    errors.append("inventory_mode must be fake_fixture_only")
for flag in ("metadata_only", "read_only", "no_production_write", "fake_fixture_only"):
    if data.get(flag) is not True:
        errors.append(f"envelope {flag} must be true")
for flag in ("content_ingestion_allowed", "student_data_allowed", "real_curriculum_content_allowed", "production_write_allowed"):
    if data.get(flag) is not False:
        errors.append(f"envelope {flag} must be false")

sources = data.get("sources")
if not isinstance(sources, list) or not sources:
    errors.append("sources must be a non-empty list")

seen_ids = set()

def scan_strings(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if STUDENT_FIELD.search(key):
                errors.append(f"student-like field name at {path}.{key}")
            scan_strings(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            scan_strings(item, f"{path}[{idx}]")
    elif isinstance(obj, str):
        if HTTP.search(obj) or DRIVE.search(obj):
            errors.append(f"URL detected in {path}")
        if ABS_PATH.search(obj):
            errors.append(f"absolute path detected in {path}")
        if STUDENT_TEXT.search(obj):
            errors.append(f"student-like text in {path}")

if isinstance(sources, list):
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{idx}] must be object")
            continue
        extra = set(source.keys()) - ALLOWED_SOURCE_FIELDS
        if extra:
            errors.append(f"sources[{idx}] has disallowed fields: {sorted(extra)}")
        for field in REQUIRED_SOURCE_FIELDS:
            if field not in source:
                errors.append(f"sources[{idx}] missing {field}")
        sid = source.get("source_id")
        if not isinstance(sid, str) or not SOURCE_ID.match(sid):
            errors.append(f"sources[{idx}] source_id must match fake-source-NNN")
        elif sid in seen_ids:
            errors.append(f"duplicate source_id: {sid}")
        else:
            seen_ids.add(sid)
        if source.get("source_type") not in SOURCE_TYPES:
            errors.append(f"sources[{idx}] invalid source_type")
        if source.get("review_state") not in REVIEW_STATES:
            errors.append(f"sources[{idx}] invalid review_state")
        if source.get("content_ingestion_allowed") is not False:
            errors.append(f"sources[{idx}] content_ingestion_allowed must be false")
        if source.get("student_data_allowed") is not False:
            errors.append(f"sources[{idx}] student_data_allowed must be false")
        if source.get("real_curriculum_content_allowed") is not False:
            errors.append(f"sources[{idx}] real_curriculum_content_allowed must be false")
        if source.get("fake_fixture_only") is not True:
            errors.append(f"sources[{idx}] fake_fixture_only must be true")
        if source.get("production_write_allowed") is not False:
            errors.append(f"sources[{idx}] production_write_allowed must be false")

scan_strings(data)

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
else:
    print(f"PASS: validated {len(sources)} fake source records")
    print("PASS: envelope safety flags ok")
    print("PASS: no URLs absolute paths or student-like fields detected")
    print("FAIL_COUNT:0")
PY
)" || true

if grep -q '^FAIL:' <<< "${validation_output}"; then
  printf '%s\n' "${validation_output}"
  while IFS= read -r line; do
    [[ "${line}" == FAIL:* ]] && fail "${line#FAIL: }"
  done <<< "${validation_output}"
else
  printf '%s\n' "${validation_output}"
  grep -q 'validated' <<< "${validation_output}" && pass "inventory validation succeeded" || fail "inventory validation produced no success marker"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
