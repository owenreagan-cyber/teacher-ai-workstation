#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "cannot syntax check missing file: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

rule_file=".cursor/rules/teacher-ai-workstation.mdc"
senior_engineer_rule_file=".cursor/rules/teacher-ai-workstation-senior-engineer.mdc"
implementation_approval_gate_doc="docs/implementation-approval-gate.md"
engineering_constitution_doc="docs/engineering-constitution.md"
curriculum_builder_section_completion_audit_doc="docs/curriculum-builder-section-completion-audit.md"
canvas_section_completion_audit_doc="docs/canvas-llm-section-completion-audit.md"
build_queue_doc="docs/build-queue.md"
active_priorities_doc="assistant/memory/active-priorities.md"
master_build_roadmap_doc="docs/master-build-roadmap.md"
workflow_guide="docs/cursor-workflow-operating-system.md"
prompt_template="docs/cursor-prompt-template.md"
pr_checklist="docs/cursor-pr-review-checklist.md"

section "Cursor Workflow Summary"
cat <<'EOF'
1. ChatGPT writes the task prompt
2. Cursor implements locally
3. Cursor runs checks
4. Owen approves commit
5. Cursor pushes and opens PR
6. ChatGPT reviews PR
7. Owen approves merge
8. main dashboard proves completion
EOF

section "Workflow Checks"

check_file "${rule_file}"
check_file "${senior_engineer_rule_file}"
check_file "${workflow_guide}"
check_file "${prompt_template}"
check_file "${pr_checklist}"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

check_text "${workflow_guide}" "ChatGPT" "workflow guide mentions ChatGPT"
check_text "${workflow_guide}" "Cursor" "workflow guide mentions Cursor"
check_text "${workflow_guide}" "GitHub" "workflow guide mentions GitHub"
check_text "${workflow_guide}" "dashboard" "workflow guide mentions dashboard"
check_text "${workflow_guide}" "mergedAt" "workflow guide mentions mergedAt"

check_text "${rule_file}" "Never commit directly to \`main\`|Never commit directly to main|commit directly to \`main\`|commit directly to main" "cursor rule mentions not committing to main"
check_text "${rule_file}" "student-sensitive data" "cursor rule mentions no student-sensitive data"
check_text "${rule_file}" "Gmail.*Drive.*Calendar|Gmail, Google Drive, Google Calendar" "cursor rule mentions no Gmail/Drive/Calendar/API/OAuth/secrets without approval"

check_text "${senior_engineer_rule_file}" "Escalation Conditions" "senior engineer rule defines escalation conditions"
check_text "${senior_engineer_rule_file}" "Permanent Hard Boundaries" "senior engineer rule defines hard boundaries"
check_text "${senior_engineer_rule_file}" "Completion Report Format" "senior engineer rule defines completion report format"
check_text "${senior_engineer_rule_file}" "branch deletion verification" "senior engineer rule requires branch deletion verification"
check_text "${senior_engineer_rule_file}" "PASS/WARN/FAIL" "senior engineer rule preserves PASS/WARN/FAIL semantics"

check_text "${prompt_template}" "no-commit review|NO-COMMIT REVIEW" "cursor prompt template includes no-commit review"
check_text "${pr_checklist}" "APPROVE TO COMMIT|REQUEST CHANGES|BLOCKED" "cursor PR checklist includes approve/request changes/block decisions"

section "Implementation Approval Gate Checks"

