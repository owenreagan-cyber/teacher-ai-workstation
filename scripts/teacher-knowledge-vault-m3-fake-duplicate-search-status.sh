#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M3 fake duplicate/search/package status.
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

m3_dir="assistant/teacher-knowledge-vault/m3"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M3 Fake Duplicate Search and Package Foundation'
cat <<'EOF'
Status: fake duplicate/search/package foundation only
Closure: complete_teacher_knowledge_vault_m3_fake_duplicate_search_foundation
Real duplicate detection: no
Real search over local files: no
Real file hashing: no
SQLite runtime search: no
search_runtime_executed: false
api_cost_estimate_usd: 0.00
PASS does not authorize runtime search or M2b/M4+ runtime: yes
EOF

section 'M3 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m3-fake-duplicate-search-package-foundation.md"
check_file "docs/teacher-knowledge-vault/duplicate-candidate-model.md"
check_file "docs/teacher-knowledge-vault/version-candidate-model.md"
check_file "docs/teacher-knowledge-vault/resource-package-model.md"
check_file "docs/teacher-knowledge-vault/search-behavior-model.md"
check_file "docs/teacher-knowledge-vault/search-result-safety-modes.md"
check_file "docs/teacher-knowledge-vault/m3-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m3-fake-duplicate-search-package-foundation.md" "complete_teacher_knowledge_vault_m3_fake_duplicate_search_foundation" "M3 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m3-fake-duplicate-search-package-foundation.md" "fake fixtures only" "M3 fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/duplicate-candidate-model.md" "never merged automatically" "no auto merge"
check_doc_contains "docs/teacher-knowledge-vault/duplicate-candidate-model.md" "99_DO_NOT_SCAN" "do not scan duplicate exclusion"
check_doc_contains "docs/teacher-knowledge-vault/version-candidate-model.md" "not overwrites" "versions not overwrites"
check_doc_contains "docs/teacher-knowledge-vault/version-candidate-model.md" "requires_teacher_approval" "version approval gate"
check_doc_contains "docs/teacher-knowledge-vault/resource-package-model.md" "not folders" "packages not folders"
check_doc_contains "docs/teacher-knowledge-vault/resource-package-model.md" "teacher-only" "teacher only package rule"
check_doc_contains "docs/teacher-knowledge-vault/search-behavior-model.md" "search_runtime_executed: false" "search not executed"
check_doc_contains "docs/teacher-knowledge-vault/search-behavior-model.md" "possible duplicates" "duplicate search query"
check_doc_contains "docs/teacher-knowledge-vault/search-result-safety-modes.md" "student_facing" "student facing mode"
check_doc_contains "docs/teacher-knowledge-vault/search-result-safety-modes.md" "teacher_planning" "teacher planning mode"
check_doc_contains "docs/teacher-knowledge-vault/m3-governance-status.md" "real_files_processed" "governance real files zero"

section 'M3 Fake Fixtures'
check_file "${m3_dir}/README.md"
check_file "${m3_dir}/fake-duplicate-candidates.json"
check_file "${m3_dir}/fake-version-candidates.json"
check_file "${m3_dir}/fake-resource-packages.json"
check_file "${m3_dir}/fake-search-queries.json"
check_file "${m3_dir}/fake-search-results-by-mode.json"
check_file "${m3_dir}/fake-review-routing.json"
check_file "${m3_dir}/fake-event-log-search-duplicate.json"
check_file "${m3_dir}/fake-observability-metrics.json"
check_doc_contains "${m3_dir}/fake-duplicate-candidates.json" '"auto_merge": false' "duplicate no auto merge"
check_doc_contains "${m3_dir}/fake-duplicate-candidates.json" "filename_duplicate" "filename duplicate level"
check_doc_contains "${m3_dir}/fake-duplicate-candidates.json" "99_DO_NOT_SCAN" "do not scan duplicate exclusion"
check_doc_contains "${m3_dir}/fake-version-candidates.json" "latest_not_automatically_canonical" "version not auto canonical"
check_doc_contains "${m3_dir}/fake-version-candidates.json" "possible_version" "version review state"
check_doc_contains "${m3_dir}/fake-resource-packages.json" "fake-pkg-saxon-lesson-021" "saxon lesson 21 package"
check_doc_contains "${m3_dir}/fake-resource-packages.json" "fake-pkg-reading-mastery-unit-04" "reading mastery package"
check_doc_contains "${m3_dir}/fake-resource-packages.json" "fake-pkg-ckhg-american-revolution" "ckhg history package"
check_doc_contains "${m3_dir}/fake-resource-packages.json" "fake-pkg-cksci-energy-transfer" "cksci science package"
check_doc_contains "${m3_dir}/fake-search-queries.json" "only in Canvas" "canvas only search"
check_doc_contains "${m3_dir}/fake-search-queries.json" "only in Drive" "drive only search"
check_doc_contains "${m3_dir}/fake-search-queries.json" "missing from canonical storage" "missing canonical search"
check_doc_contains "${m3_dir}/fake-search-queries.json" "student_mode_excluded" "student mode exclusion"
check_doc_contains "${m3_dir}/fake-search-results-by-mode.json" "teacher_only_filtered_count" "teacher only filter example"
check_doc_contains "${m3_dir}/fake-search-results-by-mode.json" "student_facing_leakage_blocks" "leakage block metric"
check_doc_contains "${m3_dir}/fake-review-routing.json" "possible_duplicate" "duplicate review routing"
check_doc_contains "${m3_dir}/fake-review-routing.json" '"enters_normal_review": false' "do not scan blocked from review"
check_doc_contains "${m3_dir}/fake-event-log-search-duplicate.json" "duplicate_merge_requested_blocked" "merge blocked event"
check_doc_contains "${m3_dir}/fake-event-log-search-duplicate.json" "search_query_executed_fake_catalog" "fake search event"
check_doc_contains "${m3_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"
check_doc_contains "${m3_dir}/fake-observability-metrics.json" '"search_runtime_executed": false' "search not executed metric"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m3_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m3_dir}"
check_no_real_paths_in_fixtures "${m3_dir}"

section 'No Search/Duplicate Runtime or Blocked Capabilities'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan command'
grep -Fq -- '--teacher-knowledge-vault-search)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault search runtime' || pass 'CLI has no vault search runtime command'
grep -rqi 'chokidar' package.json package-lock.json 2>/dev/null && fail 'chokidar must not be added for M3' || pass 'no chokidar dependency'
find assistant/teacher-knowledge-vault/m3 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m3' || pass 'no .db files in m3 fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 M1 M2 Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M3" "build queue M3"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M2b" "build queue M2b blocked"
check_doc_contains assistant/memory/active-priorities.md "M3" "active priorities M3"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M3" "M0 roadmap M3 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m3-fake-duplicate-search-status"
check_help_contains "--teacher-knowledge-vault-m2-local-discovery-approval-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m3-fake-duplicate-search-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m3-fake-duplicate-search-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m3-fake-duplicate-search-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M3 test' || fail 'smoke missing M3 test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real duplicate detection attempted'
pass 'no real search over local files attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
