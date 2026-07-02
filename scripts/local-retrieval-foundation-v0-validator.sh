#!/usr/bin/env bash
# Read-only Local Retrieval Foundation v0 validation only. No indexing, network calls, or writes.
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

default_file="assistant/local-retrieval/v0/sample-lookup-fixtures.json"
fixture_file="${1:-${default_file}}"

section 'Local Retrieval Foundation v0 Read-Only Validator'
cat <<'EOF'
Status: read-only interface validation only
Embeddings: no
RAG: no
Vector database: no
Semantic search: no
File indexing: no
Folder crawling: no
OCR: no
LLM retrieval: no
Automatic resolution: no
Network calls: no
EOF

[[ -f "${fixture_file}" ]] || { fail "fixture file missing: ${fixture_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "fixture file exists: ${fixture_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${fixture_file}" <<'PY'
import json, re, sys
fixture_file = sys.argv[1]
LOOKUP_TYPES = {"registry_id", "contract_id", "binding_report"}
RESULT_KINDS = {"registry_record", "contract_record", "binding_report", "missing_reference_report"}
REQUIRED = [
    "lookup_id", "lookup_type", "query", "expected_result_kind", "resolution_mode",
    "automatic_resolution", "semantic_search", "indexing", "local_first_safety_flags",
    "notes", "activation_status",
]
REQUIRED_FLAGS = {
    "manual_lookup_only", "no_semantic_search", "no_indexing", "no_student_data",
    "placeholder_only", "no_external_resolution",
}
ID_PATTERN = re.compile(r"^sample-lookup-[a-z0-9-]+$")
REPORT_ID_PATTERN = re.compile(r"^sample-missing-ref-report-[a-z0-9-]+$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
errors, warnings = [], []
with open(fixture_file, encoding="utf-8") as handle:
    try: data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}"); sys.exit(0)
for key, val in [
    ("lookup_version", "0.1.0"), ("lookup_status", "active_v0"),
    ("metadata_only", True), ("read_only", True), ("manual_lookup_only", True),
]:
    if data.get(key) != val: errors.append(f"{key} must be {val!r}")
lookups = data.get("lookups")
if not isinstance(lookups, list): errors.append("lookups must be an array"); lookups = []
if len(lookups) != 4: errors.append(f"lookup v0 requires exactly 4 fictional lookups (got {len(lookups)})")
seen_ids = set()
for i, lookup in enumerate(lookups):
    label = f"lookups[{i}]"
    if not isinstance(lookup, dict): errors.append(f"{label} must be an object"); continue
    for field in REQUIRED:
        if field not in lookup: errors.append(f"{label} missing required field: {field}")
    lid = lookup.get("lookup_id", "")
    if not isinstance(lid, str) or not ID_PATTERN.match(lid): errors.append(f"{label} lookup_id invalid: {lid!r}")
    elif lid in seen_ids: errors.append(f"{label} duplicate lookup_id: {lid}")
    else: seen_ids.add(lid)
    if lookup.get("lookup_type") not in LOOKUP_TYPES: errors.append(f"{label} invalid lookup_type")
    if lookup.get("expected_result_kind") not in RESULT_KINDS: errors.append(f"{label} invalid expected_result_kind")
    if lookup.get("resolution_mode") != "manual_fixture_only": errors.append(f"{label} resolution_mode must be manual_fixture_only")
    for bool_field in ("automatic_resolution", "semantic_search", "indexing"):
        if lookup.get(bool_field) is not False: errors.append(f"{label} {bool_field} must be false")
    if lookup.get("activation_status") != "local_retrieval_v0": errors.append(f"{label} activation_status must be local_retrieval_v0")
    flags = lookup.get("local_first_safety_flags")
    if isinstance(flags, list):
        missing = REQUIRED_FLAGS - set(flags)
        if missing: errors.append(f"{label} missing safety flags: {sorted(missing)}")
    if HTTP_PATTERN.search(json.dumps(lookup)): errors.append(f"{label} must not contain http(s) URLs")
reports = data.get("missing_reference_reports")
if not isinstance(reports, list): errors.append("missing_reference_reports must be an array"); reports = []
if len(reports) != 1: errors.append(f"lookup v0 requires exactly 1 missing reference report (got {len(reports)})")
for i, report in enumerate(reports):
    label = f"missing_reference_reports[{i}]"
    if not isinstance(report, dict): errors.append(f"{label} must be an object"); continue
    for field in ("report_id", "lookup_id", "registry_id", "status", "resolution_mode", "automatic_resolution", "notes"):
        if field not in report: errors.append(f"{label} missing required field: {field}")
    rid = report.get("report_id", "")
    if not isinstance(rid, str) or not REPORT_ID_PATTERN.match(rid): errors.append(f"{label} report_id invalid: {rid!r}")
    if report.get("lookup_id") != "sample-lookup-missing-001": errors.append(f"{label} lookup_id must reference sample-lookup-missing-001")
    if report.get("status") != "missing": errors.append(f"{label} status must be missing")
    if report.get("automatic_resolution") is not False: errors.append(f"{label} automatic_resolution must be false")
for w in warnings: print(f"WARN: {w}")
for e in errors: print(f"FAIL: {e}")
if not errors:
    print("PASS: lookup fixture document structure valid")
    print("PASS: fictional placeholder lookups and missing-reference report validated")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no indexing attempted'; pass 'no write action attempted'; pass 'no network call attempted'
section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
