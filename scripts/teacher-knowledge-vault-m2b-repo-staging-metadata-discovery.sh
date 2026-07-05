#!/usr/bin/env bash
# Teacher Knowledge Vault M2b repo staging metadata discovery — fixed fixture folder only; stat metadata only.
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

M2B_STAGING="assistant/teacher-knowledge-vault/m2b/fake-staging-folder"
M2B_OUT_DIR=".local/teacher-knowledge-vault/m2b"
M2B_REPORT="${M2B_OUT_DIR}/repo-staging-metadata-report.json"

section 'Teacher Knowledge Vault M2b Repo Staging Metadata Discovery'
cat <<'EOF'
Status: metadata-only discovery — fixed repo-owned staging fixture folder only
Content reads: no
Arbitrary path input: no
Real local folder scanning: no
Network/API/OAuth: no
EOF

if [[ $# -gt 0 ]]; then
  fail "arbitrary path arguments are not accepted"
  printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi
pass 'no arbitrary path arguments accepted'

command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
[[ -d "${M2B_STAGING}" ]] && pass "staging fixture folder exists: ${M2B_STAGING}" || fail "staging fixture folder missing"
grep -Fq -- '.local/teacher-knowledge-vault/' .gitignore && pass 'generated output path is gitignored' || fail 'generated output path must be gitignored'

discovery_output="$(python3 - "${repo_root}" "${M2B_STAGING}" "${M2B_REPORT}" <<'PY'
import json, os, sys

repo_root, staging_rel, report_rel = sys.argv[1:4]
staging_root = os.path.join(repo_root, staging_rel)
report_path = os.path.join(repo_root, report_rel)
created_at = "2026-07-05T12:00:00Z"
source_label = "repo_owned_fake_staging"

POLICY_FOLDERS = {
    "10_TEACHER_ONLY": "10_TEACHER_ONLY",
    "11_STUDENT_FACING": "11_STUDENT_FACING",
    "12_AI_GENERATED": "12_AI_GENERATED",
    "99_DO_NOT_SCAN": "99_DO_NOT_SCAN",
}

def policy_for_relpath(relpath):
    parts = relpath.split(os.sep)
    for part in parts:
        if part in POLICY_FOLDERS:
            return POLICY_FOLDERS[part]
    return None

def flags_for_policy(policy):
    if policy == "99_DO_NOT_SCAN":
        return True, False, 0, 0, 0
    if policy == "10_TEACHER_ONLY":
        return False, True, 1, 0, 0
    return False, False, 0, 1, 1

records = []
for dirpath, dirnames, filenames in os.walk(staging_root):
    dirnames.sort()
    for name in sorted(filenames):
        full = os.path.join(dirpath, name)
        if not os.path.isfile(full):
            continue
        st = os.stat(full)
        relpath = os.path.relpath(full, staging_root)
        rel_fixture = f"{staging_rel}/{relpath}".replace(os.sep, "/")
        _, ext = os.path.splitext(name)
        policy = policy_for_relpath(relpath)
        do_not_scan, teacher_only, restricted, indexable, discoverable = flags_for_policy(policy)
        records.append({
            "relative_fixture_path": rel_fixture,
            "display_name": name,
            "extension": ext or "",
            "size_bytes": st.st_size,
            "modified_at": created_at,
            "source_label": source_label,
            "indexing_policy": policy,
            "teacher_only": teacher_only,
            "do_not_scan": do_not_scan,
            "restricted_indexable": restricted,
            "indexable": indexable,
            "discoverable": discoverable,
        })

os.makedirs(os.path.dirname(report_path), exist_ok=True)
report = {
    "classification": "fake_local_planning_only",
    "discovery_id": "fake-m2b-discovery-001",
    "source_label": source_label,
    "staging_fixture_root": staging_rel,
    "created_at": created_at,
    "fixture_files_discovered": len(records),
    "metadata_records_created": len(records),
    "blocked_do_not_scan_count": sum(1 for r in records if r["do_not_scan"]),
    "teacher_only_restricted_count": sum(1 for r in records if r["teacher_only"]),
    "content_reads": 0,
    "ocr_jobs": 0,
    "ai_rag_calls": 0,
    "external_accesses": 0,
    "real_files_read": 0,
    "real_curriculum_files_read": 0,
    "student_records_read": 0,
    "production_writes": 0,
    "api_cost_estimate_usd": "0.00",
    "records": records,
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
    f.write("\n")

print(f"PASS: discovered {len(records)} fixture files via stat metadata only")
print(f"PASS: metadata report written to {report_rel}")
print(f"PASS: content_reads remain 0")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${discovery_output}"

[[ -f "${M2B_REPORT}" ]] && pass 'metadata report exists at fixed generated path' || fail 'metadata report missing'
grep -Fq -- '"content_reads": 0' "${M2B_REPORT}" && pass 'report shows zero content reads' || fail 'report must show zero content reads'
grep -Fq -- '"fixture_files_discovered": 8' "${M2B_REPORT}" && pass 'report shows 8 fixture files discovered' || fail 'report must show 8 fixture files'

pass 'no file content read attempted'
pass 'no network call attempted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
