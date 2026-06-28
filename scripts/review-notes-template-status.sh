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

template_doc="docs/review-notes-template.md"
review_notes_readme="assistant/lesson-planning/review-notes/README.md"
review_notes_dir="assistant/lesson-planning/review-notes"

section "Review Notes Template"
cat <<'EOF'
1. Inspect one lesson slug
2. Copy the review notes template locally if desired
3. Record optional personal review thinking
4. Keep notes local and non-student-specific
5. Make a human review decision outside any official status system
EOF

section "Template Reminders"
cat <<'EOF'
- Notes are local only
- Notes are optional
- Notes are not official review status
- Human review is required before classroom use
EOF

section "Workflow Checks"

check_file "${template_doc}"
check_file "${review_notes_readme}"

check_text "${template_doc}" "local only" "template mentions local only"
check_text "${template_doc}" "optional" "template mentions optional notes"
check_text "${template_doc}" "not official review status|not an official approval system" "template mentions notes are not official review status"
check_text "${template_doc}" "human review" "template mentions human review"
check_text "${template_doc}" "no student-sensitive data|student-sensitive data" "template mentions no student-sensitive data"
check_text "${template_doc}" "no real student names|real student names" "template mentions no real student names"
check_text "${template_doc}" "Lesson Slug" "template includes lesson slug field"
check_text "${template_doc}" "Date Reviewed" "template includes date reviewed field"
check_text "${template_doc}" "Reviewer" "template includes reviewer field"
check_text "${template_doc}" "Source Files Checked" "template includes source files checked field"
check_text "${template_doc}" "Privacy Check" "template includes privacy check field"
check_text "${template_doc}" "Source and Accuracy Check" "template includes source and accuracy check field"
check_text "${template_doc}" "Curriculum Fit Check" "template includes curriculum fit check field"
check_text "${template_doc}" "Classroom Readiness Check" "template includes classroom readiness check field"
check_text "${template_doc}" "Accessibility and Safety Check" "template includes accessibility and safety check field"
check_text "${template_doc}" "Materials Check" "template includes materials check field"
check_text "${template_doc}" "Revision Notes" "template includes revision notes field"
check_text "${template_doc}" "Human Decision" "template includes human decision field"
check_text "${template_doc}" "Next Action" "template includes next action field"
check_text "${template_doc}" "READY FOR CLASSROOM USE AFTER HUMAN REVIEW" "template includes READY FOR CLASSROOM USE AFTER HUMAN REVIEW"
check_text "${template_doc}" "NEEDS REVISION" "template includes NEEDS REVISION"
check_text "${template_doc}" "HOLD" "template includes HOLD"
check_text "${template_doc}" "DO NOT USE" "template includes DO NOT USE"
check_text "${review_notes_readme}" "not official review status" "review notes README mentions not official review status"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/lesson-planning-status.sh"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

if [[ -d "${review_notes_dir}" ]]; then
  personal_notes="$(find "${review_notes_dir}" -maxdepth 1 -type f ! -name "README.md" -print 2>/dev/null || true)"
  if [[ -n "${personal_notes}" ]]; then
    warn "personal review note files currently exist in review-notes folder"
    printf '%s\n' "${personal_notes}" | sed 's/^/  /'
  fi
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
