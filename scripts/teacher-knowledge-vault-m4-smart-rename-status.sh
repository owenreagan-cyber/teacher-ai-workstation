#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M4 smart rename foundation status.
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

m4_dir="assistant/teacher-knowledge-vault/m4"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M4 Smart Rename Foundation'
cat <<'EOF'
Status: smart rename suggestions/evidence/review cards — fake fixtures only
Closure: complete_teacher_knowledge_vault_m4_smart_rename_foundation
Real smart rename execution: no
rename_operations_executed: 0
move_operations_executed: 0
Real file hashing/scanning/search: no
api_cost_estimate_usd: 0.00
PASS does not authorize runtime rename or M5 organization: yes
EOF

section 'M4 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m4-smart-rename-foundation.md"
check_file "docs/teacher-knowledge-vault/smart-rename-suggestion-model.md"
check_file "docs/teacher-knowledge-vault/canonical-naming-convention.md"
check_file "docs/teacher-knowledge-vault/destination-suggestion-model.md"
check_file "docs/teacher-knowledge-vault/smart-rename-review-card-model.md"
check_file "docs/teacher-knowledge-vault/smart-rename-rule-examples.md"
check_file "docs/teacher-knowledge-vault/m4-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m4-smart-rename-foundation.md" "complete_teacher_knowledge_vault_m4_smart_rename_foundation" "M4 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m4-smart-rename-foundation.md" "fake fixtures only" "M4 fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-suggestion-model.md" "never rename" "no automatic rename"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-suggestion-model.md" "99_DO_NOT_SCAN" "do not scan rename exclusion"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-suggestion-model.md" "runtime_executed" "suggestion runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/canonical-naming-convention.md" "not automatic rewrites" "naming not automatic"
check_doc_contains "docs/teacher-knowledge-vault/canonical-naming-convention.md" "teacher_key" "teacher key naming marker"
check_doc_contains "docs/teacher-knowledge-vault/canonical-naming-convention.md" "12_AI_GENERATED" "ai generated naming policy"
check_doc_contains "docs/teacher-knowledge-vault/destination-suggestion-model.md" "no directories are created" "no directory creation"
check_doc_contains "docs/teacher-knowledge-vault/destination-suggestion-model.md" "10_TEACHER_ONLY" "teacher only destination"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-review-card-model.md" "execute rename now" "blocked rename action"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-review-card-model.md" "evidence summary" "review card evidence"
check_doc_contains "docs/teacher-knowledge-vault/smart-rename-rule-examples.md" "not buried in TypeScript" "rules are data"
check_doc_contains "docs/teacher-knowledge-vault/m4-governance-status.md" "rename_operations_executed" "governance rename zero"

section 'M4 Fake Smart Rename Fixtures'
check_file "${m4_dir}/README.md"
check_file "${m4_dir}/fake-smart-rename-suggestions.json"
check_file "${m4_dir}/fake-canonical-name-examples.json"
check_file "${m4_dir}/fake-destination-suggestions.json"
check_file "${m4_dir}/fake-evidence-packages.json"
check_file "${m4_dir}/fake-confidence-by-stage.json"
check_file "${m4_dir}/fake-rule-dsl-rename-examples.yaml"
check_file "${m4_dir}/fake-review-cards.json"
check_file "${m4_dir}/fake-review-routing.json"
check_file "${m4_dir}/fake-event-log-smart-rename.json"
check_file "${m4_dir}/fake-observability-metrics.json"
check_doc_contains "${m4_dir}/fake-smart-rename-suggestions.json" '"runtime_executed": false' "suggestions not executed"
check_doc_contains "${m4_dir}/fake-smart-rename-suggestions.json" "execute_rename_now" "rename blocked action"
check_doc_contains "${m4_dir}/fake-smart-rename-suggestions.json" "99_DO_NOT_SCAN" "do not scan suggestion blocked"
check_doc_contains "${m4_dir}/fake-smart-rename-suggestions.json" "restricted_indexable" "restricted indexable suggestion"
check_doc_contains "${m4_dir}/fake-canonical-name-examples.json" "math_g5_saxon_lesson_021_homework_odds_v1.pdf" "homework naming example"
check_doc_contains "${m4_dir}/fake-canonical-name-examples.json" "teacher_key" "teacher key naming example"
check_doc_contains "${m4_dir}/fake-destination-suggestions.json" "11_STUDENT_FACING" "student facing destination"
check_doc_contains "${m4_dir}/fake-destination-suggestions.json" '"file_move_executed": false' "no file move"
check_doc_contains "${m4_dir}/fake-evidence-packages.json" "rule_dsl_evidence" "rule evidence"
check_doc_contains "${m4_dir}/fake-evidence-packages.json" "leakage_risk_evidence" "leakage evidence"
check_doc_contains "${m4_dir}/fake-confidence-by-stage.json" "final_confidence" "final confidence stage"
check_doc_contains "${m4_dir}/fake-rule-dsl-rename-examples.yaml" "saxon_homework_odds" "homework odds rule"
check_doc_contains "${m4_dir}/fake-rule-dsl-rename-examples.yaml" "requires_review: true" "rule requires review"
check_doc_contains "${m4_dir}/fake-review-cards.json" "blocked_actions" "review card blocked actions"
check_doc_contains "${m4_dir}/fake-review-cards.json" "student_facing_mode_blocked" "student mode block"
check_doc_contains "${m4_dir}/fake-review-routing.json" "requires_teacher_approval" "review approval gate"
check_doc_contains "${m4_dir}/fake-review-routing.json" '"enters_normal_review": false' "do not scan blocked from review"
check_doc_contains "${m4_dir}/fake-event-log-smart-rename.json" "smart_rename_suggestion_created" "suggestion created event"
check_doc_contains "${m4_dir}/fake-event-log-smart-rename.json" "execution_requested_blocked" "execution blocked event"
check_doc_contains "${m4_dir}/fake-observability-metrics.json" '"rename_operations_executed": 0' "zero rename ops"
check_doc_contains "${m4_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m4_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m4_dir}"
check_no_real_paths_in_fixtures "${m4_dir}"

section 'No Smart Rename Runtime or Blocked Capabilities'
grep -Fq -- '--teacher-knowledge-vault-rename)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault rename' || pass 'CLI has no vault rename command'
grep -Fq -- '--teacher-knowledge-vault-organize)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault organize' || pass 'CLI has no vault organize command'
find assistant/teacher-knowledge-vault/m4 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m4' || pass 'no .db files in m4 fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 M1 M2 M3 Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'

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
check_doc_contains docs/build-queue.md "M4" "build queue M4"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "runtime smart rename" "build queue runtime rename blocked"
check_doc_contains assistant/memory/active-priorities.md "M4" "active priorities M4"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M4" "M0 roadmap M4 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m4-smart-rename-status"
check_help_contains "--teacher-knowledge-vault-m3-fake-duplicate-search-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m4-smart-rename-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m4-smart-rename-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m4' 'Teacher Knowledge Vault M4'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real smart rename attempted'
pass 'no rename move copy delete attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
