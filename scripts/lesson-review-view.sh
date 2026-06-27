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

usage() {
  cat <<'EOF'
Usage: scripts/lesson-review-view.sh LESSON_SLUG

Show a read-only single-slug lesson review view for one safe lesson slug.
EOF
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s\n' "${value}"
}

is_safe_slug() {
  [[ "$1" =~ ^[a-z0-9][a-z0-9-]*$ ]]
}

cell_at() {
  local index="$1"
  shift
  if (( index < $# )); then
    local cells=("$@")
    printf '%s\n' "${cells[$index]}"
  else
    printf '\n'
  fi
}

risky_label_found() {
  local value="$1"
  local label
  for label in "Student:" "IEP:" "504:" "Medical:" "Behavior:" "API key:" "Secret:" "Token:" "Password:"; do
    if [[ "${value}" == *"${label}"* ]]; then
      return 0
    fi
  done
  return 1
}

yes_no() {
  if [[ "$1" == "1" ]]; then
    printf 'yes\n'
  else
    printf 'no\n'
  fi
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

lesson_slug="$1"

if ! is_safe_slug "${lesson_slug}"; then
  echo "ERROR: unsafe or invalid LESSON_SLUG: ${lesson_slug}" >&2
  echo "Use lowercase letters, numbers, and hyphens only. No spaces, slashes, uppercase, or leading hyphen." >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

queue_file="assistant/lesson-planning/planning-queue.md"
checklist_doc="docs/safe-local-lesson-review-checklist.md"
checklist_script="scripts/lesson-review-checklist-status.sh"
pack_status_script="scripts/lesson-pack-status.sh"
queue_status_script="scripts/lesson-queue-status.sh"
brief_path="assistant/lesson-planning/briefs/${lesson_slug}.md"
activity_path="assistant/lesson-planning/drafts/${lesson_slug}-activity.md"
assessment_path="assistant/lesson-planning/drafts/${lesson_slug}-assessment.md"
materials_path="assistant/lesson-planning/drafts/${lesson_slug}-materials.md"

for required_path in \
  "${queue_file}" \
  "${checklist_doc}" \
  "${checklist_script}" \
  "${pack_status_script}" \
  "${queue_status_script}"; do
  if [[ -f "${required_path}" ]]; then
    pass "required repo file exists: ${required_path}"
  else
    fail "required repo file missing: ${required_path}"
  fi
done

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  printf '\nSummary\n'
  printf '%s\n' '----------------------------------------'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

queue_match=0
queue_title=""
queue_status=""
queue_review_status=""
queue_next_action=""
matched_row_line=""

if [[ -f "${queue_file}" ]]; then
  header_found=0
  separator_found=0
  slug_index=-1
  title_index=-1
  status_index=-1
  review_status_index=-1
  next_action_index=-1
  parse_rows=0
  line_number=0

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line_number=$((line_number + 1))
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
          case "${header_cells[$i]}" in
            Title) title_index="${i}" ;;
            "Lesson Slug") slug_index="${i}" ;;
            Status) status_index="${i}" ;;
            "Review Status") review_status_index="${i}" ;;
            "Next Action") next_action_index="${i}" ;;
          esac
        done
        continue
      fi
    elif (( separator_found == 0 )); then
      if [[ "${line}" == \|* && "${line}" == *"---"* ]]; then
        separator_found=1
        parse_rows=1
        continue
      fi
    elif (( parse_rows == 1 )); then
      if [[ "${line}" != \|* ]]; then
        break
      fi

      if [[ "${line}" == *"| ${lesson_slug} |"* || "${line}" == *"|${lesson_slug}|"* ]]; then
        raw_row="${line#|}"
        raw_row="${raw_row%|}"
        IFS='|' read -r -a row_cells_raw <<< "${raw_row}"
        row_cells=()
        for raw_cell in "${row_cells_raw[@]}"; do
          row_cells+=("$(trim "${raw_cell}")")
        done

        row_slug="$(cell_at "${slug_index}" "${row_cells[@]}")"
        if [[ "${row_slug}" == "${lesson_slug}" ]]; then
          queue_match=1
          matched_row_line="${line_number}"
          queue_title="$(cell_at "${title_index}" "${row_cells[@]}")"
          queue_status="$(cell_at "${status_index}" "${row_cells[@]}")"
          queue_review_status="$(cell_at "${review_status_index}" "${row_cells[@]}")"
          queue_next_action="$(cell_at "${next_action_index}" "${row_cells[@]}")"

          if risky_label_found "${line}"; then
            warn "planning queue row contains risky label for slug: ${lesson_slug}"
          fi
        fi
      fi
    fi
  done < "${queue_file}"
