#!/usr/bin/env bash
# Validate empty production registry shell. No writes.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

default_registry="assistant/curriculum-builder/registry/v0-2/production-registry.json"
registry_file="${1:-${default_registry}}"

if [[ ! -f "${registry_file}" ]]; then
  fail "production registry file missing: ${registry_file}"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "production registry file exists: ${registry_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for production registry validation"
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${registry_file}" <<'PY'
import json
import re
import sys

registry_file = sys.argv[1]
RESOURCE_ID = re.compile(r"^resource-", re.IGNORECASE)

errors = []

with open(registry_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        print("FAIL_COUNT:1")
        sys.exit(0)

if data.get("version") != "0.2":
    errors.append('version must be "0.2"')
if data.get("registry_type") != "production":
    errors.append('registry_type must be "production"')
records = data.get("records")
if not isinstance(records, list):
    errors.append("records must be an array")
elif len(records) != 0:
    errors.append("records must be empty array")
    for idx, record in enumerate(records):
        if isinstance(record, dict):
            rid = record.get("id") or record.get("resource_id") or ""
            if RESOURCE_ID.match(str(rid)):
                errors.append(f"records[{idx}] must not contain resource-* id in empty shell")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
else:
    print("PASS: empty production registry shell validation succeeded")
    print("FAIL_COUNT:0")
PY
)"

printf '%s\n' "${validation_output}"
if grep -q 'empty production registry shell validation succeeded' <<< "${validation_output}"; then
  pass "empty shell validation succeeded"
else
  fail "empty shell validation failed"
fi

printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
