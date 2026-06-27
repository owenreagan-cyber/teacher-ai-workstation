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

is_safe_slug() {
  [[ "$1" =~ ^[a-z0-9][a-z0-9-]*$ ]]
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s\n' "${value}"
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

guide="docs/lesson-planning-workflow-guide.md"
queue_file="assistant/lesson-planning/planning-queue.md"
briefs_dir="assistant/lesson-planning/briefs"
drafts_dir="assistant/lesson-planning/drafts"

required_files=(
  "${guide}"
  "${queue_file}"
  "scripts/lesson-planning-status.sh"
  "scripts/lesson-brief-status.sh"
  "scripts/lesson-draft-status.sh"
  "scripts/lesson-pack-status.sh"
  "scripts/lesson-queue-status.sh"
  "scripts/create-lesson-brief.sh"
  "scripts/create-lesson-draft.sh"
  "bin/chief-of-staff"
)

syntax_files=(
  "scripts/lesson-planning-status.sh"
  "scripts/lesson-brief-status.sh"
  "scripts/lesson-draft-status.sh"
  "scripts/lesson-pack-status.sh"
  "scripts/lesson-queue-status.sh"
  "scripts/create-lesson-brief.sh"
  "scripts/create-lesson-draft.sh"
  "bin/chief-of-staff"
)

section "Workflow Sequence"
cat <<'EOF'
1. Review planning queue
2. Confirm safe lesson slug
3. Create/review lesson brief draft
4. Create/review supporting drafts
5. Check lesson pack status
6. Check lesson queue status
7. Human review before classroom use
EOF

section "Command Reference"
cat <<'EOF'
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --create-lesson-brief LESSON_SLUG
bin/chief-of-staff --create-lesson-draft activity LESSON_SLUG
bin/chief-of-staff --create-lesson-draft assessment LESSON_SLUG
bin/chief-of-staff --create-lesson-draft materials LESSON_SLUG
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --dashboard
EOF

section "Workflow Checks"

for file in "${required_files[@]}"; do
  check_file "${file}"
done

for file in "${syntax_files[@]}"; do
  check_bash_syntax "${file}"
done

check_text "${queue_file}" "Lesson Slug" "planning queue includes Lesson Slug"
check_text "${guide}" "human review" "workflow guide mentions human review"
check_text "${guide}" "no student-sensitive data" "workflow guide mentions no student-sensitive data"
check_text "${guide}" "local only" "workflow guide mentions local only"
check_text "${guide}" "lesson-queue-status|lesson queue status" "workflow guide mentions lesson queue status"
check_text "${guide}" "lesson-pack-status|lesson pack status" "workflow guide mentions lesson pack status"
check_text "${guide}" "Gmail/Drive integrations|Gmail.*Google Drive|Gmail.*Drive" "workflow guide mentions no Gmail/Drive integrations"
for command in \
  "bin/chief-of-staff --lesson-status" \
  "bin/chief-of-staff --lesson-queue-status" \
  "bin/chief-of-staff --create-lesson-brief LESSON_SLUG" \
  "bin/chief-of-staff --create-lesson-draft activity LESSON_SLUG" \
  "bin/chief-of-staff --create-lesson-draft assessment LESSON_SLUG" \
  "bin/chief-of-staff --create-lesson-draft materials LESSON_SLUG" \
  "bin/chief-of-staff --lesson-pack-status" \
  "bin/chief-of-staff --dashboard"; do
  check_text "${guide}" "${command}" "workflow guide mentions command: ${command}"
done

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

if [[ -f "${queue_file}" ]]; then
  header_found=0
  slug_index=-1
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if (( header_found == 0 )); then
      if [[ "${line}" == \|* && "${line}" == *"Title"* && "${line}" == *"Lesson Slug"* ]]; then
        header_found=1
        raw_header="${line#|}"
        raw_header="${raw_header%|}"
        IFS='|' read -r -a header_cells_raw <<< "${raw_header}"
        header_cells=()
        for raw_cell in "${header_cells_raw[@]}"; do
          header_cells+=("$(trim "${raw_cell}")")
        done
        for ((i=0; i<${#header_cells[@]}; i++)); do
          if [[ "${header_cells[$i]}" == "Lesson Slug" ]]; then
            slug_index="${i}"
          fi
        done
        continue
      fi
    elif [[ "${line}" == \|* && "${line}" == *"---"* ]]; then
      continue
    elif [[ "${line}" == \|* ]]; then
      raw_row="${line#|}"
      raw_row="${raw_row%|}"
      IFS='|' read -r -a row_cells_raw <<< "${raw_row}"
      if (( slug_index >= 0 && ${#row_cells_raw[@]} > slug_index )); then
        slug="$(trim "${row_cells_raw[$slug_index]}")"
        if [[ -z "${slug}" ]]; then
          warn "planning queue contains blank Lesson Slug"
        elif ! is_safe_slug "${slug}"; then
          warn "planning queue contains unsafe Lesson Slug: ${slug}"
        fi
      fi
    elif (( header_found == 1 )); then
      break
    fi
  done < "${queue_file}"
fi

if [[ -f scripts/lesson-queue-status.sh ]]; then
  queue_result=0
  queue_output="$(bash scripts/lesson-queue-status.sh 2>&1)" || queue_result=$?
  queue_warn="$(summary_count "${queue_output}" "WARN")"
  queue_fail="$(summary_count "${queue_output}" "FAIL")"
  if [[ "${queue_result}" != "0" ]]; then
    fail "lesson queue status command failed"
  elif [[ -n "${queue_warn}" && "${queue_warn}" -gt 0 ]]; then
    warn "lesson queue status currently reports ${queue_warn} warning(s)"
  fi
  if [[ -n "${queue_fail}" && "${queue_fail}" -gt 0 ]]; then
    fail "lesson queue status reports ${queue_fail} failure(s)"
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
