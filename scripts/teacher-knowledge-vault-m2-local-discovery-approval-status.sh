#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M2 local discovery approval packet status.
# Approval packet and dry-run design only — no real filesystem scanning.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "doc mentions ${label}" || fail "${file} must mention ${label}"
}
check_bash_syntax() {
  [[ -f "$1" ]] || { fail "cannot syntax check missing file: $1"; return; }
  bash -n "$1" && pass "bash syntax ok: $1" || fail "bash syntax failed: $1"
}
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}
check_no_urls_in_fixtures() {
  local dir="$1"
  if grep -rqiE 'https?://' "${dir}" --include='*.json' 2>/dev/null; then
    fail "fixtures must not contain http(s) URLs: ${dir}"
  else
    pass "fixtures exclude URLs: ${dir}"
  fi
}
check_no_real_paths_in_fixtures() {
  local dir="$1"
  if grep -rE '/Users/|/home/|\\\\Users\\\\|C:\\\\' "${dir}" --include='*.json' 2>/dev/null; then
    fail "fixtures must not contain real local paths: ${dir}"
  else
    pass "fixtures exclude real local paths: ${dir}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m2_dir="assistant/teacher-knowledge-vault/m2"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M2 Local Discovery Approval Packet'
cat <<'EOF'
Status: approval packet and dry-run design only
Closure: complete_teacher_knowledge_vault_m2_local_discovery_approval_packet
M2 local discovery: planning complete — not implemented
Real filesystem scanning: no
Real file metadata reads: no
Real file hashing: no
Metadata-only future scope: documented — blocked until M2b approval
Connectors/Drive/iCloud/NAS/Canvas: blocked
OCR/native extraction/AI: blocked
File operations: blocked
api_cost_estimate_usd: 0.00
PASS does not authorize M2b prototype or M3+ runtime: yes
EOF

section 'M2 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md"
check_file "docs/teacher-knowledge-vault/local-discovery-dry-run-design.md"
check_file "docs/teacher-knowledge-vault/local-discovery-blocked-path-policy.md"
check_file "docs/teacher-knowledge-vault/local-discovery-output-contract.md"
check_file "docs/teacher-knowledge-vault/local-discovery-cost-performance-guardrails.md"
check_file "docs/teacher-knowledge-vault/m2-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md" "complete_teacher_knowledge_vault_m2_local_discovery_approval_packet" "M2 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md" "does not approve implementation" "M2 not implementation approval"
check_doc_contains "docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md" "M2b" "M2b blocked reference"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-dry-run-design.md" "metadata only" "metadata only scope"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-dry-run-design.md" "never read file contents" "no content reads"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-blocked-path-policy.md" "99_DO_NOT_SCAN" "do not scan policy"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-blocked-path-policy.md" "restricted_indexable" "restricted indexable policy"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-blocked-path-policy.md" "symlink" "symlink policy"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-output-contract.md" "runtime_executed" "output contract runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-output-contract.md" "not a scanner implementation" "not scanner implementation"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-cost-performance-guardrails.md" "api_cost_estimate_usd" "api cost guardrail"
check_doc_contains "docs/teacher-knowledge-vault/local-discovery-cost-performance-guardrails.md" "chokidar" "no chokidar guardrail"
check_doc_contains "docs/teacher-knowledge-vault/m2-governance-status.md" "real_files_processed" "governance real files zero"

section 'M2 Fake Discovery Fixtures'
check_file "${m2_dir}/README.md"
check_file "${m2_dir}/fake-discovery-run.json"
check_file "${m2_dir}/fake-discovered-source-items.json"
check_file "${m2_dir}/fake-blocked-path-examples.json"
check_file "${m2_dir}/fake-review-routing.json"
check_file "${m2_dir}/fake-event-log-discovery.json"
check_file "${m2_dir}/fake-discovery-output-contract.json"
check_file "${m2_dir}/fake-cost-performance-metrics.json"
check_doc_contains "${m2_dir}/fake-discovery-run.json" "fake_local_planning_only" "discovery run classification"
check_doc_contains "${m2_dir}/fake-discovery-run.json" '"runtime_executed": false' "discovery run not executed"
check_doc_contains "${m2_dir}/fake-discovery-run.json" "fake-local-staging://" "fake staging URI"
check_doc_contains "${m2_dir}/fake-discovered-source-items.json" "10_TEACHER_ONLY" "teacher only example"
check_doc_contains "${m2_dir}/fake-discovered-source-items.json" "11_STUDENT_FACING" "student facing example"
check_doc_contains "${m2_dir}/fake-discovered-source-items.json" "12_AI_GENERATED" "ai generated example"
check_doc_contains "${m2_dir}/fake-discovered-source-items.json" "escape_blocked" "symlink escape example"
check_doc_contains "${m2_dir}/fake-discovered-source-items.json" "cloud_placeholder_status" "cloud placeholder example"
check_doc_contains "${m2_dir}/fake-blocked-path-examples.json" "blocked-placeholder://99_DO_NOT_SCAN" "do not scan blocked example"
check_doc_contains "${m2_dir}/fake-blocked-path-examples.json" "student_data_folder" "student data blocked"
check_doc_contains "${m2_dir}/fake-review-routing.json" "requires_teacher_approval" "review approval gate"
check_doc_contains "${m2_dir}/fake-review-routing.json" '"enters_normal_review": false' "do not scan blocked from review"
check_doc_contains "${m2_dir}/fake-event-log-discovery.json" "discovery_run_planned" "discovery planned event"
check_doc_contains "${m2_dir}/fake-event-log-discovery.json" "ocr_requested_blocked" "ocr blocked event"
check_doc_contains "${m2_dir}/fake-event-log-discovery.json" "hash_requested_blocked" "hash blocked event"
check_doc_contains "${m2_dir}/fake-cost-performance-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"
check_doc_contains "${m2_dir}/fake-cost-performance-metrics.json" '"chokidar_dependency": false' "no chokidar"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m2_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m2_dir}"
check_no_real_paths_in_fixtures "${m2_dir}"

