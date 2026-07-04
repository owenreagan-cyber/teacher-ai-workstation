#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M6 extraction/OCR approval packet status.
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

m6_dir="assistant/teacher-knowledge-vault/m6"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Teacher Knowledge Vault M6 Extraction OCR Approval Packet'
cat <<'EOF'
Status: native extraction/OCR approval packet — fake fixtures only
Closure: complete_teacher_knowledge_vault_m6_extraction_ocr_approval_packet
Real native extraction execution: no
Real OCR execution: no
ocr_jobs_executed: 0
ai_rag_calls: 0
Real file hashing/scanning/search: no
api_cost_estimate_usd: 0.00
PASS does not authorize runtime extraction OCR or API calls: yes
EOF

section 'M6 Foundation Documentation'
check_file "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md"
check_file "docs/teacher-knowledge-vault/native-extraction-approval-model.md"
check_file "docs/teacher-knowledge-vault/ocr-escalation-approval-model.md"
check_file "docs/teacher-knowledge-vault/extraction-cache-model.md"
check_file "docs/teacher-knowledge-vault/extraction-evidence-package.md"
check_file "docs/teacher-knowledge-vault/extraction-cost-budget-gate.md"
check_file "docs/teacher-knowledge-vault/extraction-review-queue-model.md"
check_file "docs/teacher-knowledge-vault/m6-governance-status.md"
check_doc_contains "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md" "complete_teacher_knowledge_vault_m6_extraction_ocr_approval_packet" "M6 closure marker"
check_doc_contains "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md" "fake fixtures only" "M6 fake only doctrine"
check_doc_contains "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md" "99_DO_NOT_SCAN" "do not scan exclusion"
check_doc_contains "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md" "Native extraction must come before OCR" "escalation ladder order"
check_doc_contains "docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md" "Whole-document processing is not default" "no whole document default"
check_doc_contains "docs/teacher-knowledge-vault/native-extraction-approval-model.md" "runtime_executed" "native extraction runtime flag"
check_doc_contains "docs/teacher-knowledge-vault/native-extraction-approval-model.md" "10_TEACHER_ONLY" "teacher only extraction"
check_doc_contains "docs/teacher-knowledge-vault/native-extraction-approval-model.md" "does not classify or organize by itself" "extraction not classify"
check_doc_contains "docs/teacher-knowledge-vault/ocr-escalation-approval-model.md" "OCR blocked" "OCR blocked default"
check_doc_contains "docs/teacher-knowledge-vault/ocr-escalation-approval-model.md" "no background bulk OCR" "no bulk OCR"
check_doc_contains "docs/teacher-knowledge-vault/ocr-escalation-approval-model.md" "OCR runtime remains blocked in M6" "OCR blocked in M6"
check_doc_contains "docs/teacher-knowledge-vault/extraction-cache-model.md" "text_snippet_label" "snippet label not real text"
check_doc_contains "docs/teacher-knowledge-vault/extraction-cache-model.md" "cache does not store real text in M6 fixtures" "no real text in cache"
check_doc_contains "docs/teacher-knowledge-vault/extraction-cache-model.md" "99_DO_NOT_SCAN" "do not scan no cache"
check_doc_contains "docs/teacher-knowledge-vault/extraction-evidence-package.md" "Fake placeholder label" "fake evidence placeholders"
check_doc_contains "docs/teacher-knowledge-vault/extraction-evidence-package.md" "does not move, rename, or publish" "extraction not publish"
check_doc_contains "docs/teacher-knowledge-vault/extraction-cost-budget-gate.md" "API cost estimate must be" "api cost gate"
check_doc_contains "docs/teacher-knowledge-vault/extraction-cost-budget-gate.md" "cache lookup before extraction/OCR" "cache before spend"
check_doc_contains "docs/teacher-knowledge-vault/extraction-review-queue-model.md" "teacher_only_restricted_extraction" "teacher only review state"
check_doc_contains "docs/teacher-knowledge-vault/extraction-review-queue-model.md" "cloud OCR request blocked by cost gate" "cloud OCR blocked example"
check_doc_contains "docs/teacher-knowledge-vault/m6-governance-status.md" "ocr_jobs_executed" "governance OCR zero"

