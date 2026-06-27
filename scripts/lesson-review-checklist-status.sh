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

summary_count() {
  local output="$1"
  local label="$2"
  printf '%s\n' "${output}" | awk -v label="${label}" '$1 == label ":" && $2 ~ /^[0-9]+$/ { value = $2 } END { if (value != "") print value }'
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

checklist="docs/safe-local-lesson-review-checklist.md"
briefs_dir="assistant/lesson-planning/briefs"
drafts_dir="assistant/lesson-planning/drafts"

future_ideas=(
  "mark-reviewed workflow"
  "single-slug review view"
  "review notes template"
  "JSON output"
  "Google Docs export"
  "Gmail/Drive integrations"
  "AI lesson revision"
  "rubric scoring"
)

section "Lesson Review Checklist"
cat <<'EOF'
1. Confirm lesson files are local drafts
2. Check student privacy
3. Check source accuracy
4. Check curriculum fit
5. Check classroom readiness
6. Check accessibility and safety
7. Make a human review decision
EOF

section "Review Outcomes"
cat <<'EOF'
READY FOR CLASSROOM USE AFTER HUMAN REVIEW
NEEDS REVISION
HOLD
DO NOT USE
EOF

section "Workflow Checks"

check_file "${checklist}"

check_text "${checklist}" "local only" "checklist mentions local only"
check_text "${checklist}" "read-only" "checklist mentions read-only"
check_text "${checklist}" "human review" "checklist mentions human review"
check_text "${checklist}" "no student-sensitive data|student-sensitive data" "checklist mentions no student-sensitive data"
check_text "${checklist}" "no real student names|real student names" "checklist mentions no real student names"
check_text "${checklist}" "No Gmail|no Gmail" "checklist mentions no Gmail"
check_text "${checklist}" "No Google Drive|no Google Drive|Google Drive" "checklist mentions no Google Drive"
check_text "${checklist}" "No Google Calendar|no Google Calendar|Google Calendar" "checklist mentions no Google Calendar"
check_text "${checklist}" "No APIs|no APIs" "checklist mentions no APIs"
check_text "${checklist}" "No OAuth|no OAuth" "checklist mentions no OAuth"
check_text "${checklist}" "No secrets|no secrets" "checklist mentions no secrets"
check_text "${checklist}" "No school systems|no school systems|school systems" "checklist mentions no school systems"
check_text "${checklist}" "No publishing|no publishing|publishing, sharing, or sending" "checklist mentions no publishing/sharing/sending"

check_text "${checklist}" "READY FOR CLASSROOM USE AFTER HUMAN REVIEW" "checklist includes READY FOR CLASSROOM USE AFTER HUMAN REVIEW"
check_text "${checklist}" "NEEDS REVISION" "checklist includes NEEDS REVISION"
check_text "${checklist}" "HOLD" "checklist includes HOLD"
check_text "${checklist}" "DO NOT USE" "checklist includes DO NOT USE"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/lesson-planning-status.sh"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

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

if [[ -f scripts/lesson-queue-status.sh ]]; then
  queue_result=0
  queue_output="$(bash scripts/lesson-queue-status.sh 2>&1)" || queue_result=$?
  queue_warn="$(summary_count "${queue_output}" "WARN")"
  if [[ "${queue_result}" != "0" ]]; then
    warn "lesson queue status command returned nonzero"
  elif [[ -n "${queue_warn}" && "${queue_warn}" -gt 0 ]]; then
    warn "lesson queue status currently reports ${queue_warn} warning(s), including possible missing-artifact warnings"
  fi
fi

if [[ -f "${checklist}" ]]; then
  future_section_start="$(grep -n '^## Future Ideas Not Included' "${checklist}" | head -1 | cut -d: -f1 || true)"
  if [[ -z "${future_section_start}" ]]; then
    fail "checklist missing Future Ideas Not Included section"
  else
    pass "checklist includes Future Ideas Not Included section"
    pre_future_content="$(sed -n "1,$((future_section_start - 1))p" "${checklist}")"
    for idea in "${future_ideas[@]}"; do
      if printf '%s\n' "${pre_future_content}" | grep -Fiq "${idea}"; then
        if ! printf '%s\n' "${pre_future_content}" | grep -Fiq "${idea}.*not included|not part of|Future Ideas|intentionally not"; then
          warn "checklist may reference future idea as active feature before Future Ideas section: ${idea}"
        fi
      fi
    done
    active_feature_patterns=(
      "currently supports mark-reviewed"
      "automatically approves"
      "mark-reviewed workflow is available"
      "use the JSON output command"
      "export to Google Docs"
    )
    for pattern in "${active_feature_patterns[@]}"; do
      if grep -Eiq "${pattern}" "${checklist}"; then
        warn "checklist may describe a future idea as an active feature: ${pattern}"
      fi
    done
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
