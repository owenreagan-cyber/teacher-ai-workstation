#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault knowledge entry v0 validation only. No scanning, network calls, or writes.
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

default_file="assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json"
vault_file="${1:-${default_file}}"

section 'Teacher Knowledge Vault Knowledge Entry v0 Read-Only Validator'
cat <<'EOF'
Status: read-only validation only
Folder scanning: no
Document scanning: no
File indexing: no
OCR: no
Embeddings: no
RAG: no
Auto-loading memory: no
Network calls: no
Student data: no
EOF

[[ -f "${vault_file}" ]] || { fail "vault file missing: ${vault_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "vault file exists: ${vault_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${vault_file}" <<'PY'
import json, re, sys
vault_file = sys.argv[1]
CATEGORIES = {"reference_summary", "teaching_note", "workflow_guide"}
REVIEW_STATUSES = {"not_reviewed", "teacher_reviewed", "needs_review", "archived_planning_only"}
REQUIRED = [
    "knowledge_entry_id", "title", "category", "summary_label", "source_intake_ref",
    "review_status", "metadata_only", "local_first_safety_flags", "notes", "activation_status"
]
REQUIRED_FLAGS = {"metadata_only", "no_student_data", "not_indexed", "not_scanned", "placeholder_only", "no_auto_load"}
ID_PATTERN = re.compile(r"^sample-knowledge-entry-[a-z0-9-]+$")
INTAKE_PATTERN = re.compile(r"^fake-intake-ref-[a-z0-9-]+$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
errors, warnings = [], []
with open(vault_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        sys.exit(0)
for key, val in [
    ("vault_version", "0.1.0"),
    ("vault_status", "active_m0_architecture_freeze"),
    ("metadata_only", True),
    ("read_only", True),
    ("classification", "fake_local_planning_only"),
]:
    if data.get(key) != val:
        errors.append(f"{key} must be {val!r}")
entries = data.get("entries")
if not isinstance(entries, list):
    errors.append("entries must be an array")
    entries = []
if len(entries) != 3:
    errors.append(f"vault v0 requires exactly 3 fictional entries (got {len(entries)})")
seen = set()
for i, entry in enumerate(entries):
    label = f"entries[{i}]"
    if not isinstance(entry, dict):
        errors.append(f"{label} must be an object")
        continue
    for field in REQUIRED:
        if field not in entry:
            errors.append(f"{label} missing required field: {field}")
    eid = entry.get("knowledge_entry_id", "")
    if not isinstance(eid, str) or not ID_PATTERN.match(eid):
        errors.append(f"{label} knowledge_entry_id invalid: {eid!r}")
    elif eid in seen:
        errors.append(f"{label} duplicate knowledge_entry_id: {eid}")
    else:
        seen.add(eid)
    if "placeholder" not in str(entry.get("title", "")).lower():
        warnings.append(f"{label} title should contain Placeholder")
    if entry.get("category") not in CATEGORIES:
        errors.append(f"{label} invalid category")
    src = entry.get("source_intake_ref", "")
    if not isinstance(src, str) or not INTAKE_PATTERN.match(src):
        errors.append(f"{label} source_intake_ref must use fake-intake-ref pattern")
    if HTTP_PATTERN.search(json.dumps(entry)):
        errors.append(f"{label} must not contain http(s) URLs")
    if entry.get("review_status") not in REVIEW_STATUSES:
        errors.append(f"{label} invalid review_status")
    if entry.get("metadata_only") is not True:
        errors.append(f"{label} metadata_only must be true")
    if entry.get("activation_status") != "teacher_knowledge_vault_m0":
        errors.append(f"{label} activation_status must be teacher_knowledge_vault_m0")
    flags = entry.get("local_first_safety_flags")
    if isinstance(flags, list):
        missing = REQUIRED_FLAGS - set(flags)
        if missing:
            errors.append(f"{label} missing safety flags: {sorted(missing)}")
for w in warnings:
    print(f"WARN: {w}")
for e in errors:
    print(f"FAIL: {e}")
if not errors:
    print("PASS: knowledge entry document structure valid")
    print("PASS: fictional placeholder entries validated")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no auto-load attempted'
section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
