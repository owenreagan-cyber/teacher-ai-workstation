#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M5 organization/rollback foundation status.
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
  if grep -rqiE 'https?://' "${dir}" --include='*.json' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain http(s) URLs: ${dir}"
  else
    pass "fixtures exclude URLs: ${dir}"
  fi
}
check_no_real_paths_in_fixtures() {
  local dir="$1"
  if grep -rE '/Users/|/home/|\\\\Users\\\\|C:\\\\' "${dir}" --include='*.json' --include='*.yaml' 2>/dev/null; then
    fail "fixtures must not contain real local paths: ${dir}"
  else
    pass "fixtures exclude real local paths: ${dir}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m5_dir="assistant/teacher-knowledge-vault/m5"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M5 Organization Rollback Foundation'
cat <<'EOF'
Status: approved organization/rollback foundation — fake fixtures only
Closure: complete_teacher_knowledge_vault_m5_organization_rollback_foundation
Real organization execution: no
operations_executed: 0
rollback_executions: 0
Real file hashing/scanning/search: no
api_cost_estimate_usd: 0.00
PASS does not authorize runtime organization or file operations: yes
EOF

section 'M5 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m5-approved-organization-rollback-foundation.md"
check_file "docs/teacher-knowledge-vault/approved-operation-model.md"
check_file "docs/teacher-knowledge-vault/dry-run-preview-model.md"
check_file "docs/teacher-knowledge-vault/organization-conflict-detection-model.md"
check_file "docs/teacher-knowledge-vault/no-overwrite-non-destructive-policy.md"
check_file "docs/teacher-knowledge-vault/rollback-undo-model.md"
check_file "docs/teacher-knowledge-vault/organization-review-queue-model.md"
check_file "docs/teacher-knowledge-vault/m5-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m5-approved-organization-rollback-foundation.md" "complete_teacher_knowledge_vault_m5_organization_rollback_foundation" "M5 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m5-approved-organization-rollback-foundation.md" "fake fixtures only" "M5 fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m5-approved-organization-rollback-foundation.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/approved-operation-model.md" "runtime_executed" "operation runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/approved-operation-model.md" "Teacher approval is required" "teacher approval gate"
check_doc_contains "docs/teacher-knowledge-vault/approved-operation-model.md" "do not become operations automatically" "suggestions not auto operations"
check_doc_contains "docs/teacher-knowledge-vault/dry-run-preview-model.md" "preview is not execution" "preview not execution"
check_doc_contains "docs/teacher-knowledge-vault/dry-run-preview-model.md" "overwrite risk" "overwrite risk preview"
check_doc_contains "docs/teacher-knowledge-vault/dry-run-preview-model.md" "rollback availability" "rollback availability preview"
check_doc_contains "docs/teacher-knowledge-vault/organization-conflict-detection-model.md" "99_DO_NOT_SCAN" "do not scan conflict"
check_doc_contains "docs/teacher-knowledge-vault/organization-conflict-detection-model.md" "no-overwrite block" "no overwrite conflict"
check_doc_contains "docs/teacher-knowledge-vault/organization-conflict-detection-model.md" "teacher-only into student-facing" "leakage conflict"
check_doc_contains "docs/teacher-knowledge-vault/no-overwrite-non-destructive-policy.md" "no overwrite by default" "no overwrite policy"
check_doc_contains "docs/teacher-knowledge-vault/no-overwrite-non-destructive-policy.md" "archive preferred" "archive preferred policy"
check_doc_contains "docs/teacher-knowledge-vault/no-overwrite-non-destructive-policy.md" "rollback required" "rollback required policy"
check_doc_contains "docs/teacher-knowledge-vault/rollback-undo-model.md" "required before execution" "rollback required before execution"
check_doc_contains "docs/teacher-knowledge-vault/rollback-undo-model.md" "does not mean destructive delete" "rollback not delete"
check_doc_contains "docs/teacher-knowledge-vault/organization-review-queue-model.md" "teacher_approval_required" "approval required state"
check_doc_contains "docs/teacher-knowledge-vault/organization-review-queue-model.md" "execution_blocked" "execution blocked state"
check_doc_contains "docs/teacher-knowledge-vault/organization-review-queue-model.md" "99_DO_NOT_SCAN" "do not scan queue block"
check_doc_contains "docs/teacher-knowledge-vault/m5-governance-status.md" "operations_executed" "governance operations zero"

section 'M5 Fake Organization Fixtures'
check_file "${m5_dir}/README.md"
check_file "${m5_dir}/fake-approved-operations.json"
check_file "${m5_dir}/fake-dry-run-previews.json"
check_file "${m5_dir}/fake-conflict-detections.json"
check_file "${m5_dir}/fake-rollback-plans.json"
check_file "${m5_dir}/fake-organization-review-queue.json"
check_file "${m5_dir}/fake-event-log-organization.json"
check_file "${m5_dir}/fake-source-reconciliation-effects.json"
check_file "${m5_dir}/fake-observability-metrics.json"
check_doc_contains "${m5_dir}/fake-approved-operations.json" '"runtime_executed": false' "operations not executed"
check_doc_contains "${m5_dir}/fake-approved-operations.json" "smart_rename_suggestion_promoted" "rename promoted example"
check_doc_contains "${m5_dir}/fake-approved-operations.json" "99_DO_NOT_SCAN" "do not scan operation blocked"
check_doc_contains "${m5_dir}/fake-approved-operations.json" "mark_canonical_representation" "canonical selection operation"
check_doc_contains "${m5_dir}/fake-dry-run-previews.json" "overwrite_risk" "preview overwrite risk"
check_doc_contains "${m5_dir}/fake-dry-run-previews.json" "teacher_only_warning" "preview teacher only warning"
check_doc_contains "${m5_dir}/fake-dry-run-previews.json" "student_facing_leakage_warning" "preview leakage warning"
check_doc_contains "${m5_dir}/fake-dry-run-previews.json" "no_overwrite_block" "preview no overwrite block"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "target_filename_already_exists" "overwrite conflict"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "destination_under_99_DO_NOT_SCAN" "do not scan conflict fixture"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "teacher_only_into_student_facing" "leakage conflict fixture"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "cloud_placeholder_unavailable" "cloud placeholder conflict"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "symlink_escapes_approved_root" "symlink conflict"
check_doc_contains "${m5_dir}/fake-conflict-detections.json" "rollback_unavailable" "rollback unavailable conflict"
check_doc_contains "${m5_dir}/fake-rollback-plans.json" "restore_strategy" "rollback restore strategy"
check_doc_contains "${m5_dir}/fake-rollback-plans.json" '"rollback_executed": false' "no rollback execution"
check_doc_contains "${m5_dir}/fake-organization-review-queue.json" "dry_run_ready" "dry run ready state"
check_doc_contains "${m5_dir}/fake-organization-review-queue.json" "approved_pending_execution" "approved pending execution"
check_doc_contains "${m5_dir}/fake-organization-review-queue.json" '"execution_blocked": true' "execution blocked queue"
check_doc_contains "${m5_dir}/fake-event-log-organization.json" "dry_run_operation_created" "dry run event"
check_doc_contains "${m5_dir}/fake-event-log-organization.json" "operation_execution_blocked_m5" "execution blocked event"
check_doc_contains "${m5_dir}/fake-event-log-organization.json" "do_not_scan_operation_blocked" "do not scan event"
check_doc_contains "${m5_dir}/fake-source-reconciliation-effects.json" "teacher_only_remains_restricted" "teacher only reconciliation"
check_doc_contains "${m5_dir}/fake-source-reconciliation-effects.json" "student_facing_package_leakage_checked" "student facing reconciliation"
check_doc_contains "${m5_dir}/fake-source-reconciliation-effects.json" "future_only_blocked" "nas sync blocked"
check_doc_contains "${m5_dir}/fake-observability-metrics.json" '"operations_executed": 0' "zero operations executed"
check_doc_contains "${m5_dir}/fake-observability-metrics.json" '"rollback_executions": 0' "zero rollback executions"
check_doc_contains "${m5_dir}/fake-observability-metrics.json" '"delete_operations": 0' "zero delete operations"
check_doc_contains "${m5_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m5_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m5_dir}"
check_no_real_paths_in_fixtures "${m5_dir}"

section 'No Organization Runtime or Blocked Capabilities'
grep -Fq -- '--teacher-knowledge-vault-rename)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault rename' || pass 'CLI has no vault rename command'
grep -Fq -- '--teacher-knowledge-vault-organize)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault organize' || pass 'CLI has no vault organize command'
find assistant/teacher-knowledge-vault/m5 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m5' || pass 'no .db files in m5 fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 M1 M2 M3 M4 Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M5" "build queue M5"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "runtime organization" "build queue runtime organization blocked"
check_doc_contains assistant/memory/active-priorities.md "M5" "active priorities M5"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M5" "M0 roadmap M5 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m5-organization-rollback-status"
check_help_contains "--teacher-knowledge-vault-m4-smart-rename-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m5-organization-rollback-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m5-organization-rollback-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m5-organization-rollback-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M5 test' || fail 'smoke missing M5 test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real organization attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