check_file "${implementation_approval_gate_doc}"
check_text "${implementation_approval_gate_doc}" "documentation/status only" "implementation gate documentation/status only"
check_text "${implementation_approval_gate_doc}" "Gate status: active" "implementation gate status active"
check_text "${implementation_approval_gate_doc}" "Implementation approval status: not approved" "implementation gate not approved by default"
check_text "${implementation_approval_gate_doc}" "planning/status work" "implementation gate defines planning/status work"
check_text "${implementation_approval_gate_doc}" "implementation work" "implementation gate defines implementation work"
check_text "${implementation_approval_gate_doc}" "Required Intake Fields" "implementation gate required intake fields"
check_text "${implementation_approval_gate_doc}" "Required Risk Review" "implementation gate required risk review"
check_text "${implementation_approval_gate_doc}" "Required Validation Proof" "implementation gate required validation proof"
check_text "${implementation_approval_gate_doc}" "Required Rollback/Stop Plan" "implementation gate required rollback stop plan"
check_text "${implementation_approval_gate_doc}" "Non-Activation Confirmation" "implementation gate non-activation confirmation"
check_text "${implementation_approval_gate_doc}" "Curriculum Builder live registry" "implementation gate curriculum builder live registry checklist"
check_text "${implementation_approval_gate_doc}" "Output contract schema activation" "implementation gate output contract schema checklist"
check_text "${implementation_approval_gate_doc}" "Validators/renderers" "implementation gate validators renderers checklist"
check_text "${implementation_approval_gate_doc}" "Drive/NAS/iCloud resolution" "implementation gate drive nas icloud checklist"
check_text "${implementation_approval_gate_doc}" "Canvas export/package work" "implementation gate canvas export checklist"
check_text "${implementation_approval_gate_doc}" "Ingestion/RAG/vector/search work" "implementation gate ingestion rag checklist"
check_text "${implementation_approval_gate_doc}" "Lesson generation/review generation" "implementation gate lesson generation checklist"
check_text "${implementation_approval_gate_doc}" "Automation/background jobs" "implementation gate automation checklist"
check_text "${curriculum_builder_section_completion_audit_doc}" "docs/implementation-approval-gate.md" "curriculum builder section audit links implementation gate"
check_text "${canvas_section_completion_audit_doc}" "docs/implementation-approval-gate.md" "canvas section audit links implementation gate"
check_text "${senior_engineer_rule_file}" "docs/implementation-approval-gate.md" "senior engineer rule links implementation gate"
check_text "${build_queue_doc}" "implementation approval gate" "build queue references implementation approval gate"
check_text "${active_priorities_doc}" "implementation approval gate" "active priorities references implementation approval gate"

section "Engineering Constitution Checks"

check_file "${engineering_constitution_doc}"
check_text "${engineering_constitution_doc}" "documentation/status only" "engineering constitution documentation/status only"
check_text "${engineering_constitution_doc}" "Constitution status: active" "engineering constitution status active"
check_text "${engineering_constitution_doc}" "Local-first" "engineering constitution local-first principle"
check_text "${engineering_constitution_doc}" "Human approval" "engineering constitution human approval principle"
check_text "${engineering_constitution_doc}" "Chief of Staff" "engineering constitution chief of staff layer"
check_text "${engineering_constitution_doc}" "Curriculum Registry" "engineering constitution curriculum registry layer"
check_text "${engineering_constitution_doc}" "Output Contracts" "engineering constitution output contracts layer"
check_text "${engineering_constitution_doc}" "Renderers" "engineering constitution renderers layer"
check_text "${engineering_constitution_doc}" "Version 1.0" "engineering constitution version 1.0 definition"
check_text "${engineering_constitution_doc}" "Escalation Conditions" "engineering constitution escalation conditions"
check_text "${engineering_constitution_doc}" "Definition of Done" "engineering constitution definition of done"
check_text "${engineering_constitution_doc}" "implementation tracks" "engineering constitution implementation tracks"
check_text "${engineering_constitution_doc}" "PASS/WARN/FAIL" "engineering constitution PASS WARN FAIL invariants"
check_text "${engineering_constitution_doc}" "docs/implementation-approval-gate.md" "engineering constitution links implementation gate"
check_text "${implementation_approval_gate_doc}" "docs/engineering-constitution.md" "implementation gate links engineering constitution"
check_text "${senior_engineer_rule_file}" "docs/engineering-constitution.md" "senior engineer rule links engineering constitution"
check_text "${workflow_guide}" "docs/engineering-constitution.md" "cursor workflow guide links engineering constitution"
check_text "${curriculum_builder_section_completion_audit_doc}" "docs/engineering-constitution.md" "curriculum builder section audit links engineering constitution"
check_text "${build_queue_doc}" "engineering constitution" "build queue references engineering constitution"
check_text "${active_priorities_doc}" "engineering constitution" "active priorities references engineering constitution"

section "Master Build Roadmap Checks"

