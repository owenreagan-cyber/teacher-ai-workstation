#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M0 expanded architecture freeze status.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

m0_freeze="docs/teacher-knowledge-vault/m0-architecture-freeze.md"
foundation_doc="docs/teacher-knowledge-vault-m0-foundation.md"
samples_dir="assistant/teacher-knowledge-vault/samples"
adr_dir="docs/adr/teacher-knowledge-vault"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M0 Expanded Architecture Freeze'
cat <<'EOF'
Status: documentation/status/fake fixtures only
M0 expanded architecture freeze: active
Expansion alignment: complete_teacher_knowledge_vault_m0_expansion_m1_alignment
M1 fake catalog: aligned — not runtime permission
SQLite runtime: no
Connectors/scanning/OCR/AI: blocked
Student data: blocked
PASS does not authorize M2+ runtime: yes
EOF

section 'M0 Freeze and Anti-Drift Doctrine'
check_file "${m0_freeze}"
check_file "${foundation_doc}"
check_doc_contains "${m0_freeze}" "complete_teacher_knowledge_vault_m0_architecture_freeze" "M0 closure marker"
check_doc_contains "${m0_freeze}" "complete_teacher_knowledge_vault_m0_expansion_m1_alignment" "expansion alignment marker"
check_doc_contains "${m0_freeze}" "not file storage" "intelligence layer doctrine"
check_doc_contains "${m0_freeze}" "Future changes require ADRs" "anti-drift ADR rule"
check_doc_contains "${m0_freeze}" "Fake fixtures do not authorize" "M1 not M2 permission"
check_doc_contains "${foundation_doc}" "complete_teacher_knowledge_vault_m1_fake_catalog_foundation" "M1 closure cross-link"

section 'Expanded M0 Architecture Documents'
for doc in \
  v1-architecture-spec.md \
  canonical-storage-and-taxonomy.md \
  connector-sdk-contract.md \
  resource-identity-model.md \
  fingerprinting-model.md \
  classification-rule-dsl.md \
  human-review-workspace.md \
  observability-and-metrics.md \
  qa-gates.md \
  plugin-extension-points.md \
  document-understanding-pipeline.md \
  smart-rename-policy.md \
  evidence-package-and-confidence-model.md \
  restricted-indexing-and-pacing-guardrails.md \
  source-reconciliation-model.md \
  airplay-classroom-runtime-requirements.md \
  architecture-freeze-plan.md \
  blocked-runtime-boundaries.md \
  event-log-foundation.md \
  intake-to-vault-approval-gate.md; do
  check_file "docs/teacher-knowledge-vault/${doc}"
done
check_doc_contains "docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md" "12_AI_GENERATED" "AI generated taxonomy"
check_doc_contains "docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md" "10_TEACHER_ONLY" "teacher only taxonomy"
check_doc_contains "docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md" "99_DO_NOT_SCAN" "do not scan taxonomy"
check_doc_contains "docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md" "not 09_TEACHER_ONLY" "stale taxonomy correction"
check_doc_contains "docs/teacher-knowledge-vault/restricted-indexing-and-pacing-guardrails.md" "restricted-indexable" "restricted indexable policy"
check_doc_contains "docs/teacher-knowledge-vault/restricted-indexing-and-pacing-guardrails.md" "not non-indexable" "teacher-only not non-indexable correction"
check_doc_contains "docs/teacher-knowledge-vault/resource-identity-model.md" "not the resource" "file is not resource"
check_doc_contains "docs/teacher-knowledge-vault/connector-sdk-contract.md" "discover()" "connector discover method"
check_doc_contains "docs/teacher-knowledge-vault/connector-sdk-contract.md" "not connector implementations" "M1 not connectors"

