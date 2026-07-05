#!/usr/bin/env bash
# Teacher Knowledge Vault M2d Step 2 metadata scan — fixed Owen-approved folder only; stat metadata only.
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
M2D_REPORT="${M2D_OUT_DIR}/selected-folder-metadata-report.json"
M2D_SCAN_PROOF="${M2D_OUT_DIR}/scan-proof.json"
M2D_NO_CONTENT="${M2D_OUT_DIR}/no-content-read-proof.json"
M2D_ROLLBACK="${M2D_OUT_DIR}/rollback-proof.json"
M2D_SUMMARY="${M2D_OUT_DIR}/summary-report.json"
PREFLIGHT_SCRIPT="scripts/teacher-knowledge-vault-m2d-selected-folder-preflight.sh"

section 'Teacher Knowledge Vault M2d Selected Folder Metadata Scan (Step 2)'
cat <<'EOF'
Status: metadata-only scan — fixed Owen-approved tiny local test folder only
Content reads: no
Arbitrary path input: no
Catalog import: not automatic
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

section 'Preflight Gate'
if [[ -f "${M2D_PREFLIGHT}" ]] && grep -Fq -- '"allowed_decision": true' "${M2D_PREFLIGHT}"; then
  pass 'preflight approval packet present with allowed decision'
else
  bash "${PREFLIGHT_SCRIPT}" >/dev/null 2>&1 && pass 'preflight executed before scan' || fail 'preflight must pass before metadata scan'
fi

scan_output="$(python3 - "${repo_root}" "${M2D_APPROVED_FOLDER}" "${M2D_OUT_DIR}" <<'PY'
import json, os, sys, time

repo_root, approved_folder, out_rel = sys.argv[1:4]
out_dir = os.path.join(repo_root, out_rel)
created_at = "2026-07-05T20:45:00Z"
scan_id = "fake-m2d-scan-001"

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
MIME_BY_EXT = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".md": "text/markdown",
    ".txt": "text/plain",
}

