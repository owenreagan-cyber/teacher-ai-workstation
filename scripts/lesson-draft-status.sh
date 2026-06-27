#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '[PASS] %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf '[WARN] %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf '[FAIL] %s\n' "$1"; }

check_file() { [[ -f "$1" ]] && pass "$2 exists: $1" || fail "$2 missing: $1"; }
check_dir() { [[ -d "$1" ]] && pass "$2 exists: $1" || fail "$2 missing: $1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

if [[ ! -d "${repo_root}/assistant/lesson-planning/templates" ]]; then
  fail "Could not resolve repo root correctly."
fi

drafts_dir="assistant/lesson-planning/drafts"
readme="${drafts_dir}/README.md"
create_script="scripts/create-lesson-draft.sh"
templates=(
  "assistant/lesson-planning/templates/activity-template.md"
  "assistant/lesson-planning/templates/assessment-template.md"
  "assistant/lesson-planning/templates/materials-checklist-template.md"
)

printf '\nLesson Draft Helper Status\n'
printf 'Repo: %s\n' "${repo_root}"
printf 'Read-only: yes\n\n'

check_dir "${drafts_dir}" "lesson drafts directory"
check_file "${readme}" "lesson drafts README"
check_file "${create_script}" "create lesson draft script"

if [[ -f "${create_script}" ]]; then
  if bash -n "${create_script}"; then
    pass "create lesson draft script passes bash syntax"
  else
    fail "create lesson draft script fails bash syntax"
  fi
fi

for template in "${templates[@]}"; do
  check_file "${template}" "lesson draft template"
  if [[ -f "${template}" ]]; then
    if [[ -s "${template}" ]]; then
      pass "lesson draft template is non-empty: ${template}"
    else
      fail "lesson draft template is empty: ${template}"
    fi
  fi
done

if git check-ignore -q "assistant/lesson-planning/drafts/test-ignore-check.md" 2>/dev/null; then
  pass ".gitignore protects generated lesson drafts"
else
  fail ".gitignore does not protect generated lesson drafts"
fi

if git check-ignore -q "assistant/lesson-planning/drafts/README.md" 2>/dev/null; then
  fail ".gitignore incorrectly ignores drafts README"
else
  pass ".gitignore allows drafts README"
fi

drafts=()
if [[ -d "${drafts_dir}" ]]; then
  while IFS= read -r -d '' file; do
    drafts+=("${file}")
  done < <(find "${drafts_dir}" -maxdepth 1 -type f -name "*.md" ! -name "README.md" -print0 2>/dev/null | sort -z)
fi

draft_count="${#drafts[@]}"
pass "generated lesson draft count: ${draft_count}"

if (( draft_count > 0 )); then
  printf 'Existing lesson drafts:\n'
  limit="${draft_count}"
  (( limit > 5 )) && limit=5
  for ((i=0; i<limit; i++)); do
    printf -- '- %s\n' "$(basename "${drafts[$i]}" .md)"
  done
  if (( draft_count > 5 )); then
    printf -- '- and %s more\n' "$((draft_count - 5))"
  fi

  for file in "${drafts[@]}"; do
    base="$(basename "${file}")"
    head_15="$(head -15 "${file}")"
    grep -q 'Status: draft' <<<"${head_15}" && pass "${base} metadata includes Status: draft" || warn "${base} metadata missing Status: draft"
    grep -q 'Human review required: yes' <<<"${head_15}" && pass "${base} metadata includes human review requirement" || warn "${base} metadata missing Human review required: yes"
    grep -q 'Student-sensitive data allowed: no' <<<"${head_15}" && pass "${base} metadata blocks student-sensitive data" || warn "${base} metadata missing Student-sensitive data allowed: no"
    grep -q 'Safety Notice' "${file}" && pass "${base} includes Safety Notice" || warn "${base} missing Safety Notice"
    risky_found=0
    for label in 'Student:' 'Parent email:' 'IEP:' '504:' 'Medical:' 'Behavior:' 'API key:' 'Secret:' 'Token:' 'Password:'; do
      if grep -q "${label}" "${file}"; then
        warn "${base} contains risky label: ${label}"
        risky_found=1
      fi
    done
    [[ "${risky_found}" == "0" ]] && pass "${base} has no obvious risky labels"
  done
fi

printf '\nSummary\n'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
