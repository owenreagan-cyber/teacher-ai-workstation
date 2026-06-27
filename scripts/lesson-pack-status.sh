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

is_safe_slug() {
  [[ "$1" =~ ^[a-z0-9][a-z0-9-]*$ ]]
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

contains_slug() {
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

add_unique_slug() {
  local slug="$1"
  if (( ${#pack_slugs[@]} == 0 )) || ! contains_slug "${slug}" "${pack_slugs[@]}"; then
    pack_slugs+=("${slug}")
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

briefs_dir="assistant/lesson-planning/briefs"
drafts_dir="assistant/lesson-planning/drafts"

pack_slugs=()
brief_slugs=()
activity_slugs=()
assessment_slugs=()
materials_slugs=()

generated_briefs=0
generated_drafts=0

if [[ ! -d "${briefs_dir}" ]]; then
  fail "lesson briefs directory missing: ${briefs_dir}"
else
  pass "lesson briefs directory exists: ${briefs_dir}"
  while IFS= read -r -d '' file; do
    filename="$(basename "${file}" .md)"
    if ! is_safe_slug "${filename}"; then
      warn "ignored unsafe lesson slug: ${filename}"
      continue
    fi
    brief_slugs+=("${filename}")
    add_unique_slug "${filename}"
    generated_briefs=$((generated_briefs + 1))
  done < <(find "${briefs_dir}" -maxdepth 1 -type f -name "*.md" ! -name "README.md" -print0 2>/dev/null | sort -z)
  pass "generated lesson brief scan completed"
fi

if [[ ! -d "${drafts_dir}" ]]; then
  fail "lesson drafts directory missing: ${drafts_dir}"
else
  pass "lesson drafts directory exists: ${drafts_dir}"
  while IFS= read -r -d '' file; do
    filename="$(basename "${file}" .md)"
    slug=""
    type=""

    if [[ "${filename}" == *"-activity" ]]; then
      slug="${filename%-activity}"
      type="activity"
    elif [[ "${filename}" == *"-assessment" ]]; then
      slug="${filename%-assessment}"
      type="assessment"
    elif [[ "${filename}" == *"-materials" ]]; then
      slug="${filename%-materials}"
      type="materials"
    else
      warn "unrecognized draft file ignored: ${file}"
      continue
    fi

    if ! is_safe_slug "${slug}"; then
      warn "ignored unsafe lesson slug: ${slug}"
      continue
    fi

    case "${type}" in
      activity) activity_slugs+=("${slug}") ;;
      assessment) assessment_slugs+=("${slug}") ;;
      materials) materials_slugs+=("${slug}") ;;
    esac
    add_unique_slug "${slug}"
    generated_drafts=$((generated_drafts + 1))
  done < <(find "${drafts_dir}" -maxdepth 1 -type f -name "*.md" ! -name "README.md" -print0 2>/dev/null | sort -z)
  pass "generated lesson draft scan completed"
fi

pack_count="${#pack_slugs[@]}"
complete_packs=0
draft_only_packs=0

if (( pack_count > 0 )); then
  while IFS= read -r slug; do
    has_brief="no"
    has_activity="no"
    has_assessment="no"
    has_materials="no"

    if (( ${#brief_slugs[@]} > 0 )) && contains_slug "${slug}" "${brief_slugs[@]}"; then
      has_brief="yes"
    fi
    if (( ${#activity_slugs[@]} > 0 )) && contains_slug "${slug}" "${activity_slugs[@]}"; then
      has_activity="yes"
    fi
    if (( ${#assessment_slugs[@]} > 0 )) && contains_slug "${slug}" "${assessment_slugs[@]}"; then
      has_assessment="yes"
    fi
    if (( ${#materials_slugs[@]} > 0 )) && contains_slug "${slug}" "${materials_slugs[@]}"; then
      has_materials="yes"
    fi

    if [[ "${has_brief}" == "yes" && "${has_activity}" == "yes" && "${has_assessment}" == "yes" && "${has_materials}" == "yes" ]]; then
      complete_packs=$((complete_packs + 1))
    fi
    if [[ "${has_brief}" == "no" && ( "${has_activity}" == "yes" || "${has_assessment}" == "yes" || "${has_materials}" == "yes" ) ]]; then
      draft_only_packs=$((draft_only_packs + 1))
    fi
  done < <(printf '%s\n' "${pack_slugs[@]}" | sort)
fi

incomplete_packs=$((pack_count - complete_packs))
pass "lesson pack counts calculated"

section "Pack Counts"
printf 'Generated briefs: %s\n' "${generated_briefs}"
printf 'Generated drafts: %s\n' "${generated_drafts}"
printf 'Lesson packs: %s\n' "${pack_count}"
printf 'Complete packs: %s\n' "${complete_packs}"
printf 'Incomplete packs: %s\n' "${incomplete_packs}"
printf 'Draft-only packs: %s\n' "${draft_only_packs}"

section "Lesson Packs"
if (( pack_count == 0 )); then
  printf 'No lesson packs found yet.\n'
  warn "no lesson packs found yet"
else
  printf '%-28s %-5s %-8s %-10s %-9s %s\n' "Slug" "Brief" "Activity" "Assessment" "Materials" "Status"
  while IFS= read -r slug; do
    has_brief="no"
    has_activity="no"
    has_assessment="no"
    has_materials="no"
    status="incomplete"

    if (( ${#brief_slugs[@]} > 0 )) && contains_slug "${slug}" "${brief_slugs[@]}"; then
      has_brief="yes"
    fi
    if (( ${#activity_slugs[@]} > 0 )) && contains_slug "${slug}" "${activity_slugs[@]}"; then
      has_activity="yes"
    fi
    if (( ${#assessment_slugs[@]} > 0 )) && contains_slug "${slug}" "${assessment_slugs[@]}"; then
      has_assessment="yes"
    fi
    if (( ${#materials_slugs[@]} > 0 )) && contains_slug "${slug}" "${materials_slugs[@]}"; then
      has_materials="yes"
    fi

    if [[ "${has_brief}" == "yes" && "${has_activity}" == "yes" && "${has_assessment}" == "yes" && "${has_materials}" == "yes" ]]; then
      status="complete"
    elif [[ "${has_brief}" == "no" ]]; then
      status="draft-only"
    fi

    display_slug="${slug}"
    if (( ${#display_slug} > 28 )); then
      display_slug="${display_slug:0:25}..."
    fi
    printf '%-28s %-5s %-8s %-10s %-9s %s\n' "${display_slug}" "${has_brief}" "${has_activity}" "${has_assessment}" "${has_materials}" "${status}"
  done < <(printf '%s\n' "${pack_slugs[@]}" | sort)
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
