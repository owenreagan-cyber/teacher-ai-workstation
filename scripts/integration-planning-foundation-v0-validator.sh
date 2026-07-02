#!/usr/bin/env bash
# Read-only Integration Planning Foundation v0 validation only. No APIs, OAuth, or network calls.
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

default_file="assistant/integration-planning/v0/integration-inactive-manifest.json"
manifest_file="${1:-${default_file}}"

section 'Integration Planning Foundation v0 Read-Only Validator'
cat <<'EOF'
Status: read-only inactive-integration validation only
Live integrations: no
APIs: no
OAuth: no
Credential storage: no
Sync jobs: no
Webhooks: no
Background jobs: no
Network calls: no
EOF

[[ -f "${manifest_file}" ]] || { fail "manifest file missing: ${manifest_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "manifest file exists: ${manifest_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${manifest_file}" <<'PY'
import json, os, re, sys
manifest_file = sys.argv[1]
INTEGRATION_TYPES = {"google_drive", "canvas_lms", "oauth_broker"}
REQUIRED = [
    "integration_id", "title", "integration_type", "activation_status",
    "oauth_enabled", "api_enabled", "sync_jobs", "webhooks", "background_jobs",
    "network_calls", "credential_storage", "local_first_safety_flags", "notes", "planning_doc",
]
REQUIRED_FLAGS = {"planning_only", "inactive", "no_oauth", "no_api", "no_sync_jobs", "no_network_calls"}
ID_PATTERN = re.compile(r"^sample-integration-[a-z0-9-]+$")
DOC_PATTERN = re.compile(r"^docs/[a-z0-9-]+\.md$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
errors, warnings = [], []
with open(manifest_file, encoding="utf-8") as handle:
    try: data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}"); sys.exit(0)
for key, val in [
    ("manifest_version", "0.1.0"), ("manifest_status", "active_v0"),
    ("metadata_only", True), ("read_only", True), ("integrations_inactive", True),
]:
    if data.get(key) != val: errors.append(f"{key} must be {val!r}")
integrations = data.get("integrations")
if not isinstance(integrations, list): errors.append("integrations must be an array"); integrations = []
if len(integrations) != 3: errors.append(f"integration v0 requires exactly 3 inactive fixtures (got {len(integrations)})")
seen_ids, seen_types = set(), set()
for i, item in enumerate(integrations):
    label = f"integrations[{i}]"
    if not isinstance(item, dict): errors.append(f"{label} must be an object"); continue
    for field in REQUIRED:
        if field not in item: errors.append(f"{label} missing required field: {field}")
    iid = item.get("integration_id", "")
    if not isinstance(iid, str) or not ID_PATTERN.match(iid): errors.append(f"{label} integration_id invalid: {iid!r}")
    elif iid in seen_ids: errors.append(f"{label} duplicate integration_id: {iid}")
    else: seen_ids.add(iid)
    itype = item.get("integration_type")
    if itype not in INTEGRATION_TYPES: errors.append(f"{label} invalid integration_type: {itype!r}")
    elif itype in seen_types: errors.append(f"{label} duplicate integration_type: {itype}")
    else: seen_types.add(itype)
    if item.get("activation_status") != "inactive": errors.append(f"{label} activation_status must be inactive")
    for bool_field in ("oauth_enabled", "api_enabled", "sync_jobs", "webhooks", "background_jobs", "network_calls", "credential_storage"):
        if item.get(bool_field) is not False: errors.append(f"{label} {bool_field} must be false")
    doc = item.get("planning_doc", "")
    if not isinstance(doc, str) or not DOC_PATTERN.match(doc): errors.append(f"{label} planning_doc invalid")
    elif not os.path.isfile(doc): errors.append(f"{label} planning_doc missing: {doc}")
    flags = item.get("local_first_safety_flags")
    if isinstance(flags, list):
        missing = REQUIRED_FLAGS - set(flags)
        if missing: errors.append(f"{label} missing safety flags: {sorted(missing)}")
    if HTTP_PATTERN.search(json.dumps(item)): errors.append(f"{label} must not contain http(s) URLs")
for w in warnings: print(f"WARN: {w}")
for e in errors: print(f"FAIL: {e}")
if not errors:
    print("PASS: integration inactive manifest structure valid")
    print("PASS: all integrations confirmed inactive in fixtures")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no live integration attempted'; pass 'no write action attempted'; pass 'no network call attempted'
section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
