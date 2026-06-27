#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '[PASS] %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf '[WARN] %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '[FAIL] %s\n' "$1"
}

check_dir() {
  local path="$1"
  if [[ -d "${path}" ]]; then
    pass "directory exists: ${path}"
  else
    fail "directory missing: ${path}"
  fi
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local message="$3"

  if [[ ! -f "${path}" ]]; then
    fail "cannot check missing file: ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${message}"
  else
    fail "${message}"
  fi
}

check_template_review_phrase() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "cannot check missing template: ${path}"
    return
  fi

  if grep -iq "human review" "${path}"; then
    pass "template includes human review phrase: ${path}"
  else
    fail "template missing human review phrase: ${path}"
  fi
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  fail "could not resolve Git repo root"
  repo_root="$(pwd -P)"
else
  cd "${repo_root}"
fi

workspace_dir="assistant/lesson-planning"
queue_file="${workspace_dir}/planning-queue.md"
templates_dir="${workspace_dir}/templates"
templates=(
  "${templates_dir}/lesson-brief-template.md"
  "${templates_dir}/activity-template.md"
  "${templates_dir}/assessment-template.md"
  "${templates_dir}/materials-checklist-template.md"
)

printf '\nLesson Planning Workspace Status\n'
printf 'Repo: %s\n' "${repo_root}"
printf 'Read-only: yes\n\n'

check_dir "${workspace_dir}"
check_file "${workspace_dir}/README.md"
check_file "${queue_file}"
check_dir "${templates_dir}"
check_file "${workspace_dir}/briefs/README.md"
check_file "scripts/lesson-brief-status.sh"
check_file "${workspace_dir}/drafts/README.md"
check_file "scripts/lesson-draft-status.sh"
check_file "scripts/lesson-pack-status.sh"
if [[ -f scripts/lesson-pack-status.sh ]]; then
  if bash -n scripts/lesson-pack-status.sh; then
    pass "lesson pack status script passes bash syntax"
  else
    fail "lesson pack status script fails bash syntax"
  fi
fi
check_file "scripts/lesson-queue-status.sh"
if [[ -f scripts/lesson-queue-status.sh ]]; then
  if bash -n scripts/lesson-queue-status.sh; then
    pass "lesson queue status script passes bash syntax"
  else
    fail "lesson queue status script fails bash syntax"
  fi
fi
check_file "scripts/lesson-workflow-status.sh"
check_file "docs/lesson-planning-workflow-guide.md"
check_file "docs/safe-local-lesson-review-checklist.md"
check_file "scripts/lesson-review-checklist-status.sh"
check_file "docs/single-slug-lesson-review-view.md"
check_file "scripts/lesson-review-view.sh"
if [[ -f scripts/lesson-review-checklist-status.sh ]]; then
  if bash -n scripts/lesson-review-checklist-status.sh; then
    pass "lesson review checklist status script passes bash syntax"
  else
    fail "lesson review checklist status script fails bash syntax"
  fi
fi
if [[ -f scripts/lesson-review-view.sh ]]; then
  if bash -n scripts/lesson-review-view.sh; then
    pass "lesson review view script passes bash syntax"
  else
    fail "lesson review view script fails bash syntax"
  fi
fi
if [[ -f scripts/lesson-workflow-status.sh ]]; then
  if bash -n scripts/lesson-workflow-status.sh; then
    pass "lesson workflow status script passes bash syntax"
  else
    fail "lesson workflow status script fails bash syntax"
  fi
fi

for template in "${templates[@]}"; do
  check_file "${template}"
done

check_text "${queue_file}" "Do not include real student names" "planning queue includes safety warning language"

for status in idea drafted reviewed ready archived; do
  check_text "${queue_file}" "(^|[^[:alnum:]])${status}([^[:alnum:]]|$)" "planning queue mentions allowed status: ${status}"
done

for column in \
  "Title" \
  "Lesson Slug" \
  "Grade/Subject" \
  "Date Needed" \
  "Standards/Source Notes" \
  "Materials" \
  "Status" \
  "Review Status" \
  "Next Action"; do
  check_text "${queue_file}" "${column}" "planning queue includes table column: ${column}"
done

for template in "${templates[@]}"; do
  check_template_review_phrase "${template}"
done

if [[ -f "${queue_file}" ]]; then
  risky_labels_found=0
  for label in "Student:" "Parent email:" "IEP:" "504:" "Medical:" "Behavior:"; do
    if grep -q "${label}" "${queue_file}"; then
      warn "planning queue contains risky label: ${label}"
      risky_labels_found=1
    fi
  done
  if [[ "${risky_labels_found}" == "0" ]]; then
    pass "planning queue has no obvious risky labels"
  fi

  printf '\nStatus Counts\n'
  awk -F '|' '
    BEGIN {
      statuses["idea"] = 0
      statuses["drafted"] = 0
      statuses["reviewed"] = 0
      statuses["ready"] = 0
      statuses["archived"] = 0
    }
    /^\|/ && $0 !~ /^\|[[:space:]]*---/ && $0 !~ /^\|[[:space:]]*Title[[:space:]]*\|/ {
      status = $8
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
      if (status in statuses) {
        statuses[status]++
      }
    }
    END {
      print "- idea: " statuses["idea"]
      print "- drafted: " statuses["drafted"]
      print "- reviewed: " statuses["reviewed"]
      print "- ready: " statuses["ready"]
      print "- archived: " statuses["archived"]
    }
  ' "${queue_file}" || warn "could not parse planning queue status counts"
else
  warn "skipping status counts because planning queue is missing"
fi

printf '\n## Summary\n\n'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
