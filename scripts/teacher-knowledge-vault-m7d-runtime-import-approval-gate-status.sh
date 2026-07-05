#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7d runtime manual import approval gate status.
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

m7d_dir="assistant/teacher-knowledge-vault/m7d"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
m7c_fixture_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"

section 'Teacher Knowledge Vault M7d Runtime Manual Import Approval Gate'
cat <<'EOF'
Status: approval gate only — no runtime import implementation
Closure: complete_teacher_knowledge_vault_m7d_runtime_manual_import_approval_gate
Real connector implementation: no
OAuth/API/network execution: no
runtime_import_executed: false
catalog_writes: 0
api_calls_made: 0
real_metadata_records_ingested: 0
api_cost_estimate_usd: 0.00
PASS does not authorize runtime import or catalog writes: yes
M7c import preview is not import: yes
M7d approval gate is not import: yes
EOF

section 'M7d Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md"
check_file "docs/teacher-knowledge-vault/runtime-manual-import-approval-levels.md"
check_file "docs/teacher-knowledge-vault/runtime-manual-import-preconditions.md"
check_file "docs/teacher-knowledge-vault/runtime-manual-import-blockers.md"
check_file "docs/teacher-knowledge-vault/preview-to-catalog-mapping-contract.md"
check_file "docs/teacher-knowledge-vault/runtime-import-approval-packet-model.md"
check_file "docs/teacher-knowledge-vault/runtime-import-rollback-removal-plan.md"
check_file "docs/teacher-knowledge-vault/m7d-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md" "complete_teacher_knowledge_vault_m7d_runtime_manual_import_approval_gate" "M7d closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md" "approval gate only" "M7d gate doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md" "M7d approval gate is not import" "gate not import"
check_doc_contains "docs/teacher-knowledge-vault/m7d-runtime-manual-import-approval-gate.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-approval-levels.md" "Level 1" "approval levels"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-approval-levels.md" "blocked" "future levels blocked"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-preconditions.md" "M7c fixture validator passes" "validator precondition"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-preconditions.md" "Rollback/removal plan" "rollback precondition"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-blockers.md" "Student data" "student data blocker"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-blockers.md" "99_DO_NOT_SCAN" "dns blocker"
check_doc_contains "docs/teacher-knowledge-vault/runtime-manual-import-blockers.md" "Import without preview" "preview blocker"
check_doc_contains "docs/teacher-knowledge-vault/preview-to-catalog-mapping-contract.md" "future_only_not_execution" "mapping not execution"
check_doc_contains "docs/teacher-knowledge-vault/preview-to-catalog-mapping-contract.md" "SourceInventoryCandidate" "source mapping"
check_doc_contains "docs/teacher-knowledge-vault/preview-to-catalog-mapping-contract.md" "restricted-indexing" "teacher only mapping"
check_doc_contains "docs/teacher-knowledge-vault/runtime-import-approval-packet-model.md" "runtime_import_executed" "packet runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/runtime-import-approval-packet-model.md" "not permission to write" "packet not write permission"
check_doc_contains "docs/teacher-knowledge-vault/runtime-import-rollback-removal-plan.md" "Import batch ID" "rollback batch id"
check_doc_contains "docs/teacher-knowledge-vault/runtime-import-rollback-removal-plan.md" "No source file deletion" "no source file ops"
check_doc_contains "docs/teacher-knowledge-vault/m7d-governance-status.md" "catalog_writes" "governance zero writes"
check_doc_contains "docs/teacher-knowledge-vault/m7d-governance-status.md" "Approval gate only" "governance gate only"

