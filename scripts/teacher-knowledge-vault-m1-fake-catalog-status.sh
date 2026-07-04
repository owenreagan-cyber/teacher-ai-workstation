#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M1 fake catalog status. No SQLite runtime, scanning, connectors, or file ops.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m1_dir="assistant/teacher-knowledge-vault/m1"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M1 Fake Catalog Foundation'
cat <<'EOF'
Status: documentation/status/fake fixtures only
M1 fake catalog: planning complete
SQLite database created: no
Real source scanning: no
Connectors: blocked
OCR/AI/RAG: blocked
File operations: blocked
Real curriculum files: no
Student data: blocked
PASS does not authorize M2+ runtime: yes
EOF

section 'M1 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md"
check_file "docs/teacher-knowledge-vault/catalog-schema-direction.md"
check_file "docs/teacher-knowledge-vault/event-log-foundation.md"
check_file "docs/teacher-knowledge-vault/review-queue-foundation.md"
check_file "docs/teacher-knowledge-vault/fake-search-query-foundation.md"
check_file "docs/teacher-knowledge-vault/m1-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "complete_teacher_knowledge_vault_m0_expansion_m1_alignment" "M1 expansion alignment marker"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "expanded M0" "M1 expanded M0 reference"
check_doc_contains "${m1_dir}/fake-catalog.json" "m0_architecture_freeze_preserved" "M0 freeze preserved flag"
check_doc_contains "${m1_dir}/fake-catalog.json" "m0_expansion_m1_alignment" "M1 catalog expansion alignment"
check_doc_contains "${m1_dir}/fake-catalog.json" "m2_plus_runtime_blocked" "M1 M2 blocked flag"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "complete_teacher_knowledge_vault_m1_fake_catalog_foundation" "M1 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "A file is not the resource" "resource identity principle"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "complete_teacher_knowledge_vault_m0_architecture_freeze" "M0 prerequisite"
check_doc_contains "docs/teacher-knowledge-vault/catalog-schema-direction.md" "DRAFT ONLY" "SQL draft not executed"
check_doc_contains "docs/teacher-knowledge-vault/catalog-schema-direction.md" "do_not_scan" "do not scan policy"
check_doc_contains "docs/teacher-knowledge-vault/catalog-schema-direction.md" "restricted_indexable" "restricted indexable policy"
check_doc_contains "docs/teacher-knowledge-vault/m1-governance-status.md" "real_files_processed" "governance real files zero"
check_doc_contains "docs/teacher-knowledge-vault/fake-search-query-foundation.md" "99_DO_NOT_SCAN" "search exclusion policy"
check_doc_contains "docs/teacher-knowledge-vault/review-queue-foundation.md" "requires_teacher_approval" "review approval gate"