check_file "${master_build_roadmap_doc}"
check_text "${master_build_roadmap_doc}" "documentation/status only" "master roadmap documentation/status only"
check_text "${master_build_roadmap_doc}" "Roadmap status: active" "master roadmap status active"
check_text "${master_build_roadmap_doc}" "Implementation does not proceed automatically" "master roadmap no auto implementation"
check_text "${master_build_roadmap_doc}" "Curriculum Builder Complete" "master roadmap curriculum builder program"
check_text "${master_build_roadmap_doc}" "Chief of Staff v1" "master roadmap chief of staff program"
check_text "${master_build_roadmap_doc}" "Chief of Staff v1 Agent Core" "master roadmap immediate next mission"
check_text "${master_build_roadmap_doc}" "Canvas Manual Restart" "master roadmap canvas program"
check_text "${master_build_roadmap_doc}" "Local LLM / Ollama Workstation" "master roadmap local llm program"
check_text "${master_build_roadmap_doc}" "Teacher Workstation Health Monitor" "master roadmap health monitor program"
check_text "${master_build_roadmap_doc}" "Teacher Workstation System Updater" "master roadmap system updater program"
check_text "${master_build_roadmap_doc}" "3D Builder Workshop Agent" "master roadmap 3d builder program"
check_text "${master_build_roadmap_doc}" "Mac Workstation Experience" "master roadmap mac workstation program"
check_text "${master_build_roadmap_doc}" "Widget and Shortcut Builder" "master roadmap widget shortcut program"
check_text "${master_build_roadmap_doc}" "Lovable Classroom App Builder" "master roadmap lovable program"
check_text "${master_build_roadmap_doc}" "Version 1.0 Definition" "master roadmap v1 definition"
check_text "${master_build_roadmap_doc}" "teacher-workstation-capability-map.md" "master roadmap links capability map"
check_text "${build_queue_doc}" "Chief of Staff v1" "build queue references chief of staff v1"
check_file "docs/chief-of-staff-v1-foundation.md"
check_file "docs/chief-of-staff-agent-core.md"
check_file "docs/teacher-workstation-health-monitor-foundation.md"
check_file "docs/teacher-workstation-system-updater-foundation.md"
check_file "docs/ai-tool-routing-foundation.md"
check_file "docs/local-llm-workstation-status-foundation.md"
check_file "docs/mac-workstation-experience-foundation.md"
check_file "docs/widget-shortcut-builder-catalog-foundation.md"
check_file "docs/classroom-app-lab-prototype-rescue-foundation.md"
check_text "${build_queue_doc}" "Classroom App Lab" "build queue references classroom app lab"
check_text "${build_queue_doc}" "Health Monitor" "build queue references health monitor"
check_text "${build_queue_doc}" "System Updater" "build queue references system updater"
check_text "${build_queue_doc}" "master-build-roadmap" "build queue references master roadmap"
check_text "${active_priorities_doc}" "Master Build Roadmap" "active priorities references master roadmap"
check_text "${engineering_constitution_doc}" "master-build-roadmap.md" "engineering constitution links master roadmap"

branch="$(git branch --show-current 2>/dev/null || true)"
if [[ "${branch}" == "main" ]] && [[ -n "$(git status --short 2>/dev/null || true)" ]]; then
  warn "current branch is main and there are uncommitted changes"
fi

briefs_dir="assistant/lesson-planning/briefs"
drafts_dir="assistant/lesson-planning/drafts"

if [[ -d "${briefs_dir}" ]]; then
  generated_briefs="$(find "${briefs_dir}" -maxdepth 1 -type f ! -name "README.md" -print 2>/dev/null || true)"
  if [[ -n "${generated_briefs}" ]]; then
    warn "generated lesson brief files currently exist"
    printf '%s\n' "${generated_briefs}" | sed 's/^/  /'
  fi
fi

if [[ -d "${drafts_dir}" ]]; then
  generated_drafts="$(find "${drafts_dir}" -maxdepth 1 -type f ! -name "README.md" -print 2>/dev/null || true)"
  if [[ -n "${generated_drafts}" ]]; then
    warn "generated lesson draft files currently exist"
    printf '%s\n' "${generated_drafts}" | sed 's/^/  /'
  fi
fi

if [[ -f .cursorrules ]]; then
  warn ".cursorrules exists; project rules should live under .cursor/rules/ unless intentionally kept for compatibility"
fi

pass "no write action attempted"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
