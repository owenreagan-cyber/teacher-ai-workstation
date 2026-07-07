#!/usr/bin/env bash
# Validate only committed fake/local Canvas LLM fixtures. No Canvas, network, or real content access.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "fixture mentions ${label}" || fail "${file} must mention ${label}"
}
check_absent() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "cannot check missing file: ${file}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && fail "${file} must not contain ${label}" || pass "fixture omits ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

fixture_dir="fixtures/canvas-llm"
json_fixtures=(
  "${fixture_dir}/fake-page-metadata.json"
  "${fixture_dir}/fake-module-metadata.json"
  "${fixture_dir}/fake-assignment-metadata.json"
)

section 'Canvas LLM Fake/Local Validator'
cat <<'EOF'
Status: canvas_llm_fake_local_validator_complete
Classification: fake/local fixture validation only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Network access: no
EOF

section 'Fixed Fixture Path'
[[ -d "${fixture_dir}" ]] && pass "fixture directory exists: ${fixture_dir}" || fail "fixture directory missing: ${fixture_dir}"
case "${fixture_dir}" in
  fixtures/canvas-llm) pass "validator is fixed to fixtures/canvas-llm" ;;
  *) fail "validator fixture path must remain fixtures/canvas-llm" ;;
esac

section 'Expected Fixture Files'
check_file "${fixture_dir}/README.md"
check_file "${fixture_dir}/fake-html-patterns.md"
for f in "${json_fixtures[@]}"; do
  check_file "${f}"
done

section 'Boundary Text'
check_contains "${fixture_dir}/README.md" "fake_local_only" "fake-local classification"
check_contains "${fixture_dir}/README.md" "Canvas API/OAuth/live reads: blocked" "Canvas live access blocked"
check_contains "${fixture_dir}/README.md" "Student data: blocked" "student data blocked"
check_contains "${fixture_dir}/fake-html-patterns.md" "not exported from Canvas" "fake HTML non-export boundary"
check_absent "${fixture_dir}/fake-html-patterns.md" "https://" "live URL"
check_absent "${fixture_dir}/fake-html-patterns.md" "canvas.instructure.com" "Canvas host"

section 'Evidence Schema Fields'
if command -v python3 >/dev/null 2>&1; then
  if python3 - "${json_fixtures[@]}" <<'PY'
import json
import sys

required = {
    "fixture_status",
    "runtime_activation",
    "canvas_api",
    "student_data",
    "evidence_id",
    "source_type",
    "authority_level",
    "canvas_area",
    "claim",
    "evidence_summary",
    "student_data_status",
    "live_canvas_status",
    "review_status",
    "safe_next_step",
}
allowed_source_types = {"fake_page", "fake_module", "fake_assignment"}
allowed_areas = {"page", "module", "assignment"}
unsafe_keys = {
    "student_name",
    "student_id",
    "grade",
    "submission",
    "roster",
    "access_token",
    "canvas_token",
    "oauth",
    "api_key",
    "supabase_url",
    "firebase_config",
}

failed = False
for path in sys.argv[1:]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        print(f"FAIL: JSON parse failed: {path}: {exc}")
        failed = True
        continue

    missing = sorted(required - set(data))
    if missing:
        print(f"FAIL: {path} missing required fields: {', '.join(missing)}")
        failed = True
    else:
        print(f"PASS: {path} has required evidence fields")

    if data.get("fixture_status") == "fake_local_only":
        print(f"PASS: {path} is fake_local_only")
    else:
        print(f"FAIL: {path} fixture_status must be fake_local_only")
        failed = True

    if data.get("runtime_activation") is False:
        print(f"PASS: {path} runtime activation false")
    else:
        print(f"FAIL: {path} runtime_activation must be false")
        failed = True

    for field in ("canvas_api", "student_data", "student_data_status", "live_canvas_status"):
        if data.get(field) == "blocked":
            print(f"PASS: {path} {field} blocked")
        else:
            print(f"FAIL: {path} {field} must be blocked")
            failed = True

    if data.get("source_type") in allowed_source_types:
        print(f"PASS: {path} source_type allowed")
    else:
        print(f"FAIL: {path} source_type must be fake page/module/assignment")
        failed = True

    if data.get("authority_level") == "fake_local_example":
        print(f"PASS: {path} authority_level fake_local_example")
    else:
        print(f"FAIL: {path} authority_level must be fake_local_example")
        failed = True

    if data.get("canvas_area") in allowed_areas:
        print(f"PASS: {path} canvas_area allowed")
    else:
        print(f"FAIL: {path} canvas_area must match fixture type")
        failed = True

    lowered_values = " ".join(str(value).lower() for value in data.values())
    if "https://" in lowered_values or "canvas.instructure.com" in lowered_values:
        print(f"FAIL: {path} must not include live URLs or Canvas hosts")
        failed = True
    else:
        print(f"PASS: {path} has no live URLs or Canvas hosts")

    present_unsafe = sorted(unsafe_keys & set(k.lower() for k in data))
    if present_unsafe:
        print(f"FAIL: {path} contains unsafe keys: {', '.join(present_unsafe)}")
        failed = True
    else:
        print(f"PASS: {path} has no unsafe keys")

sys.exit(1 if failed else 0)
PY
  then
    pass "all fake JSON fixtures satisfy schema and boundary checks"
  else
    fail "fake JSON fixture schema/boundary checks failed"
  fi
else
  warn "python3 not available for structured fixture checks"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
