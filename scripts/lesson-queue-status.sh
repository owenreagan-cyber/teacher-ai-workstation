#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
pass_messages=()
warning_messages=()
failure_messages=()

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  pass_messages+=("PASS: $1")
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  warning_messages+=("WARN: $1")
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  failure_messages+=("FAIL: $1")
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
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

contains_value() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    if [[ "${item}" == "${needle}" ]]; then
      return 0
    fi
  done
  return 1
}

truncate_display() {
  local value="$1"
  local max_length="$2"
  if (( ${#value} > max_length )); then
    printf '%s...\n' "${value:0:$((max_length - 3))}"
  else
    printf '%s\n' "${value}"
  fi
}

risky_label_found() {
  local value="$1"
  local label
  for label in "Student:" "Parent email:" "IEP:" "504:" "Medical:" "Behavior:" "API key:" "Secret:" "Token:" "Password:"; do
    if [[ "${value}" == *"${label}"* ]]; then
      return 0
    fi
  done
  return 1
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

queue_file="assistant/lesson-planning/planning-queue.md"
briefs_dir="assistant/lesson-planning/briefs"
drafts_dir="assistant/lesson-planning/drafts"
pack_status_script="scripts/lesson-pack-status.sh"
self_script="scripts/lesson-queue-status.sh"

queue_titles=()
queue_slugs=()
queue_statuses=()
queue_review_statuses=()
queue_next_actions=()
safe_slugs_seen=()

queue_entries=0
safe_slug_rows=0
missing_slug_rows=0
unsafe_slug_rows=0
matching_brief_rows=0
supporting_draft_rows=0
complete_pack_rows=0
no_generated_file_rows=0

if [[ -f "${queue_file}" ]]; then
  pass "planning queue file exists: ${queue_file}"
else
  fail "planning queue file missing: ${queue_file}"
fi

if [[ -d "${briefs_dir}" ]]; then
  pass "briefs directory exists: ${briefs_dir}"
else
  fail "briefs directory missing: ${briefs_dir}"
fi

if [[ -d "${drafts_dir}" ]]; then
  pass "drafts directory exists: ${drafts_dir}"
else
  fail "drafts directory missing: ${drafts_dir}"
fi

if [[ -f "${pack_status_script}" ]]; then
  pass "lesson pack status script exists: ${pack_status_script}"
else
  fail "lesson pack status script missing: ${pack_status_script}"
fi

if [[ -f "${self_script}" ]] && bash -n "${self_script}"; then
  pass "lesson queue status script passes bash syntax"
else
  fail "lesson queue status script fails bash syntax"
fi

header_found=0
separator_found=0
title_index=-1
slug_index=-1
status_index=-1
review_status_index=-1
next_action_index=-1
parse_rows=0
line_number=0

if [[ -f "${queue_file}" ]]; then
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
      fail "planning queue table separator missing after header"
      parse_rows=0
      break
    elif (( parse_rows == 1 )); then
      if [[ "${line}" != \|* ]]; then
        break
      fi
      raw_row="${line#|}"
      raw_row="${raw_row%|}"
      IFS='|' read -r -a row_cells_raw <<< "${raw_row}"
      row_cells=()
      for raw_cell in "${row_cells_raw[@]}"; do
        row_cells+=("$(trim "${raw_cell}")")
      done

      required_max="${title_index}"
      for required_index in "${slug_index}" "${status_index}" "${review_status_index}" "${next_action_index}"; do
        if (( required_index > required_max )); then
          required_max="${required_index}"
        fi
      done
      if (( ${#row_cells[@]} <= required_max )); then
        warn "unexpected table shape skipped safely at line ${line_number}"
        continue
      fi

      title="$(cell_at "${title_index}" "${row_cells[@]}")"
      slug="$(cell_at "${slug_index}" "${row_cells[@]}")"
      queue_status="$(cell_at "${status_index}" "${row_cells[@]}")"
      review_status="$(cell_at "${review_status_index}" "${row_cells[@]}")"
      next_action="$(cell_at "${next_action_index}" "${row_cells[@]}")"
      queue_entries=$((queue_entries + 1))

      if risky_label_found "${line}"; then
        warn "queue row contains risky label: ${title:-line ${line_number}}"
      fi

      if [[ -z "${slug}" ]]; then
        missing_slug_rows=$((missing_slug_rows + 1))
        warn "queue row missing Lesson Slug: ${title:-line ${line_number}}"
        queue_titles+=("${title}")
        queue_slugs+=("")
        queue_statuses+=("${queue_status}")
        queue_review_statuses+=("${review_status}")
        queue_next_actions+=("${next_action}")
        continue
      fi

      if ! is_safe_slug "${slug}"; then
        unsafe_slug_rows=$((unsafe_slug_rows + 1))
        warn "queue row has unsafe Lesson Slug: ${slug}"
        queue_titles+=("${title}")
        queue_slugs+=("${slug}")
        queue_statuses+=("${queue_status}")
        queue_review_statuses+=("${review_status}")
        queue_next_actions+=("${next_action}")
        continue
      fi

      if (( ${#safe_slugs_seen[@]} > 0 )) && contains_value "${slug}" "${safe_slugs_seen[@]}"; then
        warn "duplicate safe lesson slug in queue: ${slug}"
      else
        safe_slugs_seen+=("${slug}")
      fi

      safe_slug_rows=$((safe_slug_rows + 1))
      queue_titles+=("${title}")
      queue_slugs+=("${slug}")
      queue_statuses+=("${queue_status}")
      queue_review_statuses+=("${review_status}")
      queue_next_actions+=("${next_action}")
    fi
  done < "${queue_file}"
fi

if (( header_found == 1 )); then
  pass "planning queue has a Markdown table"
else
  fail "planning queue Markdown table missing"
fi

if (( slug_index >= 0 )); then
  pass "planning queue has Lesson Slug column"
else
  fail "planning queue missing Lesson Slug column"
fi

if (( queue_entries == 0 )); then
  warn "zero planning queue entries found"
fi

pass "queue scan completed"

for ((i=0; i<${#queue_slugs[@]}; i++)); do
  slug="${queue_slugs[$i]}"
  [[ -n "${slug}" ]] || continue
  is_safe_slug "${slug}" || continue

  has_brief="no"
  has_activity="no"
  has_assessment="no"
  has_materials="no"

  [[ -f "${briefs_dir}/${slug}.md" ]] && has_brief="yes"
  [[ -f "${drafts_dir}/${slug}-activity.md" ]] && has_activity="yes"
  [[ -f "${drafts_dir}/${slug}-assessment.md" ]] && has_assessment="yes"
  [[ -f "${drafts_dir}/${slug}-materials.md" ]] && has_materials="yes"

  if [[ "${has_brief}" == "yes" ]]; then
    matching_brief_rows=$((matching_brief_rows + 1))
  else
    warn "queue row has slug but no matching brief: ${slug}"
  fi

  if [[ "${has_activity}" == "yes" || "${has_assessment}" == "yes" || "${has_materials}" == "yes" ]]; then
    supporting_draft_rows=$((supporting_draft_rows + 1))
  else
    warn "queue row has slug but no supporting drafts: ${slug}"
  fi

  if [[ "${has_brief}" == "yes" && "${has_activity}" == "yes" && "${has_assessment}" == "yes" && "${has_materials}" == "yes" ]]; then
    complete_pack_rows=$((complete_pack_rows + 1))
  fi

  if [[ "${has_brief}" == "no" && "${has_activity}" == "no" && "${has_assessment}" == "no" && "${has_materials}" == "no" ]]; then
    no_generated_file_rows=$((no_generated_file_rows + 1))
  fi
done

pass "local artifact lookup completed"
pass "no write action attempted"

section "Queue Counts"
printf 'Queue entries: %s\n' "${queue_entries}"
printf 'Rows with safe slugs: %s\n' "${safe_slug_rows}"
printf 'Rows missing slugs: %s\n' "${missing_slug_rows}"
printf 'Rows with unsafe slugs: %s\n' "${unsafe_slug_rows}"
printf 'Rows with matching briefs: %s\n' "${matching_brief_rows}"
printf 'Rows with any supporting drafts: %s\n' "${supporting_draft_rows}"
printf 'Rows with complete packs: %s\n' "${complete_pack_rows}"
printf 'Rows with no generated lesson files: %s\n' "${no_generated_file_rows}"

section "Lesson Queue Integration"
if (( queue_entries == 0 )); then
  printf 'No planning queue entries found yet.\n'
else
  printf '%-30s %-28s %-5s %-8s %-10s %-9s %-12s %s\n' "Title" "Slug" "Brief" "Activity" "Assessment" "Materials" "Queue Status" "Review Status"
  for ((i=0; i<${#queue_titles[@]}; i++)); do
    title="${queue_titles[$i]}"
    slug="${queue_slugs[$i]}"
    queue_status="${queue_statuses[$i]}"
    review_status="${queue_review_statuses[$i]}"
    has_brief="no"
    has_activity="no"
    has_assessment="no"
    has_materials="no"

    if [[ -n "${slug}" ]] && is_safe_slug "${slug}"; then
      [[ -f "${briefs_dir}/${slug}.md" ]] && has_brief="yes"
      [[ -f "${drafts_dir}/${slug}-activity.md" ]] && has_activity="yes"
      [[ -f "${drafts_dir}/${slug}-assessment.md" ]] && has_assessment="yes"
      [[ -f "${drafts_dir}/${slug}-materials.md" ]] && has_materials="yes"
    fi

    display_title="$(truncate_display "${title}" 30)"
    display_slug="$(truncate_display "${slug:-[blank]}" 28)"
    printf '%-30s %-28s %-5s %-8s %-10s %-9s %-12s %s\n' "${display_title}" "${display_slug}" "${has_brief}" "${has_activity}" "${has_assessment}" "${has_materials}" "${queue_status}" "${review_status}"
  done
fi

if (( ${#failure_messages[@]} > 0 )); then
  for message in "${failure_messages[@]}"; do
    printf '%s\n' "${message}"
  done
fi

if (( ${#pass_messages[@]} > 0 )); then
  for message in "${pass_messages[@]}"; do
    printf '%s\n' "${message}"
  done
fi

if (( ${#warning_messages[@]} > 0 )); then
  for message in "${warning_messages[@]}"; do
    printf '%s\n' "${message}"
  done
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