fi

brief_exists=0
activity_exists=0
assessment_exists=0
materials_exists=0

[[ -f "${brief_path}" ]] && brief_exists=1
[[ -f "${activity_path}" ]] && activity_exists=1
[[ -f "${assessment_path}" ]] && assessment_exists=1
[[ -f "${materials_path}" ]] && materials_exists=1

supporting_count=$((activity_exists + assessment_exists + materials_exists))
generated_count=$((brief_exists + supporting_count))

if (( queue_match == 0 )); then
  warn "slug not found in planning queue: ${lesson_slug}"
fi

if (( brief_exists == 0 )); then
  warn "no matching lesson brief found: ${brief_path}"
fi

if (( supporting_count == 0 )); then
  warn "no supporting drafts found for slug: ${lesson_slug}"
elif (( supporting_count < 3 )); then
  warn "only some supporting drafts exist for slug: ${lesson_slug}"
fi

if (( generated_count > 0 )) && [[ ! -f "${checklist_doc}" ]]; then
  warn "generated files exist for slug but checklist doc is missing: ${checklist_doc}"
fi

pass "slug format is safe: ${lesson_slug}"
pass "single-slug review view completed read-only scan"

printf '\nSingle-Slug Lesson Review View\n'
printf '%s\n' '----------------------------------------'
printf 'Slug: %s\n' "${lesson_slug}"
printf 'Read-only: yes\n'

printf '\nQueue Match\n'
printf '%s\n' '----------------------------------------'
printf 'Planning queue row: %s\n' "$(yes_no "${queue_match}")"
if (( queue_match == 1 )); then
  printf '%s\n' "Title: ${queue_title:-unknown}"
  printf '%s\n' "Status: ${queue_status:-unknown}"
  printf '%s\n' "Review status: ${queue_review_status:-unknown}"
  printf '%s\n' "Next action: ${queue_next_action:-unknown}"
  printf '%s\n' "Queue line: ${matched_row_line}"
fi

printf '\nLocal Files\n'
printf '%s\n' '----------------------------------------'
printf 'Brief: %s\n' "$(yes_no "${brief_exists}")"
printf 'Activity draft: %s\n' "$(yes_no "${activity_exists}")"
printf 'Assessment draft: %s\n' "$(yes_no "${assessment_exists}")"
printf 'Materials draft: %s\n' "$(yes_no "${materials_exists}")"

if (( brief_exists == 1 && supporting_count == 3 )); then
  printf 'Pack completeness: complete\n'
elif (( generated_count == 0 )); then
  printf 'Pack completeness: no generated files\n'
else
  printf 'Pack completeness: incomplete\n'
fi

printf '\nReview Reminders\n'
printf '%s\n' '----------------------------------------'
cat <<'EOF'
- Human review required before classroom use.
- Do not include student-sensitive data.
- Do not include real student names.
- Verify source accuracy and curriculum fit.
- Check accessibility, safety, and materials.
EOF

printf '\nSuggested Commands\n'
printf '%s\n' '----------------------------------------'
cat <<'EOF'
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --dashboard
EOF

printf '\nSummary\n'
printf '%s\n' '----------------------------------------'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