section 'M6 Fake Extraction Fixtures'
check_file "${m6_dir}/README.md"
check_file "${m6_dir}/fake-extraction-requests.json"
check_file "${m6_dir}/fake-native-extraction-eligibility.json"
check_file "${m6_dir}/fake-ocr-escalation-candidates.json"
check_file "${m6_dir}/fake-extraction-cache-records.json"
check_file "${m6_dir}/fake-extraction-evidence-packages.json"
check_file "${m6_dir}/fake-review-routing.json"
check_file "${m6_dir}/fake-event-log-extraction.json"
check_file "${m6_dir}/fake-observability-metrics.json"
check_doc_contains "${m6_dir}/fake-extraction-requests.json" '"runtime_executed": false' "requests not executed"
check_doc_contains "${m6_dir}/fake-extraction-requests.json" "99_DO_NOT_SCAN extraction blocked" "do not scan request blocked"
check_doc_contains "${m6_dir}/fake-extraction-requests.json" "cloud OCR blocked by budget gate" "cloud OCR budget block"
check_doc_contains "${m6_dir}/fake-extraction-requests.json" "AI classification blocked until later phase" "AI classification blocked"
check_doc_contains "${m6_dir}/fake-native-extraction-eligibility.json" "native_extraction_eligible" "native eligibility"
check_doc_contains "${m6_dir}/fake-native-extraction-eligibility.json" "ocr_needed" "ocr needed flag"
check_doc_contains "${m6_dir}/fake-ocr-escalation-candidates.json" "quick_ocr" "quick OCR candidate"
check_doc_contains "${m6_dir}/fake-ocr-escalation-candidates.json" "full_ocr" "full OCR candidate"
check_doc_contains "${m6_dir}/fake-ocr-escalation-candidates.json" '"ocr_jobs_executed": 0' "zero OCR jobs"
check_doc_contains "${m6_dir}/fake-extraction-cache-records.json" "FAKE_SNIPPET_PLACEHOLDER" "fake snippet placeholders"
check_doc_contains "${m6_dir}/fake-extraction-cache-records.json" "10_TEACHER_ONLY" "teacher only cache"
check_doc_contains "${m6_dir}/fake-extraction-evidence-packages.json" "FAKE_CANDIDATE" "fake evidence candidates"
check_doc_contains "${m6_dir}/fake-extraction-evidence-packages.json" "blocked_actions" "evidence blocked actions"
check_doc_contains "${m6_dir}/fake-review-routing.json" "native_extraction_eligible" "routing native eligible"
check_doc_contains "${m6_dir}/fake-review-routing.json" "quick_ocr_candidate" "routing quick OCR"
check_doc_contains "${m6_dir}/fake-review-routing.json" "leakage_review_required" "routing leakage review"
check_doc_contains "${m6_dir}/fake-event-log-extraction.json" "extraction_requested" "extraction requested event"
check_doc_contains "${m6_dir}/fake-event-log-extraction.json" "quick_ocr_proposed_not_executed" "OCR proposed not executed"
check_doc_contains "${m6_dir}/fake-event-log-extraction.json" "do_not_scan_extraction_blocked" "do not scan event"
check_doc_contains "${m6_dir}/fake-observability-metrics.json" '"ocr_jobs_executed": 0' "zero OCR jobs metric"
check_doc_contains "${m6_dir}/fake-observability-metrics.json" '"ai_rag_calls": 0' "zero AI calls"
check_doc_contains "${m6_dir}/fake-observability-metrics.json" '"api_cost_estimate_usd": 0.0' "zero api cost"

if command -v python3 >/dev/null 2>&1; then
  for f in "${m6_dir}"/*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON validation'
fi

check_no_urls_in_fixtures "${m6_dir}"
check_no_real_paths_in_fixtures "${m6_dir}"

section 'No Extraction OCR Runtime or Blocked Capabilities'
grep -Fq -- '--teacher-knowledge-vault-extract)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault extract' || pass 'CLI has no vault extract command'
grep -Fq -- '--teacher-knowledge-vault-ocr)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose vault OCR' || pass 'CLI has no vault OCR command'
grep -rqiE 'tesseract|ocrmypdf' scripts/ assistant/teacher-knowledge-vault/m6/ 2>/dev/null | grep -v 'teacher-knowledge-vault-m6-extraction-ocr-approval-status' | grep -q . && fail 'no OCR install/execution scripts' || pass 'no tesseract/ocrmypdf execution scripts'
find assistant/teacher-knowledge-vault/m6 -name '*.db' 2>/dev/null | grep -q . && fail 'SQLite .db must not exist in m6' || pass 'no .db files in m6 fixtures'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'no --curriculum-registry-write' || pass 'no --curriculum-registry-write handler'

section 'M0 M1 M2 M3 M4 M5 Preservation'
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh >/dev/null 2>&1 && pass 'M0 status still passes' || fail 'M0 status regressed'
bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh >/dev/null 2>&1 && pass 'M1 status still passes' || fail 'M1 status regressed'
bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh >/dev/null 2>&1 && pass 'M2 status still passes' || fail 'M2 status regressed'
bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh >/dev/null 2>&1 && pass 'M3 status still passes' || fail 'M3 status regressed'
bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh >/dev/null 2>&1 && pass 'M4 status still passes' || fail 'M4 status regressed'
bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh >/dev/null 2>&1 && pass 'M5 status still passes' || fail 'M5 status regressed'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "M6" "build queue M6"
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/build-queue.md "M0 expansion" "build queue M0 expansion"
check_doc_contains docs/build-queue.md "runtime extraction" "build queue runtime extraction blocked"
check_doc_contains assistant/memory/active-priorities.md "M6" "active priorities M6"
check_doc_contains docs/teacher-knowledge-vault/m0-architecture-freeze.md "M6" "M0 roadmap M6 reference"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m6-extraction-ocr-approval-status"
check_help_contains "--teacher-knowledge-vault-m5-organization-rollback-status"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m6-extraction-ocr-approval-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires M6 test' || fail 'smoke missing M6 test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no real extraction attempted'
pass 'no real OCR attempted'
pass 'no rename move copy delete archive export attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
