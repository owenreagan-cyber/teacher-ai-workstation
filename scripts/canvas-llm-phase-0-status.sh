#!/usr/bin/env bash
# Read-only Canvas LLM Phase 0 standards foundation status. Docs/status/fake-local only.
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
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Canvas LLM Phase 0 Status'
cat <<'EOF'
Status: canvas_llm_phase_0_standards_foundation_complete
Classification: docs/status/fake-local only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Supabase/Firebase new usage: blocked
PASS does not authorize Canvas access, generation, export, publishing, or self-healing.
EOF

section 'Phase 0 Documentation'
for path in \
  docs/programs/canvas-llm/THALES_CANVAS_STANDARD.md \
  docs/programs/canvas-llm/canvas-evidence-schema.md \
  docs/programs/canvas-llm/canvas-safe-data-boundaries.md \
  docs/programs/canvas-llm/canvas-authority-and-conflict-policy.md \
  docs/programs/canvas-llm/canvas-validation-tiers.md \
  docs/programs/canvas-llm/canvas-report-templates.md \
  docs/programs/canvas-llm/canvas-fake-local-fixtures-plan.md \
  docs/programs/canvas-llm/canvas-phase-0-readiness.md; do
  check_file "${path}"
done

section 'Safety Boundaries'
check_doc_contains docs/programs/canvas-llm/THALES_CANVAS_STANDARD.md "Canvas API/OAuth/live reads: blocked" "Canvas live access blocked"
check_doc_contains docs/programs/canvas-llm/THALES_CANVAS_STANDARD.md "Canvas writes/publishing: blocked" "Canvas writes blocked"
check_doc_contains docs/programs/canvas-llm/canvas-safe-data-boundaries.md "Student data: blocked" "student data blocked"
check_doc_contains docs/programs/canvas-llm/canvas-safe-data-boundaries.md "Canvas API or OAuth" "Canvas API OAuth blocked"
check_doc_contains docs/programs/canvas-llm/canvas-safe-data-boundaries.md "Supabase/Firebase" "Supabase Firebase blocked"
check_doc_contains docs/programs/canvas-llm/canvas-validation-tiers.md "Runtime validation of Canvas content is blocked" "runtime validation blocked"
check_doc_contains docs/programs/canvas-llm/canvas-validation-tiers.md "Self-healing is blocked" "self-healing runtime blocked"
check_doc_contains docs/programs/canvas-llm/canvas-report-templates.md "These templates are for Markdown reporting only" "report templates non-runtime"
check_doc_contains docs/programs/canvas-llm/canvas-authority-and-conflict-policy.md "Owen must explicitly approve" "Owen approval gate"

section 'Fake Local Fixtures'
check_file fixtures/canvas-llm/README.md
check_file fixtures/canvas-llm/fake-page-metadata.json
check_file fixtures/canvas-llm/fake-module-metadata.json
check_file fixtures/canvas-llm/fake-assignment-metadata.json
check_file fixtures/canvas-llm/fake-html-patterns.md
check_doc_contains fixtures/canvas-llm/README.md "fake_local_only" "fixture fake-local classification"
check_doc_contains fixtures/canvas-llm/README.md "Student data: blocked" "fixture student data blocked"
check_doc_contains fixtures/canvas-llm/fake-html-patterns.md "not exported from Canvas" "fake HTML non-export boundary"

if command -v python3 >/dev/null 2>&1; then
  for f in fixtures/canvas-llm/fake-page-metadata.json fixtures/canvas-llm/fake-module-metadata.json fixtures/canvas-llm/fake-assignment-metadata.json; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn "python3 not available for fake JSON parse checks"
fi

section 'Command And Roadmap Integration'
check_help_contains "--canvas-llm-phase-0-status"
check_doc_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--canvas-llm-phase-0-status"' "manifest Canvas Phase 0 command"
check_doc_contains docs/chief-of-staff-command-index-v1.md "--canvas-llm-phase-0-status" "command index Canvas Phase 0 command"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM Phase 0 standards foundation" "build-state Canvas Phase 0"
check_doc_contains docs/build-queue.md "canvas_llm_phase_0_standards_foundation_complete" "build queue Canvas Phase 0 closure"
check_doc_contains assistant/memory/active-priorities.md "Canvas LLM Phase 0 standards foundation: complete" "active priorities Canvas Phase 0 closure"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
