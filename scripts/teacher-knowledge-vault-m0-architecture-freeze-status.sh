#!/usr/bin/env bash
# Read-only Teacher Knowledge Vault M0 architecture freeze status. No scanning, network calls, vault writes, or auto-load.
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

foundation_doc="docs/teacher-knowledge-vault-m0-foundation.md"
architecture_plan="docs/teacher-knowledge-vault/architecture-freeze-plan.md"
folder_taxonomy="docs/teacher-knowledge-vault/folder-taxonomy.md"
intake_gate="docs/teacher-knowledge-vault/intake-to-vault-approval-gate.md"
manual_entry="docs/teacher-knowledge-vault/manual-entry-plan.md"
boundary_doc="docs/teacher-knowledge-vault/blocked-runtime-boundaries.md"
fake_promotion="assistant/teacher-knowledge-vault/samples/fake-intake-promotion-record.json"
fake_outline="assistant/teacher-knowledge-vault/samples/fake-knowledge-entry-outline.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
knowledge_dir="assistant/memory/knowledge"

section 'Teacher Knowledge Vault M0 Architecture Freeze'
cat <<'EOF'
Status: documentation/status/fake fixtures only
M0 architecture freeze: planning complete
Real knowledge files on disk: no
assistant/memory/knowledge/ population: blocked — future Owen mission
Auto-loading memory: no
Folder scanning: no
Indexing/OCR/embeddings: no
APIs/network: no
Student data: blocked — absolute
PASS does not populate knowledge files: yes
EOF

section 'Foundation Documentation (M0 Closure)'
check_file "${foundation_doc}"
check_file "${architecture_plan}"
check_file "${folder_taxonomy}"
check_file "${intake_gate}"
check_file "${manual_entry}"
check_file "${boundary_doc}"
check_doc_contains "${foundation_doc}" "automatic memory loading" "auto-loading boundary"
check_doc_contains "${foundation_doc}" "--teacher-knowledge-vault-m0-architecture-freeze-status" "M0 status command"
check_doc_contains "${foundation_doc}" "complete_teacher_knowledge_vault_m0_architecture_freeze" "M0 closure marker"
check_doc_contains "${architecture_plan}" "complete_teacher_knowledge_vault_m0_architecture_freeze" "architecture plan closure marker"
check_doc_contains "${architecture_plan}" "Knowledge directory population: blocked" "knowledge directory population blocked"
check_doc_contains "${folder_taxonomy}" "Real knowledge files on disk: no" "taxonomy no real files banner"
check_doc_contains "${intake_gate}" "Automatic intake promotion: blocked" "intake promotion blocked"
check_doc_contains "${manual_entry}" "Automatic entry creation: blocked" "manual entry blocked"
check_doc_contains "${boundary_doc}" "Auto-loading" "auto-loading blocked"
check_doc_contains "${boundary_doc}" "Student data" "student data blocked"

section 'Fake Local Planning Fixtures'
check_file "assistant/teacher-knowledge-vault/samples/README.md"
check_file "${fake_promotion}"
check_file "${fake_outline}"
check_doc_contains "${fake_promotion}" "fake_local_planning_only" "promotion fixture classification"
check_doc_contains "${fake_promotion}" '"vault_promotion_approved": false' "promotion fixture vault blocked"
check_doc_contains "${fake_promotion}" '"runtime_approved": false' "promotion fixture runtime blocked"
check_doc_contains "${fake_outline}" "fake_local_planning_only" "outline fixture classification"
check_doc_contains "${fake_outline}" "not a real vault file" "outline not real file banner"

if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${fake_promotion}" >/dev/null 2>&1 && pass "JSON parses: ${fake_promotion}" || fail "JSON does not parse: ${fake_promotion}"
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Knowledge Entry Schema v0'
check_file "assistant/teacher-knowledge-vault/v0/knowledge-entry-schema.json"
check_file "assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json"
check_file "assistant/teacher-knowledge-vault/v0/README.md"
check_file "scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh"
check_bash_syntax "scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh"
bash scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh >/dev/null 2>&1 && pass "knowledge entry v0 validator exits 0" || fail "knowledge entry v0 validator failed"

if command -v python3 >/dev/null 2>&1; then
  for f in assistant/teacher-knowledge-vault/v0/knowledge-entry-schema.json assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for v0 JSON parse checks'
fi

section 'No Knowledge Directory Population or Auto-Load Scripts'
[[ -d "${knowledge_dir}" ]] && fail "knowledge directory must not exist in M0: ${knowledge_dir}" || pass 'assistant/memory/knowledge/ not populated'
vault_script_hits=0
for candidate in scripts/*knowledge-vault*; do
  [[ -e "${candidate}" ]] || continue
  [[ "${candidate}" == *architecture-freeze-status* ]] && continue
  [[ "${candidate}" == *knowledge-entry-v0-validator* ]] && continue
  if grep -Eq '(mkdir|tee|cat >|>>.*assistant/memory/knowledge)' "${candidate}" 2>/dev/null; then
    vault_script_hits=1
    fail "knowledge vault script must not populate knowledge directory: ${candidate}"
  fi
done
[[ "${vault_script_hits}" == "0" ]] && pass 'no knowledge vault population scripts detected'
grep -Fq -- '--teacher-knowledge-vault-populate)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose knowledge vault populate command' || pass 'CLI has no knowledge vault populate command'
grep -Fq -- '--teacher-knowledge-vault-auto-load)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose knowledge vault auto-load command' || pass 'CLI has no knowledge vault auto-load command'
grep -Fq -- '--teacher-knowledge-vault-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose knowledge vault scan command' || pass 'CLI has no knowledge vault scan command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'

section 'Memory and Intake Cross-Links'
check_doc_contains "assistant/memory-policy.md" "Knowledge Vault" "memory policy knowledge vault row"
check_doc_contains "assistant/memory-policy.md" "assistant/memory/knowledge/" "memory policy knowledge path"
check_doc_contains "assistant/intake/intake-policy.md" "assistant/memory/knowledge/" "intake policy knowledge vault path"

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "Knowledge Vault" "build queue knowledge vault"
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "teacher-knowledge-vault" "whole-system report knowledge vault"
check_doc_contains assistant/memory/active-priorities.md "Knowledge Vault" "active priorities knowledge vault"

section 'Chief of Staff Integration'
check_help_contains "--teacher-knowledge-vault-m0-architecture-freeze-status"
check_help_contains "--teacher-knowledge-vault-knowledge-entry-v0-validate"
check_bash_syntax "bin/chief-of-staff"
check_file tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
check_bash_syntax tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
grep -Fq -- 'teacher-knowledge-vault-m0-architecture-freeze-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires knowledge vault M0 test' || fail 'smoke missing knowledge vault M0 test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no knowledge directory population attempted'
pass 'no auto-load attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
