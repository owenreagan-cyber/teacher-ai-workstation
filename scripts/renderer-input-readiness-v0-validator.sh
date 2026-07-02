#!/usr/bin/env bash
# Read-only Renderer input readiness v0 validation only. No rendering, network calls, or writes.
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

default_file="assistant/renderer/v0/renderer-manifest.json"
manifest_file="${1:-${default_file}}"

section 'Renderer Input Readiness v0 Read-Only Validator'
cat <<'EOF'
Status: read-only input readiness validation only
Rendering: no
Generation: no
Network calls: no
EOF

[[ -f "${manifest_file}" ]] || { fail "manifest file missing: ${manifest_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "manifest file exists: ${manifest_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${manifest_file}" <<'PY'
import json, os, re, sys
manifest_file = sys.argv[1]
REQUIRED_ROOT = [
    ("manifest_version", "0.1.0"), ("manifest_status", "active_v0"),
    ("foundation_level", "v1_planning"), ("metadata_only", True),
    ("read_only", True), ("interface_only", True),
    ("rendering_enabled", False), ("generation_enabled", False),
]
REQUIRED_INPUT_FIELDS = [
    "input_id", "input_type", "artifact_path", "status_command",
    "validate_command", "required_for_rendering", "automatic_resolution",
]
FAIL_SAFE_RULES = {
    "input_validation_must_pass", "dependencies_must_be_present",
    "source_must_be_verified", "review_status_must_be_approved_or_manual_ready",
    "quarantined_resources_blocked", "placeholder_only_blocked_for_real_output",
    "student_data_blocked", "canvas_api_network_blocked",
}
RENDERER_TYPES = {
    "slide_renderer", "teacher_script_renderer", "worksheet_renderer",
    "review_game_renderer", "canvas_package_renderer", "printable_artifact_renderer",
}
errors = []
with open(manifest_file, encoding="utf-8") as handle:
    try: data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}"); sys.exit(0)
for key, val in REQUIRED_ROOT:
    if data.get(key) != val: errors.append(f"{key} must be {val!r}")
interfaces = data.get("renderer_interfaces_path", "")
if interfaces != "assistant/renderer-foundation/v0/sample-renderer-manifests.json":
    errors.append("renderer_interfaces_path must point to sample-renderer-manifests.json")
elif not os.path.isfile(interfaces):
    errors.append(f"renderer_interfaces_path missing: {interfaces}")
inputs = data.get("required_inputs")
if not isinstance(inputs, list): errors.append("required_inputs must be an array"); inputs = []
if len(inputs) != 7: errors.append(f"required_inputs must contain exactly 7 entries (got {len(inputs)})")
seen = set()
for i, item in enumerate(inputs):
    label = f"required_inputs[{i}]"
    if not isinstance(item, dict): errors.append(f"{label} must be an object"); continue
    for field in REQUIRED_INPUT_FIELDS:
        if field not in item: errors.append(f"{label} missing required field: {field}")
    iid = item.get("input_id", "")
    if iid in seen: errors.append(f"{label} duplicate input_id: {iid}")
    else: seen.add(iid)
    path = item.get("artifact_path", "")
    if not isinstance(path, str) or not path: errors.append(f"{label} artifact_path invalid")
    elif not os.path.isfile(path): errors.append(f"{label} artifact_path missing: {path}")
    if item.get("automatic_resolution") is not False: errors.append(f"{label} automatic_resolution must be false")
    cmd = item.get("status_command", "")
    if not isinstance(cmd, str) or "bin/chief-of-staff" not in cmd:
        errors.append(f"{label} status_command must reference bin/chief-of-staff")
types = data.get("future_renderer_types")
if not isinstance(types, list): errors.append("future_renderer_types must be an array"); types = []
if len(types) != 6: errors.append(f"future_renderer_types must contain exactly 6 entries (got {len(types)})")
seen_types = set()
for i, rt in enumerate(types):
    label = f"future_renderer_types[{i}]"
    rtype = rt.get("renderer_type") if isinstance(rt, dict) else None
    if rtype not in RENDERER_TYPES: errors.append(f"{label} invalid renderer_type: {rtype!r}")
    elif rtype in seen_types: errors.append(f"{label} duplicate renderer_type: {rtype}")
    else: seen_types.add(rtype)
    if rt.get("status") != "inactive": errors.append(f"{label} status must be inactive")
rules = data.get("fail_safe_rules")
if not isinstance(rules, list): errors.append("fail_safe_rules must be an array")
else:
    missing = FAIL_SAFE_RULES - set(rules)
    if missing: errors.append(f"fail_safe_rules missing: {sorted(missing)}")
for e in errors: print(f"FAIL: {e}")
if not errors:
    print("PASS: renderer input manifest structure valid")
    print("PASS: all required input artifact paths exist")
PY
)"

while IFS= read -r line; do
  case "${line}" in PASS:*) pass "${line#PASS: }" ;; WARN:*) warn "${line#WARN: }" ;; FAIL:*) fail "${line#FAIL: }" ;; esac
done <<< "${validation_output}"

pass 'no rendering attempted'; pass 'no write action attempted'; pass 'no network call attempted'
section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