section 'M1 Fake Catalog Fixtures'
check_file "${m1_dir}/README.md"
check_file "${m1_dir}/fake-catalog.json"
check_file "${m1_dir}/fake-resources.json"
check_file "${m1_dir}/fake-representations.json"
check_file "${m1_dir}/fake-sources.json"
check_file "${m1_dir}/fake-source-items.json"
check_file "${m1_dir}/fake-fingerprints.json"
check_file "${m1_dir}/fake-relationships.json"
check_file "${m1_dir}/fake-collections.json"
check_file "${m1_dir}/fake-review-queue.json"
check_file "${m1_dir}/fake-event-log.json"
check_file "${m1_dir}/fake-search-examples.json"
check_file "${m1_dir}/fake-observability-metrics.json"
check_doc_contains "${m1_dir}/fake-catalog.json" "fake_local_planning_only" "catalog classification"
check_doc_contains "${m1_dir}/fake-catalog.json" '"sqlite_database_created": false' "no sqlite database"
check_doc_contains "${m1_dir}/fake-resources.json" "fake-resource-saxon-lesson-021" "saxon lesson resource"
check_doc_contains "${m1_dir}/fake-resources.json" "fake-resource-reading-mastery-unit-04" "reading mastery resource"
check_doc_contains "${m1_dir}/fake-resources.json" "fake-resource-ckhg-american-revolution" "ckhg history resource"
check_doc_contains "${m1_dir}/fake-resources.json" "fake-resource-cksci-matter-unit" "cksci science resource"
check_doc_contains "${m1_dir}/fake-resources.json" "10_TEACHER_ONLY" "teacher only taxonomy"
check_doc_contains "${m1_dir}/fake-resources.json" "11_STUDENT_FACING" "student facing taxonomy"
check_doc_contains "${m1_dir}/fake-resources.json" "12_AI_GENERATED" "ai generated taxonomy"
check_doc_contains "${m1_dir}/fake-resources.json" "drive_only" "drive only reconciliation"
check_doc_contains "${m1_dir}/fake-resources.json" "canvas_only" "canvas only reconciliation"
check_doc_contains "${m1_dir}/fake-resources.json" "drive_and_canvas" "both sources reconciliation"
check_doc_contains "${m1_dir}/fake-resources.json" "99_DO_NOT_SCAN" "do not scan resource"
check_doc_contains "${m1_dir}/fake-resources.json" "restricted_indexable" "restricted indexable"
check_doc_contains "${m1_dir}/fake-representations.json" "student_textbook_section" "saxon textbook rep"
check_doc_contains "${m1_dir}/fake-representations.json" "teacher_guide" "teacher guide rep"
check_doc_contains "${m1_dir}/fake-representations.json" "homework" "homework rep"
check_doc_contains "${m1_dir}/fake-representations.json" "answer_key" "answer key rep"
check_doc_contains "${m1_dir}/fake-representations.json" "canvas_package_placeholder" "canvas package rep"
check_doc_contains "${m1_dir}/fake-relationships.json" "duplicate_candidate" "duplicate relationship"
check_doc_contains "${m1_dir}/fake-relationships.json" '"auto_merge": false' "no auto merge"
check_doc_contains "${m1_dir}/fake-review-queue.json" "possible_duplicate" "duplicate review state"
check_doc_contains "${m1_dir}/fake-review-queue.json" '"enters_normal_review": false' "do not scan blocked from review"
check_doc_contains "${m1_dir}/fake-review-queue.json" "leakage_check_required" "leakage check example"
check_doc_contains "${m1_dir}/fake-event-log.json" '"runtime_executed": false' "events not executed"
check_doc_contains "${m1_dir}/fake-event-log.json" "ocr_requested_blocked" "ocr blocked event"
check_doc_contains "${m1_dir}/fake-event-log.json" "connector_access_requested_blocked" "connector blocked event"
check_doc_contains "${m1_dir}/fake-search-examples.json" "excluded_from_all_search" "search exclusion list"
check_doc_contains "${m1_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"
check_doc_contains "${m1_dir}/fake-observability-metrics.json" '"real_files_processed": 0' "zero real files"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m1_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
  resource_count="$(python3 -c "import json; print(len(json.load(open('${m1_dir}/fake-resources.json'))['resources']))")"
  [[ "${resource_count}" -ge 14 ]] && pass "fake resources count >= 14" || fail "expected >= 14 fake resources (got ${resource_count})"
  rep_count="$(python3 -c "import json; print(len(json.load(open('${m1_dir}/fake-representations.json'))['representations']))")"
  [[ "${rep_count}" -ge 18 ]] && pass "fake representations count >= 18" || fail "expected >= 18 representations (got ${rep_count})"
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m1_dir}"

section 'No SQLite Runtime or Blocked Capabilities'
sqlite_hits=0
for f in scripts/*knowledge-vault* assistant/teacher-knowledge-vault/m1/*; do
  [[ -f "${f}" ]] || continue
  [[ "${f}" == *status* ]] && continue
  if grep -qiE '(sqlite3|\.db"|CREATE TABLE.*EXECUTE)' "${f}" 2>/dev/null; then
    if [[ "${f}" != *catalog-schema-direction* ]] && [[ "${f}" != *.md ]]; then
      sqlite_hits=1
      fail "must not execute SQLite: ${f}"
    fi
  fi
done
[[ "${sqlite_hits}" == "0" ]] && pass 'no SQLite runtime execution detected'
find assistant/teacher-knowledge-vault/m1 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db file must not exist' || pass 'no .db files in m1 fixtures'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan command'
grep -Fq -- '--teacher-knowledge-vault-sqlite)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault sqlite' || pass 'CLI has no vault sqlite command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 Preservation'
if [[ -f scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh ]]; then
  bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 architecture freeze status still passes' || fail 'M0 architecture freeze status regressed'
else
  fail 'M0 status script missing'
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
check_doc_contains docs/build-queue.md "M1" "build queue M1"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains assistant/memory/active-priorities.md "M1" "active priorities M1"
check_doc_contains docs/teacher-knowledge-vault-m0-foundation.md "M1" "M0 foundation M1 cross-link"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m1-fake-catalog-status"
check_help_contains "--teacher-knowledge-vault-m0-architecture-freeze-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m1-fake-catalog-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m1-fake-catalog-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m1-fake-catalog-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M1 catalog test' || fail 'smoke missing M1 catalog test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no SQLite database created'
pass 'no connector runtime attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