section 'ADR Set (0001-0010)'
check_file "${adr_dir}/README.md"
for n in 0001 0002 0003 0004 0005 0006 0007 0008 0009 0010; do
  adr_file="${adr_dir}/${n}-"*.md
  found=0
  for f in ${adr_file}; do
    [[ -f "${f}" ]] || continue
    found=1
    pass "ADR exists: ${f}"
    grep -Fq -- 'Blocked runtime' "${f}" && pass "ADR ${n} blocked runtime section" || fail "ADR ${n} must mention Blocked runtime"
    grep -Fq -- 'Validation hooks' "${f}" && pass "ADR ${n} validation hooks" || fail "ADR ${n} must mention Validation hooks"
  done
  [[ "${found}" == "1" ]] || fail "ADR missing: ${n}"
done

section 'M0 Sample Fixtures'
check_file "${samples_dir}/README.md"
for fixture in \
  fake-connector-capabilities.json \
  fake-source-item.json \
  fake-resource-identity.json \
  fake-representation-source-map.json \
  fake-fingerprint-set.json \
  fake-classification-rule.yaml \
  fake-observability-metrics.json \
  fake-evidence-package.json \
  fake-smart-rename-suggestion.json \
  fake-source-reconciliation-record.json \
  fake-taxonomy-target.json \
  fake-intake-promotion-record.json; do
  check_file "${samples_dir}/${fixture}"
done
check_doc_contains "${samples_dir}/fake-connector-capabilities.json" '"connector_status": "blocked"' "connector blocked"
check_doc_contains "${samples_dir}/fake-resource-identity.json" "not the resource" "resource identity principle"
check_doc_contains "${samples_dir}/fake-taxonomy-target.json" "10_TEACHER_ONLY" "taxonomy teacher only"
check_doc_contains "${samples_dir}/fake-classification-rule.yaml" "requires_review: true" "rule requires review"
check_doc_contains "${samples_dir}/fake-smart-rename-suggestion.json" '"runtime_executed": false' "rename not executed"
check_doc_contains "${samples_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${samples_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON parse checks'
fi
if grep -rqiE 'https?://' "${samples_dir}" --include='*.json' 2>/dev/null; then
  fail 'M0 sample JSON fixtures must not contain URLs'
else
  pass 'M0 sample JSON fixtures exclude URLs'
fi

section 'Knowledge Entry v0 (PR #253 Preserved)'
check_file "assistant/teacher-knowledge-vault/v0/knowledge-entry-schema.json"
check_file "scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh"
bash scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh >/dev/null 2>&1 && pass "knowledge entry v0 validator exits 0" || fail "knowledge entry v0 validator failed"

section 'M1 Alignment (Expanded M0)'
check_file "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md"
check_file "assistant/teacher-knowledge-vault/m1/fake-catalog.json"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "A file is not the resource" "M1 resource principle"
check_doc_contains "docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md" "complete_teacher_knowledge_vault_m0_expansion_m1_alignment" "M1 expansion alignment marker"
check_doc_contains "assistant/teacher-knowledge-vault/m1/fake-catalog.json" "m0_expansion_m1_alignment" "M1 catalog expansion alignment"
check_doc_contains "assistant/teacher-knowledge-vault/m1/fake-catalog.json" "m2_plus_runtime_blocked" "M1 M2 blocked flag"
check_doc_contains "assistant/teacher-knowledge-vault/m1/fake-event-log.json" '"runtime_executed": false' "M1 events not executed"
check_file "assistant/teacher-knowledge-vault/m1/fake-resources.json"
check_file "assistant/teacher-knowledge-vault/m1/fake-representations.json"
pass 'M1 alignment verified inline (M1 status independently verifies M0 preservation)'

section 'Blocked Runtime Guards'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault scan' || pass 'CLI has no vault scan'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'
[[ -d assistant/memory/knowledge ]] && fail 'assistant/memory/knowledge must not exist' || pass 'memory knowledge path not populated'

section 'Roadmap Cross-Links'
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "M1" "build queue M1"
check_doc_contains assistant/memory/active-priorities.md "M0 expansion" "active priorities M0 expansion"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m0-architecture-freeze-status"
check_help_contains "--teacher-knowledge-vault-m1-fake-catalog-status"
check_file tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m0' 'Teacher Knowledge Vault M0'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no connector runtime attempted'
pass 'no knowledge directory population attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
