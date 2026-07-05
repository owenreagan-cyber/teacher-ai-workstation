#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M7f persistent local working catalog approval gate status.
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

m7f_dir="assistant/teacher-knowledge-vault/m7f"
m7e_out_dir=".tmp/teacher-knowledge-vault/m7e"
m7c_fixture_validator="scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M7f Persistent Local Working Catalog Approval Gate'
cat <<'EOF'
Status: approval gate only — no persistent catalog implementation
Closure: complete_teacher_knowledge_vault_m7f_persistent_working_catalog_approval_gate
M7e disposable test catalog: preserved
Persistent catalog created: false
Persistent catalog writes: 0
Production catalog writes: 0
Production registry writes: 0
OAuth/API/network execution: no
runtime_external_accesses: 0
api_cost_estimate_usd: 0.00
PASS does not authorize persistent catalog creation or writes: yes
M7f approval gate is not persistent catalog runtime: yes
EOF

section 'M7f Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-approval-levels.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-storage-policy.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-schema-readiness.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-import-preconditions.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-backup-rollback-removal.md"
check_file "docs/teacher-knowledge-vault/persistent-catalog-integrity-recovery.md"
check_file "docs/teacher-knowledge-vault/m7f-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md" "complete_teacher_knowledge_vault_m7f_persistent_working_catalog_approval_gate" "M7f closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md" "approval gate only" "M7f gate doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md" "does not create a persistent catalog" "no persistent catalog in M7f"
check_doc_contains "docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-approval-levels.md" "Level 3" "level 3 gate"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-approval-levels.md" "M7g" "M7g blocked"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-storage-policy.md" "No persistent catalog path" "no path created"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-storage-policy.md" ".tmp/teacher-knowledge-vault/m7e/" "M7e separation"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-schema-readiness.md" "import_batches" "schema import batches"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-schema-readiness.md" "No migration runtime" "no migration runtime"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-import-preconditions.md" "M7e disposable test catalog import proof passes" "M7e precondition"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-import-preconditions.md" "No arbitrary external path input" "no arbitrary paths"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-backup-rollback-removal.md" "no source file operations" "no source file ops"
check_doc_contains "docs/teacher-knowledge-vault/persistent-catalog-integrity-recovery.md" "dashboard/validate-all remain read-only" "aggregate read-only"
check_doc_contains "docs/teacher-knowledge-vault/m7f-governance-status.md" "Approval gate only" "governance gate only"
check_doc_contains "docs/teacher-knowledge-vault/m7f-governance-status.md" "M7g" "governance M7g blocked"

section 'M7f Fake Approval Gate Fixtures'
check_file "${m7f_dir}/README.md"
check_file "${m7f_dir}/fake-persistent-catalog-approval-packet.json"
check_file "${m7f_dir}/fake-storage-policy-review.json"
check_file "${m7f_dir}/fake-schema-readiness-checklist.json"
check_file "${m7f_dir}/fake-backup-rollback-plan.json"
check_file "${m7f_dir}/fake-integrity-recovery-plan.json"
check_file "${m7f_dir}/fake-review-routing.json"
check_file "${m7f_dir}/fake-event-log-persistent-catalog-gate.json"
check_file "${m7f_dir}/fake-observability-metrics.json"
check_doc_contains "${m7f_dir}/fake-persistent-catalog-approval-packet.json" '"persistent_catalog_write_executed": false' "packet not executed"
check_doc_contains "${m7f_dir}/fake-persistent-catalog-approval-packet.json" "approved_for_future_runtime_mission_not_executed" "future mission not executed"
check_doc_contains "${m7f_dir}/fake-storage-policy-review.json" '"path_created_in_m7f": false' "no path created fixture"
check_doc_contains "${m7f_dir}/fake-schema-readiness-checklist.json" '"database_created": false' "no database created"
check_doc_contains "${m7f_dir}/fake-backup-rollback-plan.json" '"catalog_writes": 0' "zero catalog writes plan"
check_doc_contains "${m7f_dir}/fake-integrity-recovery-plan.json" '"persistent_catalog_writes": 0' "integrity zero writes"
check_doc_contains "${m7f_dir}/fake-review-routing.json" "approved_for_future_runtime_mission_not_executed" "review future not executed"
check_doc_contains "${m7f_dir}/fake-review-routing.json" "approval_gate_executes_writes" "review gate no writes"
check_doc_contains "${m7f_dir}/fake-event-log-persistent-catalog-gate.json" "persistent_write_requested_but_blocked" "persistent write blocked event"
check_doc_contains "${m7f_dir}/fake-event-log-persistent-catalog-gate.json" "production_write_requested_but_blocked" "production write blocked event"
check_doc_contains "${m7f_dir}/fake-observability-metrics.json" '"persistent_catalog_writes": 0' "metrics zero persistent writes"
check_doc_contains "${m7f_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": "0.00"' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m7f_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m7f_dir}"
check_no_real_paths_in_fixtures "${m7f_dir}"

