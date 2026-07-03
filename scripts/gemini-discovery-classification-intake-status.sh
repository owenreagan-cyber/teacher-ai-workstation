#!/usr/bin/env bash
# Read-only Gemini discovery/classification external planning intake status. Classification only — no runtime.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} must mention ${label}"; return; }
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

intake_doc="docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md"
blocked_doc="docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md"
intake_map="docs/proposals/ideas/external-planning-input-intake-map.md"
summary_fixture="assistant/external-planning/intake/gemini-discovery-classification-architecture-summary.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Gemini Discovery & Classification Intake (External Planning Only)'
cat <<'EOF'
Status: external_planning_reference_only
Runtime discovery/classification: no
Full Gemini memo text in repo: no
Student data: blocked — absolute
Integrations: no
AI classification of real curriculum: no
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Canonical Intake Docs'
check_file "${intake_doc}"
check_file "${blocked_doc}"
check_file "${intake_map}"
check_doc_contains "${intake_doc}" "complete_gemini_discovery_classification_intake" "intake closure marker"
check_doc_contains "${intake_doc}" "not repo authority" "non-authority banner"
check_doc_contains "${intake_doc}" "Three-level discovery governance" "three-level discovery cross-link"
check_doc_contains "${intake_doc}" "safe-local-document-indexing-plan" "document indexing cross-link"
check_doc_contains "${blocked_doc}" "Embeddings / vector database / RAG" "embeddings blocked"
check_doc_contains "${intake_map}" "gemini-discovery-classification-architecture-intake" "intake map cross-link"

section 'Summary Fixture (Metadata Only)'
check_file "${summary_fixture}"
check_file assistant/external-planning/intake/README.md
check_doc_contains "${summary_fixture}" "external_planning_intake_summary_only" "fixture classification"
check_doc_contains "${summary_fixture}" '"repo_authority": false' "repo authority false"
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${summary_fixture}" >/dev/null 2>&1 && pass "JSON parses: ${summary_fixture}" || fail "JSON does not parse: ${summary_fixture}"
else
  warn 'python3 not available for JSON parse checks'
fi

section 'No Runtime Discovery/Classification Scripts'
runtime_hits=0
for pattern in '*discovery-orchestrator*' '*classification-engine*' '*gemini-api*' '*auto-classif*'; do
  for candidate in scripts/${pattern}; do
    [[ -e "${candidate}" ]] || continue
    [[ "${candidate}" == *intake-status* ]] && continue
    runtime_hits=1
    fail "runtime discovery/classification script must not exist: ${candidate}"
  done
done
[[ "${runtime_hits}" == "0" ]] && pass 'no discovery/classification runtime scripts in scripts/'
grep -Fq -- '--gemini-discovery-run)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose gemini discovery run command' || pass 'CLI has no gemini discovery run command'
grep -Fq -- '--discovery-orchestrator)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose discovery orchestrator command' || pass 'CLI has no discovery orchestrator command'
grep -Fq -- '--classification-engine)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose classification engine command' || pass 'CLI has no classification engine command'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Coherence Cross-Links'
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "complete_gemini_discovery_classification_intake" "whole-system report gemini intake closure"
check_doc_contains docs/proposals/index.md "Gemini discovery/classification architecture intake" "proposal ledger gemini intake"
check_doc_contains docs/build-queue.md "Gemini discovery/classification" "build queue gemini intake"
check_doc_contains assistant/memory/active-priorities.md "Gemini discovery/classification" "active priorities gemini intake"

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--gemini-discovery-classification-intake-status' bin/chief-of-staff && pass 'CLI exposes --gemini-discovery-classification-intake-status' || fail 'CLI missing --gemini-discovery-classification-intake-status'
grep -Fq -- '"--gemini-discovery-classification-intake-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --gemini-discovery-classification-intake-status' || fail 'manifest missing --gemini-discovery-classification-intake-status'
check_file tests/gemini-discovery-classification-intake-status-test.sh
bash -n tests/gemini-discovery-classification-intake-status-test.sh && pass 'bash syntax ok: gemini intake test' || fail 'bash syntax failed: gemini intake test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no runtime discovery execution attempted'
pass 'no runtime classification execution attempted'
pass 'no student data ingestion attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
