#!/usr/bin/env bash
# Registry v0.2 local fake records validator. Fixture-only — no production registry writes.
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

default_fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
fixture_file="${1:-${default_fixture}}"

section 'Curriculum Registry v0.2 Local Fake Records Validation'
cat <<'EOF'
Status: fake fixture validation only
Production registry writes: no
Active user-facing --write: no
Network calls: no
Student data: no
Real curriculum content: no
EOF

if [[ ! -f "${fixture_file}" ]]; then
  fail "fixture file missing: ${fixture_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "fixture file exists: ${fixture_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for local records validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${fixture_file}" <<'PY'
import json
import re
import sys

fixture_file = sys.argv[1]

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
RECORD_FIELDS = [
    "resource_id", "title", "resource_type", "subject", "grade_band", "course",
    "unit", "lesson", "topic", "source_reference_id", "source_reference",
    "source_system", "teacher_only", "student_facing_allowed", "review_status",
    "lesson_link_id", "notes",
]
ID_PATTERN = re.compile(r"^example-[a-z0-9-]+$")
PLACEHOLDER_REF = re.compile(
    r"^(placeholder://|gdrive://placeholder/|nas://placeholder/|icloud://placeholder/|local://placeholder/)"
)
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
STUDENT_PATTERN = re.compile(r"\b(student name|real student|pupil name)\b", re.IGNORECASE)

errors = []

with open(fixture_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        print("FAIL_COUNT:1")
        sys.exit(0)

if data.get("local_registry_version") != "0.2.0":
    errors.append("local_registry_version must be 0.2.0")
if data.get("local_registry_mode") != "fake_fixture_only":
    errors.append("local_registry_mode must be fake_fixture_only")
for flag in ("metadata_only", "read_only", "no_production_write", "fixture_only"):
    if data.get(flag) is not True:
        errors.append(f"{flag} must be true")

records = data.get("records")
if not isinstance(records, list) or len(records) < 1:
    errors.append("records must be a non-empty array")

source_refs = data.get("source_references")
if not isinstance(source_refs, list) or len(source_refs) < 1:
    errors.append("source_references must be a non-empty array")

lesson_links = data.get("lesson_links")
if not isinstance(lesson_links, list) or len(lesson_links) < 1:
    errors.append("lesson_links must be a non-empty array")

seen_resource_ids = set()
seen_source_ids = set()
seen_link_ids = set()

for idx, record in enumerate(records or []):
    if not isinstance(record, dict):
        errors.append(f"record[{idx}] must be object")
        continue
    for field in RECORD_FIELDS:
        if field not in record:
            errors.append(f"record[{idx}] missing field: {field}")
    rid = record.get("resource_id", "")
    if not isinstance(rid, str) or not ID_PATTERN.match(rid):
        errors.append(f"record[{idx}] resource_id invalid: {rid!r}")
    elif rid in seen_resource_ids:
        errors.append(f"duplicate resource_id: {rid}")
    else:
        seen_resource_ids.add(rid)
    if record.get("resource_type") not in RESOURCE_TYPES:
        errors.append(f"record[{idx}] invalid resource_type")
    if record.get("source_system") not in SOURCE_SYSTEMS:
        errors.append(f"record[{idx}] invalid source_system")
    if record.get("review_status") not in REVIEW_STATUSES:
        errors.append(f"record[{idx}] invalid review_status")
    ref = record.get("source_reference", "")
    if not isinstance(ref, str) or not PLACEHOLDER_REF.match(ref):
        errors.append(f"record[{idx}] source_reference must use placeholder URI")
    if isinstance(ref, str) and HTTP_PATTERN.search(ref):
        errors.append(f"record[{idx}] source_reference must not contain http(s)")
    for field in ("title", "subject", "grade_band", "course", "unit", "lesson", "topic", "notes"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"record[{idx}] {field} must be non-empty string")
        elif isinstance(value, str) and STUDENT_PATTERN.search(value):
            errors.append(f"record[{idx}] {field} student-data guard triggered")

for idx, src in enumerate(source_refs or []):
    if not isinstance(src, dict):
        errors.append(f"source_references[{idx}] must be object")
        continue
    sid = src.get("source_reference_id", "")
    if not isinstance(sid, str) or not ID_PATTERN.match(sid):
        errors.append(f"source_references[{idx}] invalid source_reference_id")
    elif sid in seen_source_ids:
        errors.append(f"duplicate source_reference_id: {sid}")
    else:
        seen_source_ids.add(sid)
    path_ref = src.get("path_or_url_reference", "")
    if not isinstance(path_ref, str) or not PLACEHOLDER_REF.match(path_ref):
        errors.append(f"source_references[{idx}] path_or_url_reference must be placeholder URI")
    if src.get("not_scanned") is not True or src.get("not_ingested") is not True:
        errors.append(f"source_references[{idx}] must have not_scanned and not_ingested true")

for idx, link in enumerate(lesson_links or []):
    if not isinstance(link, dict):
        errors.append(f"lesson_links[{idx}] must be object")
        continue
    lid = link.get("lesson_link_id", "")
    if not isinstance(lid, str) or not ID_PATTERN.match(lid):
        errors.append(f"lesson_links[{idx}] invalid lesson_link_id")
    elif lid in seen_link_ids:
        errors.append(f"duplicate lesson_link_id: {lid}")
    else:
        seen_link_ids.add(lid)
    if link.get("generation_blocked") is not True:
        errors.append(f"lesson_links[{idx}] generation_blocked must be true")
    for rid in link.get("resource_ids", []):
        if rid not in seen_resource_ids:
            errors.append(f"lesson_links[{idx}] references unknown resource_id: {rid}")

for record in records or []:
    sid = record.get("source_reference_id")
    if sid and sid not in seen_source_ids:
        errors.append(f"record {record.get('resource_id')} references unknown source_reference_id: {sid}")
    lid = record.get("lesson_link_id")
    if lid and lid not in seen_link_ids:
        errors.append(f"record {record.get('resource_id')} references unknown lesson_link_id: {lid}")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
    sys.exit(0)

print("PASS: local fake registry fixture validation succeeded")
print("fixture_only: true")
print("no_production_write: true")
print("FAIL_COUNT:0")
PY
)"

while IFS= read -r line; do
  case "${line}" in
    PASS:*) pass "${line#PASS: }" ;;
    WARN:*) warn "${line#WARN: }" ;;
    FAIL:*) fail "${line#FAIL: }" ;;
    fixture_only:*) pass "${line}" ;;
    no_production_write:*) pass "${line}" ;;
  esac
done <<< "${validation_output}"

if grep -q '^FAIL:' <<< "${validation_output}" || grep -q 'FAIL_COUNT:[1-9]' <<< "${validation_output}"; then
  :
elif grep -q 'PASS: local fake registry fixture validation succeeded' <<< "${validation_output}"; then
  pass "local records validator completed"
else
  fail "local records validator did not report success"
  printf '%s\n' "${validation_output}"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