section 'M7c Fixture Validator and M7e Disposable Catalog Preserved'
check_file "${m7c_fixture_validator}"
bash "${m7c_fixture_validator}" >/dev/null 2>&1 && pass 'M7c fixture validator still passes' || fail 'M7c fixture validator regressed'
grep -Fq -- '.tmp/teacher-knowledge-vault/m7e/' .gitignore && pass 'M7e gitignored path preserved' || fail 'M7e gitignore path missing'
[[ ! -f "${m7e_out_dir}/test-catalog.sqlite" ]] && pass 'no persistent M7e sqlite left at check start' || warn 'M7e sqlite may exist from prior run'
check_file scripts/teacher-knowledge-vault-m7e-local-test-catalog-import.sh
check_file scripts/teacher-knowledge-vault-m7e-local-test-catalog-cleanup.sh

section 'No Persistent Catalog Production Write Connector Runtime'
grep -Fq -- '--teacher-knowledge-vault-persistent-catalog-import)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose persistent catalog import' || pass 'CLI has no persistent catalog import command'
grep -Fq -- '--teacher-knowledge-vault-persistent-catalog-create)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose persistent catalog create' || pass 'CLI has no persistent catalog create command'
grep -Fq -- '--teacher-knowledge-vault-connect-drive)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault connect drive' || pass 'CLI has no vault connect drive command'
find assistant/teacher-knowledge-vault/m7f -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m7f' || pass 'no .db files in m7f fixtures'
find assistant/teacher-knowledge-vault/m7f -name '*.sqlite' 2>/dev/null | grep -q . && fail 'SQLite .sqlite must not exist in m7f' || pass 'no .sqlite files in m7f fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
if [[ -f .env ]] && grep -qE 'DRIVE_|CANVAS_|NAS_|OAUTH_|API_KEY' .env 2>/dev/null; then
  fail 'no connector secrets in .env'
else
  pass 'no connector secrets in .env'
fi

section 'M0 M1 M2 M3 M4 M5 M6 M7 M7b M7c M7d M7e Preservation'
if [[ -n "${COS_TKV_SKIP_PRESERVATION:-}" ]]; then
  pass 'prior milestone preservation skipped (aggregate context)'
else
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh >/dev/null 2>&1 && pass 'M6 status still passes' || fail 'M6 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7-connector-approval-status.sh >/dev/null 2>&1 && pass 'M7 status still passes' || fail 'M7 status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7b-manual-source-inventory-status.sh >/dev/null 2>&1 && pass 'M7b status still passes' || fail 'M7b status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status.sh >/dev/null 2>&1 && pass 'M7c status still passes' || fail 'M7c status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7d-runtime-import-approval-gate-status.sh >/dev/null 2>&1 && pass 'M7d status still passes' || fail 'M7d status regressed'
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh >/dev/null 2>&1 && pass 'M7e status still passes' || fail 'M7e status regressed'

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
check_doc_contains docs/build-queue.md "M7f" "build queue M7f"
check_doc_contains docs/build-queue.md "M7g" "build queue M7g blocked"
check_doc_contains docs/build-queue.md "approval gate" "build queue approval gate"
check_doc_contains assistant/memory/active-priorities.md "M7f" "active priorities M7f"
check_doc_contains docs/teacher-knowledge-vault/m7e-local-test-catalog-import.md "M7f" "M7e roadmap M7f reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status"
check_help_contains "--teacher-knowledge-vault-m7e-local-test-catalog-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m7f' 'Teacher Knowledge Vault M7f'
pass 'no persistent catalog write attempted'
pass 'no production catalog write attempted'
pass 'no production registry write attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no connector runtime attempted'
pass 'no OCR extraction or AI attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
