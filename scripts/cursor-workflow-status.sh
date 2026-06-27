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

check_text "${prompt_template}" "no-commit review|NO-COMMIT REVIEW" "cursor prompt template includes no-commit review"
check_text "${pr_checklist}" "APPROVE TO COMMIT|REQUEST CHANGES|BLOCKED" "cursor PR checklist includes approve/request changes/block decisions"

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
