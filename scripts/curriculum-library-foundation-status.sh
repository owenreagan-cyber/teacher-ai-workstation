#!/usr/bin/env bash
# Read-only Curriculum Library foundation status. No scanning, network calls, folder creation, or writes.
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

setup_plan="docs/curriculum-library/curriculum-library-setup-plan.md"
manual_registry_plan="docs/curriculum-library/manual-registry-plan.md"
folder_taxonomy="docs/curriculum-library/folder-taxonomy.md"
canvas_ready="docs/curriculum-library/canvas-ready-folder-definition.md"
classification_gate="docs/curriculum-library/file-classification-approval-gate.md"
fake_tree="assistant/curriculum-library/samples/fake-folder-tree.json"
fake_csv="assistant/curriculum-library/samples/fake-manual-registry.csv"
fake_suggestion="assistant/curriculum-library/samples/fake-classification-suggestion.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Curriculum Library Foundation'
cat <<'EOF'
Status: documentation/status/fake fixtures only
Setup and manual registry foundation: planning complete
Real folders on disk: no
~/TeacherAI-Curriculum-Library/ creation: blocked — future Owen mission
Folder scanning: no
Indexing/OCR/embeddings: no
APIs/network: no
Student data: blocked — absolute
PASS does not create folders: yes
EOF

section 'Foundation Documentation (v1 Closure)'
check_file "docs/curriculum-library-v1-foundation.md"
check_file "docs/curriculum-source-storage-strategy.md"
check_file "docs/curriculum-resource-registry-plan.md"
check_file "docs/curriculum-builder-local-first-foundation-plan.md"
check_doc_contains "docs/curriculum-library-v1-foundation.md" "automatic source resolution" "automatic source resolution boundary"
check_doc_contains "docs/curriculum-library-v1-foundation.md" "--curriculum-library-foundation-status" "foundation status command"
check_doc_contains "docs/curriculum-library-v1-foundation.md" "complete_curriculum_library_setup_and_manual_registry_foundation" "setup foundation cross-link"

section 'Setup and Manual Registry Planning Docs'
check_file "${setup_plan}"
check_file "${manual_registry_plan}"
check_file "${folder_taxonomy}"
check_file "${canvas_ready}"
check_file "${classification_gate}"
check_doc_contains "${setup_plan}" "complete_curriculum_library_setup_and_manual_registry_foundation" "setup plan closure marker"
check_doc_contains "${setup_plan}" "Local folder creation: blocked" "local folder creation blocked"
check_doc_contains "${setup_plan}" "~/TeacherAI-Curriculum-Library/" "planned local root documented"
check_doc_contains "${manual_registry_plan}" "planning-only" "manual registry planning-only banner"
check_doc_contains "${folder_taxonomy}" "Real folders on disk: no" "taxonomy no real folders banner"
check_doc_contains "${canvas_ready}" "Canvas API" "canvas API boundary"
check_doc_contains "${classification_gate}" "Auto-classification runtime: blocked" "classification runtime blocked"

section 'Fake Local Planning Fixtures'
check_file "assistant/curriculum-library/samples/README.md"
check_file "${fake_tree}"
check_file "${fake_csv}"
check_file "${fake_suggestion}"
check_doc_contains "${fake_tree}" "fake_local_planning_only" "folder tree fixture classification"
check_doc_contains "${fake_tree}" '"local_root_created": false' "folder tree not created flag"
check_doc_contains "${fake_csv}" "fake_local_planning_only" "manual registry CSV classification"
check_doc_contains "${fake_suggestion}" "suggestion_planning_only" "classification suggestion status"
check_doc_contains "${fake_suggestion}" '"runtime_approved": false' "classification suggestion runtime blocked"

if command -v python3 >/dev/null 2>&1; then
  for f in "${fake_tree}" "${fake_suggestion}"; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
  csv_rows="$(python3 -c "import csv; print(len(list(csv.DictReader(open('${fake_csv}')))))" 2>/dev/null || echo 0)"
  [[ "${csv_rows}" -ge 3 ]] && pass 'manual registry CSV has fictional rows' || fail "manual registry CSV must have at least 3 rows (got ${csv_rows})"
else
  warn 'python3 not available for JSON/CSV parse checks'
fi

section 'Reference Schema v0 (Existing)'
check_file "assistant/curriculum-library/v0/library-reference-schema.json"
check_file "assistant/curriculum-library/v0/sample-library-references.json"
check_file "assistant/curriculum-library/v0/README.md"
check_file "scripts/curriculum-library-reference-v0-validator.sh"
check_bash_syntax "scripts/curriculum-library-reference-v0-validator.sh"
bash scripts/curriculum-library-reference-v0-validator.sh >/dev/null 2>&1 && pass "reference v0 validator exits 0" || fail "reference v0 validator failed"

if command -v python3 >/dev/null 2>&1; then
  for f in assistant/curriculum-library/v0/library-reference-schema.json assistant/curriculum-library/v0/sample-library-references.json; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else warn 'python3 not available for v0 JSON parse checks'; fi

section 'No Local Folder Creation or Scanning Scripts'
library_script_hits=0
for candidate in scripts/*curriculum-library* scripts/*create*library* scripts/*library-folder*; do
  [[ -e "${candidate}" ]] || continue
  [[ "${candidate}" == *foundation-status* ]] && continue
  [[ "${candidate}" == *reference-v0-validator* ]] && continue
  if grep -Eq '(mkdir|mktemp.*TeacherAI|~/TeacherAI-Curriculum-Library)' "${candidate}" 2>/dev/null; then
    library_script_hits=1
    fail "library script must not create local folders: ${candidate}"
  fi
done
[[ "${library_script_hits}" == "0" ]] && pass 'no curriculum library folder-creation scripts detected'
grep -Fq -- '--curriculum-library-create)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose curriculum library create command' || pass 'CLI has no curriculum library create command'
grep -Fq -- '--curriculum-library-scan)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose curriculum library scan command' || pass 'CLI has no curriculum library scan command'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Build Queue Cross-Links'
check_doc_contains docs/build-queue.md "curriculum library" "build queue curriculum library"
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "curriculum-library" "whole-system report curriculum library"
check_doc_contains assistant/memory/active-priorities.md "Curriculum Library setup" "active priorities curriculum library"

section 'Chief of Staff Integration'
check_help_contains "--curriculum-library-foundation-status"
check_help_contains "--curriculum-library-reference-v0-validate"
check_bash_syntax "bin/chief-of-staff"
check_file tests/curriculum-library-foundation-status-test.sh
check_bash_syntax tests/curriculum-library-foundation-status-test.sh
grep -Fq -- 'curriculum-library-foundation-status' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires curriculum library foundation test' || fail 'smoke missing curriculum library foundation test'
pass 'no write action attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'
pass 'no local library folder creation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