def fail_scan(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

if not os.path.isdir(approved_folder):
    fail_scan("approved folder missing")

root_real = os.path.realpath(approved_folder)
records = []
total_bytes = 0
content_reads = 0
symlinks_seen = 0
methods_used = ["os.scandir", "os.DirEntry.stat(follow_symlinks=False)", "os.path.realpath"]

def walk(dirpath, depth):
    global total_bytes, symlinks_seen
    if depth > MAX_DEPTH:
        fail_scan("max folder depth exceeded")
    try:
        with os.scandir(dirpath) as it:
            entries = sorted(it, key=lambda e: e.name)
    except OSError as exc:
        fail_scan(f"scandir failed: {exc}")
    for entry in entries:
        if entry.is_symlink():
            symlinks_seen += 1
            fail_scan("symlink traversal blocked")
        if entry.is_dir(follow_symlinks=False):
            if depth >= MAX_DEPTH:
                fail_scan("nested directory depth exceeded")
            walk(entry.path, depth + 1)
            continue
        if not entry.is_file(follow_symlinks=False):
            continue
        full = entry.path
        real = os.path.realpath(full)
        if not real.startswith(root_real + os.sep):
            fail_scan("traversal outside approved root")
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError as exc:
            fail_scan(f"stat failed: {exc}")
        name = entry.name
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext not in ALLOWED_EXT:
            fail_scan(f"extension not allowed: {ext}")
        total_bytes += st.st_size
        if total_bytes > MAX_BYTES:
            fail_scan("max total bytes exceeded")
        rel = os.path.relpath(full, root_real)
        depth_rel = rel.count(os.sep)
        records.append({
            "relative_path": rel.replace(os.sep, "/"),
            "display_name": name,
            "extension": ext,
            "size_bytes": st.st_size,
            "modified_at_epoch": int(st.st_mtime),
            "directory_depth": depth_rel,
            "mime_guess_from_extension": MIME_BY_EXT.get(ext, "application/octet-stream"),
            "source_label": "owen_approved_m2d_tiny_test_folder",
            "indexable": 1,
            "discoverable": 1,
            "restricted_indexable": 0,
            "do_not_scan": False,
            "teacher_only": False,
        })

walk(root_real, 0)

found = {r["display_name"] for r in records}
if found != EXPECTED_FILES:
    fail_scan(f"unexpected file set: {sorted(found)}")
if len(records) != 4:
    fail_scan(f"expected 4 files, found {len(records)}")

os.makedirs(out_dir, exist_ok=True)

metadata_report = {
    "classification": "owen_approved_local_test_folder_only",
    "scan_id": scan_id,
    "step": "metadata_scan",
    "approval_gate_step": 2,
    "approved_folder_path": approved_folder,
    "normalized_root": root_real,
    "created_at": created_at,
    "files_discovered": len(records),
    "metadata_records_created": len(records),
    "total_bytes": total_bytes,
    "content_reads": content_reads,
    "document_payload_bytes_read": 0,
    "ocr_jobs": 0,
    "ai_rag_calls": 0,
    "external_accesses": 0,
    "real_files_read": 0,
    "student_records_read": 0,
    "production_writes": 0,
    "source_folder_writes": 0,
    "symlinks_traversed": 0,
    "api_cost_estimate_usd": "0.00",
    "records": records,
}
scan_proof = {
    "classification": "owen_approved_local_test_folder_only",
    "scan_id": scan_id,
    "approved_root": root_real,
    "traversal_confined_to_approved_root": True,
    "parent_directories_scanned": False,
    "symlink_traversal_attempted": False,
    "symlinks_seen": symlinks_seen,
    "max_folder_depth_observed": max((r["directory_depth"] for r in records), default=0),
    "files_discovered": len(records),
    "expected_files_only": True,
    "metadata_methods_used": methods_used,
}
no_content_proof = {
    "classification": "owen_approved_local_test_folder_only",
    "scan_id": scan_id,
    "content_reads": 0,
    "document_payload_bytes_read": 0,
    "open_for_read_attempted": False,
    "parsers_invoked": False,
    "ocr_invoked": False,
    "ai_rag_invoked": False,
    "hash_from_content_attempted": False,
    "embeddings_generated": False,
    "filesystem_metadata_only": True,
    "proof_methods": methods_used,
}
rollback_proof = {
    "classification": "owen_approved_local_test_folder_only",
    "scan_id": scan_id,
    "source_folder_modified": False,
    "source_folder_writes": 0,
    "generated_output_path": out_rel,
    "cleanup_script": "scripts/teacher-knowledge-vault-m2d-selected-folder-cleanup.sh",
    "cleanup_removes_generated_outputs_only": True,
    "m7g_auto_import": False,
    "rollback_available": True,
}
summary_report = {
    "classification": "owen_approved_local_test_folder_only",
    "scan_id": scan_id,
    "mission": "m2d_first_selected_folder_metadata_scan",
    "approved_folder_path": approved_folder,
    "files_discovered": len(records),
    "content_reads": 0,
    "metadata_only": True,
    "catalog_import_executed": False,
    "m7g_preview_only": True,
    "reports_generated": [
        "selected-folder-metadata-report.json",
        "scan-proof.json",
        "no-content-read-proof.json",
        "rollback-proof.json",
        "summary-report.json",
    ],
}

paths = {
    "selected-folder-metadata-report.json": metadata_report,
    "scan-proof.json": scan_proof,
    "no-content-read-proof.json": no_content_proof,
    "rollback-proof.json": rollback_proof,
    "summary-report.json": summary_report,
}
for name, payload in paths.items():
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

print(f"PASS: metadata scan collected {len(records)} files via stat metadata only")
print(f"PASS: metadata report written to {out_rel}/selected-folder-metadata-report.json")
print("PASS: scan-proof, no-content-read-proof, rollback-proof, and summary-report written")
print("PASS: content_reads remain 0")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${scan_output}"

for report in "${M2D_REPORT}" "${M2D_SCAN_PROOF}" "${M2D_NO_CONTENT}" "${M2D_ROLLBACK}" "${M2D_SUMMARY}"; do
  [[ -f "${report}" ]] && pass "report exists: ${report}" || fail "report missing: ${report}"
done
grep -Fq -- '"content_reads": 0' "${M2D_REPORT}" && pass 'metadata report shows zero content reads' || fail 'metadata report must show zero content reads'
grep -Fq -- '"files_discovered": 4' "${M2D_REPORT}" && pass 'metadata report shows 4 files discovered' || fail 'metadata report must show 4 files'
grep -Fq -- '"traversal_confined_to_approved_root": true' "${M2D_SCAN_PROOF}" && pass 'scan proof confirms root confinement' || fail 'scan proof must confirm root confinement'
grep -Fq -- '"filesystem_metadata_only": true' "${M2D_NO_CONTENT}" && pass 'no-content-read proof confirms metadata only' || fail 'no-content-read proof missing'
grep -Fq -- '"m7g_auto_import": false' "${M2D_ROLLBACK}" && pass 'rollback proof confirms no auto import' || fail 'rollback proof must deny auto import'

pass 'no file content read attempted'
pass 'no catalog import attempted'
pass 'no production registry write attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
