#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
CRITICAL_FAILURE=0

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

critical_fail() {
  CRITICAL_FAILURE=1
  fail "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

capture_command() {
  local __output_var="$1"
  local __result_var="$2"
  local output=""
  local result=0
  shift 2

  output="$("$@" 2>&1)" || result=$?
  printf -v "${__output_var}" '%s' "${output}"
  printf -v "${__result_var}" '%s' "${result}"
}

summary_count() {
  local output="$1"
  local label="$2"
  printf '%s\n' "${output}" | awk -v label="${label}" '$1 == label ":" && $2 ~ /^[0-9]+$/ { value = $2 } END { if (value != "") print value }'
}

print_compact_summary() {
  local label="$1"
  local output="$2"
  local result="$3"
  local pass_count
  local warn_count
  local fail_count

  pass_count="$(summary_count "${output}" "PASS")"
  warn_count="$(summary_count "${output}" "WARN")"
  fail_count="$(summary_count "${output}" "FAIL")"

  if [[ -n "${pass_count}" && -n "${warn_count}" && -n "${fail_count}" ]]; then
    printf '%s: PASS %s / WARN %s / FAIL %s\n' "${label}" "${pass_count}" "${warn_count}" "${fail_count}"
  else
    printf '%s: summary could not be parsed; full output follows.\n' "${label}"
    printf '%s\n' "${output}" | sed 's/^/  /'
  fi

  if [[ "${result}" == "0" ]]; then
    pass "${label} command completed"
  else
    fail "${label} command exited nonzero"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    warn "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    warn "${label}"
  fi
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  critical_fail "could not resolve Git repo root"
  repo_root="$(pwd -P)"
else
  cd "${repo_root}"
fi

branch="$(git branch --show-current 2>/dev/null || true)"
commit="$(git rev-parse --short HEAD 2>/dev/null || true)"
run_at="$(date '+%Y-%m-%d %H:%M:%S')"

printf '\nTeacher Chief of Staff Dashboard\n'
printf 'Repo: %s\n' "${repo_root}"
printf 'Branch: %s\n' "${branch:-unknown}"
printf 'Commit: %s\n' "${commit:-unknown}"
printf 'Run at: %s\n' "${run_at}"
printf 'Read-only: yes\n'

section "Workstation Phase Status"
if [[ -f scripts/verify-phase-0e.sh ]]; then
  phase_0e_output=""
  phase_0e_result=0
  capture_command phase_0e_output phase_0e_result bash scripts/verify-phase-0e.sh
  print_compact_summary "Phase 0E" "${phase_0e_output}" "${phase_0e_result}"
else
  warn "Phase 0E verifier missing: scripts/verify-phase-0e.sh"
fi

if [[ -f scripts/phase-1-status.sh ]]; then
  phase_1_output=""
  phase_1_result=0
  capture_command phase_1_output phase_1_result bash scripts/phase-1-status.sh
  print_compact_summary "Phase 1" "${phase_1_output}" "${phase_1_result}"
else
  warn "Phase 1 status script missing: scripts/phase-1-status.sh"
fi

section "Available Chief of Staff Workflows"
if [[ ! -f bin/chief-of-staff ]]; then
  fail "Chief of Staff CLI missing: bin/chief-of-staff"
elif [[ ! -x bin/chief-of-staff ]]; then
  warn "Chief of Staff CLI is not executable. Fix with: chmod +x bin/chief-of-staff"
else
  workflows_output=""
  workflows_result=0
  capture_command workflows_output workflows_result bin/chief-of-staff --list-workflows
  if [[ "${workflows_result}" == "0" ]]; then
    pass "Chief of Staff workflows loaded"
    printf '%s\n' "${workflows_output}" | sed 's/^/- /'
  else
    fail "Chief of Staff workflow listing failed"
    printf '%s\n' "${workflows_output}" | sed 's/^/  /'
  fi
fi

section "LLM CLI Readiness"
llm_path="$(command -v llm 2>/dev/null || true)"
if [[ -z "${llm_path}" ]]; then
  warn "llm CLI not found; Chief of Staff workflows that call llm may not run yet."
else
  pass "llm CLI found: ${llm_path}"
  llm_default_output=""
  llm_default_result=0
  capture_command llm_default_output llm_default_result llm models default
  if [[ "${llm_default_result}" == "0" && -n "${llm_default_output}" ]]; then
    pass "llm default model detected: ${llm_default_output}"
  else
    warn "llm default model could not be detected with a local llm command."
  fi
fi

section "Memory Status"
for memory_file in assistant/memory/active-priorities.md assistant/memory/projects.md; do
  if [[ -f "${memory_file}" ]]; then
    pass "memory file present: ${memory_file}"
  else
    warn "memory file missing: ${memory_file}"
  fi

  check_text "${memory_file}" "Phase 0E" "${memory_file} mentions Phase 0E"
  check_text "${memory_file}" "Phase 1" "${memory_file} mentions Phase 1"
  check_text "${memory_file}" "Chief of Staff|Developer Mode" "${memory_file} mentions Chief of Staff or Developer Mode"
  check_text "${memory_file}" "dashboard|command launcher" "${memory_file} mentions dashboard or command launcher"
done

old_memory_output=""
old_memory_result=0
capture_command old_memory_output old_memory_result find assistant/memory -name "*.md" -mtime +30 -print
if [[ "${old_memory_result}" != "0" ]]; then
  warn "memory age check could not run"
elif [[ -n "${old_memory_output}" ]]; then
  warn "memory file may be stale"
  printf '%s\n' "${old_memory_output}" | sed 's/^/  /'
else
  pass "memory files appear recently maintained"
fi

section "Intake Status"
if [[ -x bin/chief-of-staff ]]; then
  intake_output=""
  intake_result=0
  capture_command intake_output intake_result bin/chief-of-staff --intake-status
  if [[ "${intake_result}" == "0" ]]; then
    pass "intake status command completed"
    printf '%s\n' "${intake_output}" | sed -n '1,18p' | sed 's/^/  /'
  else
    warn "intake status needs attention"
    printf '%s\n' "${intake_output}" | sed 's/^/  /'
  fi
else
  warn "skipping intake status because bin/chief-of-staff is not executable"
fi

section "Lesson Planning Workspace"
if [[ -f scripts/lesson-planning-status.sh ]]; then
  lesson_output=""
  lesson_result=0
  capture_command lesson_output lesson_result bash scripts/lesson-planning-status.sh
  lesson_pass="$(summary_count "${lesson_output}" "PASS")"
  lesson_warn="$(summary_count "${lesson_output}" "WARN")"
  lesson_fail="$(summary_count "${lesson_output}" "FAIL")"

  if [[ -n "${lesson_pass}" && -n "${lesson_warn}" && -n "${lesson_fail}" ]]; then
    printf 'Lesson Planning: PASS %s / WARN %s / FAIL %s\n' "${lesson_pass}" "${lesson_warn}" "${lesson_fail}"
  else
    printf 'Lesson Planning: status command completed\n'
  fi

  if [[ "${lesson_result}" == "0" ]]; then
    pass "lesson planning workspace status completed"
  else
    fail "lesson planning workspace status failed"
  fi
else
  warn "lesson planning status script missing: scripts/lesson-planning-status.sh"
fi

section "Developer Mode"
if [[ -f scripts/developer-mode-status.sh ]]; then
  developer_output=""
  developer_result=0
  capture_command developer_output developer_result bash scripts/developer-mode-status.sh
  developer_pass="$(summary_count "${developer_output}" "PASS")"
  developer_warn="$(summary_count "${developer_output}" "WARN")"
  developer_fail="$(summary_count "${developer_output}" "FAIL")"

  if [[ -n "${developer_pass}" && -n "${developer_warn}" && -n "${developer_fail}" ]]; then
    printf 'Developer Mode: PASS %s / WARN %s / FAIL %s\n' "${developer_pass}" "${developer_warn}" "${developer_fail}"
  else
    printf 'Developer Mode: status command completed\n'
  fi

  if [[ "${developer_result}" == "0" ]]; then
    pass "Developer Mode status completed"
  else
    fail "Developer Mode status failed"
  fi
else
  warn "Developer Mode status script missing: scripts/developer-mode-status.sh"
fi

section "Build Queue / Next Action"
if [[ -f docs/build-queue.md ]]; then
  next_pr="$(awk '
    /^## Next PR[[:space:]]*$/ { in_next = 1; next }
    in_next && NF > 0 { print; exit }
  ' docs/build-queue.md)"
  if [[ -n "${next_pr}" ]]; then
    pass "next recommended PR found"
    printf 'Next recommended PR: %s\n' "${next_pr}"
  else
    warn "Next recommended PR could not be read from docs/build-queue.md."
  fi
else
  warn "build queue missing: docs/build-queue.md"
fi

section "Safety Reminders"
cat <<'EOF'
- Local/read-only dashboard.
- No Gmail/Drive/email yet.
- No student-sensitive data by default.
- Human review before sending/sharing.
- Connected services require explicit future permission.
EOF

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
printf 'Health: %s/%s checks passing\n' "${PASS_COUNT}" "$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))"

if (( CRITICAL_FAILURE > 0 )); then
  exit 1
fi

exit 0
