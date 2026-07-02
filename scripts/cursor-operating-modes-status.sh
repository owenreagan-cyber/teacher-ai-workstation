#!/usr/bin/env bash
# Read-only Cursor operating modes and proposal governance status. Documentation/status only.
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

operating_modes_doc="docs/cursor-operating-modes-and-approval-gates.md"
domain_boundaries_doc="docs/teacher-workstation-domain-boundaries.md"
proposals_index="docs/proposals/index.md"
status_script="scripts/cursor-operating-modes-status.sh"
status_test="tests/cursor-operating-modes-status-test.sh"

section 'Cursor Operating Modes and Proposal Governance (Read-Only Foundation)'
cat <<'EOF'
Status: documentation/status only
Runtime activation: no
Network calls: no
Proposal ledger: repo docs only
Automation: no
Student data: no
EOF

section 'Foundation Documents'
check_file "${operating_modes_doc}"
check_file "${domain_boundaries_doc}"
check_file "${proposals_index}"
check_file docs/proposals/README.md

section 'Operating Mode Coverage'
check_doc_contains "${operating_modes_doc}" "Maximum Autonomous Execution Mode" "maximum autonomous execution mode"
check_doc_contains "${operating_modes_doc}" "Full Developer Debug / Validation Authority" "developer debug validation authority"
check_doc_contains "${operating_modes_doc}" "Improvement / Hardening Mode" "improvement hardening mode"
check_doc_contains "${operating_modes_doc}" "Vulnerability / Failure-Mode Review" "vulnerability failure-mode review"
check_doc_contains "${operating_modes_doc}" "New Feature Discovery Mode" "new feature discovery mode"
check_doc_contains "${operating_modes_doc}" "approved_to_propose" "approval levels"
check_doc_contains "${operating_modes_doc}" "approved_for_live_integration" "live integration approval level"
check_doc_contains "${operating_modes_doc}" "Proposal Lifecycle" "proposal lifecycle"
check_doc_contains "${operating_modes_doc}" "Blocked-Item Routing Rule" "blocked-item routing rule"
check_doc_contains "${operating_modes_doc}" "no reads or writes outside this repository working directory" "repo-local definition"
check_doc_contains "${operating_modes_doc}" "Prompt Override Rule" "prompt override rule"
check_doc_contains "${operating_modes_doc}" "Mixed-Category File Rule" "mixed-category file rule"
check_doc_contains "${operating_modes_doc}" "Test Assertion Change Rule" "test assertion change rule"
check_doc_contains "${operating_modes_doc}" "Discovery Scope / Proposal Cap" "discovery scope proposal cap"
check_doc_contains "${operating_modes_doc}" "Session Boundary / Persistence" "session persistence"
check_doc_contains "${operating_modes_doc}" "Sub-Agent / Tool Inheritance" "sub-agent tool inheritance"
check_doc_contains "${operating_modes_doc}" "Final Report Additions" "final report additions"

section 'Domain Boundary Coverage'
check_doc_contains "${domain_boundaries_doc}" "Parent Communication Agents" "parent communication boundary"
check_doc_contains "${domain_boundaries_doc}" "Automatic sending of messages" "parent automatic sending blocked"
check_doc_contains "${domain_boundaries_doc}" "Curriculum / Lesson / Worksheet / Presentation Generation" "curriculum boundary"
check_doc_contains "${domain_boundaries_doc}" "Real lesson generation" "real lesson generation blocked"
check_doc_contains "${domain_boundaries_doc}" "Canvas / Drive / Gmail / Calendar / External Integrations" "integration boundary"
check_doc_contains "${domain_boundaries_doc}" "OAuth, API clients, credential handling" "oauth api blocked"
check_doc_contains "${domain_boundaries_doc}" "Classroom App Lab / Prototype Rescue" "classroom app lab boundary"
check_doc_contains "${domain_boundaries_doc}" "Mac Workstation Experience" "mac workstation boundary"
check_doc_contains "${domain_boundaries_doc}" "Widgets and Shortcuts" "widgets shortcuts boundary"
check_doc_contains "${domain_boundaries_doc}" "VIBE Mode" "vibe mode boundary"
check_doc_contains "${domain_boundaries_doc}" "3D Design Studio" "3d design studio boundary"
check_doc_contains "${domain_boundaries_doc}" "Lovable / App Builder Workflows" "lovable app builder boundary"
check_doc_contains "${domain_boundaries_doc}" "Local LLM / Ollama Workflows" "local llm ollama boundary"