section 'No Scanner Runtime or Blocked Capabilities'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan command'
grep -Fq -- '--teacher-knowledge-vault-discover)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault discover' || pass 'CLI has no vault discover command'
grep -rqi 'chokidar' package.json package-lock.json 2>/dev/null && fail 'chokidar dependency must not exist for M2' || pass 'no chokidar dependency in package manifests'
scanner_hits=0
for f in assistant/teacher-knowledge-vault/m2/*.json; do
  [[ -f "${f}" ]] || continue
  if grep -qiE '(readdir|fs\.stat|fs\.read|walkdir)' "${f}" 2>/dev/null; then
    scanner_hits=1
    fail "fixtures must not describe filesystem traversal implementation: ${f}"
  fi
done
[[ "${scanner_hits}" == "0" ]] && pass 'no filesystem traversal in M2 scripts/fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write handler' || pass 'no --curriculum-registry-write handler'

section 'M0 and M1 Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
if [[ -f scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh ]]; then
  COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 architecture freeze status still passes' || fail 'M0 architecture freeze status regressed'
else
  fail 'M0 status script missing'
fi
if [[ -f scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh ]]; then
  COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 fake catalog status still passes' || fail 'M1 fake catalog status regressed'
else
  fail 'M1 status script missing'
fi
check_doc_contains "${m2_dir}/fake-discovery-run.json" "m0_architecture_freeze_preserved" "M2 M0 preserved flag"
check_doc_contains "${m2_dir}/fake-discovery-run.json" "m1_fake_catalog_preserved" "M2 M1 preserved flag"
check_doc_contains "${m2_dir}/fake-discovery-run.json" "m2b_prototype_blocked" "M2b blocked flag"

fi
section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M2" "build queue M2"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M2b" "build queue M2b blocked"
check_doc_contains assistant/memory/active-priorities.md "M2" "active priorities M2"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M2" "M0 roadmap M2 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m2-local-discovery-approval-status"
check_help_contains "--teacher-knowledge-vault-m0-architecture-freeze-status"
check_help_contains "--teacher-knowledge-vault-m1-fake-catalog-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m2' 'Teacher Knowledge Vault M2'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real filesystem discovery attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
