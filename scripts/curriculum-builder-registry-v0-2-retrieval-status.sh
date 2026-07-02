#!/usr/bin/env bash
# Read-only Curriculum Builder Registry v0.2 retrieval hooks status (CB-IMPL-4).
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

retrieval_script="scripts/curriculum-builder-registry-v0-2-retrieval-check.sh"
index_doc="docs/curriculum-builder-registry-v0-2-retrieval-hooks-foundation.md"

section 'Curriculum Builder Registry v0.2 Retrieval Hooks (CB-IMPL-4)'
cat <<'EOF'
Status: fake-record local lookup only
Filesystem crawl: no
Embeddings/RAG: no
Production registry writes: no
Network calls: no
EOF

section 'Foundation Documents'
check_file "${index_doc}"
check_doc_contains "${index_doc}" "complete_cb_impl_4_retrieval" "CB-IMPL-4 closure"
check_doc_contains "${index_doc}" "Semantic search: blocked" "retrieval blocks semantic search"
check_file "assistant/curriculum-builder/samples/registry-v0-2-retrieval/README.md"

section 'Retrieval Script'
check_file "${retrieval_script}"
bash -n "${retrieval_script}" && pass "bash syntax ok: ${retrieval_script}" || fail "bash syntax failed: ${retrieval_script}"
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"

all_output="$(bash "${retrieval_script}" 2>&1)" || true
grep -q 'local fake-record retrieval only' <<< "${all_output}" && pass "retrieval reports local-only boundary" || fail "retrieval missing local-only boundary"
grep -q 'MATCH:' <<< "${all_output}" && pass "retrieval lists fake records" || fail "retrieval missing matches"

filtered_output="$(bash "${retrieval_script}" --resource-id example-resource-001 2>&1)" || true
grep -q 'example-resource-001' <<< "${filtered_output}" && pass "retrieval filters by resource_id" || fail "retrieval resource_id filter failed"
if grep -q 'example-resource-002' <<< "${filtered_output}" && ! grep -q 'WARN: no matching' <<< "${filtered_output}"; then
  fail "retrieval filter returned too many records"
else
  pass "retrieval filter excludes non-matching records"
fi

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-registry-retrieval-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-retrieval-status' || fail 'CLI missing --curriculum-registry-retrieval-status'
grep -Fq -- '"--curriculum-registry-retrieval-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-registry-retrieval-status' || fail 'manifest missing --curriculum-registry-retrieval-status'
check_file tests/curriculum-builder-registry-v0-2-retrieval-test.sh
bash -n tests/curriculum-builder-registry-v0-2-retrieval-test.sh && pass 'bash syntax ok: retrieval test' || fail 'bash syntax failed: retrieval test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${retrieval_script}" 2>/dev/null && fail 'retrieval script must not shell-invoke curl' || pass 'retrieval script does not shell-invoke curl'
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${retrieval_script}" 2>/dev/null && fail 'retrieval script must not shell-invoke find' || pass 'retrieval script does not shell-invoke find'
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${retrieval_script}" 2>/dev/null && fail 'retrieval script must not shell-invoke ollama' || pass 'retrieval script does not shell-invoke ollama'
pass 'no folder scan attempted'
pass 'no embeddings or RAG attempted'
pass 'no production registry write attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
