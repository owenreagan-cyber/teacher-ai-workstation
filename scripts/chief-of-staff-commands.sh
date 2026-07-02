#!/usr/bin/env bash
# Read-only deterministic Chief of Staff command surface index.
# Prints manifest categories; verifies implemented flags exist in bin/chief-of-staff.
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

manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
chief_of_staff="bin/chief-of-staff"
index_doc="docs/chief-of-staff-command-index-v1.md"

section 'Chief of Staff Command Surface'
cat <<'EOF'
Status: read-only command index only
Network calls: no
File mutation: no
Automation: no
Student data: no
EOF

[[ -f "${manifest}" ]] && pass "command surface manifest exists" || { fail "command surface manifest missing"; exit 1; }
[[ -f "${chief_of_staff}" ]] && pass "chief-of-staff CLI exists" || { fail "chief-of-staff CLI missing"; exit 1; }
[[ -f "${index_doc}" ]] && pass "command index doc exists" || fail "command index doc missing"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for command surface manifest"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

if python3 -m json.tool "${manifest}" >/dev/null 2>&1; then
  pass "manifest JSON syntax valid"
else
  fail "manifest JSON syntax invalid"
  exit 1
fi

python3 - "${manifest}" "${chief_of_staff}" <<'PY'
import json
import sys

manifest_path, cli_path = sys.argv[1], sys.argv[2]
with open(manifest_path, encoding="utf-8") as f:
    data = json.load(f)

try:
    cli_text = open(cli_path, encoding="utf-8").read()
except OSError as e:
    print(f"FAIL: cannot read {cli_path}: {e}")
    sys.exit(1)

print(f"Program: {data.get('program', 'unknown')}")
print(f"Manifest version: {data.get('version', 'unknown')}")
print(f"Surface status: {data.get('status', 'unknown')}")
print()
print("Legend: [implemented] [planned] [blocked]")
print()

counts = {"implemented": 0, "planned": 0, "blocked": 0}
missing = []

for cat in data.get("categories", []):
    print(f"## {cat.get('name', cat.get('id', 'category'))}")
    for cmd in cat.get("commands", []):
        flag = cmd.get("flag", "")
        status = cmd.get("status", "unknown")
        purpose = cmd.get("purpose", "")
        counts[status] = counts.get(status, 0) + 1
        tag = f"[{status}]"
        print(f"  {tag:14} bin/chief-of-staff {flag}")
        print(f"                 {purpose}")
        if status == "implemented" and flag and flag not in cli_text:
            missing.append(flag)
    print()

print("Counts:")
for k in ("implemented", "planned", "blocked"):
    print(f"  {k}: {counts.get(k, 0)}")

if missing:
    for m in missing:
        print(f"FAIL: implemented flag missing from CLI: {m}")
    sys.exit(2)
PY

py_result=$?
if [[ "${py_result}" == 0 ]]; then
  pass "command surface printed from manifest"
  pass "all implemented flags present in CLI"
elif [[ "${py_result}" == 2 ]]; then
  fail "implemented command missing from chief-of-staff CLI"
else
  fail "command surface manifest processing failed"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
