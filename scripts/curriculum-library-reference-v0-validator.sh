#!/usr/bin/env bash
# Read-only Curriculum Library reference v0 validation only. No scanning, network calls, or writes.
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

default_file="assistant/curriculum-library/v0/sample-library-references.json"
library_file="${1:-${default_file}}"

section 'Curriculum Library Reference v0 Read-Only Validator'
cat <<'EOF'
Status: read-only validation only
Folder scanning: no
Document scanning: no
File indexing: no
OCR: no
Embeddings: no
RAG: no
Drive API: no
NAS resolution: no
Network calls: no
Student data: no
EOF

[[ -f "${library_file}" ]] || { fail "library file missing: ${library_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "library file exists: ${library_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${library_file}" <<'PY'
import json, re, sys
library_file = sys.argv[1]
SOURCE_SYSTEMS = {"google_drive", "nas", "icloud", "local_folder"}
RESOURCE_TYPES = {"worksheet", "study_guide", "slides", "test", "textbook", "folder_index", "pacing_link"}
STORAGE_SCOPES = {"active", "archive", "local"}
REVIEW_STATUSES = {"not_reviewed", "metadata_only", "teacher_reviewed", "needs_review"}
REQUIRED = ["reference_id", "title", "source_system", "source_reference", "source_reference_type", "resource_type", "storage_scope", "review_status", "metadata_only", "local_first_safety_flags", "notes", "activation_status"]
REQUIRED_FLAGS = {"metadata_only", "no_student_data", "not_indexed", "not_scanned", "placeholder_only", "no_external_resolution"}
ID_PATTERN = re.compile(r"^sample-library-ref-[a-z0-9-]+$")
REF_PATTERN = re.compile(r"^(gdrive|nas|local|icloud)://placeholder/")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
errors, warnings = [], []
with open(library_file, encoding="utf-8") as handle:
    try: data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}"); sys.exit(0)
for key, val in [("library_version", "0.1.0"), ("library_status", "active_v0"), ("metadata_only", True), ("read_only", True)]:
    if data.get(key) != val: errors.append(f"{key} must be {val!r}")
refs = data.get("references")
if not isinstance(refs, list): errors.append("references must be an array"); refs = []
if len(refs) != 3: errors.append(f"library v0 requires exactly 3 fictional references (got {len(refs)})")
seen = set()
for i, ref in enumerate(refs):
    label = f"references[{i}]"
    if not isinstance(ref, dict): errors.append(f"{label} must be an object"); continue
    for field in REQUIRED:
        if field not in ref: errors.append(f"{label} missing required field: {field}")
    rid = ref.get("reference_id", "")
    if not isinstance(rid, str) or not ID_PATTERN.match(rid): errors.append(f"{label} reference_id invalid: {rid!r}")
    elif rid in seen: errors.append(f"{label} duplicate reference_id: {rid}")
    else: seen.add(rid)
    if "placeholder" not in str(ref.get("title", "")).lower(): warnings.append(f"{label} title should contain Placeholder")
    if ref.get("source_system") not in SOURCE_SYSTEMS: errors.append(f"{label} invalid source_system")
    src = ref.get("source_reference", "")
    if not isinstance(src, str) or not REF_PATTERN.match(src): errors.append(f"{label} source_reference must use placeholder URI scheme")
    if HTTP_PATTERN.search(json.dumps(ref)): errors.append(f"{label} must not contain http(s) URLs")
    if ref.get("resource_type") not in RESOURCE_TYPES: errors.append(f"{label} invalid resource_type")
    if ref.get("storage_scope") not in STORAGE_SCOPES: errors.append(f"{label} invalid storage_scope")
    if ref.get("review_status") not in REVIEW_STATUSES: errors.append(f"{label} invalid review_status")
    if ref.get("metadata_only") is not True: errors.append(f"{label} metadata_only must be true")
    if ref.get("activation_status") != "curriculum_library_v0": errors.append(f"{label} activation_status must be curriculum_library_v0")
    flags = ref.get("local_first_safety_flags")
    if isinstance(flags, list):
        missing = REQUIRED_FLAGS - set(flags)
        if missing: errors.append(f"{label} missing safety flags: {sorted(missing)}")
for w in warnings: print(f"WARN: {w}")
for e in errors: print(f"FAIL: {e}")
if not errors:
    print("PASS: library reference document structure valid")
    print("PASS: fictional placeholder references validated")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no write action attempted'; pass 'no folder scanning attempted'; pass 'no network call attempted'
section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
