#!/usr/bin/env bash
# Read-only Renderer Foundation v0 manifest validation only. No rendering, network calls, or writes.
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

default_file="assistant/renderer-foundation/v0/sample-renderer-manifests.json"
manifest_file="${1:-${default_file}}"
contract_root="assistant/curriculum-builder/output-contract/v0"

section 'Renderer Foundation v0 Read-Only Validator'
cat <<'EOF'
Status: read-only interface validation only
HTML rendering: no
PDF rendering: no
Worksheet generation: no
Review game generation: no
Canvas package generation: no
Live export: no
Lesson generation: no
LLM calls: no
APIs: no
Network calls: no
EOF

[[ -f "${manifest_file}" ]] || { fail "manifest file missing: ${manifest_file}"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }
pass "manifest file exists: ${manifest_file}"
command -v python3 >/dev/null 2>&1 || { fail "python3 required"; printf '\nSummary\nPASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"; exit 1; }

validation_output="$(python3 - "${manifest_file}" "${contract_root}" <<'PY'
import json, re, sys, os
manifest_file, contract_root = sys.argv[1], sys.argv[2]
CONTRACT_TYPES = {
    "direct_instruction_slide_deck_contract": "contracts/sample-di-slide-deck-001.json",
    "teacher_script_contract": "contracts/sample-teacher-script-001.json",
    "worksheet_contract": "contracts/sample-worksheet-001.json",
    "review_game_contract": "contracts/sample-review-game-001.json",
    "canvas_export_package_contract": "contracts/sample-canvas-package-001.json",
}
REQUIRED = [
    "renderer_id", "title", "contract_type", "compatible_contract_sample",
    "interface_status", "implementation_status", "generation_enabled",
    "html_rendering", "pdf_rendering", "canvas_package_generation",
    "student_facing_output", "local_first_safety_flags", "notes", "activation_status",
]
REQUIRED_FLAGS = {
    "interface_only", "no_rendering", "no_generation", "no_student_data",
    "placeholder_only", "no_external_resolution",
}
ID_PATTERN = re.compile(r"^sample-renderer-[a-z0-9-]+$")
SAMPLE_PATTERN = re.compile(r"^contracts/sample-[a-z0-9-]+\.json$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
errors, warnings = [], []
with open(manifest_file, encoding="utf-8") as handle:
    try: data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}"); sys.exit(0)
for key, val in [
    ("manifest_version", "0.1.0"), ("manifest_status", "active_v0"),
    ("metadata_only", True), ("read_only", True), ("interface_only", True),
]:
    if data.get(key) != val: errors.append(f"{key} must be {val!r}")
renderers = data.get("renderers")
if not isinstance(renderers, list): errors.append("renderers must be an array"); renderers = []
if len(renderers) != 5: errors.append(f"renderer v0 requires exactly 5 fictional interfaces (got {len(renderers)})")
seen_ids, seen_types = set(), set()
for i, renderer in enumerate(renderers):
    label = f"renderers[{i}]"
    if not isinstance(renderer, dict): errors.append(f"{label} must be an object"); continue
    for field in REQUIRED:
        if field not in renderer: errors.append(f"{label} missing required field: {field}")
    rid = renderer.get("renderer_id", "")
    if not isinstance(rid, str) or not ID_PATTERN.match(rid): errors.append(f"{label} renderer_id invalid: {rid!r}")
    elif rid in seen_ids: errors.append(f"{label} duplicate renderer_id: {rid}")
    else: seen_ids.add(rid)
    if "placeholder" not in str(renderer.get("title", "")).lower(): warnings.append(f"{label} title should contain Placeholder")
    ctype = renderer.get("contract_type")
    if ctype not in CONTRACT_TYPES: errors.append(f"{label} invalid contract_type: {ctype!r}")
    elif ctype in seen_types: errors.append(f"{label} duplicate contract_type: {ctype}")
    else: seen_types.add(ctype)
    sample = renderer.get("compatible_contract_sample", "")
    if sample != CONTRACT_TYPES.get(ctype, ""): errors.append(f"{label} compatible_contract_sample mismatch for {ctype}")
    if not isinstance(sample, str) or not SAMPLE_PATTERN.match(sample): errors.append(f"{label} compatible_contract_sample invalid")
    contract_path = os.path.join(contract_root, sample)
    if not os.path.isfile(contract_path): errors.append(f"{label} compatible contract sample missing: {contract_path}")
    for bool_field in ("generation_enabled", "html_rendering", "pdf_rendering", "canvas_package_generation", "student_facing_output"):
        if renderer.get(bool_field) is not False: errors.append(f"{label} {bool_field} must be false")
    if renderer.get("interface_status") != "interface_only": errors.append(f"{label} interface_status must be interface_only")
    if renderer.get("implementation_status") != "not_started": errors.append(f"{label} implementation_status must be not_started")
    if renderer.get("activation_status") != "renderer_foundation_v0": errors.append(f"{label} activation_status must be renderer_foundation_v0")
    flags = renderer.get("local_first_safety_flags")
    if isinstance(flags, list):
        missing = REQUIRED_FLAGS - set(flags)
        if missing: errors.append(f"{label} missing safety flags: {sorted(missing)}")
    if HTTP_PATTERN.search(json.dumps(renderer)): errors.append(f"{label} must not contain http(s) URLs")
for w in warnings: print(f"WARN: {w}")
for e in errors: print(f"FAIL: {e}")
if not errors:
    print("PASS: renderer manifest document structure valid")
    print("PASS: fictional placeholder renderer interfaces validated")
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
