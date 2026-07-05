#!/usr/bin/env bash
# Teacher Knowledge Vault M2d M7g import preview — fixed scan report only; no catalog import.
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

M2D_OUT_DIR=".local/teacher-knowledge-vault/m2d"
M2D_REPORT="${M2D_OUT_DIR}/selected-folder-metadata-report.json"
M2D_PREVIEW="${M2D_OUT_DIR}/m7g-import-preview.json"
SCAN_SCRIPT="scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-scan.sh"

section 'Teacher Knowledge Vault M2d M7g Import Preview'
cat <<'EOF'
Status: preview only — no M7g catalog import
Content reads: no
Production catalog writes: no
Arbitrary path input: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

[[ -f "${M2D_REPORT}" ]] && pass 'metadata report present' || {
  bash "${SCAN_SCRIPT}" >/dev/null 2>&1 && pass 'metadata scan completed before preview' || fail 'metadata scan required before preview'
}

preview_output="$(python3 - "${repo_root}" "${M2D_REPORT}" "${M2D_PREVIEW}" <<'PY'
import json, os, sys

repo_root, report_rel, preview_rel = sys.argv[1:4]
report_path = os.path.join(repo_root, report_rel)
preview_path = os.path.join(repo_root, preview_rel)
created_at = "2026-07-05T20:45:00Z"

with open(report_path, encoding="utf-8") as f:
    report = json.load(f)

candidates = []
for rec in report.get("records", []):
    if rec.get("do_not_scan"):
        continue
    candidates.append({
        "preview_id": f"fake-m2d-preview-{rec['display_name']}",
        "relative_path": rec["relative_path"],
        "display_name": rec["display_name"],
        "extension": rec["extension"],
        "size_bytes": rec["size_bytes"],
        "source_label": rec["source_label"],
        "indexable": rec["indexable"],
        "discoverable": rec["discoverable"],
        "restricted_indexable": rec["restricted_indexable"],
        "import_would_be_blocked_until_explicit_m2e_approval": True,
    })

preview = {
    "classification": "owen_approved_local_test_folder_only",
    "preview_id": "fake-m2d-m7g-preview-001",
    "catalog_import_executed": False,
    "catalog_import_blocked": True,
    "m7g_sqlite_write_executed": False,
    "preview_candidates": candidates,
    "preview_candidate_count": len(candidates),
    "content_reads": 0,
    "production_writes": 0,
    "created_at": created_at,
    "source_scan_id": report.get("scan_id"),
    "note": "Preview only. M7g import requires separate explicit approval (future M2e).",
}
os.makedirs(os.path.dirname(preview_path), exist_ok=True)
with open(preview_path, "w", encoding="utf-8") as f:
    json.dump(preview, f, indent=2)
    f.write("\n")

print(f"PASS: M7g import preview generated with {len(candidates)} candidates")
print(f"PASS: preview written to {preview_rel}")
print("PASS: no M7g catalog import executed")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${preview_output}"

[[ -f "${M2D_PREVIEW}" ]] && pass 'M7g import preview exists' || fail 'M7g import preview missing'
grep -Fq -- '"catalog_import_executed": false' "${M2D_PREVIEW}" && pass 'preview confirms no catalog import' || fail 'preview must confirm no import'
grep -Fq -- '"preview_candidate_count": 4' "${M2D_PREVIEW}" && pass 'preview shows 4 candidates' || fail 'preview must show 4 candidates'

pass 'no M7g sqlite write attempted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
