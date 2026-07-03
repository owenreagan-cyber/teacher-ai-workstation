#!/usr/bin/env bash
# Fake metadata-boundary planning record validator. Planning-only — no production writes.
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

default_fixture="assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json"
fixture_file="${1:-${default_fixture}}"

section 'Metadata Boundary Planning Fixture Validation'
cat <<'EOF'
Status: fake fixture validation only
Production registry writes: no
Real metadata intake: no
Metadata pilot execution: no
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
  fail "python3 required for metadata boundary validation"
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

EXAMPLE_ID = re.compile(r"^example-[a-z0-9-]+$")
RESOURCE_ID = re.compile(r"^resource-", re.IGNORECASE)
HTTP = re.compile(r"https?://", re.IGNORECASE)
DRIVE = re.compile(r"drive\.google\.com", re.IGNORECASE)
CANVAS = re.compile(r"canvas\.instructure\.com", re.IGNORECASE)
ABS_PATH = re.compile(r"(^|[\s\"'])(/Volumes/|smb://|file://)", re.IGNORECASE)
BLOCKED_KEYS = re.compile(
    r"student_|roster|iep_|accommodation|ocr_|embedding|vector_|rag_|api_key|oauth_|webhook|file_hash|drive_file_id|canvas_course_id|import_manifest|auto_promote",
    re.IGNORECASE,
)
SOURCE_TYPES = {
    "manual_label", "print_resource", "drive_label", "local_label",
    "nas_label", "icloud_label", "canvas_label",
}
REVIEW_STATES = {
    "draft", "candidate", "validated", "teacher_reviewed", "approved",
    "approved_placeholder", "not_started", "in_review",
}
AUDIENCE = {"teacher_facing", "student_facing"}

errors = []

with open(fixture_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        print("FAIL_COUNT:1")
        sys.exit(0)

for flag in ("fake_fixture_only", "planning_only", "metadata_only", "no_registry_write"):
    if data.get(flag) is not True:
        errors.append(f"envelope {flag} must be true")
if data.get("would_write") is not False:
    errors.append("would_write must be false")
if data.get("production_namespace") is not False:
    errors.append("production_namespace must be false for planning fixtures")

record_id = data.get("id", "")
if RESOURCE_ID.match(str(record_id)):
    errors.append("planning fixture id must not use resource-* namespace")
elif not EXAMPLE_ID.match(str(record_id)):
    errors.append("planning fixture id must match example-* pattern")

for key in data:
    if BLOCKED_KEYS.search(key):
        errors.append(f"blocked field name: {key}")

title = str(data.get("title", ""))
if len(title) > 200:
    errors.append("title exceeds 200 characters")
if HTTP.search(title) or DRIVE.search(title):
    errors.append("title must not contain URL patterns")

notes = str(data.get("notes", ""))
if len(notes) > 500:
    errors.append("notes exceeds 500 characters")

audience = data.get("audience")
if audience is not None and audience not in AUDIENCE:
    errors.append(f"invalid audience: {audience}")

review_state = data.get("review_state")
if review_state is not None and review_state not in REVIEW_STATES:
    errors.append(f"invalid review_state: {review_state}")

tags = data.get("manual_tags")
if tags is not None:
    if not isinstance(tags, list):
        errors.append("manual_tags must be an array")
    else:
        for tag in tags:
            if len(str(tag)) > 64:
                errors.append("manual_tags entry exceeds 64 characters")

src = data.get("source_reference")
if src is not None:
    if not isinstance(src, dict):
        errors.append("source_reference must be an object")
    else:
        st = src.get("source_type")
        if st not in SOURCE_TYPES:
            errors.append(f"invalid source_type: {st}")
        for field in ("display_label", "location_note", "citation_note"):
            val = str(src.get(field, ""))
            if len(val) > 300 and field != "display_label":
                errors.append(f"{field} exceeds 300 characters")
            if field == "display_label" and len(val) > 200:
                errors.append("display_label exceeds 200 characters")
            if HTTP.search(val) or DRIVE.search(val) or CANVAS.search(val) or ABS_PATH.search(val):
                errors.append(f"{field} must not contain resolvable URL or path patterns")

blob = json.dumps(data)
if HTTP.search(blob) and "negative-drive-url" in fixture_file:
    pass  # negative fixture expected to fail below
elif HTTP.search(json.dumps(src or {})):
    errors.append("source_reference contains URL patterns")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
else:
    print("PASS: metadata boundary planning fixture validation succeeded")
    print("FAIL_COUNT:0")
PY
)"

printf '%s\n' "${validation_output}"
if grep -q 'planning fixture validation succeeded' <<< "${validation_output}"; then
  pass "fixture validation succeeded"
elif grep -q '^FAIL:' <<< "${validation_output}"; then
  if [[ "${fixture_file}" == *"/negative/"* ]]; then
    pass "negative fixture correctly rejected"
  else
    fail "fixture validation failed"
  fi
else
  fail "unexpected validator output"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
