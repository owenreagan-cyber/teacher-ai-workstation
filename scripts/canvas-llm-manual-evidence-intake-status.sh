#!/usr/bin/env bash
# Read-only Canvas LLM Phase 2 manual evidence intake status. No live Canvas access.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_dir() { [[ -d "$1" ]] && pass "directory exists: $1" || fail "directory missing: $1"; }
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

intake_root="evidence/canvas-llm"
manual_dir="${intake_root}/manual-exported"
examples_dir="${intake_root}/redacted-examples"
example_files=(
  "${examples_dir}/README.md"
  "${examples_dir}/redacted-page-snippet.md"
  "${examples_dir}/redacted-assignment-metadata.json"
  "${examples_dir}/redacted-module-structure.json"
)
safety_scan_files=(
  "${examples_dir}/redacted-page-snippet.md"
  "${examples_dir}/redacted-assignment-metadata.json"
  "${examples_dir}/redacted-module-structure.json"
)

section 'Canvas LLM Phase 2 Manual Evidence Intake'
cat <<'EOF'
Status: canvas_llm_phase_2_manual_evidence_intake_complete
Classification: manual/exported/redacted evidence scaffold
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Automatic scanning: blocked
Network access: no
EOF

section 'Intake Folders'
check_dir "${intake_root}"
check_dir "${manual_dir}"
check_dir "${examples_dir}"
check_file "${intake_root}/README.md"
check_file "${manual_dir}/README.md"
check_file "${manual_dir}/.gitkeep"
check_file "${examples_dir}/README.md"

section 'Manual-Only Boundaries'
check_doc_contains "${intake_root}/README.md" "local/manual only" "local/manual boundary"
check_doc_contains "${intake_root}/README.md" "not an automatic scanner target" "no automatic scanner target"
check_doc_contains "${manual_dir}/README.md" "non-authoritative until reviewed" "manual inbox non-authority"
check_doc_contains "${manual_dir}/README.md" "Do not add scripts that automatically scan" "manual folder no automatic scan"
check_doc_contains "${intake_root}/README.md" "student data is prohibited" "student data prohibited"
check_doc_contains "${intake_root}/README.md" "Canvas API/OAuth/live reads: blocked" "Canvas live access blocked"
check_doc_contains "${intake_root}/README.md" "Canvas writes/publishing: blocked" "Canvas writes blocked"
check_doc_contains "${intake_root}/README.md" "Credentials/secrets: blocked" "credentials blocked"
check_doc_contains "${intake_root}/README.md" "Supabase/Firebase" "Supabase Firebase blocked"

section 'Allowed And Prohibited Evidence'
check_doc_contains "${intake_root}/README.md" "redacted page HTML snippets" "allowed page snippets"
check_doc_contains "${intake_root}/README.md" "redacted assignment metadata" "allowed assignment metadata"
check_doc_contains "${intake_root}/README.md" "redacted module structures" "allowed module structures"
check_doc_contains "${intake_root}/README.md" "redacted screenshot notes" "allowed screenshot notes"
check_doc_contains "${intake_root}/README.md" "exported page content with all student/private data removed" "allowed redacted exported page content"
check_doc_contains "${intake_root}/README.md" "rosters" "prohibited rosters"
check_doc_contains "${intake_root}/README.md" "submissions" "prohibited submissions"
check_doc_contains "${intake_root}/README.md" "grades" "prohibited grades"
check_doc_contains "${intake_root}/README.md" "OAuth files" "prohibited OAuth files"
check_doc_contains "${intake_root}/README.md" "full unreviewed course dumps" "prohibited course dumps"
check_doc_contains "${intake_root}/README.md" "real curriculum folders" "prohibited real curriculum folders"

section 'Committed Redacted Examples'
for f in "${example_files[@]}"; do
  check_file "${f}"
done

if command -v python3 >/dev/null 2>&1; then
  for f in "${examples_dir}/redacted-assignment-metadata.json" "${examples_dir}/redacted-module-structure.json"; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn "python3 not available for JSON parse checks"
fi

section 'Committed Example Safety Scan'
unsafe_patterns=(
  "access_token"
  "api_key"
  "client_secret"
  "canvas_token"
  "oauth"
  "student_name"
  "student_id"
  "roster"
  "student_submission"
  "submission_body"
  "submission_text"
  "grade"
  "accommodation"
  "analytics"
  "canvas.instructure.com"
  "supabase"
  "firebase"
)

for f in "${safety_scan_files[@]}"; do
  for pattern in "${unsafe_patterns[@]}"; do
    if grep -Eiq "${pattern}" "${f}"; then
      fail "${f} must not contain prohibited pattern: ${pattern}"
    else
      pass "${f} omits prohibited pattern: ${pattern}"
    fi
  done
done

section 'Phase 2 Documentation And Integration'
check_file docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md
check_doc_contains docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md "manual/exported/redacted evidence scaffold" "Phase 2 classification"
check_doc_contains docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md "does not scan arbitrary manual evidence" "Phase 2 no arbitrary scanning"
check_doc_contains docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md "Next Approval Gate" "Phase 2 next approval gate"
check_help_contains "--canvas-llm-phase-2-status"
check_doc_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--canvas-llm-phase-2-status"' "manifest Canvas Phase 2 command"
check_doc_contains docs/chief-of-staff-command-index-v1.md "--canvas-llm-phase-2-status" "command index Canvas Phase 2 command"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM Phase 2 manual/exported evidence intake" "build-state Canvas Phase 2"
check_doc_contains docs/build-queue.md "canvas_llm_phase_2_manual_evidence_intake_complete" "build queue Canvas Phase 2 closure"
check_doc_contains assistant/memory/active-priorities.md "Canvas LLM Phase 2 manual evidence intake: complete" "active priorities Canvas Phase 2 closure"

section 'Phase 1 Regression'
if bash scripts/canvas-llm-fake-local-validator.sh >/tmp/canvas-llm-fake-local-validator.out 2>&1; then
  pass "Phase 1 fake/local validator still passes"
else
  fail "Phase 1 fake/local validator failed"
  tail -40 /tmp/canvas-llm-fake-local-validator.out || true
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
