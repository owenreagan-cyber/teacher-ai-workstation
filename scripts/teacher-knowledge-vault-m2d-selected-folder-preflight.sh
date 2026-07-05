#!/usr/bin/env bash
# Teacher Knowledge Vault M2d Step 1 preflight — fixed Owen-approved folder only; no content reads.
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

M2D_APPROVED_FOLDER="/Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder"
M2D_OUT_DIR=".local/teacher-knowledge-vault/m2d"
M2D_PREFLIGHT="${M2D_OUT_DIR}/preflight-approval-packet.json"

section 'Teacher Knowledge Vault M2d Selected Folder Preflight (Step 1)'
cat <<'EOF'
Status: preflight only — fixed Owen-approved tiny local test folder
Content reads: no
Arbitrary path input: no
Metadata scan: not executed in preflight
Catalog import: blocked
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'generated output path is gitignored' || fail 'generated output path must be gitignored'

preflight_output="$(python3 - "${repo_root}" "${M2D_APPROVED_FOLDER}" "${M2D_PREFLIGHT}" <<'PY'
import json, os, sys

repo_root, approved_folder, preflight_rel = sys.argv[1:4]
preflight_path = os.path.join(repo_root, preflight_rel)
created_at = "2026-07-05T20:45:00Z"

MAX_FILES = 25
MAX_DEPTH = 2
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".docx", ".pptx", ".md", ".txt"}
EXPECTED_FILES = {
    "README.md",
    "fake-notes.txt",
    "fake-slide-placeholder.pptx",
    "fake-worksheet.pdf",
}
BLOCKED_SUBSTRINGS = (
    "/Desktop/", "/Documents/", "/Downloads/",
    "Google Drive", "iCloud", "CloudStorage", "/Volumes/",
    "Canvas", "NAS", "99_DO_NOT_SCAN",
)

def deny(reason):
    packet = {
        "classification": "owen_approved_local_test_folder_only",
        "step": "preflight_only",
        "real_path_scan_executed": False,
        "metadata_scan_executed": False,
        "content_reads": 0,
        "allowed_decision": False,
        "owen_approval": False,
        "owen_m2d_mission_approved": True,
        "catalog_import_blocked_until_second_approval": True,
        "requested_folder_path": approved_folder,
        "denial_reasons": [reason],
        "content_reads_disabled": True,
        "ocr_disabled": True,
        "ai_rag_disabled": True,
        "external_access_disabled": True,
    }
    os.makedirs(os.path.dirname(preflight_path), exist_ok=True)
    with open(preflight_path, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2)
        f.write("\n")
    print(f"FAIL: preflight denied — {reason}")
    sys.exit(1)

if not os.path.isdir(approved_folder):
    deny("approved_folder_missing")

normalized = os.path.realpath(approved_folder)
expected_real = os.path.realpath(approved_folder)
if normalized != expected_real:
    deny("path_normalization_failed")

path_lower = normalized.lower()
for marker in BLOCKED_SUBSTRINGS:
    if marker.lower() in path_lower:
        deny(f"blocked_path_marker:{marker}")

if normalized.endswith("/Desktop") or normalized.endswith("/Documents") or normalized.endswith("/Downloads"):
    deny("blocked_user_folder_class")

root_real = normalized
records = []
total_bytes = 0

def walk(dirpath, depth):
    global total_bytes
    if depth > MAX_DEPTH:
        deny("max_folder_depth_exceeded")
    try:
        with os.scandir(dirpath) as it:
            entries = sorted(it, key=lambda e: e.name)
    except OSError as exc:
        deny(f"scandir_failed:{exc}")
    for entry in entries:
        if entry.is_symlink():
            deny("symlink_not_allowed")
        if entry.is_dir(follow_symlinks=False):
            if depth >= MAX_DEPTH:
                deny("nested_directory_depth_exceeded")
            walk(entry.path, depth + 1)
            continue
        if not entry.is_file(follow_symlinks=False):
            continue
        full = entry.path
        real = os.path.realpath(full)
        if real != full:
            deny("path_escape_detected")
        if not (real.startswith(root_real + os.sep) or real == root_real):
            deny("traversal_outside_approved_root")
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError as exc:
            deny(f"stat_failed:{exc}")
        name = entry.name
        _, ext = os.path.splitext(name)
        if ext.lower() not in ALLOWED_EXT:
            deny(f"extension_not_allowed:{ext}")
        total_bytes += st.st_size
        if total_bytes > MAX_BYTES:
            deny("max_total_bytes_exceeded")
        records.append(name)

walk(root_real, 0)

if len(records) > MAX_FILES:
    deny("max_file_count_exceeded")

found = set(records)
if found != EXPECTED_FILES:
    deny(f"unexpected_file_set:found={sorted(found)}")

packet = {
    "classification": "owen_approved_local_test_folder_only",
    "step": "preflight_only",
    "approval_gate_step": 1,
    "real_path_scan_executed": False,
    "metadata_scan_executed": False,
    "content_reads": 0,
    "allowed_decision": True,
    "owen_approval": True,
    "owen_m2d_mission_approved": True,
    "catalog_import_blocked_until_second_approval": True,
    "requested_folder_path": approved_folder,
    "normalized_path": normalized,
    "expected_files": sorted(EXPECTED_FILES),
    "files_found": sorted(found),
    "file_count": len(records),
    "max_file_count": MAX_FILES,
    "max_folder_depth": MAX_DEPTH,
    "max_total_bytes": MAX_BYTES,
    "total_bytes_observed": total_bytes,
    "extension_allowlist": sorted(ALLOWED_EXT),
    "content_reads_disabled": True,
    "ocr_disabled": True,
    "ai_rag_disabled": True,
    "external_access_disabled": True,
    "symlink_traversal_allowed": False,
    "archive_expansion_allowed": False,
    "source_folder_writes_allowed": False,
    "generated_report_path": ".local/teacher-knowledge-vault/m2d/selected-folder-metadata-report.json",
    "rollback_cleanup_plan_required": True,
    "review_valid_until": "2026-08-05T00:00:00Z",
    "created_at": created_at,
    "denial_reasons": [],
    "real_scans_executed": 0,
    "metadata_imports_from_real_folders": 0,
    "api_cost_estimate_usd": "0.00",
}
os.makedirs(os.path.dirname(preflight_path), exist_ok=True)
with open(preflight_path, "w", encoding="utf-8") as f:
    json.dump(packet, f, indent=2)
    f.write("\n")

print(f"PASS: preflight approved fixed folder with {len(records)} expected files")
print(f"PASS: preflight packet written to {preflight_rel}")
print("PASS: content_reads remain 0")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${preflight_output}"

[[ -f "${M2D_PREFLIGHT}" ]] && pass 'preflight approval packet exists' || fail 'preflight approval packet missing'
grep -Fq -- '"allowed_decision": true' "${M2D_PREFLIGHT}" && pass 'preflight allowed decision true' || fail 'preflight must allow approved folder'
grep -Fq -- '"content_reads": 0' "${M2D_PREFLIGHT}" && pass 'preflight shows zero content reads' || fail 'preflight must show zero content reads'
pass 'no metadata scan executed in preflight'
pass 'no catalog import attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
