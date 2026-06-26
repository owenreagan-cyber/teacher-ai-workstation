#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
CRITICAL_FAILURE=0

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

critical_fail() {
  CRITICAL_FAILURE=1
  fail "$1"
}

check_dir() {
  local path="$1"
  if [[ -d "${path}" ]]; then
    pass "directory exists: ${path}"
  else
    critical_fail "directory missing: ${path}"
  fi
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    critical_fail "file missing: ${path}"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local message="$3"

  if [[ ! -f "${path}" ]]; then
    critical_fail "cannot check missing file: ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${message}"
  else
    fail "${message}"
  fi
}

check_review_phrase() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    critical_fail "cannot check missing template: ${path}"
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
  critical_fail "could not resolve Git repo root"
  repo_root="$(pwd -P)"
else
  cd "${repo_root}"
fi

workspace_dir="developer-mode"
queue_file="${workspace_dir}/project-queue.md"
templates_dir="${workspace_dir}/templates"

template_dirs=(
  "${templates_dir}/local-script-tool"
  "${templates_dir}/lesson-helper"
  "${templates_dir}/checklist-generator"
  "${templates_dir}/rubric-helper"
  "${templates_dir}/mini-app-plan"
)

required_files=(
  "${workspace_dir}/README.md"
  "${queue_file}"
  "${templates_dir}/local-script-tool/README.md"
  "${templates_dir}/local-script-tool/tool.sh"
  "${templates_dir}/local-script-tool/test-tool.sh"
  "${templates_dir}/lesson-helper/README.md"
  "${templates_dir}/lesson-helper/lesson-helper.md"
  "${templates_dir}/checklist-generator/README.md"
  "${templates_dir}/checklist-generator/checklist-template.md"
  "${templates_dir}/rubric-helper/README.md"
  "${templates_dir}/rubric-helper/rubric-template.md"
  "${templates_dir}/mini-app-plan/README.md"
  "${templates_dir}/mini-app-plan/app-plan-template.md"
)

planning_templates=(
  "${templates_dir}/lesson-helper/lesson-helper.md"
  "${templates_dir}/checklist-generator/checklist-template.md"
  "${templates_dir}/rubric-helper/rubric-template.md"
  "${templates_dir}/mini-app-plan/app-plan-template.md"
)

printf '\nDeveloper Mode Status\n'
printf 'Repo: %s\n' "${repo_root}"
printf 'Read-only: yes\n\n'

check_dir "${workspace_dir}"
check_dir "${templates_dir}"

for template_dir in "${template_dirs[@]}"; do
  check_dir "${template_dir}"
done

for file in "${required_files[@]}"; do
  check_file "${file}"
done

for status in idea scaffolded testing reviewed ready archived; do
  check_text "${queue_file}" "(^|[^[:alnum:]])${status}([^[:alnum:]]|$)" "project queue mentions allowed status: ${status}"
done

for column in Project Type Purpose Status "Safety Notes" "Next Action"; do
  check_text "${queue_file}" "${column}" "project queue includes table column: ${column}"
done

check_text "${queue_file}" "student-sensitive data|private student data" "project queue includes no student-sensitive data safety language"

for template in "${planning_templates[@]}"; do
  check_review_phrase "${template}"
done

mini_app_template="${templates_dir}/mini-app-plan/app-plan-template.md"
for field in \
  "## Constraints Declaration" \
  "Runs locally:" \
  "Requires internet:" \
  "Requires secrets:" \
  "Writes files:" \
  "Reads files:" \
  "Handles student-sensitive data:" \
  "Requires deployment:" \
  "Requires database:"; do
  check_text "${mini_app_template}" "${field}" "mini-app plan includes constraints field: ${field}"
done

for script in "${templates_dir}/local-script-tool/tool.sh" "${templates_dir}/local-script-tool/test-tool.sh"; do
  if [[ -f "${script}" ]]; then
    if bash -n "${script}"; then
      pass "bash syntax ok: ${script}"
    else
      critical_fail "bash syntax failed: ${script}"
    fi
  else
    critical_fail "cannot syntax-check missing script: ${script}"
  fi
done

if [[ -f "${templates_dir}/local-script-tool/test-tool.sh" ]]; then
  if bash "${templates_dir}/local-script-tool/test-tool.sh" >/dev/null; then
    pass "local-script-tool test passes"
  else
    critical_fail "local-script-tool test failed"
  fi
fi

if [[ -f .gitignore ]] && grep -Fxq "developer-mode/projects/" .gitignore; then
  pass ".gitignore protects developer-mode/projects/"
else
  critical_fail ".gitignore missing developer-mode/projects/"
fi

if [[ -f "${queue_file}" ]]; then
  risky_labels_found=0
  for label in "Student:" "Parent email:" "IEP:" "504:" "Medical:" "Behavior:" "API key:" "Secret:"; do
    if grep -q "${label}" "${queue_file}"; then
      warn "project queue contains risky label: ${label}"
      risky_labels_found=1
    fi
  done
  if [[ "${risky_labels_found}" == "0" ]]; then
    pass "project queue has no obvious risky labels"
  fi

  printf '\nStatus Counts\n'
  status_output="$(awk -F '|' '
    BEGIN {
      allowed["idea"] = 1
      allowed["scaffolded"] = 1
      allowed["testing"] = 1
      allowed["reviewed"] = 1
      allowed["ready"] = 1
      allowed["archived"] = 1
      statuses["idea"] = 0
      statuses["scaffolded"] = 0
      statuses["testing"] = 0
      statuses["reviewed"] = 0
      statuses["ready"] = 0
      statuses["archived"] = 0
    }
    /^\|/ && $0 !~ /^\|[[:space:]]*---/ && $0 !~ /^\|[[:space:]]*Project[[:space:]]*\|/ {
      status = $5
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
      if (status in statuses) {
        statuses[status]++
      } else if (status != "") {
        invalid[status] = 1
      }
    }
    END {
      print "- idea: " statuses["idea"]
      print "- scaffolded: " statuses["scaffolded"]
      print "- testing: " statuses["testing"]
      print "- reviewed: " statuses["reviewed"]
      print "- ready: " statuses["ready"]
      print "- archived: " statuses["archived"]
      for (status in invalid) {
        print "INVALID_STATUS:" status
      }
    }
  ' "${queue_file}")"
  while IFS= read -r line; do
    case "${line}" in
      INVALID_STATUS:*)
        warn "project queue contains invalid status: ${line#INVALID_STATUS:}"
        ;;
      *)
        printf '%s\n' "${line}"
        ;;
    esac
  done <<< "${status_output}"
else
  warn "skipping status counts because project queue is missing"
fi

printf '\n## Summary\n\n'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if (( CRITICAL_FAILURE > 0 )); then
  exit 1
fi

exit 0
