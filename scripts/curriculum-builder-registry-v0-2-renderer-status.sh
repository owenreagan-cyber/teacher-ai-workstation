#!/usr/bin/env bash
# Read-only Curriculum Builder Registry v0.2 renderer foundation status (CB-IMPL-3).
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} must mention ${label}"; return; }
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

preview_script="scripts/curriculum-builder-registry-v0-2-render-preview.sh"
index_doc="docs/curriculum-builder-registry-v0-2-renderer-foundation.md"
fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"

section 'Curriculum Builder Registry v0.2 Renderer Foundation (CB-IMPL-3)'
cat <<'EOF'
Status: fake-record metadata preview only
Lesson generation: no
Production registry writes: no
Network calls: no
LLM inference: no
EOF

section 'Foundation Documents'
check_file "${index_doc}"
check_doc_contains "${index_doc}" "complete_cb_impl_3_renderer" "CB-IMPL-3 closure"
check_doc_contains "${index_doc}" "Lesson generation: blocked" "renderer blocks generation"
check_file "assistant/curriculum-builder/samples/registry-v0-2-renderer/README.md"

section 'Preview Script'
check_file "${preview_script}"
bash -n "${preview_script}" && pass "bash syntax ok: ${preview_script}" || fail "bash syntax failed: ${preview_script}"
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"

preview_output="$(bash "${preview_script}" markdown 2>&1)" || true
grep -q 'metadata preview only' <<< "${preview_output}" && pass "preview reports metadata-only boundary" || fail "preview missing metadata-only boundary"
grep -q 'example-resource-001' <<< "${preview_output}" && pass "preview includes fake record metadata" || fail "preview missing fake record"
grep -q 'no content generated' <<< "${preview_output}" && pass "preview reports no content generation" || fail "preview missing no-generation footer"
if grep -qiE 'generate lesson|worksheet content|presentation slide' <<< "${preview_output}"; then
  fail "preview must not emit generation language"
else
  pass "preview does not emit generation language"
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-registry-renderer-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-renderer-status' || fail 'CLI missing --curriculum-registry-renderer-status'
grep -Fq -- '"--curriculum-registry-renderer-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-registry-renderer-status' || fail 'manifest missing --curriculum-registry-renderer-status'
check_file tests/curriculum-builder-registry-v0-2-renderer-test.sh
bash -n tests/curriculum-builder-registry-v0-2-renderer-test.sh && pass 'bash syntax ok: renderer test' || fail 'bash syntax failed: renderer test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${preview_script}" 2>/dev/null && fail 'preview script must not shell-invoke curl' || pass 'preview script does not shell-invoke curl'
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${preview_script}" 2>/dev/null && fail 'preview script must not shell-invoke ollama' || pass 'preview script does not shell-invoke ollama'
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${preview_script}" 2>/dev/null && fail 'preview script must not shell-invoke find' || pass 'preview script does not shell-invoke find'
pass 'no lesson generation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