section 'Three-Level Discovery Governance'
check_doc_contains "${operating_modes_doc}" "## Three-Level Discovery Governance {#three-level-discovery-governance}" "three-level discovery anchor"
check_doc_contains "${operating_modes_doc}" "Level 1 — End-of-Mission Discovery Scan" "level 1 end-of-mission scan"
check_doc_contains "${operating_modes_doc}" "Level 2 — End-of-Lane Discovery Review" "level 2 lane discovery review"
check_doc_contains "${operating_modes_doc}" "Level 3 — Full-Product Discovery Strategy Review" "level 3 full-product discovery"
check_doc_contains "${operating_modes_doc}" "Discovery is never implementation approval" "discovery not implementation approval"
check_doc_contains "${operating_modes_doc}" "No discovery findings this mission" "no discovery findings rule"
check_file docs/proposals/templates/lane-level-discovery-mission.md
check_file docs/proposals/templates/full-product-discovery-mission.md
check_doc_contains docs/proposals/templates/lane-level-discovery-mission.md "[INSERT LANE NAME]" "level 2 template lane placeholder"

section 'Proposal Ledger'
check_doc_contains "${proposals_index}" "Proposal Ledger" "proposal ledger heading"
check_doc_contains "${proposals_index}" "| Candidate | Area | Level | Value | Risk | Technical Complexity | Student-Data Risk | Curriculum-Content Risk | API/Network Requirement | Status | Recommended Next Step | Source Mission | Date |" "unified proposal ledger schema"
check_doc_contains "${proposals_index}" "Migration Note (2026-07-02)" "proposal ledger migration note"
check_doc_contains "${proposals_index}" "implemented" "ledger documents implemented status"
check_doc_contains "${proposals_index}" "Cursor proposal → ChatGPT review → Owen Reagan approval" "approval chain"
check_doc_contains docs/proposals/README.md "Three-Level Discovery Relationship" "proposals readme discovery levels"
check_doc_contains docs/master-build-roadmap.md "Program Lane Status" "roadmap program lane status"
check_doc_contains docs/master-build-roadmap.md "complete_pending_review" "roadmap lane_status complete_pending_review"
check_doc_contains docs/master-build-roadmap.md "reviewed" "roadmap lane_status reviewed rule"

section 'Cross-Links and Roadmap Coherence'
check_doc_contains docs/cursor-workflow-operating-system.md "docs/engineering-constitution.md" "workflow guide links engineering constitution"
check_doc_contains docs/cursor-workflow-operating-system.md "cursor-operating-modes-and-approval-gates" "workflow guide links operating modes"
check_doc_contains docs/implementation-approval-gate.md "documentation/status only" "implementation gate status only"
check_doc_contains docs/build-queue.md "master-build-roadmap" "build queue links roadmap"
check_doc_contains assistant/memory/active-priorities.md "Implementation approval gate" "active priorities links gate"

section 'CLI, Manifest, Status Script, and Tests'
grep -Fq -- '--cursor-operating-modes-status' bin/chief-of-staff && pass 'CLI exposes --cursor-operating-modes-status' || fail 'CLI missing --cursor-operating-modes-status'
grep -Fq -- '"--cursor-operating-modes-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --cursor-operating-modes-status' || fail 'manifest missing --cursor-operating-modes-status'
check_file "${status_script}"
check_file "${status_test}"
check_bash_syntax() {
  local path="$1"
  if bash -n "${path}" 2>/dev/null; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}
check_bash_syntax "${status_script}"
check_bash_syntax "${status_test}"

section 'Negative Non-Activation Assertions'
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'cursor operating modes status script must not shell-invoke curl'
else
  pass 'cursor operating modes status script does not shell-invoke curl'
fi
if grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'cursor operating modes status script must not shell-invoke wget'
else
  pass 'cursor operating modes status script does not shell-invoke wget'
fi
if grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'cursor operating modes status script must not shell-invoke brew'
else
  pass 'cursor operating modes status script does not shell-invoke brew'
fi
if grep -Eq '(^|[;&|[:space:]])npm[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'cursor operating modes status script must not shell-invoke npm'
else
  pass 'cursor operating modes status script does not shell-invoke npm'
fi
if grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(add|commit|push|merge|reset)' "${status_script}" 2>/dev/null; then
  fail 'cursor operating modes status script must not mutate git state'
else
  pass 'cursor operating modes status script does not mutate git state'
fi
pass 'no network call attempted'
pass 'no package manager invoked'
pass 'no runtime behavior activated'
pass 'no write action attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
