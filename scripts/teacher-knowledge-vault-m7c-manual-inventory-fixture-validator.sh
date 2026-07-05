#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7c manual inventory fixture validator.
# Fixed fixture paths only — no arbitrary external paths.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m7b_inventory="assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json"
m7b_csv="assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.csv"

section 'Teacher Knowledge Vault M7c Manual Inventory Fixture Validator'
cat <<'EOF'
Status: read-only fixture validation only
Fixture paths: fixed repo fixtures only
Folder scanning: no
Network calls: no
Catalog writes: no
Runtime import: no
EOF

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

for fixture in "${m7b_inventory}" "${m7b_csv}"; do
  [[ -f "${fixture}" ]] && pass "fixture exists: ${fixture}" || fail "fixture missing: ${fixture}"
done

validation_output="$(python3 - "${m7b_inventory}" <<'PY'
import json, re, sys

inventory_file = sys.argv[1]
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
REAL_PATH_PATTERN = re.compile(r"/Users/|/home/|\\\\Users\\\\|C:\\\\")
DRIVE_ID_PATTERN = re.compile(r"1[A-Za-z0-9_-]{20,}")
CANVAS_ID_PATTERN = re.compile(r"^\d{5,}$")
BLOCKED_ACTIONS = {
    "runtime_ingest", "connector_sync", "content_read", "scan", "ocr",
    "ai_classify", "rename", "move", "copy", "delete", "archive", "export", "publish"
}
FORBIDDEN_FIELDS = {
    "access_token", "refresh_token", "api_key", "oauth_token", "secret",
    "extracted_text", "file_content", "answer_key", "student_name"
}
REQUIRED_RECORD = ["manual_inventory_id", "source_label", "runtime_connected", "runtime_ingested"]
errors, warnings = [], []

with open(inventory_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: {exc}")
        data = {}

if data.get("runtime_connected") is not False:
    errors.append("root runtime_connected must be false")
if data.get("runtime_ingested") is not False:
    errors.append("root runtime_ingested must be false")

records = data.get("records", [])
if not isinstance(records, list) or not records:
    errors.append("records must be a non-empty array")

for i, record in enumerate(records if isinstance(records, list) else []):
    label = f"records[{i}]"
    if not isinstance(record, dict):
        errors.append(f"{label} must be an object")
        continue
    for field in REQUIRED_RECORD:
        if field not in record:
            errors.append(f"{label} missing required field: {field}")
    if record.get("runtime_connected") is not False:
        errors.append(f"{label} runtime_connected must be false")
    if record.get("runtime_ingested") is not False:
        errors.append(f"{label} runtime_ingested must be false")
    for key in record:
        if key.lower() in FORBIDDEN_FIELDS or key in FORBIDDEN_FIELDS:
            errors.append(f"{label} forbidden field: {key}")
    blob = json.dumps(record)
    if HTTP_PATTERN.search(blob):
        errors.append(f"{label} must not contain http(s) URLs")
    if REAL_PATH_PATTERN.search(blob):
        errors.append(f"{label} must not contain real local paths")
    for val in record.values():
        if isinstance(val, str):
            if DRIVE_ID_PATTERN.search(val):
                warnings.append(f"{label} possible real-looking Drive ID pattern (M7b fixture may be pre-sanitized)")
            if CANVAS_ID_PATTERN.match(val.strip()):
                warnings.append(f"{label} possible real-looking Canvas ID pattern")
    allowed = record.get("allowed_next_actions", [])
    if isinstance(allowed, list):
        for action in allowed:
            if action in BLOCKED_ACTIONS:
                errors.append(f"{label} allowed_next_actions must not include {action}")
    if record.get("do_not_scan_flag") is True:
        blocked = record.get("blocked_next_actions", [])
        if isinstance(blocked, list) and "index" not in blocked and "discover" not in blocked:
            warnings.append(f"{label} 99_DO_NOT_SCAN should block index/discover")
    if record.get("indexing_policy") == "10_TEACHER_ONLY":
        pass  # restricted-indexable policy preserved

for w in warnings:
    print(f"WARN: {w}")
for e in errors:
    print(f"FAIL: {e}")
if not errors:
    print(f"PASS: validated {len(records)} fixture rows from fixed path")
    print("PASS: no OAuth/API/network fields detected")
    print("PASS: no arbitrary path arguments used")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no catalog import attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
