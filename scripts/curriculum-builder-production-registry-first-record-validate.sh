#!/usr/bin/env bash
# Validate first governed production registry record. No writes.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

default_registry="assistant/curriculum-builder/registry/v0-2/production-registry.json"
registry_file="${1:-${default_registry}}"
APPROVED_ID="resource-math-lesson-108-presentation"

if [[ ! -f "${registry_file}" ]]; then
  fail "production registry file missing: ${registry_file}"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "production registry file exists: ${registry_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for first-record validation"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${registry_file}" "${APPROVED_ID}" <<'PY'
import json
import re
import sys

registry_file = sys.argv[1]
approved_id = sys.argv[2]

RESOURCE_ID = re.compile(r"^resource-[a-z0-9-]+$")
HTTP = re.compile(r"https?://", re.IGNORECASE)
DRIVE = re.compile(r"drive\.google\.com", re.IGNORECASE)
CANVAS = re.compile(r"canvas\.instructure\.com", re.IGNORECASE)
ABS_PATH = re.compile(r"(^|[\s\"'])(/Volumes/|smb://|file://|~/)", re.IGNORECASE)
BLOCKED_KEYS = re.compile(
    r"student_|roster|iep_|accommodation|ocr_|embedding|vector_|rag_|api_key|oauth_|webhook|file_hash|drive_file_id|canvas_course_id|import_manifest|auto_promote",
    re.IGNORECASE,
)
SOURCE_TYPES = {
    "manual_label", "print_resource", "drive_label", "local_label",
    "nas_label", "icloud_label", "canvas_label",
}
AUDIENCE = {"teacher_facing", "student_facing"}

errors = []

with open(registry_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        print("FAIL_COUNT:1")
        sys.exit(0)

if data.get("version") != "0.2":
    errors.append('version must be "0.2"')
if data.get("registry_type") != "production":
    errors.append('registry_type must be "production"')
records = data.get("records")
if not isinstance(records, list):
    errors.append("records must be an array")
elif len(records) != 1:
    errors.append(f"records must contain exactly one record (got {len(records) if isinstance(records, list) else 'non-list'})")
else:
    record = records[0]
    if not isinstance(record, dict):
        errors.append("record must be an object")
    else:
        rid = str(record.get("id", ""))
        if rid != approved_id:
            errors.append(f"record id must be {approved_id}")
        elif not RESOURCE_ID.match(rid):
            errors.append("record id must match resource-* namespace")
        if rid.startswith("sample-") or rid.startswith("example-"):
            errors.append("production id must not use sample-* or example-*")

        for key in record:
            if BLOCKED_KEYS.search(key):
                errors.append(f"blocked field name: {key}")

        title = str(record.get("title", ""))
        if not title:
            errors.append("title is required")
        elif len(title) > 200:
            errors.append("title exceeds 200 characters")
        if HTTP.search(title) or DRIVE.search(title):
            errors.append("title must not contain URL patterns")

        notes = str(record.get("notes", ""))
        if len(notes) > 500:
            errors.append("notes exceeds 500 characters")
        if HTTP.search(notes) or DRIVE.search(notes):
            errors.append("notes must not contain URL patterns")

        audience = record.get("audience")
        if audience not in AUDIENCE:
            errors.append(f"audience must be teacher_facing or student_facing (got {audience})")

        review_state = record.get("review_state")
        if review_state != "approved":
            errors.append(f"review_state must be approved (got {review_state})")

        tags = record.get("manual_tags")
        if not isinstance(tags, list):
            errors.append("manual_tags must be an array")
        else:
            for tag in tags:
                if len(str(tag)) > 64:
                    errors.append("manual_tags entry exceeds 64 characters")

        src = record.get("source_reference")
        if not isinstance(src, dict):
            errors.append("source_reference must be an object")
        else:
            st = src.get("source_type")
            if st not in SOURCE_TYPES:
                errors.append(f"invalid source_type: {st}")
            if st != "manual_label":
                errors.append("first record source_type must be manual_label")
            for field in ("display_label", "location_note", "citation_note"):
                val = str(src.get(field, ""))
                if field == "display_label" and not val:
                    errors.append("source_reference.display_label is required")
                if len(val) > 300 and field != "display_label":
                    errors.append(f"source_reference.{field} exceeds 300 characters")
                if len(str(src.get("display_label", ""))) > 200:
                    errors.append("display_label exceeds 200 characters")
                if HTTP.search(val) or DRIVE.search(val) or CANVAS.search(val) or ABS_PATH.search(val):
                    errors.append(f"source_reference.{field} must not contain URL or path patterns")

        if not record.get("created_by"):
            errors.append("created_by is required")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
else:
    print("PASS: first production registry record validation succeeded")
    print("FAIL_COUNT:0")
PY
)"

printf '%s\n' "${validation_output}"
if grep -q 'first production registry record validation succeeded' <<< "${validation_output}"; then
  pass "first record validation succeeded"
else
  fail "first record validation failed"
fi

printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