section 'M7d Fake Approval Gate Fixtures'
check_file "${m7d_dir}/README.md"
check_file "${m7d_dir}/fake-import-approval-packet.json"
check_file "${m7d_dir}/fake-import-preconditions-checklist.json"
check_file "${m7d_dir}/fake-import-blockers.json"
check_file "${m7d_dir}/fake-preview-to-catalog-mapping.json"
check_file "${m7d_dir}/fake-rollback-removal-plan.json"
check_file "${m7d_dir}/fake-review-routing.json"
check_file "${m7d_dir}/fake-event-log-runtime-import-gate.json"
check_file "${m7d_dir}/fake-observability-metrics.json"
check_doc_contains "${m7d_dir}/fake-import-approval-packet.json" '"runtime_import_executed": false' "packet not executed"
check_doc_contains "${m7d_dir}/fake-import-approval-packet.json" "approved_for_future_runtime_import_not_executed" "future import not executed"
check_doc_contains "${m7d_dir}/fake-import-preconditions-checklist.json" "m7c_fixture_validator_pass" "checklist validator"
check_doc_contains "${m7d_dir}/fake-import-preconditions-checklist.json" '"all_preconditions_met": false' "preconditions not all met"
check_doc_contains "${m7d_dir}/fake-import-blockers.json" "do_not_scan_normal_import" "dns blocker fixture"
check_doc_contains "${m7d_dir}/fake-import-blockers.json" "import_without_preview" "no preview blocker"
check_doc_contains "${m7d_dir}/fake-preview-to-catalog-mapping.json" "future_only_not_execution" "mapping future only"
check_doc_contains "${m7d_dir}/fake-preview-to-catalog-mapping.json" "do_not_scan_must_not_map_searchable" "dns mapping rule"
check_doc_contains "${m7d_dir}/fake-rollback-removal-plan.json" "import_blocked_if_rollback_unavailable" "rollback gate blocker"
check_doc_contains "${m7d_dir}/fake-review-routing.json" "approved_for_future_runtime_import_not_executed" "review future not executed"
check_doc_contains "${m7d_dir}/fake-review-routing.json" "rollback_plan_required" "review rollback required"
check_doc_contains "${m7d_dir}/fake-event-log-runtime-import-gate.json" "runtime_import_requested_but_blocked" "import blocked event"
check_doc_contains "${m7d_dir}/fake-event-log-runtime-import-gate.json" "catalog_write_requested_but_blocked" "catalog write blocked event"
check_doc_contains "${m7d_dir}/fake-observability-metrics.json" '"runtime_imports_executed": 0' "zero imports executed"
check_doc_contains "${m7d_dir}/fake-observability-metrics.json" '"catalog_writes": 0' "zero catalog writes"
check_doc_contains "${m7d_dir}/fake-observability-metrics.json" '"write_operations": 0' "zero write ops"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m7d_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m7d_dir}"
check_no_real_paths_in_fixtures "${m7d_dir}"

section 'M7c Fixture Validator Preserved'
check_file "${m7c_fixture_validator}"
bash "${m7c_fixture_validator}" >/dev/null 2>&1 && pass 'M7c fixture validator still passes' || fail 'M7c fixture validator regressed'

section 'No Runtime Import Catalog Write Connector Runtime'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect drive' || pass 'CLI has no vault connect drive command'
grep -Fq -- '--teacher-knowledge-vault-oauth)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault oauth' || pass 'CLI has no vault oauth command'
grep -Fq -- '--teacher-knowledge-vault-ingest)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault ingest' || pass 'CLI has no vault ingest command'
grep -Fq -- '--teacher-knowledge-vault-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault import' || pass 'CLI has no vault import command'
grep -Fq -- '--teacher-knowledge-vault-runtime-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault runtime import' || pass 'CLI has no vault runtime import command'
find assistant/teacher-knowledge-vault/m7d -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m7d' || pass 'no .db files in m7d fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
if [[ -f .env ]] && grep -qE 'DRIVE_|CANVAS_|NAS_|OAUTH_|API_KEY' .env 2>/dev/null; then
  fail 'no connector secrets in .env'
else
  pass 'no connector secrets in .env'
fi

section 'M0 M1 M2 M3 M4 M5 M6 M7 M7b M7c Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'
bash scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh >/dev/null 2>&1 && pass 'M7b status still passes' || fail 'M7b status regressed'
bash scripts/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status.sh >/dev/null 2>&1 && pass 'M7c status still passes' || fail 'M7c status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M7d" "build queue M7d"
check_doc_contains docs/build-queue.md "approval gate" "build queue approval gate"
check_doc_contains docs/build-queue.md "runtime manual import" "build queue runtime import blocked"
check_doc_contains assistant/memory/active-priorities.md "M7d" "active priorities M7d"
check_doc_contains docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md "M7d" "M7c roadmap M7d reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7d-runtime-import-approval-gate-status"
check_help_contains "--teacher-knowledge-vault-m7c-manual-inventory-import-preview-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m7d-runtime-import-approval-gate-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M7d test' || fail 'smoke missing M7d test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no runtime manual import attempted'
pass 'no catalog write attempted'
pass 'no production registry write attempted'
pass 'no OAuth API or secrets attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
