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

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  fail "could not resolve Git repo root"
  repo_root="$(pwd -P)"
else
  cd "${repo_root}"
fi

briefs_dir="assistant/lesson-planning/briefs"
readme="${briefs_dir}/README.md"
create_script="scripts/create-lesson-brief.sh"
template="assistant/lesson-planning/templates/lesson-brief-template.md"

printf '\nLesson Brief Helper Status\n'
printf 'Repo: %s\n' "${repo_root}"
printf 'Read-only: yes\n\n'

check_dir "${briefs_dir}" "lesson briefs directory"
check_file "${readme}" "lesson briefs README"
check_file "${create_script}" "create lesson brief script"

if [[ -f "${create_script}" ]]; then
  if bash -n "${create_script}"; then
    pass "create lesson brief script passes bash syntax"
  else
    fail "create lesson brief script fails bash syntax"
  fi
fi

check_file "${template}" "lesson brief template"
if [[ -f "${template}" ]]; then
  if [[ -s "${template}" ]]; then
    pass "lesson brief template is non-empty"
  else
    fail "lesson-brief-template.md is empty - cannot seed brief draft."
  fi
fi

if [[ -f .gitignore ]] && grep -Fxq 'assistant/lesson-planning/briefs/*.md' .gitignore && grep -Fxq '!assistant/lesson-planning/briefs/README.md' .gitignore; then
  pass ".gitignore protects generated brief drafts and allows README"
else
  fail ".gitignore must ignore assistant/lesson-planning/briefs/*.md and allow briefs/README.md"
fi

briefs=()
if [[ -d "${briefs_dir}" ]]; then
  while IFS= read -r -d '' file; do
    [[ "$(basename "${file}")" == "README.md" ]] && continue
    briefs+=("${file}")
  done < <(find "${briefs_dir}" -maxdepth 1 -type f -name '*.md' -print0 | sort -z)
fi

brief_count="${#briefs[@]}"
pass "generated brief draft count: ${brief_count}"
if (( brief_count > 0 )); then
  printf 'Existing brief drafts:\n'
  limit="${brief_count}"
  (( limit > 5 )) && limit=5
  for ((i=0; i<limit; i++)); do
    printf -- '- %s\n' "$(basename "${briefs[$i]}" .md)"
  done
  if (( brief_count > 5 )); then
    printf -- '- and %s more\n' "$((brief_count - 5))"
  fi
fi

for file in "${briefs[@]}"; do
  base="$(basename "${file}")"
  head_15="$(head -15 "${file}")"
  grep -q 'Status: draft' <<<"${head_15}" && pass "${base} metadata includes Status: draft" || warn "${base} metadata missing Status: draft"
  grep -q 'Human review required: yes' <<<"${head_15}" && pass "${base} metadata includes human review requirement" || warn "${base} metadata missing Human review required: yes"
  grep -q 'Student-sensitive data allowed: no' <<<"${head_15}" && pass "${base} metadata blocks student-sensitive data" || warn "${base} metadata missing Student-sensitive data allowed: no"
  grep -q 'Safety Notice' "${file}" && pass "${base} includes Safety Notice" || warn "${base} missing Safety Notice"
  risky_found=0
  for label in 'Student:' 'Parent email:' 'IEP:' '504:' 'Medical:' 'Behavior:' 'API key:' 'Secret:'; do
    if grep -q "${label}" "${file}"; then
      warn "${base} contains risky label: ${label}"
      risky_found=1
    fi
  done
  [[ "${risky_found}" == "0" ]] && pass "${base} has no obvious risky labels"
done

printf '\nSummary\n'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
