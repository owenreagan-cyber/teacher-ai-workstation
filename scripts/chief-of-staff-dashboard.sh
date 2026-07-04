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

group_banner() {
  printf '\n'
  printf '=== %s ===\n' "$1"
  printf '%s\n' '----------------------------------------'
}

SECTION_START_PASS=0
SECTION_START_WARN=0
SECTION_START_FAIL=0

begin_section_summary() {
  SECTION_START_PASS=${PASS_COUNT}
  SECTION_START_WARN=${WARN_COUNT}
  SECTION_START_FAIL=${FAIL_COUNT}
}

end_section_summary() {
  local label="$1"
  local pass_delta=$((PASS_COUNT - SECTION_START_PASS))
  local warn_delta=$((WARN_COUNT - SECTION_START_WARN))
  local fail_delta=$((FAIL_COUNT - SECTION_START_FAIL))
  printf '\nSection summary: %s: PASS %s / WARN %s / FAIL %s\n' "${label}" "${pass_delta}" "${warn_delta}" "${fail_delta}"
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
printf 'Dashboard scan order: Core Workstation -> Chief of Staff Workflow -> Lesson Planning -> Future-Safety -> Appearance & Vibe Foundation -> Developer/Cursor -> Recommendation -> Final Health Summary\n'
printf 'Health summary: see Final Health Summary at end (PASS/WARN/FAIL)\n'

group_banner "Core Workstation Status"
begin_section_summary

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

section "Return to Chief of Staff / Teacher Workstation Core"
if [[ -f scripts/return-to-chief-of-staff-core-status.sh ]]; then
  return_to_core_result=0
  return_to_core_output="$(bash scripts/return-to-chief-of-staff-core-status.sh 2>&1)" || return_to_core_result=$?
  return_to_core_pass="$(summary_count "${return_to_core_output}" "PASS")"
  return_to_core_warn="$(summary_count "${return_to_core_output}" "WARN")"
  return_to_core_fail="$(summary_count "${return_to_core_output}" "FAIL")"

  if [[ "${return_to_core_result}" != "0" ]]; then
    printf 'Return to Chief of Staff / Teacher Workstation Core: status command completed\n'
    printf '%s\n' "${return_to_core_output}"
    fail "return to Chief of Staff core status failed"
  elif [[ -n "${return_to_core_pass}" && -n "${return_to_core_warn}" && -n "${return_to_core_fail}" ]]; then
    printf 'Return to Chief of Staff / Teacher Workstation Core: PASS %s / WARN %s / FAIL %s\n' "${return_to_core_pass}" "${return_to_core_warn}" "${return_to_core_fail}"
    pass "return to Chief of Staff core status completed"
  else
    printf 'Return to Chief of Staff / Teacher Workstation Core: status command completed\n'
    pass "return to Chief of Staff core status completed"
  fi
else
  warn "return to Chief of Staff core status script missing: scripts/return-to-chief-of-staff-core-status.sh"
fi

section "Chief of Staff Dashboard Readability Pass"
if [[ -f scripts/chief-of-staff-dashboard-readability-status.sh ]]; then
  dashboard_readability_result=0
  dashboard_readability_output="$(bash scripts/chief-of-staff-dashboard-readability-status.sh 2>&1)" || dashboard_readability_result=$?
  dashboard_readability_pass="$(summary_count "${dashboard_readability_output}" "PASS")"
  dashboard_readability_warn="$(summary_count "${dashboard_readability_output}" "WARN")"
  dashboard_readability_fail="$(summary_count "${dashboard_readability_output}" "FAIL")"

  if [[ "${dashboard_readability_result}" != "0" ]]; then
    printf 'Chief of Staff Dashboard Readability Pass: status command completed\n'
    printf '%s\n' "${dashboard_readability_output}"
    fail "Chief of Staff dashboard readability status failed"
  elif [[ -n "${dashboard_readability_pass}" && -n "${dashboard_readability_warn}" && -n "${dashboard_readability_fail}" ]]; then
    printf 'Chief of Staff Dashboard Readability Pass: PASS %s / WARN %s / FAIL %s\n' "${dashboard_readability_pass}" "${dashboard_readability_warn}" "${dashboard_readability_fail}"
    pass "Chief of Staff dashboard readability status completed"
  else
    printf 'Chief of Staff Dashboard Readability Pass: status command completed\n'
    pass "Chief of Staff dashboard readability status completed"
  fi
else
  warn "Chief of Staff dashboard readability status script missing: scripts/chief-of-staff-dashboard-readability-status.sh"
fi

section "Chief of Staff Command Map Cleanup"
if [[ -f scripts/chief-of-staff-command-map-status.sh ]]; then
  command_map_result=0
  command_map_output="$(bash scripts/chief-of-staff-command-map-status.sh 2>&1)" || command_map_result=$?
  command_map_pass="$(summary_count "${command_map_output}" "PASS")"
  command_map_warn="$(summary_count "${command_map_output}" "WARN")"
  command_map_fail="$(summary_count "${command_map_output}" "FAIL")"

  if [[ "${command_map_result}" != "0" ]]; then
    printf 'Chief of Staff Command Map Cleanup: status command completed\n'
    printf '%s\n' "${command_map_output}"
    fail "Chief of Staff command map status failed"
  elif [[ -n "${command_map_pass}" && -n "${command_map_warn}" && -n "${command_map_fail}" ]]; then
    printf 'Chief of Staff Command Map Cleanup: PASS %s / WARN %s / FAIL %s\n' "${command_map_pass}" "${command_map_warn}" "${command_map_fail}"
    pass "Chief of Staff command map status completed"
  else
    printf 'Chief of Staff Command Map Cleanup: status command completed\n'
    pass "Chief of Staff command map status completed"
  fi
else
  warn "Chief of Staff command map status script missing: scripts/chief-of-staff-command-map-status.sh"
fi

section "Chief of Staff Help Examples Polish"
if [[ -f scripts/chief-of-staff-help-examples-status.sh ]]; then
  help_examples_result=0
  help_examples_output="$(bash scripts/chief-of-staff-help-examples-status.sh 2>&1)" || help_examples_result=$?
  help_examples_pass="$(summary_count "${help_examples_output}" "PASS")"
  help_examples_warn="$(summary_count "${help_examples_output}" "WARN")"
  help_examples_fail="$(summary_count "${help_examples_output}" "FAIL")"

  if [[ "${help_examples_result}" != "0" ]]; then
    printf 'Chief of Staff Help Examples Polish: status command completed\n'
    printf '%s\n' "${help_examples_output}"
    fail "Chief of Staff help examples status failed"
  elif [[ -n "${help_examples_pass}" && -n "${help_examples_warn}" && -n "${help_examples_fail}" ]]; then
    printf 'Chief of Staff Help Examples Polish: PASS %s / WARN %s / FAIL %s\n' "${help_examples_pass}" "${help_examples_warn}" "${help_examples_fail}"
    pass "Chief of Staff help examples status completed"
  else
    printf 'Chief of Staff Help Examples Polish: status command completed\n'
    pass "Chief of Staff help examples status completed"
  fi
else
  warn "Chief of Staff help examples status script missing: scripts/chief-of-staff-help-examples-status.sh"
fi

section "Chief of Staff Workflow Quick-Start Guide"
if [[ -f scripts/chief-of-staff-workflow-quick-start-status.sh ]]; then
  workflow_quick_start_result=0
  workflow_quick_start_output="$(bash scripts/chief-of-staff-workflow-quick-start-status.sh 2>&1)" || workflow_quick_start_result=$?
  workflow_quick_start_pass="$(summary_count "${workflow_quick_start_output}" "PASS")"
  workflow_quick_start_warn="$(summary_count "${workflow_quick_start_output}" "WARN")"
  workflow_quick_start_fail="$(summary_count "${workflow_quick_start_output}" "FAIL")"

  if [[ "${workflow_quick_start_result}" != "0" ]]; then
    printf 'Chief of Staff Workflow Quick-Start Guide: status command completed\n'
    printf '%s\n' "${workflow_quick_start_output}"
    fail "Chief of Staff workflow quick-start status failed"
  elif [[ -n "${workflow_quick_start_pass}" && -n "${workflow_quick_start_warn}" && -n "${workflow_quick_start_fail}" ]]; then
    printf 'Chief of Staff Workflow Quick-Start Guide: PASS %s / WARN %s / FAIL %s\n' "${workflow_quick_start_pass}" "${workflow_quick_start_warn}" "${workflow_quick_start_fail}"
    pass "Chief of Staff workflow quick-start status completed"
  else
    printf 'Chief of Staff Workflow Quick-Start Guide: status command completed\n'
    pass "Chief of Staff workflow quick-start status completed"
  fi
else
  warn "Chief of Staff workflow quick-start status script missing: scripts/chief-of-staff-workflow-quick-start-status.sh"
fi

section "Dashboard Section Summary Polish"
if [[ -f scripts/dashboard-section-summary-status.sh ]]; then
  if [[ "${COS_DASHBOARD_SKIP_SECTION_SUMMARY_STATUS:-}" == "1" ]]; then
    warn "skipping dashboard section summary status during dashboard self-check"
  else
  dashboard_section_summary_result=0
  dashboard_section_summary_output="$(COS_DASHBOARD_SKIP_SECTION_SUMMARY_STATUS=1 bash scripts/dashboard-section-summary-status.sh 2>&1)" || dashboard_section_summary_result=$?
  dashboard_section_summary_pass="$(summary_count "${dashboard_section_summary_output}" "PASS")"
  dashboard_section_summary_warn="$(summary_count "${dashboard_section_summary_output}" "WARN")"
  dashboard_section_summary_fail="$(summary_count "${dashboard_section_summary_output}" "FAIL")"

  if [[ "${dashboard_section_summary_result}" != "0" ]]; then
    printf 'Dashboard Section Summary Polish: status command completed\n'
    printf '%s\n' "${dashboard_section_summary_output}"
    fail "dashboard section summary status failed"
  elif [[ -n "${dashboard_section_summary_pass}" && -n "${dashboard_section_summary_warn}" && -n "${dashboard_section_summary_fail}" ]]; then
    printf 'Dashboard Section Summary Polish: PASS %s / WARN %s / FAIL %s\n' "${dashboard_section_summary_pass}" "${dashboard_section_summary_warn}" "${dashboard_section_summary_fail}"
    pass "dashboard section summary status completed"
  else
    printf 'Dashboard Section Summary Polish: status command completed\n'
    pass "dashboard section summary status completed"
  fi
  fi
else
  warn "dashboard section summary status script missing: scripts/dashboard-section-summary-status.sh"
fi

end_section_summary "Core Workstation Status"

group_banner "Chief of Staff Workflow Status"
begin_section_summary

section "Available Chief of Staff Workflows and Command Groups"
if [[ ! -f bin/chief-of-staff ]]; then
  fail "Chief of Staff CLI missing: bin/chief-of-staff"
elif [[ ! -x bin/chief-of-staff ]]; then
  warn "Chief of Staff CLI is not executable. Fix with: chmod +x bin/chief-of-staff"
else
  printf 'Grouped discovery: bin/chief-of-staff --list-workflows\n'
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

section "Command Launcher"
if [[ -f scripts/command-launcher-status.sh ]]; then
  printf 'Use --command-launcher-status for grouped Everyday / Lesson / Developer / Future-Safety commands.\n'
  command_launcher_result=0
  command_launcher_output="$(bash scripts/command-launcher-status.sh 2>&1)" || command_launcher_result=$?
  command_launcher_pass="$(summary_count "${command_launcher_output}" "PASS")"
  command_launcher_warn="$(summary_count "${command_launcher_output}" "WARN")"
  command_launcher_fail="$(summary_count "${command_launcher_output}" "FAIL")"

  if [[ "${command_launcher_result}" != "0" ]]; then
    printf 'Command Launcher: status command completed\n'
    printf '%s\n' "${command_launcher_output}"
    fail "command launcher status failed"
  elif [[ -n "${command_launcher_pass}" && -n "${command_launcher_warn}" && -n "${command_launcher_fail}" ]]; then
    printf 'Command Launcher: PASS %s / WARN %s / FAIL %s\n' "${command_launcher_pass}" "${command_launcher_warn}" "${command_launcher_fail}"
    pass "command launcher status completed"
  else
    printf 'Command Launcher: status command completed\n'
    pass "command launcher status completed"
  fi
else
  warn "command launcher status script missing: scripts/command-launcher-status.sh"
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

end_section_summary "Chief of Staff Workflow Status"

group_banner "Lesson Planning Status"
begin_section_summary

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

section "Lesson Briefs"
if [[ -f scripts/lesson-brief-status.sh ]]; then
  brief_output=""
  brief_result=0
  capture_command brief_output brief_result bash scripts/lesson-brief-status.sh
  brief_pass="$(summary_count "${brief_output}" "PASS")"
  brief_warn="$(summary_count "${brief_output}" "WARN")"
  brief_fail="$(summary_count "${brief_output}" "FAIL")"

  if [[ -n "${brief_pass}" && -n "${brief_warn}" && -n "${brief_fail}" ]]; then
    printf 'Lesson Briefs: PASS %s / WARN %s / FAIL %s\n' "${brief_pass}" "${brief_warn}" "${brief_fail}"
  else
    printf 'Lesson Briefs: status command completed\n'
  fi

  if [[ "${brief_result}" == "0" ]]; then
    pass "lesson brief status completed"
  else
    fail "lesson brief status failed"
  fi
else
  warn "lesson brief status script missing: scripts/lesson-brief-status.sh"
fi

section "Lesson Drafts"
if [[ -f scripts/lesson-draft-status.sh ]]; then
  draft_result=0
  draft_output="$(bash scripts/lesson-draft-status.sh 2>&1)" || draft_result=$?
  draft_pass="$(summary_count "${draft_output}" "PASS")"
  draft_warn="$(summary_count "${draft_output}" "WARN")"
  draft_fail="$(summary_count "${draft_output}" "FAIL")"

  if [[ "${draft_result}" != "0" ]]; then
    printf 'Lesson Drafts: status command completed\n'
  elif [[ -n "${draft_pass}" && -n "${draft_warn}" && -n "${draft_fail}" ]]; then
    printf 'Lesson Drafts: PASS %s / WARN %s / FAIL %s\n' "${draft_pass}" "${draft_warn}" "${draft_fail}"
  else
    printf 'Lesson Drafts: status command completed\n'
  fi

  if [[ "${draft_result}" == "0" ]]; then
    pass "lesson draft status completed"
  else
    fail "lesson draft status failed"
  fi
else
  warn "lesson draft status script missing: scripts/lesson-draft-status.sh"
fi

section "Lesson Packs"
if [[ -f scripts/lesson-pack-status.sh ]]; then
  pack_result=0
  pack_output="$(bash scripts/lesson-pack-status.sh 2>&1)" || pack_result=$?
  pack_pass="$(summary_count "${pack_output}" "PASS")"
  pack_warn="$(summary_count "${pack_output}" "WARN")"
  pack_fail="$(summary_count "${pack_output}" "FAIL")"

  if [[ "${pack_result}" != "0" ]]; then
    printf 'Lesson Packs: status command completed\n'
    printf '%s\n' "${pack_output}"
    fail "lesson pack status failed"
  elif [[ -n "${pack_pass}" && -n "${pack_warn}" && -n "${pack_fail}" ]]; then
    printf 'Lesson Packs: PASS %s / WARN %s / FAIL %s\n' "${pack_pass}" "${pack_warn}" "${pack_fail}"
    pass "lesson pack status completed"
  else
    printf 'Lesson Packs: status command completed\n'
    pass "lesson pack status completed"
  fi
else
  warn "lesson pack status script missing: scripts/lesson-pack-status.sh"
fi

section "Lesson Queue"
if [[ -f scripts/lesson-queue-status.sh ]]; then
  queue_result=0
  queue_output="$(bash scripts/lesson-queue-status.sh 2>&1)" || queue_result=$?
  queue_pass="$(summary_count "${queue_output}" "PASS")"
  queue_warn="$(summary_count "${queue_output}" "WARN")"
  queue_fail="$(summary_count "${queue_output}" "FAIL")"

  if [[ "${queue_result}" != "0" ]]; then
    printf 'Lesson Queue: status command completed\n'
    printf '%s\n' "${queue_output}"
    fail "lesson queue status failed"
  elif [[ -n "${queue_pass}" && -n "${queue_warn}" && -n "${queue_fail}" ]]; then
    printf 'Lesson Queue: PASS %s / WARN %s / FAIL %s\n' "${queue_pass}" "${queue_warn}" "${queue_fail}"
    pass "lesson queue status completed"
  else
    printf 'Lesson Queue: status command completed\n'
    pass "lesson queue status completed"
  fi
else
  warn "lesson queue status script missing: scripts/lesson-queue-status.sh"
fi

section "Lesson Workflow"
if [[ -f scripts/lesson-workflow-status.sh ]]; then
  workflow_result=0
  workflow_output="$(bash scripts/lesson-workflow-status.sh 2>&1)" || workflow_result=$?
  workflow_pass="$(summary_count "${workflow_output}" "PASS")"
  workflow_warn="$(summary_count "${workflow_output}" "WARN")"
  workflow_fail="$(summary_count "${workflow_output}" "FAIL")"

  if [[ "${workflow_result}" != "0" ]]; then
    printf 'Lesson Workflow: status command completed\n'
    printf '%s\n' "${workflow_output}"
    fail "lesson workflow status failed"
  elif [[ -n "${workflow_pass}" && -n "${workflow_warn}" && -n "${workflow_fail}" ]]; then
    printf 'Lesson Workflow: PASS %s / WARN %s / FAIL %s\n' "${workflow_pass}" "${workflow_warn}" "${workflow_fail}"
    pass "lesson workflow status completed"
  else
    printf 'Lesson Workflow: status command completed\n'
    pass "lesson workflow status completed"
  fi
else
  warn "lesson workflow status script missing: scripts/lesson-workflow-status.sh"
fi

section "Lesson Review Checklist"
if [[ -f scripts/lesson-review-checklist-status.sh ]]; then
  review_result=0
  review_output="$(bash scripts/lesson-review-checklist-status.sh 2>&1)" || review_result=$?
  review_pass="$(summary_count "${review_output}" "PASS")"
  review_warn="$(summary_count "${review_output}" "WARN")"
  review_fail="$(summary_count "${review_output}" "FAIL")"

  if [[ "${review_result}" != "0" ]]; then
    printf 'Lesson Review Checklist: status command completed\n'
    printf '%s\n' "${review_output}"
    fail "lesson review checklist status failed"
  elif [[ -n "${review_pass}" && -n "${review_warn}" && -n "${review_fail}" ]]; then
    printf 'Lesson Review Checklist: PASS %s / WARN %s / FAIL %s\n' "${review_pass}" "${review_warn}" "${review_fail}"
    pass "lesson review checklist status completed"
  else
    printf 'Lesson Review Checklist: status command completed\n'
    pass "lesson review checklist status completed"
  fi
else
  warn "lesson review checklist status script missing: scripts/lesson-review-checklist-status.sh"
fi

section "Single-Slug Lesson Review"
if [[ -f scripts/lesson-review-view.sh ]] && bash -n scripts/lesson-review-view.sh 2>/dev/null && [[ -f bin/chief-of-staff ]] && grep -q -- '--lesson-review-view' bin/chief-of-staff; then
  printf 'Single-Slug Lesson Review: available\n'
  pass "Single-Slug Lesson Review available"
else
  fail "Single-Slug Lesson Review is not available"
fi

section "Review Notes Template"
if [[ -f scripts/review-notes-template-status.sh ]]; then
  notes_result=0
  notes_output="$(bash scripts/review-notes-template-status.sh 2>&1)" || notes_result=$?
  notes_pass="$(summary_count "${notes_output}" "PASS")"
  notes_warn="$(summary_count "${notes_output}" "WARN")"
  notes_fail="$(summary_count "${notes_output}" "FAIL")"

  if [[ "${notes_result}" != "0" ]]; then
    printf 'Review Notes Template: status command completed\n'
    printf '%s\n' "${notes_output}"
    fail "review notes template status failed"
  elif [[ -n "${notes_pass}" && -n "${notes_warn}" && -n "${notes_fail}" ]]; then
    printf 'Review Notes Template: PASS %s / WARN %s / FAIL %s\n' "${notes_pass}" "${notes_warn}" "${notes_fail}"
    pass "review notes template status completed"
  else
    printf 'Review Notes Template: status command completed\n'
    pass "review notes template status completed"
  fi
else
  warn "review notes template status script missing: scripts/review-notes-template-status.sh"
fi

section "Teacher Planning Command Organization"
if [[ -f scripts/teacher-planning-command-organization-status.sh ]]; then
  teacher_planning_command_result=0
  teacher_planning_command_output="$(bash scripts/teacher-planning-command-organization-status.sh 2>&1)" || teacher_planning_command_result=$?
  teacher_planning_command_pass="$(summary_count "${teacher_planning_command_output}" "PASS")"
  teacher_planning_command_warn="$(summary_count "${teacher_planning_command_output}" "WARN")"
  teacher_planning_command_fail="$(summary_count "${teacher_planning_command_output}" "FAIL")"

  if [[ "${teacher_planning_command_result}" != "0" ]]; then
    printf 'Teacher Planning Command Organization: status command completed\n'
    printf '%s\n' "${teacher_planning_command_output}"
    fail "teacher planning command organization status failed"
  elif [[ -n "${teacher_planning_command_pass}" && -n "${teacher_planning_command_warn}" && -n "${teacher_planning_command_fail}" ]]; then
    printf 'Teacher Planning Command Organization: PASS %s / WARN %s / FAIL %s\n' "${teacher_planning_command_pass}" "${teacher_planning_command_warn}" "${teacher_planning_command_fail}"
    pass "teacher planning command organization status completed"
  else
    printf 'Teacher Planning Command Organization: status command completed\n'
    pass "teacher planning command organization status completed"
  fi
else
  warn "teacher planning command organization status script missing: scripts/teacher-planning-command-organization-status.sh"
fi

section "Teacher Planning Command Detail Polish"
if [[ -f scripts/teacher-planning-command-detail-status.sh ]]; then
  teacher_planning_command_detail_result=0
  teacher_planning_command_detail_output="$(bash scripts/teacher-planning-command-detail-status.sh 2>&1)" || teacher_planning_command_detail_result=$?
  teacher_planning_command_detail_pass="$(summary_count "${teacher_planning_command_detail_output}" "PASS")"
  teacher_planning_command_detail_warn="$(summary_count "${teacher_planning_command_detail_output}" "WARN")"
  teacher_planning_command_detail_fail="$(summary_count "${teacher_planning_command_detail_output}" "FAIL")"

  if [[ "${teacher_planning_command_detail_result}" != "0" ]]; then
    printf 'Teacher Planning Command Detail Polish: status command completed\n'
    printf '%s\n' "${teacher_planning_command_detail_output}"
    fail "Teacher Planning command detail polish status failed"
  elif [[ -n "${teacher_planning_command_detail_pass}" && -n "${teacher_planning_command_detail_warn}" && -n "${teacher_planning_command_detail_fail}" ]]; then
    printf 'Teacher Planning Command Detail Polish: PASS %s / WARN %s / FAIL %s\n' "${teacher_planning_command_detail_pass}" "${teacher_planning_command_detail_warn}" "${teacher_planning_command_detail_fail}"
    pass "Teacher Planning command detail polish status completed"
  else
    printf 'Teacher Planning Command Detail Polish: status command completed\n'
    pass "Teacher Planning command detail polish status completed"
  fi
else
  warn "Teacher Planning command detail status script missing: scripts/teacher-planning-command-detail-status.sh"
fi

section "Lesson Review Command Detail Polish"
if [[ -f scripts/lesson-review-command-detail-status.sh ]]; then
  lesson_review_command_detail_result=0
  lesson_review_command_detail_output="$(bash scripts/lesson-review-command-detail-status.sh 2>&1)" || lesson_review_command_detail_result=$?
  lesson_review_command_detail_pass="$(summary_count "${lesson_review_command_detail_output}" "PASS")"
  lesson_review_command_detail_warn="$(summary_count "${lesson_review_command_detail_output}" "WARN")"
  lesson_review_command_detail_fail="$(summary_count "${lesson_review_command_detail_output}" "FAIL")"

  if [[ "${lesson_review_command_detail_result}" != "0" ]]; then
    printf 'Lesson Review Command Detail Polish: status command completed\n'
    printf '%s\n' "${lesson_review_command_detail_output}"
    fail "Lesson Review command detail polish status failed"
  elif [[ -n "${lesson_review_command_detail_pass}" && -n "${lesson_review_command_detail_warn}" && -n "${lesson_review_command_detail_fail}" ]]; then
    printf 'Lesson Review Command Detail Polish: PASS %s / WARN %s / FAIL %s\n' "${lesson_review_command_detail_pass}" "${lesson_review_command_detail_warn}" "${lesson_review_command_detail_fail}"
    pass "Lesson Review command detail polish status completed"
  else
    printf 'Lesson Review Command Detail Polish: status command completed\n'
    pass "Lesson Review command detail polish status completed"
  fi
else
  warn "Lesson Review command detail status script missing: scripts/lesson-review-command-detail-status.sh"
fi

section "Review Notes Command Detail Polish"
if [[ -f scripts/review-notes-command-detail-status.sh ]]; then
  review_notes_command_detail_result=0
  review_notes_command_detail_output="$(bash scripts/review-notes-command-detail-status.sh 2>&1)" || review_notes_command_detail_result=$?
  review_notes_command_detail_pass="$(summary_count "${review_notes_command_detail_output}" "PASS")"
  review_notes_command_detail_warn="$(summary_count "${review_notes_command_detail_output}" "WARN")"
  review_notes_command_detail_fail="$(summary_count "${review_notes_command_detail_output}" "FAIL")"

  if [[ "${review_notes_command_detail_result}" != "0" ]]; then
    printf 'Review Notes Command Detail Polish: status command completed\n'
    printf '%s\n' "${review_notes_command_detail_output}"
    fail "Review Notes command detail polish status failed"
  elif [[ -n "${review_notes_command_detail_pass}" && -n "${review_notes_command_detail_warn}" && -n "${review_notes_command_detail_fail}" ]]; then
    printf 'Review Notes Command Detail Polish: PASS %s / WARN %s / FAIL %s\n' "${review_notes_command_detail_pass}" "${review_notes_command_detail_warn}" "${review_notes_command_detail_fail}"
    pass "Review Notes command detail polish status completed"
  else
    printf 'Review Notes Command Detail Polish: status command completed\n'
    pass "Review Notes command detail polish status completed"
  fi
else
  warn "Review Notes command detail status script missing: scripts/review-notes-command-detail-status.sh"
fi

section "Lesson Review Workflow Polish"
if [[ -f scripts/lesson-review-workflow-polish-status.sh ]]; then
  lesson_review_workflow_result=0
  lesson_review_workflow_output="$(bash scripts/lesson-review-workflow-polish-status.sh 2>&1)" || lesson_review_workflow_result=$?
  lesson_review_workflow_pass="$(summary_count "${lesson_review_workflow_output}" "PASS")"
  lesson_review_workflow_warn="$(summary_count "${lesson_review_workflow_output}" "WARN")"
  lesson_review_workflow_fail="$(summary_count "${lesson_review_workflow_output}" "FAIL")"

  if [[ "${lesson_review_workflow_result}" != "0" ]]; then
    printf 'Lesson Review Workflow Polish: status command completed\n'
    printf '%s\n' "${lesson_review_workflow_output}"
    fail "lesson review workflow polish status failed"
  elif [[ -n "${lesson_review_workflow_pass}" && -n "${lesson_review_workflow_warn}" && -n "${lesson_review_workflow_fail}" ]]; then
    printf 'Lesson Review Workflow Polish: PASS %s / WARN %s / FAIL %s\n' "${lesson_review_workflow_pass}" "${lesson_review_workflow_warn}" "${lesson_review_workflow_fail}"
    pass "lesson review workflow polish status completed"
  else
    printf 'Lesson Review Workflow Polish: status command completed\n'
    pass "lesson review workflow polish status completed"
  fi
else
  warn "lesson review workflow polish status script missing: scripts/lesson-review-workflow-polish-status.sh"
fi

section "Review Notes Workflow Polish"
if [[ -f scripts/review-notes-workflow-polish-status.sh ]]; then
  review_notes_workflow_result=0
  review_notes_workflow_output="$(bash scripts/review-notes-workflow-polish-status.sh 2>&1)" || review_notes_workflow_result=$?
  review_notes_workflow_pass="$(summary_count "${review_notes_workflow_output}" "PASS")"
  review_notes_workflow_warn="$(summary_count "${review_notes_workflow_output}" "WARN")"
  review_notes_workflow_fail="$(summary_count "${review_notes_workflow_output}" "FAIL")"

  if [[ "${review_notes_workflow_result}" != "0" ]]; then
    printf 'Review Notes Workflow Polish: status command completed\n'
    printf '%s\n' "${review_notes_workflow_output}"
    fail "review notes workflow polish status failed"
  elif [[ -n "${review_notes_workflow_pass}" && -n "${review_notes_workflow_warn}" && -n "${review_notes_workflow_fail}" ]]; then
    printf 'Review Notes Workflow Polish: PASS %s / WARN %s / FAIL %s\n' "${review_notes_workflow_pass}" "${review_notes_workflow_warn}" "${review_notes_workflow_fail}"
    pass "review notes workflow polish status completed"
  else
    printf 'Review Notes Workflow Polish: status command completed\n'
    pass "review notes workflow polish status completed"
  fi
else
  warn "review notes workflow polish status script missing: scripts/review-notes-workflow-polish-status.sh"
fi

section "Core Teacher Workstation Planning Cleanup"
if [[ -f scripts/core-teacher-workstation-planning-cleanup-status.sh ]]; then
  core_teacher_workstation_planning_cleanup_result=0
  core_teacher_workstation_planning_cleanup_output="$(bash scripts/core-teacher-workstation-planning-cleanup-status.sh 2>&1)" || core_teacher_workstation_planning_cleanup_result=$?
  core_teacher_workstation_planning_cleanup_pass="$(summary_count "${core_teacher_workstation_planning_cleanup_output}" "PASS")"
  core_teacher_workstation_planning_cleanup_warn="$(summary_count "${core_teacher_workstation_planning_cleanup_output}" "WARN")"
  core_teacher_workstation_planning_cleanup_fail="$(summary_count "${core_teacher_workstation_planning_cleanup_output}" "FAIL")"

  if [[ "${core_teacher_workstation_planning_cleanup_result}" != "0" ]]; then
    printf 'Core Teacher Workstation Planning Cleanup: status command completed\n'
    printf '%s\n' "${core_teacher_workstation_planning_cleanup_output}"
    fail "core Teacher Workstation planning cleanup status failed"
  elif [[ -n "${core_teacher_workstation_planning_cleanup_pass}" && -n "${core_teacher_workstation_planning_cleanup_warn}" && -n "${core_teacher_workstation_planning_cleanup_fail}" ]]; then
    printf 'Core Teacher Workstation Planning Cleanup: PASS %s / WARN %s / FAIL %s\n' "${core_teacher_workstation_planning_cleanup_pass}" "${core_teacher_workstation_planning_cleanup_warn}" "${core_teacher_workstation_planning_cleanup_fail}"
    pass "core Teacher Workstation planning cleanup status completed"
  else
    printf 'Core Teacher Workstation Planning Cleanup: status command completed\n'
    pass "core Teacher Workstation planning cleanup status completed"
  fi
else
  warn "core Teacher Workstation planning cleanup status script missing: scripts/core-teacher-workstation-planning-cleanup-status.sh"
fi

section "Teacher Workflow Quick-Reference Polish"
if [[ -f scripts/teacher-workflow-quick-reference-status.sh ]]; then
  teacher_workflow_quick_reference_result=0
  teacher_workflow_quick_reference_output="$(bash scripts/teacher-workflow-quick-reference-status.sh 2>&1)" || teacher_workflow_quick_reference_result=$?
  teacher_workflow_quick_reference_pass="$(summary_count "${teacher_workflow_quick_reference_output}" "PASS")"
  teacher_workflow_quick_reference_warn="$(summary_count "${teacher_workflow_quick_reference_output}" "WARN")"
  teacher_workflow_quick_reference_fail="$(summary_count "${teacher_workflow_quick_reference_output}" "FAIL")"

  if [[ "${teacher_workflow_quick_reference_result}" != "0" ]]; then
    printf 'Teacher Workflow Quick-Reference Polish: status command completed\n'
    printf '%s\n' "${teacher_workflow_quick_reference_output}"
    fail "Teacher Workflow quick-reference polish status failed"
  elif [[ -n "${teacher_workflow_quick_reference_pass}" && -n "${teacher_workflow_quick_reference_warn}" && -n "${teacher_workflow_quick_reference_fail}" ]]; then
    printf 'Teacher Workflow Quick-Reference Polish: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_quick_reference_pass}" "${teacher_workflow_quick_reference_warn}" "${teacher_workflow_quick_reference_fail}"
    pass "Teacher Workflow quick-reference polish status completed"
  else
    printf 'Teacher Workflow Quick-Reference Polish: status command completed\n'
    pass "Teacher Workflow quick-reference polish status completed"
  fi
else
  warn "Teacher Workflow quick-reference status script missing: scripts/teacher-workflow-quick-reference-status.sh"
fi

section "Teacher Workflow Status Summary"
if [[ -f scripts/teacher-workflow-status-summary.sh ]]; then
  teacher_workflow_status_summary_result=0
  teacher_workflow_status_summary_output="$(bash scripts/teacher-workflow-status-summary.sh 2>&1)" || teacher_workflow_status_summary_result=$?
  teacher_workflow_status_summary_pass="$(summary_count "${teacher_workflow_status_summary_output}" "PASS")"
  teacher_workflow_status_summary_warn="$(summary_count "${teacher_workflow_status_summary_output}" "WARN")"
  teacher_workflow_status_summary_fail="$(summary_count "${teacher_workflow_status_summary_output}" "FAIL")"

  if [[ "${teacher_workflow_status_summary_result}" != "0" ]]; then
    printf 'Teacher Workflow Status Summary: status command completed\n'
    printf '%s\n' "${teacher_workflow_status_summary_output}"
    fail "Teacher Workflow status summary failed"
  elif [[ -n "${teacher_workflow_status_summary_pass}" && -n "${teacher_workflow_status_summary_warn}" && -n "${teacher_workflow_status_summary_fail}" ]]; then
    printf 'Teacher Workflow Status Summary: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_status_summary_pass}" "${teacher_workflow_status_summary_warn}" "${teacher_workflow_status_summary_fail}"
    pass "Teacher Workflow status summary completed"
  else
    printf 'Teacher Workflow Status Summary: status command completed\n'
    pass "Teacher Workflow status summary completed"
  fi
else
  warn "Teacher Workflow status summary script missing: scripts/teacher-workflow-status-summary.sh"
fi

section "Teacher Workflow Command Detail Summary"
if [[ -f scripts/teacher-workflow-command-detail-summary-status.sh ]]; then
  teacher_workflow_command_detail_summary_result=0
  teacher_workflow_command_detail_summary_output="$(bash scripts/teacher-workflow-command-detail-summary-status.sh 2>&1)" || teacher_workflow_command_detail_summary_result=$?
  teacher_workflow_command_detail_summary_pass="$(summary_count "${teacher_workflow_command_detail_summary_output}" "PASS")"
  teacher_workflow_command_detail_summary_warn="$(summary_count "${teacher_workflow_command_detail_summary_output}" "WARN")"
  teacher_workflow_command_detail_summary_fail="$(summary_count "${teacher_workflow_command_detail_summary_output}" "FAIL")"

  if [[ "${teacher_workflow_command_detail_summary_result}" != "0" ]]; then
    printf 'Teacher Workflow Command Detail Summary: status command completed\n'
    printf '%s\n' "${teacher_workflow_command_detail_summary_output}"
    fail "Teacher Workflow command detail summary status failed"
  elif [[ -n "${teacher_workflow_command_detail_summary_pass}" && -n "${teacher_workflow_command_detail_summary_warn}" && -n "${teacher_workflow_command_detail_summary_fail}" ]]; then
    printf 'Teacher Workflow Command Detail Summary: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_command_detail_summary_pass}" "${teacher_workflow_command_detail_summary_warn}" "${teacher_workflow_command_detail_summary_fail}"
    pass "Teacher Workflow command detail summary status completed"
  else
    printf 'Teacher Workflow Command Detail Summary: status command completed\n'
    pass "Teacher Workflow command detail summary status completed"
  fi
else
  warn "Teacher Workflow command detail summary status script missing: scripts/teacher-workflow-command-detail-summary-status.sh"
fi

section "Teacher Workflow Safe-Output Examples"
if [[ -f scripts/teacher-workflow-safe-output-examples-status.sh ]]; then
  teacher_workflow_safe_output_examples_result=0
  teacher_workflow_safe_output_examples_output="$(bash scripts/teacher-workflow-safe-output-examples-status.sh 2>&1)" || teacher_workflow_safe_output_examples_result=$?
  teacher_workflow_safe_output_examples_pass="$(summary_count "${teacher_workflow_safe_output_examples_output}" "PASS")"
  teacher_workflow_safe_output_examples_warn="$(summary_count "${teacher_workflow_safe_output_examples_output}" "WARN")"
  teacher_workflow_safe_output_examples_fail="$(summary_count "${teacher_workflow_safe_output_examples_output}" "FAIL")"

  if [[ "${teacher_workflow_safe_output_examples_result}" != "0" ]]; then
    printf 'Teacher Workflow Safe-Output Examples: status command completed\n'
    printf '%s\n' "${teacher_workflow_safe_output_examples_output}"
    fail "Teacher Workflow safe-output examples status failed"
  elif [[ -n "${teacher_workflow_safe_output_examples_pass}" && -n "${teacher_workflow_safe_output_examples_warn}" && -n "${teacher_workflow_safe_output_examples_fail}" ]]; then
    printf 'Teacher Workflow Safe-Output Examples: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_safe_output_examples_pass}" "${teacher_workflow_safe_output_examples_warn}" "${teacher_workflow_safe_output_examples_fail}"
    pass "Teacher Workflow safe-output examples status completed"
  else
    printf 'Teacher Workflow Safe-Output Examples: status command completed\n'
    pass "Teacher Workflow safe-output examples status completed"
  fi
else
  warn "Teacher Workflow safe-output examples status script missing: scripts/teacher-workflow-safe-output-examples-status.sh"
fi

section "Teacher Workflow Safe-Output Checker"
if [[ -f scripts/teacher-workflow-safe-output-checker-status.sh ]]; then
  teacher_workflow_safe_output_checker_result=0
  teacher_workflow_safe_output_checker_output="$(bash scripts/teacher-workflow-safe-output-checker-status.sh 2>&1)" || teacher_workflow_safe_output_checker_result=$?
  teacher_workflow_safe_output_checker_pass="$(summary_count "${teacher_workflow_safe_output_checker_output}" "PASS")"
  teacher_workflow_safe_output_checker_warn="$(summary_count "${teacher_workflow_safe_output_checker_output}" "WARN")"
  teacher_workflow_safe_output_checker_fail="$(summary_count "${teacher_workflow_safe_output_checker_output}" "FAIL")"

  if [[ "${teacher_workflow_safe_output_checker_result}" != "0" ]]; then
    printf 'Teacher Workflow Safe-Output Checker: status command completed\n'
    printf '%s\n' "${teacher_workflow_safe_output_checker_output}"
    fail "Teacher Workflow safe-output checker status failed"
  elif [[ -n "${teacher_workflow_safe_output_checker_pass}" && -n "${teacher_workflow_safe_output_checker_warn}" && -n "${teacher_workflow_safe_output_checker_fail}" ]]; then
    printf 'Teacher Workflow Safe-Output Checker: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_safe_output_checker_pass}" "${teacher_workflow_safe_output_checker_warn}" "${teacher_workflow_safe_output_checker_fail}"
    pass "Teacher Workflow safe-output checker status completed"
  else
    printf 'Teacher Workflow Safe-Output Checker: status command completed\n'
    pass "Teacher Workflow safe-output checker status completed"
  fi
else
  warn "Teacher Workflow safe-output checker status script missing: scripts/teacher-workflow-safe-output-checker-status.sh"
fi

section "Teacher Workflow Output Examples Completion Marker"
if [[ -f scripts/teacher-workflow-output-examples-completion-status.sh ]]; then
  teacher_workflow_output_examples_completion_result=0
  teacher_workflow_output_examples_completion_output="$(bash scripts/teacher-workflow-output-examples-completion-status.sh 2>&1)" || teacher_workflow_output_examples_completion_result=$?
  teacher_workflow_output_examples_completion_pass="$(summary_count "${teacher_workflow_output_examples_completion_output}" "PASS")"
  teacher_workflow_output_examples_completion_warn="$(summary_count "${teacher_workflow_output_examples_completion_output}" "WARN")"
  teacher_workflow_output_examples_completion_fail="$(summary_count "${teacher_workflow_output_examples_completion_output}" "FAIL")"

  if [[ "${teacher_workflow_output_examples_completion_result}" != "0" ]]; then
    printf 'Teacher Workflow Output Examples Completion Marker: status command completed\n'
    printf '%s\n' "${teacher_workflow_output_examples_completion_output}"
    fail "Teacher Workflow output examples completion status failed"
  elif [[ -n "${teacher_workflow_output_examples_completion_pass}" && -n "${teacher_workflow_output_examples_completion_warn}" && -n "${teacher_workflow_output_examples_completion_fail}" ]]; then
    printf 'Teacher Workflow Output Examples Completion Marker: PASS %s / WARN %s / FAIL %s\n' "${teacher_workflow_output_examples_completion_pass}" "${teacher_workflow_output_examples_completion_warn}" "${teacher_workflow_output_examples_completion_fail}"
    pass "Teacher Workflow output examples completion status completed"
  else
    printf 'Teacher Workflow Output Examples Completion Marker: status command completed\n'
    pass "Teacher Workflow output examples completion status completed"
  fi
else
  warn "Teacher Workflow output examples completion status script missing: scripts/teacher-workflow-output-examples-completion-status.sh"
fi

section "Lesson-Planning Template Readiness Polish"
if [[ -f scripts/lesson-planning-template-readiness-status.sh ]]; then
  lesson_planning_template_readiness_result=0
  lesson_planning_template_readiness_output="$(bash scripts/lesson-planning-template-readiness-status.sh 2>&1)" || lesson_planning_template_readiness_result=$?
  lesson_planning_template_readiness_pass="$(summary_count "${lesson_planning_template_readiness_output}" "PASS")"
  lesson_planning_template_readiness_warn="$(summary_count "${lesson_planning_template_readiness_output}" "WARN")"
  lesson_planning_template_readiness_fail="$(summary_count "${lesson_planning_template_readiness_output}" "FAIL")"

  if [[ "${lesson_planning_template_readiness_result}" != "0" ]]; then
    printf 'Lesson-Planning Template Readiness Polish: status command completed\n'
    printf '%s\n' "${lesson_planning_template_readiness_output}"
    fail "Lesson-planning template readiness status failed"
  elif [[ -n "${lesson_planning_template_readiness_pass}" && -n "${lesson_planning_template_readiness_warn}" && -n "${lesson_planning_template_readiness_fail}" ]]; then
    printf 'Lesson-Planning Template Readiness Polish: PASS %s / WARN %s / FAIL %s\n' "${lesson_planning_template_readiness_pass}" "${lesson_planning_template_readiness_warn}" "${lesson_planning_template_readiness_fail}"
    pass "Lesson-planning template readiness status completed"
  else
    printf 'Lesson-Planning Template Readiness Polish: status command completed\n'
    pass "Lesson-planning template readiness status completed"
  fi
else
  warn "Lesson-planning template readiness status script missing: scripts/lesson-planning-template-readiness-status.sh"
fi

section "Teacher Workstation Foundation v0"
if [[ -f scripts/teacher-workstation-foundation-status.sh ]]; then
  teacher_workstation_foundation_result=0
  teacher_workstation_foundation_output="$(bash scripts/teacher-workstation-foundation-status.sh 2>&1)" || teacher_workstation_foundation_result=$?
  teacher_workstation_foundation_pass="$(summary_count "${teacher_workstation_foundation_output}" "PASS")"
  teacher_workstation_foundation_warn="$(summary_count "${teacher_workstation_foundation_output}" "WARN")"
  teacher_workstation_foundation_fail="$(summary_count "${teacher_workstation_foundation_output}" "FAIL")"

  if [[ "${teacher_workstation_foundation_result}" != "0" ]]; then
    printf 'Teacher Workstation Foundation v0: status command completed\n'
    printf '%s\n' "${teacher_workstation_foundation_output}"
    fail "Teacher Workstation Foundation orchestration status failed"
  elif [[ -n "${teacher_workstation_foundation_pass}" && -n "${teacher_workstation_foundation_warn}" && -n "${teacher_workstation_foundation_fail}" ]]; then
    printf 'Teacher Workstation Foundation v0: PASS %s / WARN %s / FAIL %s\n' "${teacher_workstation_foundation_pass}" "${teacher_workstation_foundation_warn}" "${teacher_workstation_foundation_fail}"
    pass "Teacher Workstation Foundation orchestration status completed"
  else
    printf 'Teacher Workstation Foundation v0: status command completed\n'
    pass "Teacher Workstation Foundation orchestration status completed"
  fi
else
  warn "Teacher Workstation Foundation status script missing: scripts/teacher-workstation-foundation-status.sh"
fi

section "Chief of Staff v1 Agent Core (Program B1)"
if [[ -f scripts/chief-of-staff-v1-foundation-status.sh ]]; then
  cos_v1_result=0
  cos_v1_output="$(bash scripts/chief-of-staff-v1-foundation-status.sh 2>&1)" || cos_v1_result=$?
  cos_v1_pass="$(summary_count "${cos_v1_output}" "PASS")"
  cos_v1_warn="$(summary_count "${cos_v1_output}" "WARN")"
  cos_v1_fail="$(summary_count "${cos_v1_output}" "FAIL")"

  if [[ "${cos_v1_result}" != "0" ]]; then
    printf '%s\n' "${cos_v1_output}"
    fail "Chief of Staff v1 Agent Core foundation status failed"
  elif [[ -n "${cos_v1_pass}" && -n "${cos_v1_warn}" && -n "${cos_v1_fail}" ]]; then
    printf 'Chief of Staff v1 Agent Core: PASS %s / WARN %s / FAIL %s\n' "${cos_v1_pass}" "${cos_v1_warn}" "${cos_v1_fail}"
    pass "Chief of Staff v1 Agent Core foundation status completed"
  else
    pass "Chief of Staff v1 Agent Core foundation status completed"
  fi
else
  warn "Chief of Staff v1 foundation status script missing: scripts/chief-of-staff-v1-foundation-status.sh"
fi

section "Chief of Staff v1 Agent Core (Program B Daily Operations)"
if [[ -f tests/chief-of-staff-daily-operations-test.sh ]]; then
  cos_daily_result=0
  cos_daily_output="$(bash tests/chief-of-staff-daily-operations-test.sh 2>&1)" || cos_daily_result=$?
  if [[ "${cos_daily_result}" != "0" ]]; then
    printf '%s\n' "${cos_daily_output}"
    fail "Chief of Staff daily operations tests failed"
  else
    pass "Chief of Staff daily operations tests completed"
  fi
else
  warn "Chief of Staff daily operations test missing: tests/chief-of-staff-daily-operations-test.sh"
fi

section "Teacher Workstation Health Monitor (Program H)"
if [[ -f scripts/teacher-workstation-health-status.sh ]]; then
  health_result=0
  health_output="$(bash scripts/teacher-workstation-health-status.sh 2>&1)" || health_result=$?
  health_pass="$(summary_count "${health_output}" "PASS")"
  health_warn="$(summary_count "${health_output}" "WARN")"
  health_fail="$(summary_count "${health_output}" "FAIL")"

  if [[ "${health_result}" != "0" ]]; then
    printf '%s\n' "${health_output}"
    fail "Teacher Workstation Health Monitor status failed"
  elif [[ -n "${health_pass}" && -n "${health_warn}" && -n "${health_fail}" ]]; then
    printf 'Health Monitor: PASS %s / WARN %s / FAIL %s\n' "${health_pass}" "${health_warn}" "${health_fail}"
    pass "Teacher Workstation Health Monitor status completed"
  else
    pass "Teacher Workstation Health Monitor status completed"
  fi
else
  warn "Health Monitor status script missing: scripts/teacher-workstation-health-status.sh"
fi

section "Teacher Workstation System Updater (Program I)"
if [[ -f scripts/teacher-workstation-system-updater-status.sh ]]; then
  updater_result=0
  updater_output="$(bash scripts/teacher-workstation-system-updater-status.sh 2>&1)" || updater_result=$?
  updater_pass="$(summary_count "${updater_output}" "PASS")"
  updater_warn="$(summary_count "${updater_output}" "WARN")"
  updater_fail="$(summary_count "${updater_output}" "FAIL")"

  if [[ "${updater_result}" != "0" ]]; then
    printf '%s\n' "${updater_output}"
    fail "Teacher Workstation System Updater status failed"
  elif [[ -n "${updater_pass}" && -n "${updater_warn}" && -n "${updater_fail}" ]]; then
    printf 'System Updater: PASS %s / WARN %s / FAIL %s\n' "${updater_pass}" "${updater_warn}" "${updater_fail}"
    pass "Teacher Workstation System Updater status completed"
  else
    pass "Teacher Workstation System Updater status completed"
  fi
else
  warn "System Updater status script missing: scripts/teacher-workstation-system-updater-status.sh"
fi

section "Workstation Operations Lane Status (Aggregate H+I)"
if [[ -f scripts/workstation-ops-lane-status.sh ]]; then
  workstation_ops_lane_result=0
  workstation_ops_lane_output="$(bash scripts/workstation-ops-lane-status.sh 2>&1)" || workstation_ops_lane_result=$?
  workstation_ops_lane_pass="$(summary_count "${workstation_ops_lane_output}" "PASS")"
  workstation_ops_lane_warn="$(summary_count "${workstation_ops_lane_output}" "WARN")"
  workstation_ops_lane_fail="$(summary_count "${workstation_ops_lane_output}" "FAIL")"

  if [[ "${workstation_ops_lane_result}" != "0" ]]; then
    printf '%s\n' "${workstation_ops_lane_output}"
    fail "Workstation ops lane status failed"
  elif [[ -n "${workstation_ops_lane_pass}" && -n "${workstation_ops_lane_warn}" && -n "${workstation_ops_lane_fail}" ]]; then
    printf 'Workstation Ops Lane: PASS %s / WARN %s / FAIL %s\n' "${workstation_ops_lane_pass}" "${workstation_ops_lane_warn}" "${workstation_ops_lane_fail}"
    pass "Workstation ops lane status completed"
  else
    pass "Workstation ops lane status completed"
  fi
else
  warn "Workstation ops lane status script missing: scripts/workstation-ops-lane-status.sh"
fi

section "AI Tool Routing Matrix (Operational Surface)"
if [[ -f scripts/ai-tool-routing-status.sh ]]; then
  routing_result=0
  routing_output="$(bash scripts/ai-tool-routing-status.sh 2>&1)" || routing_result=$?
  routing_pass="$(summary_count "${routing_output}" "PASS")"
  routing_warn="$(summary_count "${routing_output}" "WARN")"
  routing_fail="$(summary_count "${routing_output}" "FAIL")"

  if [[ "${routing_result}" != "0" ]]; then
    printf '%s\n' "${routing_output}"
    fail "AI Tool Routing operational status failed"
  elif [[ -n "${routing_pass}" && -n "${routing_warn}" && -n "${routing_fail}" ]]; then
    printf 'AI Tool Routing: PASS %s / WARN %s / FAIL %s\n' "${routing_pass}" "${routing_warn}" "${routing_fail}"
    pass "AI Tool Routing operational status completed"
  else
    pass "AI Tool Routing operational status completed"
  fi
else
  warn "AI Tool Routing status script missing: scripts/ai-tool-routing-status.sh"
fi

section "Local LLM / Ollama Workstation (Program D1)"
if [[ -f scripts/local-llm-workstation-status.sh ]]; then
  local_llm_result=0
  local_llm_output="$(bash scripts/local-llm-workstation-status.sh 2>&1)" || local_llm_result=$?
  local_llm_pass="$(summary_count "${local_llm_output}" "PASS")"
  local_llm_warn="$(summary_count "${local_llm_output}" "WARN")"
  local_llm_fail="$(summary_count "${local_llm_output}" "FAIL")"

  if [[ "${local_llm_result}" != "0" ]]; then
    printf '%s\n' "${local_llm_output}"
    fail "Local LLM workstation status failed"
  elif [[ -n "${local_llm_pass}" && -n "${local_llm_warn}" && -n "${local_llm_fail}" ]]; then
    printf 'Local LLM Workstation: PASS %s / WARN %s / FAIL %s\n' "${local_llm_pass}" "${local_llm_warn}" "${local_llm_fail}"
    pass "Local LLM workstation status completed"
  else
    pass "Local LLM workstation status completed"
  fi
else
  warn "Local LLM workstation status script missing: scripts/local-llm-workstation-status.sh"
fi

section "Mac Workstation Experience (Program E1)"
if [[ -f scripts/mac-workstation-experience-status.sh ]]; then
  mac_ws_result=0
  mac_ws_output="$(bash scripts/mac-workstation-experience-status.sh 2>&1)" || mac_ws_result=$?
  mac_ws_pass="$(summary_count "${mac_ws_output}" "PASS")"
  mac_ws_warn="$(summary_count "${mac_ws_output}" "WARN")"
  mac_ws_fail="$(summary_count "${mac_ws_output}" "FAIL")"

  if [[ "${mac_ws_result}" != "0" ]]; then
    printf '%s\n' "${mac_ws_output}"
    fail "Mac Workstation Experience status failed"
  elif [[ -n "${mac_ws_pass}" && -n "${mac_ws_warn}" && -n "${mac_ws_fail}" ]]; then
    printf 'Mac Workstation: PASS %s / WARN %s / FAIL %s\n' "${mac_ws_pass}" "${mac_ws_warn}" "${mac_ws_fail}"
    pass "Mac Workstation Experience status completed"
  else
    pass "Mac Workstation Experience status completed"
  fi
else
  warn "Mac Workstation Experience status script missing: scripts/mac-workstation-experience-status.sh"
fi

section "Widget and Shortcut Builder (Program F1)"
if [[ -f scripts/widget-shortcut-builder-status.sh ]]; then
  widget_shortcut_result=0
  widget_shortcut_output="$(bash scripts/widget-shortcut-builder-status.sh 2>&1)" || widget_shortcut_result=$?
  widget_shortcut_pass="$(summary_count "${widget_shortcut_output}" "PASS")"
  widget_shortcut_warn="$(summary_count "${widget_shortcut_output}" "WARN")"
  widget_shortcut_fail="$(summary_count "${widget_shortcut_output}" "FAIL")"

  if [[ "${widget_shortcut_result}" != "0" ]]; then
    printf '%s\n' "${widget_shortcut_output}"
    fail "Widget and Shortcut Builder status failed"
  elif [[ -n "${widget_shortcut_pass}" && -n "${widget_shortcut_warn}" && -n "${widget_shortcut_fail}" ]]; then
    printf 'Widget and Shortcut Builder: PASS %s / WARN %s / FAIL %s\n' "${widget_shortcut_pass}" "${widget_shortcut_warn}" "${widget_shortcut_fail}"
    pass "Widget and Shortcut Builder status completed"
  else
    pass "Widget and Shortcut Builder status completed"
  fi
else
  warn "Widget and Shortcut Builder status script missing: scripts/widget-shortcut-builder-status.sh"
fi

section "Vibe / Wallpaper / Widgets Planning Gate"
if [[ -f scripts/vibe-wallpaper-widgets-planning-status.sh ]]; then
  vibe_wallpaper_widgets_result=0
  vibe_wallpaper_widgets_output="$(bash scripts/vibe-wallpaper-widgets-planning-status.sh 2>&1)" || vibe_wallpaper_widgets_result=$?
  vibe_wallpaper_widgets_pass="$(summary_count "${vibe_wallpaper_widgets_output}" "PASS")"
  vibe_wallpaper_widgets_warn="$(summary_count "${vibe_wallpaper_widgets_output}" "WARN")"
  vibe_wallpaper_widgets_fail="$(summary_count "${vibe_wallpaper_widgets_output}" "FAIL")"

  if [[ "${vibe_wallpaper_widgets_result}" != "0" ]]; then
    printf '%s\n' "${vibe_wallpaper_widgets_output}"
    fail "Vibe / Wallpaper / Widgets planning status failed"
  elif [[ -n "${vibe_wallpaper_widgets_pass}" && -n "${vibe_wallpaper_widgets_warn}" && -n "${vibe_wallpaper_widgets_fail}" ]]; then
    printf 'Vibe / Wallpaper / Widgets Planning: PASS %s / WARN %s / FAIL %s\n' "${vibe_wallpaper_widgets_pass}" "${vibe_wallpaper_widgets_warn}" "${vibe_wallpaper_widgets_fail}"
    pass "Vibe / Wallpaper / Widgets planning status completed"
  else
    pass "Vibe / Wallpaper / Widgets planning status completed"
  fi
else
  warn "Vibe / Wallpaper / Widgets planning status script missing: scripts/vibe-wallpaper-widgets-planning-status.sh"
fi

section "Classroom App Lab (Prototype Rescue Foundation)"
if [[ -f scripts/classroom-app-lab-status.sh ]]; then
  classroom_app_lab_result=0
  classroom_app_lab_output="$(bash scripts/classroom-app-lab-status.sh 2>&1)" || classroom_app_lab_result=$?
  classroom_app_lab_pass="$(summary_count "${classroom_app_lab_output}" "PASS")"
  classroom_app_lab_warn="$(summary_count "${classroom_app_lab_output}" "WARN")"
  classroom_app_lab_fail="$(summary_count "${classroom_app_lab_output}" "FAIL")"

  if [[ "${classroom_app_lab_result}" != "0" ]]; then
    printf '%s\n' "${classroom_app_lab_output}"
    fail "Classroom App Lab status failed"
  elif [[ -n "${classroom_app_lab_pass}" && -n "${classroom_app_lab_warn}" && -n "${classroom_app_lab_fail}" ]]; then
    printf 'Classroom App Lab: PASS %s / WARN %s / FAIL %s\n' "${classroom_app_lab_pass}" "${classroom_app_lab_warn}" "${classroom_app_lab_fail}"
    pass "Classroom App Lab status completed"
  else
    pass "Classroom App Lab status completed"
  fi
else
  warn "Classroom App Lab status script missing: scripts/classroom-app-lab-status.sh"
fi

section "Classroom Utility Per-App Mission Templates (Planning)"
if [[ -f scripts/classroom-utility-templates-status.sh ]]; then
  classroom_utility_templates_result=0
  classroom_utility_templates_output="$(bash scripts/classroom-utility-templates-status.sh 2>&1)" || classroom_utility_templates_result=$?
  classroom_utility_templates_pass="$(summary_count "${classroom_utility_templates_output}" "PASS")"
  classroom_utility_templates_warn="$(summary_count "${classroom_utility_templates_output}" "WARN")"
  classroom_utility_templates_fail="$(summary_count "${classroom_utility_templates_output}" "FAIL")"

  if [[ "${classroom_utility_templates_result}" != "0" ]]; then
    printf '%s\n' "${classroom_utility_templates_output}"
    fail "Classroom Utility templates status failed"
  elif [[ -n "${classroom_utility_templates_pass}" && -n "${classroom_utility_templates_warn}" && -n "${classroom_utility_templates_fail}" ]]; then
    printf 'Classroom Utility Templates: PASS %s / WARN %s / FAIL %s\n' "${classroom_utility_templates_pass}" "${classroom_utility_templates_warn}" "${classroom_utility_templates_fail}"
    pass "Classroom Utility templates status completed"
  else
    pass "Classroom Utility templates status completed"
  fi
else
  warn "Classroom Utility templates status script missing: scripts/classroom-utility-templates-status.sh"
fi

section "Gemini Discovery & Classification Intake (External Planning)"
if [[ -f scripts/gemini-discovery-classification-intake-status.sh ]]; then
  gemini_intake_result=0
  gemini_intake_output="$(bash scripts/gemini-discovery-classification-intake-status.sh 2>&1)" || gemini_intake_result=$?
  gemini_intake_pass="$(summary_count "${gemini_intake_output}" "PASS")"
  gemini_intake_warn="$(summary_count "${gemini_intake_output}" "WARN")"
  gemini_intake_fail="$(summary_count "${gemini_intake_output}" "FAIL")"

  if [[ "${gemini_intake_result}" != "0" ]]; then
    printf '%s\n' "${gemini_intake_output}"
    fail "Gemini discovery/classification intake status failed"
  elif [[ -n "${gemini_intake_pass}" && -n "${gemini_intake_warn}" && -n "${gemini_intake_fail}" ]]; then
    printf 'Gemini Discovery Classification Intake: PASS %s / WARN %s / FAIL %s\n' "${gemini_intake_pass}" "${gemini_intake_warn}" "${gemini_intake_fail}"
    pass "Gemini discovery/classification intake status completed"
  else
    pass "Gemini discovery/classification intake status completed"
  fi
else
  warn "Gemini discovery/classification intake status script missing: scripts/gemini-discovery-classification-intake-status.sh"
fi

section "Markdown Frontmatter Planning (Curriculum Metadata)"
if [[ -f scripts/markdown-frontmatter-planning-status.sh ]]; then
  frontmatter_planning_result=0
  frontmatter_planning_output="$(bash scripts/markdown-frontmatter-planning-status.sh 2>&1)" || frontmatter_planning_result=$?
  frontmatter_planning_pass="$(summary_count "${frontmatter_planning_output}" "PASS")"
  frontmatter_planning_warn="$(summary_count "${frontmatter_planning_output}" "WARN")"
  frontmatter_planning_fail="$(summary_count "${frontmatter_planning_output}" "FAIL")"

  if [[ "${frontmatter_planning_result}" != "0" ]]; then
    printf '%s\n' "${frontmatter_planning_output}"
    fail "Markdown frontmatter planning status failed"
  elif [[ -n "${frontmatter_planning_pass}" && -n "${frontmatter_planning_warn}" && -n "${frontmatter_planning_fail}" ]]; then
    printf 'Markdown Frontmatter Planning: PASS %s / WARN %s / FAIL %s\n' "${frontmatter_planning_pass}" "${frontmatter_planning_warn}" "${frontmatter_planning_fail}"
    pass "Markdown frontmatter planning status completed"
  else
    pass "Markdown frontmatter planning status completed"
  fi
else
  warn "Markdown frontmatter planning status script missing: scripts/markdown-frontmatter-planning-status.sh"
fi

section "Lovable Classroom App Builder (Program G1)"
if [[ -f scripts/lovable-classroom-app-builder-status.sh ]]; then
  lovable_result=0
  lovable_output="$(bash scripts/lovable-classroom-app-builder-status.sh 2>&1)" || lovable_result=$?
  lovable_pass="$(summary_count "${lovable_output}" "PASS")"
  lovable_warn="$(summary_count "${lovable_output}" "WARN")"
  lovable_fail="$(summary_count "${lovable_output}" "FAIL")"

  if [[ "${lovable_result}" != "0" ]]; then
    printf '%s\n' "${lovable_output}"
    fail "Lovable Classroom App Builder status failed"
  elif [[ -n "${lovable_pass}" && -n "${lovable_warn}" && -n "${lovable_fail}" ]]; then
    printf 'Lovable: PASS %s / WARN %s / FAIL %s\n' "${lovable_pass}" "${lovable_warn}" "${lovable_fail}"
    pass "Lovable Classroom App Builder status completed"
  else
    pass "Lovable Classroom App Builder status completed"
  fi
else
  warn "Lovable Classroom App Builder status script missing: scripts/lovable-classroom-app-builder-status.sh"
fi

section "3D Builder Workshop Agent (Program J1)"
if [[ -f scripts/3d-builder-workshop-agent-status.sh ]]; then
  builder_result=0
  builder_output="$(bash scripts/3d-builder-workshop-agent-status.sh 2>&1)" || builder_result=$?
  builder_pass="$(summary_count "${builder_output}" "PASS")"
  builder_warn="$(summary_count "${builder_output}" "WARN")"
  builder_fail="$(summary_count "${builder_output}" "FAIL")"
  if [[ "${builder_result}" != "0" ]]; then
    printf '%s\n' "${builder_output}"
    fail "3D Builder Workshop Agent status failed"
  elif [[ -n "${builder_pass}" && -n "${builder_warn}" && -n "${builder_fail}" ]]; then
    printf '3D Builder: PASS %s / WARN %s / FAIL %s\n' "${builder_pass}" "${builder_warn}" "${builder_fail}"
    pass "3D Builder Workshop Agent status completed"
  else
    pass "3D Builder Workshop Agent status completed"
  fi
else
  warn "3D Builder Workshop Agent status script missing: scripts/3d-builder-workshop-agent-status.sh"
fi

section "Lesson Planning v1 Foundation"
if [[ -f scripts/lesson-planning-foundation-status.sh ]]; then
  lesson_planning_foundation_result=0
  lesson_planning_foundation_output="$(bash scripts/lesson-planning-foundation-status.sh 2>&1)" || lesson_planning_foundation_result=$?
  lesson_planning_foundation_pass="$(summary_count "${lesson_planning_foundation_output}" "PASS")"
  lesson_planning_foundation_warn="$(summary_count "${lesson_planning_foundation_output}" "WARN")"
  lesson_planning_foundation_fail="$(summary_count "${lesson_planning_foundation_output}" "FAIL")"

  if [[ "${lesson_planning_foundation_result}" != "0" ]]; then
    printf 'Lesson Planning v1 Foundation: status command completed\n'
    printf '%s\n' "${lesson_planning_foundation_output}"
    fail "Lesson Planning foundation status failed"
  elif [[ -n "${lesson_planning_foundation_pass}" && -n "${lesson_planning_foundation_warn}" && -n "${lesson_planning_foundation_fail}" ]]; then
    printf 'Lesson Planning v1 Foundation: PASS %s / WARN %s / FAIL %s\n' "${lesson_planning_foundation_pass}" "${lesson_planning_foundation_warn}" "${lesson_planning_foundation_fail}"
    pass "Lesson Planning foundation status completed"
  else
    printf 'Lesson Planning v1 Foundation: status command completed\n'
    pass "Lesson Planning foundation status completed"
  fi
else
  warn "Lesson Planning foundation status script missing: scripts/lesson-planning-foundation-status.sh"
fi

section "Curriculum Library v1 Foundation"
if [[ -f scripts/curriculum-library-foundation-status.sh ]]; then
  curriculum_library_foundation_result=0
  curriculum_library_foundation_output="$(bash scripts/curriculum-library-foundation-status.sh 2>&1)" || curriculum_library_foundation_result=$?
  curriculum_library_foundation_pass="$(summary_count "${curriculum_library_foundation_output}" "PASS")"
  curriculum_library_foundation_warn="$(summary_count "${curriculum_library_foundation_output}" "WARN")"
  curriculum_library_foundation_fail="$(summary_count "${curriculum_library_foundation_output}" "FAIL")"

  if [[ "${curriculum_library_foundation_result}" != "0" ]]; then
    printf 'Curriculum Library v1 Foundation: status command completed\n'
    printf '%s\n' "${curriculum_library_foundation_output}"
    fail "Curriculum Library foundation status failed"
  elif [[ -n "${curriculum_library_foundation_pass}" && -n "${curriculum_library_foundation_warn}" && -n "${curriculum_library_foundation_fail}" ]]; then
    printf 'Curriculum Library v1 Foundation: PASS %s / WARN %s / FAIL %s\n' "${curriculum_library_foundation_pass}" "${curriculum_library_foundation_warn}" "${curriculum_library_foundation_fail}"
    pass "Curriculum Library foundation status completed"
  else
    printf 'Curriculum Library v1 Foundation: status command completed\n'
    pass "Curriculum Library foundation status completed"
  fi
else
  warn "Curriculum Library foundation status script missing: scripts/curriculum-library-foundation-status.sh"
fi

section "Renderer Foundation v1"
if [[ -f scripts/renderer-foundation-status.sh ]]; then
  renderer_foundation_result=0
  renderer_foundation_output="$(bash scripts/renderer-foundation-status.sh 2>&1)" || renderer_foundation_result=$?
  renderer_foundation_pass="$(summary_count "${renderer_foundation_output}" "PASS")"
  renderer_foundation_warn="$(summary_count "${renderer_foundation_output}" "WARN")"
  renderer_foundation_fail="$(summary_count "${renderer_foundation_output}" "FAIL")"

  if [[ "${renderer_foundation_result}" != "0" ]]; then
    printf 'Renderer Foundation v1: status command completed\n'
    printf '%s\n' "${renderer_foundation_output}"
    fail "Renderer Foundation status failed"
  elif [[ -n "${renderer_foundation_pass}" && -n "${renderer_foundation_warn}" && -n "${renderer_foundation_fail}" ]]; then
    printf 'Renderer Foundation v1: PASS %s / WARN %s / FAIL %s\n' "${renderer_foundation_pass}" "${renderer_foundation_warn}" "${renderer_foundation_fail}"
    pass "Renderer Foundation status completed"
  else
    printf 'Renderer Foundation v1: status command completed\n'
    pass "Renderer Foundation status completed"
  fi
else
  warn "Renderer Foundation status script missing: scripts/renderer-foundation-status.sh"
fi

section "Presentation Engine Renderer Foundation (Planning)"
if [[ -f scripts/presentation-engine-renderer-foundation-status.sh ]]; then
  presentation_engine_renderer_foundation_result=0
  presentation_engine_renderer_foundation_output="$(bash scripts/presentation-engine-renderer-foundation-status.sh 2>&1)" || presentation_engine_renderer_foundation_result=$?
  presentation_engine_renderer_foundation_pass="$(summary_count "${presentation_engine_renderer_foundation_output}" "PASS")"
  presentation_engine_renderer_foundation_warn="$(summary_count "${presentation_engine_renderer_foundation_output}" "WARN")"
  presentation_engine_renderer_foundation_fail="$(summary_count "${presentation_engine_renderer_foundation_output}" "FAIL")"

  if [[ "${presentation_engine_renderer_foundation_result}" != "0" ]]; then
    printf '%s\n' "${presentation_engine_renderer_foundation_output}"
    fail "Presentation Engine renderer foundation status failed"
  elif [[ -n "${presentation_engine_renderer_foundation_pass}" && -n "${presentation_engine_renderer_foundation_warn}" && -n "${presentation_engine_renderer_foundation_fail}" ]]; then
    printf 'Presentation Engine Renderer Foundation: PASS %s / WARN %s / FAIL %s\n' "${presentation_engine_renderer_foundation_pass}" "${presentation_engine_renderer_foundation_warn}" "${presentation_engine_renderer_foundation_fail}"
    pass "Presentation Engine renderer foundation status completed"
  else
    pass "Presentation Engine renderer foundation status completed"
  fi
else
  warn "Presentation Engine renderer foundation status script missing: scripts/presentation-engine-renderer-foundation-status.sh"
fi

section "Teacher Knowledge Vault M0 Architecture Freeze"
if [[ -f scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh ]]; then
  teacher_knowledge_vault_m0_result=0
  teacher_knowledge_vault_m0_output="$(bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh 2>&1)" || teacher_knowledge_vault_m0_result=$?
  teacher_knowledge_vault_m0_pass="$(summary_count "${teacher_knowledge_vault_m0_output}" "PASS")"
  teacher_knowledge_vault_m0_warn="$(summary_count "${teacher_knowledge_vault_m0_output}" "WARN")"
  teacher_knowledge_vault_m0_fail="$(summary_count "${teacher_knowledge_vault_m0_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m0_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m0_output}"
    fail "Teacher Knowledge Vault M0 architecture freeze status failed"
  elif [[ -n "${teacher_knowledge_vault_m0_pass}" && -n "${teacher_knowledge_vault_m0_warn}" && -n "${teacher_knowledge_vault_m0_fail}" ]]; then
    printf 'Teacher Knowledge Vault M0 Architecture Freeze: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m0_pass}" "${teacher_knowledge_vault_m0_warn}" "${teacher_knowledge_vault_m0_fail}"
    pass "Teacher Knowledge Vault M0 architecture freeze status completed"
  else
    pass "Teacher Knowledge Vault M0 architecture freeze status completed"
  fi
else
  warn "Teacher Knowledge Vault M0 architecture freeze status script missing: scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh"
fi

section "Teacher Knowledge Vault M1 Fake Catalog Foundation"
if [[ -f scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh ]]; then
  teacher_knowledge_vault_m1_result=0
  teacher_knowledge_vault_m1_output="$(bash scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh 2>&1)" || teacher_knowledge_vault_m1_result=$?
  teacher_knowledge_vault_m1_pass="$(summary_count "${teacher_knowledge_vault_m1_output}" "PASS")"
  teacher_knowledge_vault_m1_warn="$(summary_count "${teacher_knowledge_vault_m1_output}" "WARN")"
  teacher_knowledge_vault_m1_fail="$(summary_count "${teacher_knowledge_vault_m1_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m1_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m1_output}"
    fail "Teacher Knowledge Vault M1 fake catalog status failed"
  elif [[ -n "${teacher_knowledge_vault_m1_pass}" && -n "${teacher_knowledge_vault_m1_warn}" && -n "${teacher_knowledge_vault_m1_fail}" ]]; then
    printf 'Teacher Knowledge Vault M1 Fake Catalog: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m1_pass}" "${teacher_knowledge_vault_m1_warn}" "${teacher_knowledge_vault_m1_fail}"
    pass "Teacher Knowledge Vault M1 fake catalog status completed"
  else
    pass "Teacher Knowledge Vault M1 fake catalog status completed"
  fi
else
  warn "Teacher Knowledge Vault M1 fake catalog status script missing: scripts/teacher-knowledge-vault-m1-fake-catalog-status.sh"
fi

section "Teacher Knowledge Vault M2 Local Discovery Approval Packet"
if [[ -f scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh ]]; then
  teacher_knowledge_vault_m2_result=0
  teacher_knowledge_vault_m2_output="$(bash scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh 2>&1)" || teacher_knowledge_vault_m2_result=$?
  teacher_knowledge_vault_m2_pass="$(summary_count "${teacher_knowledge_vault_m2_output}" "PASS")"
  teacher_knowledge_vault_m2_warn="$(summary_count "${teacher_knowledge_vault_m2_output}" "WARN")"
  teacher_knowledge_vault_m2_fail="$(summary_count "${teacher_knowledge_vault_m2_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m2_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m2_output}"
    fail "Teacher Knowledge Vault M2 local discovery approval status failed"
  elif [[ -n "${teacher_knowledge_vault_m2_pass}" && -n "${teacher_knowledge_vault_m2_warn}" && -n "${teacher_knowledge_vault_m2_fail}" ]]; then
    printf 'Teacher Knowledge Vault M2 Local Discovery Approval: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m2_pass}" "${teacher_knowledge_vault_m2_warn}" "${teacher_knowledge_vault_m2_fail}"
    pass "Teacher Knowledge Vault M2 local discovery approval status completed"
  else
    pass "Teacher Knowledge Vault M2 local discovery approval status completed"
  fi
else
  warn "Teacher Knowledge Vault M2 local discovery approval status script missing: scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh"
fi

section "Teacher Knowledge Vault M3 Fake Duplicate Search Foundation"
if [[ -f scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh ]]; then
  teacher_knowledge_vault_m3_result=0
  teacher_knowledge_vault_m3_output="$(bash scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh 2>&1)" || teacher_knowledge_vault_m3_result=$?
  teacher_knowledge_vault_m3_pass="$(summary_count "${teacher_knowledge_vault_m3_output}" "PASS")"
  teacher_knowledge_vault_m3_warn="$(summary_count "${teacher_knowledge_vault_m3_output}" "WARN")"
  teacher_knowledge_vault_m3_fail="$(summary_count "${teacher_knowledge_vault_m3_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m3_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m3_output}"
    fail "Teacher Knowledge Vault M3 fake duplicate search status failed"
  elif [[ -n "${teacher_knowledge_vault_m3_pass}" && -n "${teacher_knowledge_vault_m3_warn}" && -n "${teacher_knowledge_vault_m3_fail}" ]]; then
    printf 'Teacher Knowledge Vault M3 Fake Duplicate Search: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m3_pass}" "${teacher_knowledge_vault_m3_warn}" "${teacher_knowledge_vault_m3_fail}"
    pass "Teacher Knowledge Vault M3 fake duplicate search status completed"
  else
    pass "Teacher Knowledge Vault M3 fake duplicate search status completed"
  fi
else
  warn "Teacher Knowledge Vault M3 fake duplicate search status script missing: scripts/teacher-knowledge-vault-m3-fake-duplicate-search-status.sh"
fi

section "Teacher Knowledge Vault M4 Smart Rename Foundation"
if [[ -f scripts/teacher-knowledge-vault-m4-smart-rename-status.sh ]]; then
  teacher_knowledge_vault_m4_result=0
  teacher_knowledge_vault_m4_output="$(bash scripts/teacher-knowledge-vault-m4-smart-rename-status.sh 2>&1)" || teacher_knowledge_vault_m4_result=$?
  teacher_knowledge_vault_m4_pass="$(summary_count "${teacher_knowledge_vault_m4_output}" "PASS")"
  teacher_knowledge_vault_m4_warn="$(summary_count "${teacher_knowledge_vault_m4_output}" "WARN")"
  teacher_knowledge_vault_m4_fail="$(summary_count "${teacher_knowledge_vault_m4_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m4_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m4_output}"
    fail "Teacher Knowledge Vault M4 smart rename status failed"
  elif [[ -n "${teacher_knowledge_vault_m4_pass}" && -n "${teacher_knowledge_vault_m4_warn}" && -n "${teacher_knowledge_vault_m4_fail}" ]]; then
    printf 'Teacher Knowledge Vault M4 Smart Rename: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m4_pass}" "${teacher_knowledge_vault_m4_warn}" "${teacher_knowledge_vault_m4_fail}"
    pass "Teacher Knowledge Vault M4 smart rename status completed"
  else
    pass "Teacher Knowledge Vault M4 smart rename status completed"
  fi
else
  warn "Teacher Knowledge Vault M4 smart rename status script missing: scripts/teacher-knowledge-vault-m4-smart-rename-status.sh"
fi

if [[ -f scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh ]]; then
  teacher_knowledge_vault_m5_result=0
  teacher_knowledge_vault_m5_output="$(bash scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh 2>&1)" || teacher_knowledge_vault_m5_result=$?
  teacher_knowledge_vault_m5_pass="$(summary_count "${teacher_knowledge_vault_m5_output}" "PASS")"
  teacher_knowledge_vault_m5_warn="$(summary_count "${teacher_knowledge_vault_m5_output}" "WARN")"
  teacher_knowledge_vault_m5_fail="$(summary_count "${teacher_knowledge_vault_m5_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m5_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m5_output}"
    fail "Teacher Knowledge Vault M5 organization/rollback status failed"
  elif [[ -n "${teacher_knowledge_vault_m5_pass}" && -n "${teacher_knowledge_vault_m5_warn}" && -n "${teacher_knowledge_vault_m5_fail}" ]]; then
    printf 'Teacher Knowledge Vault M5 Organization Rollback: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m5_pass}" "${teacher_knowledge_vault_m5_warn}" "${teacher_knowledge_vault_m5_fail}"
    pass "Teacher Knowledge Vault M5 organization/rollback status completed"
  else
    pass "Teacher Knowledge Vault M5 organization/rollback status completed"
  fi
else
  warn "Teacher Knowledge Vault M5 organization/rollback status script missing: scripts/teacher-knowledge-vault-m5-organization-rollback-status.sh"
fi

if [[ -f scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh ]]; then
  teacher_knowledge_vault_m6_result=0
  teacher_knowledge_vault_m6_output="$(bash scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh 2>&1)" || teacher_knowledge_vault_m6_result=$?
  teacher_knowledge_vault_m6_pass="$(summary_count "${teacher_knowledge_vault_m6_output}" "PASS")"
  teacher_knowledge_vault_m6_warn="$(summary_count "${teacher_knowledge_vault_m6_output}" "WARN")"
  teacher_knowledge_vault_m6_fail="$(summary_count "${teacher_knowledge_vault_m6_output}" "FAIL")"

  if [[ "${teacher_knowledge_vault_m6_result}" != "0" ]]; then
    printf '%s\n' "${teacher_knowledge_vault_m6_output}"
    fail "Teacher Knowledge Vault M6 extraction/OCR approval status failed"
  elif [[ -n "${teacher_knowledge_vault_m6_pass}" && -n "${teacher_knowledge_vault_m6_warn}" && -n "${teacher_knowledge_vault_m6_fail}" ]]; then
    printf 'Teacher Knowledge Vault M6 Extraction OCR Approval: PASS %s / WARN %s / FAIL %s\n' "${teacher_knowledge_vault_m6_pass}" "${teacher_knowledge_vault_m6_warn}" "${teacher_knowledge_vault_m6_fail}"
    pass "Teacher Knowledge Vault M6 extraction/OCR approval status completed"
  else
    pass "Teacher Knowledge Vault M6 extraction/OCR approval status completed"
  fi
else
  warn "Teacher Knowledge Vault M6 extraction/OCR approval status script missing: scripts/teacher-knowledge-vault-m6-extraction-ocr-approval-status.sh"
fi

section "Local Retrieval Foundation v0"
if [[ -f scripts/local-retrieval-foundation-status.sh ]]; then
  local_retrieval_foundation_result=0
  local_retrieval_foundation_output="$(bash scripts/local-retrieval-foundation-status.sh 2>&1)" || local_retrieval_foundation_result=$?
  local_retrieval_foundation_pass="$(summary_count "${local_retrieval_foundation_output}" "PASS")"
  local_retrieval_foundation_warn="$(summary_count "${local_retrieval_foundation_output}" "WARN")"
  local_retrieval_foundation_fail="$(summary_count "${local_retrieval_foundation_output}" "FAIL")"

  if [[ "${local_retrieval_foundation_result}" != "0" ]]; then
    printf 'Local Retrieval Foundation v0: status command completed\n'
    printf '%s\n' "${local_retrieval_foundation_output}"
    fail "Local Retrieval Foundation status failed"
  elif [[ -n "${local_retrieval_foundation_pass}" && -n "${local_retrieval_foundation_warn}" && -n "${local_retrieval_foundation_fail}" ]]; then
    printf 'Local Retrieval Foundation v0: PASS %s / WARN %s / FAIL %s\n' "${local_retrieval_foundation_pass}" "${local_retrieval_foundation_warn}" "${local_retrieval_foundation_fail}"
    pass "Local Retrieval Foundation status completed"
  else
    printf 'Local Retrieval Foundation v0: status command completed\n'
    pass "Local Retrieval Foundation status completed"
  fi
else
  warn "Local Retrieval Foundation status script missing: scripts/local-retrieval-foundation-status.sh"
fi

section "Integration Planning Foundation v0"
if [[ -f scripts/integration-planning-foundation-status.sh ]]; then
  integration_planning_foundation_result=0
  integration_planning_foundation_output="$(bash scripts/integration-planning-foundation-status.sh 2>&1)" || integration_planning_foundation_result=$?
  integration_planning_foundation_pass="$(summary_count "${integration_planning_foundation_output}" "PASS")"
  integration_planning_foundation_warn="$(summary_count "${integration_planning_foundation_output}" "WARN")"
  integration_planning_foundation_fail="$(summary_count "${integration_planning_foundation_output}" "FAIL")"

  if [[ "${integration_planning_foundation_result}" != "0" ]]; then
    printf 'Integration Planning Foundation v0: status command completed\n'
    printf '%s\n' "${integration_planning_foundation_output}"
    fail "Integration Planning Foundation status failed"
  elif [[ -n "${integration_planning_foundation_pass}" && -n "${integration_planning_foundation_warn}" && -n "${integration_planning_foundation_fail}" ]]; then
    printf 'Integration Planning Foundation v0: PASS %s / WARN %s / FAIL %s\n' "${integration_planning_foundation_pass}" "${integration_planning_foundation_warn}" "${integration_planning_foundation_fail}"
    pass "Integration Planning Foundation status completed"
  else
    printf 'Integration Planning Foundation v0: status command completed\n'
    pass "Integration Planning Foundation status completed"
  fi
else
  warn "Integration Planning Foundation status script missing: scripts/integration-planning-foundation-status.sh"
fi

section "Curriculum Builder Local-First Foundation Plan"
if [[ -f scripts/curriculum-builder-foundation-status.sh ]]; then
  curriculum_builder_foundation_result=0
  curriculum_builder_foundation_output="$(bash scripts/curriculum-builder-foundation-status.sh 2>&1)" || curriculum_builder_foundation_result=$?
  curriculum_builder_foundation_pass="$(summary_count "${curriculum_builder_foundation_output}" "PASS")"
  curriculum_builder_foundation_warn="$(summary_count "${curriculum_builder_foundation_output}" "WARN")"
  curriculum_builder_foundation_fail="$(summary_count "${curriculum_builder_foundation_output}" "FAIL")"

  if [[ "${curriculum_builder_foundation_result}" != "0" ]]; then
    printf 'Curriculum Builder Local-First Foundation Plan: status command completed\n'
    printf '%s\n' "${curriculum_builder_foundation_output}"
    fail "Curriculum Builder foundation status failed"
  elif [[ -n "${curriculum_builder_foundation_pass}" && -n "${curriculum_builder_foundation_warn}" && -n "${curriculum_builder_foundation_fail}" ]]; then
    printf 'Curriculum Builder Local-First Foundation Plan: PASS %s / WARN %s / FAIL %s\n' "${curriculum_builder_foundation_pass}" "${curriculum_builder_foundation_warn}" "${curriculum_builder_foundation_fail}"
    pass "Curriculum Builder foundation status completed"
  else
    printf 'Curriculum Builder Local-First Foundation Plan: status command completed\n'
    pass "Curriculum Builder foundation status completed"
  fi
else
  warn "Curriculum Builder foundation status script missing: scripts/curriculum-builder-foundation-status.sh"
fi

section "Curriculum Builder Metadata Contract Schemas (Programs A4–A7)"
if [[ -f scripts/curriculum-builder-contract-schemas-status.sh ]]; then
  curriculum_contracts_result=0
  curriculum_contracts_output="$(bash scripts/curriculum-builder-contract-schemas-status.sh 2>&1)" || curriculum_contracts_result=$?
  curriculum_contracts_pass="$(summary_count "${curriculum_contracts_output}" "PASS")"
  curriculum_contracts_warn="$(summary_count "${curriculum_contracts_output}" "WARN")"
  curriculum_contracts_fail="$(summary_count "${curriculum_contracts_output}" "FAIL")"

  if [[ "${curriculum_contracts_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_contracts_output}"
    fail "Curriculum Builder contract schemas status failed"
  elif [[ -n "${curriculum_contracts_pass}" && -n "${curriculum_contracts_warn}" && -n "${curriculum_contracts_fail}" ]]; then
    printf 'Curriculum Builder Contract Schemas: PASS %s / WARN %s / FAIL %s\n' "${curriculum_contracts_pass}" "${curriculum_contracts_warn}" "${curriculum_contracts_fail}"
    pass "Curriculum Builder contract schemas status completed"
  else
    pass "Curriculum Builder contract schemas status completed"
  fi
else
  warn "Curriculum Builder contract schemas status script missing: scripts/curriculum-builder-contract-schemas-status.sh"
fi

section "Curriculum Builder Registry v0.2 Manual Entry Dry-Run (CB-IMPL-1)"
if [[ -f scripts/curriculum-builder-registry-v0-2-status.sh ]]; then
  curriculum_registry_dry_run_result=0
  curriculum_registry_dry_run_output="$(bash scripts/curriculum-builder-registry-v0-2-status.sh 2>&1)" || curriculum_registry_dry_run_result=$?
  curriculum_registry_dry_run_pass="$(summary_count "${curriculum_registry_dry_run_output}" "PASS")"
  curriculum_registry_dry_run_warn="$(summary_count "${curriculum_registry_dry_run_output}" "WARN")"
  curriculum_registry_dry_run_fail="$(summary_count "${curriculum_registry_dry_run_output}" "FAIL")"

  if [[ "${curriculum_registry_dry_run_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_registry_dry_run_output}"
    fail "Curriculum Builder Registry v0.2 dry-run status failed"
  elif [[ -n "${curriculum_registry_dry_run_pass}" && -n "${curriculum_registry_dry_run_warn}" && -n "${curriculum_registry_dry_run_fail}" ]]; then
    printf 'Curriculum Builder Registry v0.2 Dry-Run: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_dry_run_pass}" "${curriculum_registry_dry_run_warn}" "${curriculum_registry_dry_run_fail}"
    pass "Curriculum Builder Registry v0.2 dry-run status completed"
  else
    pass "Curriculum Builder Registry v0.2 dry-run status completed"
  fi
else
  warn "Curriculum Builder Registry v0.2 dry-run status script missing: scripts/curriculum-builder-registry-v0-2-status.sh"
fi

section "Curriculum Builder Registry v0.2 Local Fake Records (CB-IMPL-2)"
if [[ -f scripts/curriculum-builder-registry-v0-2-local-records-status.sh ]]; then
  curriculum_registry_records_result=0
  curriculum_registry_records_output="$(bash scripts/curriculum-builder-registry-v0-2-local-records-status.sh 2>&1)" || curriculum_registry_records_result=$?
  curriculum_registry_records_pass="$(summary_count "${curriculum_registry_records_output}" "PASS")"
  curriculum_registry_records_warn="$(summary_count "${curriculum_registry_records_output}" "WARN")"
  curriculum_registry_records_fail="$(summary_count "${curriculum_registry_records_output}" "FAIL")"

  if [[ "${curriculum_registry_records_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_registry_records_output}"
    fail "Curriculum Builder Registry v0.2 local records status failed"
  elif [[ -n "${curriculum_registry_records_pass}" && -n "${curriculum_registry_records_warn}" && -n "${curriculum_registry_records_fail}" ]]; then
    printf 'Curriculum Builder Registry v0.2 Local Records: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_records_pass}" "${curriculum_registry_records_warn}" "${curriculum_registry_records_fail}"
    pass "Curriculum Builder Registry v0.2 local records status completed"
  else
    pass "Curriculum Builder Registry v0.2 local records status completed"
  fi
else
  warn "Curriculum Builder Registry v0.2 local records status script missing: scripts/curriculum-builder-registry-v0-2-local-records-status.sh"
fi

section "Curriculum Builder Registry v0.2 Renderer Foundation (CB-IMPL-3)"
if [[ -f scripts/curriculum-builder-registry-v0-2-renderer-status.sh ]]; then
  curriculum_registry_renderer_result=0
  curriculum_registry_renderer_output="$(bash scripts/curriculum-builder-registry-v0-2-renderer-status.sh 2>&1)" || curriculum_registry_renderer_result=$?
  curriculum_registry_renderer_pass="$(summary_count "${curriculum_registry_renderer_output}" "PASS")"
  curriculum_registry_renderer_warn="$(summary_count "${curriculum_registry_renderer_output}" "WARN")"
  curriculum_registry_renderer_fail="$(summary_count "${curriculum_registry_renderer_output}" "FAIL")"

  if [[ "${curriculum_registry_renderer_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_registry_renderer_output}"
    fail "Curriculum Builder Registry v0.2 renderer status failed"
  elif [[ -n "${curriculum_registry_renderer_pass}" && -n "${curriculum_registry_renderer_warn}" && -n "${curriculum_registry_renderer_fail}" ]]; then
    printf 'Curriculum Builder Registry v0.2 Renderer: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_renderer_pass}" "${curriculum_registry_renderer_warn}" "${curriculum_registry_renderer_fail}"
    pass "Curriculum Builder Registry v0.2 renderer status completed"
  else
    pass "Curriculum Builder Registry v0.2 renderer status completed"
  fi
else
  warn "Curriculum Builder Registry v0.2 renderer status script missing: scripts/curriculum-builder-registry-v0-2-renderer-status.sh"
fi

section "Curriculum Builder Registry v0.2 Retrieval Hooks (CB-IMPL-4)"
if [[ -f scripts/curriculum-builder-registry-v0-2-retrieval-status.sh ]]; then
  curriculum_registry_retrieval_result=0
  curriculum_registry_retrieval_output="$(bash scripts/curriculum-builder-registry-v0-2-retrieval-status.sh 2>&1)" || curriculum_registry_retrieval_result=$?
  curriculum_registry_retrieval_pass="$(summary_count "${curriculum_registry_retrieval_output}" "PASS")"
  curriculum_registry_retrieval_warn="$(summary_count "${curriculum_registry_retrieval_output}" "WARN")"
  curriculum_registry_retrieval_fail="$(summary_count "${curriculum_registry_retrieval_output}" "FAIL")"

  if [[ "${curriculum_registry_retrieval_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_registry_retrieval_output}"
    fail "Curriculum Builder Registry v0.2 retrieval status failed"
  elif [[ -n "${curriculum_registry_retrieval_pass}" && -n "${curriculum_registry_retrieval_warn}" && -n "${curriculum_registry_retrieval_fail}" ]]; then
    printf 'Curriculum Builder Registry v0.2 Retrieval: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_retrieval_pass}" "${curriculum_registry_retrieval_warn}" "${curriculum_registry_retrieval_fail}"
    pass "Curriculum Builder Registry v0.2 retrieval status completed"
  else
    pass "Curriculum Builder Registry v0.2 retrieval status completed"
  fi
else
  warn "Curriculum Builder Registry v0.2 retrieval status script missing: scripts/curriculum-builder-registry-v0-2-retrieval-status.sh"
fi

section "Curriculum Builder Production Registry Workflow Planning"
if [[ -f scripts/curriculum-builder-production-registry-planning-status.sh ]]; then
  curriculum_production_registry_planning_result=0
  curriculum_production_registry_planning_output="$(bash scripts/curriculum-builder-production-registry-planning-status.sh 2>&1)" || curriculum_production_registry_planning_result=$?
  curriculum_production_registry_planning_pass="$(summary_count "${curriculum_production_registry_planning_output}" "PASS")"
  curriculum_production_registry_planning_warn="$(summary_count "${curriculum_production_registry_planning_output}" "WARN")"
  curriculum_production_registry_planning_fail="$(summary_count "${curriculum_production_registry_planning_output}" "FAIL")"

  if [[ "${curriculum_production_registry_planning_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_production_registry_planning_output}"
    fail "Curriculum Builder production registry planning status failed"
  elif [[ -n "${curriculum_production_registry_planning_pass}" && -n "${curriculum_production_registry_planning_warn}" && -n "${curriculum_production_registry_planning_fail}" ]]; then
    printf 'Curriculum Builder Production Registry Planning: PASS %s / WARN %s / FAIL %s\n' "${curriculum_production_registry_planning_pass}" "${curriculum_production_registry_planning_warn}" "${curriculum_production_registry_planning_fail}"
    pass "Curriculum Builder production registry planning status completed"
  else
    pass "Curriculum Builder production registry planning status completed"
  fi
else
  warn "Curriculum Builder production registry planning status script missing: scripts/curriculum-builder-production-registry-planning-status.sh"
fi

section "Production Registry Governance Foundation (CB-PROD-GOV)"
if [[ -f scripts/curriculum-builder-production-registry-governance-status.sh ]]; then
  curriculum_prod_gov_result=0
  curriculum_prod_gov_output="$(bash scripts/curriculum-builder-production-registry-governance-status.sh 2>&1)" || curriculum_prod_gov_result=$?
  curriculum_prod_gov_pass="$(summary_count "${curriculum_prod_gov_output}" "PASS")"
  curriculum_prod_gov_warn="$(summary_count "${curriculum_prod_gov_output}" "WARN")"
  curriculum_prod_gov_fail="$(summary_count "${curriculum_prod_gov_output}" "FAIL")"

  if [[ "${curriculum_prod_gov_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_prod_gov_output}"
    fail "Production registry governance status failed"
  elif [[ -n "${curriculum_prod_gov_pass}" && -n "${curriculum_prod_gov_warn}" && -n "${curriculum_prod_gov_fail}" ]]; then
    printf 'Production Registry Governance: PASS %s / WARN %s / FAIL %s\n' "${curriculum_prod_gov_pass}" "${curriculum_prod_gov_warn}" "${curriculum_prod_gov_fail}"
    pass "Production registry governance status completed"
  else
    pass "Production registry governance status completed"
  fi
else
  warn "Production registry governance status script missing: scripts/curriculum-builder-production-registry-governance-status.sh"
fi

section "Owen Production Registry Approval Checklist Tracker"
if [[ -f scripts/curriculum-builder-production-registry-owen-checklist-status.sh ]]; then
  curriculum_owen_checklist_result=0
  curriculum_owen_checklist_output="$(bash scripts/curriculum-builder-production-registry-owen-checklist-status.sh 2>&1)" || curriculum_owen_checklist_result=$?
  curriculum_owen_checklist_pass="$(summary_count "${curriculum_owen_checklist_output}" "PASS")"
  curriculum_owen_checklist_warn="$(summary_count "${curriculum_owen_checklist_output}" "WARN")"
  curriculum_owen_checklist_fail="$(summary_count "${curriculum_owen_checklist_output}" "FAIL")"

  if [[ "${curriculum_owen_checklist_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_owen_checklist_output}"
    fail "Owen production registry checklist tracker status failed"
  elif [[ -n "${curriculum_owen_checklist_pass}" && -n "${curriculum_owen_checklist_warn}" && -n "${curriculum_owen_checklist_fail}" ]]; then
    printf 'Owen Production Registry Checklist: PASS %s / WARN %s / FAIL %s\n' "${curriculum_owen_checklist_pass}" "${curriculum_owen_checklist_warn}" "${curriculum_owen_checklist_fail}"
    pass "Owen production registry checklist tracker status completed"
  else
    pass "Owen production registry checklist tracker status completed"
  fi
else
  warn "Owen production registry checklist status script missing: scripts/curriculum-builder-production-registry-owen-checklist-status.sh"
fi

section "Production Registry Phase 2 Preflight"
if [[ -f scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh ]]; then
  curriculum_phase2_preflight_result=0
  curriculum_phase2_preflight_output="$(bash scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh 2>&1)" || curriculum_phase2_preflight_result=$?
  curriculum_phase2_preflight_pass="$(summary_count "${curriculum_phase2_preflight_output}" "PASS")"
  curriculum_phase2_preflight_warn="$(summary_count "${curriculum_phase2_preflight_output}" "WARN")"
  curriculum_phase2_preflight_fail="$(summary_count "${curriculum_phase2_preflight_output}" "FAIL")"

  if [[ "${curriculum_phase2_preflight_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_phase2_preflight_output}"
    fail "Production registry Phase 2 preflight status failed"
  elif [[ -n "${curriculum_phase2_preflight_pass}" && -n "${curriculum_phase2_preflight_warn}" && -n "${curriculum_phase2_preflight_fail}" ]]; then
    printf 'Production Registry Phase 2 Preflight: PASS %s / WARN %s / FAIL %s\n' "${curriculum_phase2_preflight_pass}" "${curriculum_phase2_preflight_warn}" "${curriculum_phase2_preflight_fail}"
    pass "Production registry Phase 2 preflight status completed"
  else
    pass "Production registry Phase 2 preflight status completed"
  fi
else
  warn "Production registry Phase 2 preflight status script missing: scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh"
fi

section "Production Registry Metadata Boundary Refinement"
if [[ -f scripts/curriculum-builder-production-registry-metadata-boundary-status.sh ]]; then
  curriculum_metadata_boundary_result=0
  curriculum_metadata_boundary_output="$(bash scripts/curriculum-builder-production-registry-metadata-boundary-status.sh 2>&1)" || curriculum_metadata_boundary_result=$?
  curriculum_metadata_boundary_pass="$(summary_count "${curriculum_metadata_boundary_output}" "PASS")"
  curriculum_metadata_boundary_warn="$(summary_count "${curriculum_metadata_boundary_output}" "WARN")"
  curriculum_metadata_boundary_fail="$(summary_count "${curriculum_metadata_boundary_output}" "FAIL")"

  if [[ "${curriculum_metadata_boundary_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_metadata_boundary_output}"
    fail "Production registry metadata boundary status failed"
  elif [[ -n "${curriculum_metadata_boundary_pass}" && -n "${curriculum_metadata_boundary_warn}" && -n "${curriculum_metadata_boundary_fail}" ]]; then
    printf 'Production Registry Metadata Boundary: PASS %s / WARN %s / FAIL %s\n' "${curriculum_metadata_boundary_pass}" "${curriculum_metadata_boundary_warn}" "${curriculum_metadata_boundary_fail}"
    pass "Production registry metadata boundary status completed"
  else
    pass "Production registry metadata boundary status completed"
  fi
else
  warn "Production registry metadata boundary status script missing: scripts/curriculum-builder-production-registry-metadata-boundary-status.sh"
fi

section "Production Registry Empty-File Shell"
if [[ -f scripts/curriculum-builder-production-registry-empty-file-status.sh ]]; then
  curriculum_empty_file_result=0
  curriculum_empty_file_output="$(bash scripts/curriculum-builder-production-registry-empty-file-status.sh 2>&1)" || curriculum_empty_file_result=$?
  curriculum_empty_file_pass="$(summary_count "${curriculum_empty_file_output}" "PASS")"
  curriculum_empty_file_warn="$(summary_count "${curriculum_empty_file_output}" "WARN")"
  curriculum_empty_file_fail="$(summary_count "${curriculum_empty_file_output}" "FAIL")"

  if [[ "${curriculum_empty_file_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_empty_file_output}"
    fail "Production registry empty-file status failed"
  elif [[ -n "${curriculum_empty_file_pass}" && -n "${curriculum_empty_file_warn}" && -n "${curriculum_empty_file_fail}" ]]; then
    printf 'Production Registry Empty File: PASS %s / WARN %s / FAIL %s\n' "${curriculum_empty_file_pass}" "${curriculum_empty_file_warn}" "${curriculum_empty_file_fail}"
    pass "Production registry empty-file status completed"
  else
    pass "Production registry empty-file status completed"
  fi
else
  warn "Production registry empty-file status script missing: scripts/curriculum-builder-production-registry-empty-file-status.sh"
fi

section "Production Registry Metadata Pilot Execution Planning"
if [[ -f scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh ]]; then
  curriculum_metadata_pilot_plan_result=0
  curriculum_metadata_pilot_plan_output="$(bash scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh 2>&1)" || curriculum_metadata_pilot_plan_result=$?
  curriculum_metadata_pilot_plan_pass="$(summary_count "${curriculum_metadata_pilot_plan_output}" "PASS")"
  curriculum_metadata_pilot_plan_warn="$(summary_count "${curriculum_metadata_pilot_plan_output}" "WARN")"
  curriculum_metadata_pilot_plan_fail="$(summary_count "${curriculum_metadata_pilot_plan_output}" "FAIL")"

  if [[ "${curriculum_metadata_pilot_plan_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_metadata_pilot_plan_output}"
    fail "Production registry metadata pilot plan status failed"
  elif [[ -n "${curriculum_metadata_pilot_plan_pass}" && -n "${curriculum_metadata_pilot_plan_warn}" && -n "${curriculum_metadata_pilot_plan_fail}" ]]; then
    printf 'Production Registry Metadata Pilot Plan: PASS %s / WARN %s / FAIL %s\n' "${curriculum_metadata_pilot_plan_pass}" "${curriculum_metadata_pilot_plan_warn}" "${curriculum_metadata_pilot_plan_fail}"
    pass "Production registry metadata pilot plan status completed"
  else
    pass "Production registry metadata pilot plan status completed"
  fi
else
  warn "Production registry metadata pilot plan status script missing: scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh"
fi

section "Production Registry First Governed Record"
if [[ -f scripts/curriculum-builder-production-registry-first-record-status.sh ]]; then
  curriculum_first_record_result=0
  curriculum_first_record_output="$(bash scripts/curriculum-builder-production-registry-first-record-status.sh 2>&1)" || curriculum_first_record_result=$?
  curriculum_first_record_pass="$(summary_count "${curriculum_first_record_output}" "PASS")"
  curriculum_first_record_warn="$(summary_count "${curriculum_first_record_output}" "WARN")"
  curriculum_first_record_fail="$(summary_count "${curriculum_first_record_output}" "FAIL")"

  if [[ "${curriculum_first_record_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_first_record_output}"
    fail "Production registry first-record status failed"
  elif [[ -n "${curriculum_first_record_pass}" && -n "${curriculum_first_record_warn}" && -n "${curriculum_first_record_fail}" ]]; then
    printf 'Production Registry First Record: PASS %s / WARN %s / FAIL %s\n' "${curriculum_first_record_pass}" "${curriculum_first_record_warn}" "${curriculum_first_record_fail}"
    pass "Production registry first-record status completed"
  else
    pass "Production registry first-record status completed"
  fi
else
  warn "Production registry first-record status script missing: scripts/curriculum-builder-production-registry-first-record-status.sh"
fi

section "Production Registry Next-Gate Decision Prep"
if [[ -f scripts/curriculum-builder-production-registry-next-gate-status.sh ]]; then
  curriculum_next_gate_result=0
  curriculum_next_gate_output="$(bash scripts/curriculum-builder-production-registry-next-gate-status.sh 2>&1)" || curriculum_next_gate_result=$?
  curriculum_next_gate_pass="$(summary_count "${curriculum_next_gate_output}" "PASS")"
  curriculum_next_gate_warn="$(summary_count "${curriculum_next_gate_output}" "WARN")"
  curriculum_next_gate_fail="$(summary_count "${curriculum_next_gate_output}" "FAIL")"

  if [[ "${curriculum_next_gate_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_next_gate_output}"
    fail "Production registry next-gate status failed"
  elif [[ -n "${curriculum_next_gate_pass}" && -n "${curriculum_next_gate_warn}" && -n "${curriculum_next_gate_fail}" ]]; then
    printf 'Production Registry Next Gate: PASS %s / WARN %s / FAIL %s\n' "${curriculum_next_gate_pass}" "${curriculum_next_gate_warn}" "${curriculum_next_gate_fail}"
    pass "Production registry next-gate status completed"
  else
    pass "Production registry next-gate status completed"
  fi
else
  warn "Production registry next-gate status script missing: scripts/curriculum-builder-production-registry-next-gate-status.sh"
fi

section "Whole-System Master Roadmap Build-State"
if [[ -f scripts/whole-system-master-roadmap-status.sh ]]; then
  whole_system_master_roadmap_result=0
  whole_system_master_roadmap_output="$(bash scripts/whole-system-master-roadmap-status.sh 2>&1)" || whole_system_master_roadmap_result=$?
  whole_system_master_roadmap_pass="$(summary_count "${whole_system_master_roadmap_output}" "PASS")"
  whole_system_master_roadmap_warn="$(summary_count "${whole_system_master_roadmap_output}" "WARN")"
  whole_system_master_roadmap_fail="$(summary_count "${whole_system_master_roadmap_output}" "FAIL")"

  if [[ "${whole_system_master_roadmap_result}" != "0" ]]; then
    printf '%s\n' "${whole_system_master_roadmap_output}"
    fail "Whole-system master roadmap status failed"
  elif [[ -n "${whole_system_master_roadmap_pass}" && -n "${whole_system_master_roadmap_warn}" && -n "${whole_system_master_roadmap_fail}" ]]; then
    printf 'Whole-System Master Roadmap: PASS %s / WARN %s / FAIL %s\n' "${whole_system_master_roadmap_pass}" "${whole_system_master_roadmap_warn}" "${whole_system_master_roadmap_fail}"
    pass "Whole-system master roadmap status completed"
  else
    pass "Whole-system master roadmap status completed"
  fi
else
  warn "Whole-system master roadmap status script missing: scripts/whole-system-master-roadmap-status.sh"
fi

section "Whole-System Coherence Maintenance"
if [[ -f scripts/whole-system-coherence-status.sh ]]; then
  whole_system_coherence_result=0
  whole_system_coherence_output="$(bash scripts/whole-system-coherence-status.sh 2>&1)" || whole_system_coherence_result=$?
  whole_system_coherence_pass="$(summary_count "${whole_system_coherence_output}" "PASS")"
  whole_system_coherence_warn="$(summary_count "${whole_system_coherence_output}" "WARN")"
  whole_system_coherence_fail="$(summary_count "${whole_system_coherence_output}" "FAIL")"

  if [[ "${whole_system_coherence_result}" != "0" ]]; then
    printf '%s\n' "${whole_system_coherence_output}"
    fail "Whole-system coherence status failed"
  elif [[ -n "${whole_system_coherence_pass}" && -n "${whole_system_coherence_warn}" && -n "${whole_system_coherence_fail}" ]]; then
    printf 'Whole-System Coherence: PASS %s / WARN %s / FAIL %s\n' "${whole_system_coherence_pass}" "${whole_system_coherence_warn}" "${whole_system_coherence_fail}"
    pass "Whole-system coherence status completed"
  else
    pass "Whole-system coherence status completed"
  fi
else
  warn "Whole-system coherence status script missing: scripts/whole-system-coherence-status.sh"
fi

section "Agent Builder Compatibility Governance"
if [[ -f scripts/agent-builder-compatibility-governance-status.sh ]]; then
  agent_builder_governance_result=0
  agent_builder_governance_output="$(bash scripts/agent-builder-compatibility-governance-status.sh 2>&1)" || agent_builder_governance_result=$?
  agent_builder_governance_pass="$(summary_count "${agent_builder_governance_output}" "PASS")"
  agent_builder_governance_warn="$(summary_count "${agent_builder_governance_output}" "WARN")"
  agent_builder_governance_fail="$(summary_count "${agent_builder_governance_output}" "FAIL")"

  if [[ "${agent_builder_governance_result}" != "0" ]]; then
    printf '%s\n' "${agent_builder_governance_output}"
    fail "Agent builder compatibility governance status failed"
  elif [[ -n "${agent_builder_governance_pass}" && -n "${agent_builder_governance_warn}" && -n "${agent_builder_governance_fail}" ]]; then
    printf 'Agent Builder Governance: PASS %s / WARN %s / FAIL %s\n' "${agent_builder_governance_pass}" "${agent_builder_governance_warn}" "${agent_builder_governance_fail}"
    pass "Agent builder compatibility governance status completed"
  else
    pass "Agent builder compatibility governance status completed"
  fi
else
  warn "Agent builder compatibility governance status script missing: scripts/agent-builder-compatibility-governance-status.sh"
fi

section "Owen Architecture Decision Packets"
if [[ -f scripts/owen-architecture-decision-packets-status.sh ]]; then
  decision_packets_result=0
  decision_packets_output="$(bash scripts/owen-architecture-decision-packets-status.sh 2>&1)" || decision_packets_result=$?
  decision_packets_pass="$(summary_count "${decision_packets_output}" "PASS")"
  decision_packets_warn="$(summary_count "${decision_packets_output}" "WARN")"
  decision_packets_fail="$(summary_count "${decision_packets_output}" "FAIL")"

  if [[ "${decision_packets_result}" != "0" ]]; then
    printf '%s\n' "${decision_packets_output}"
    fail "Owen architecture decision packets status failed"
  elif [[ -n "${decision_packets_pass}" && -n "${decision_packets_warn}" && -n "${decision_packets_fail}" ]]; then
    printf 'Owen Decision Packets: PASS %s / WARN %s / FAIL %s\n' "${decision_packets_pass}" "${decision_packets_warn}" "${decision_packets_fail}"
    pass "Owen architecture decision packets status completed"
  else
    pass "Owen architecture decision packets status completed"
  fi
else
  warn "Owen architecture decision packets status script missing: scripts/owen-architecture-decision-packets-status.sh"
fi

section "App Ecosystem Inventory"
if [[ -f scripts/app-ecosystem-inventory-status.sh ]]; then
  app_ecosystem_result=0
  app_ecosystem_output="$(bash scripts/app-ecosystem-inventory-status.sh 2>&1)" || app_ecosystem_result=$?
  app_ecosystem_pass="$(summary_count "${app_ecosystem_output}" "PASS")"
  app_ecosystem_warn="$(summary_count "${app_ecosystem_output}" "WARN")"
  app_ecosystem_fail="$(summary_count "${app_ecosystem_output}" "FAIL")"

  if [[ "${app_ecosystem_result}" != "0" ]]; then
    printf '%s\n' "${app_ecosystem_output}"
    fail "App ecosystem inventory status failed"
  elif [[ -n "${app_ecosystem_pass}" && -n "${app_ecosystem_warn}" && -n "${app_ecosystem_fail}" ]]; then
    printf 'App Ecosystem Inventory: PASS %s / WARN %s / FAIL %s\n' "${app_ecosystem_pass}" "${app_ecosystem_warn}" "${app_ecosystem_fail}"
    pass "App ecosystem inventory status completed"
  else
    pass "App ecosystem inventory status completed"
  fi
else
  warn "App ecosystem inventory status script missing: scripts/app-ecosystem-inventory-status.sh"
fi

section "Classroom Timer & Stopwatch Planning"
if [[ -f scripts/classroom-timer-stopwatch-planning-status.sh ]]; then
  timer_planning_result=0
  timer_planning_output="$(bash scripts/classroom-timer-stopwatch-planning-status.sh 2>&1)" || timer_planning_result=$?
  timer_planning_pass="$(summary_count "${timer_planning_output}" "PASS")"
  timer_planning_warn="$(summary_count "${timer_planning_output}" "WARN")"
  timer_planning_fail="$(summary_count "${timer_planning_output}" "FAIL")"

  if [[ "${timer_planning_result}" != "0" ]]; then
    printf '%s\n' "${timer_planning_output}"
    fail "Classroom Timer & Stopwatch planning status failed"
  elif [[ -n "${timer_planning_pass}" && -n "${timer_planning_warn}" && -n "${timer_planning_fail}" ]]; then
    printf 'Timer & Stopwatch Planning: PASS %s / WARN %s / FAIL %s\n' "${timer_planning_pass}" "${timer_planning_warn}" "${timer_planning_fail}"
    pass "Classroom Timer & Stopwatch planning status completed"
  else
    pass "Classroom Timer & Stopwatch planning status completed"
  fi
else
  warn "Classroom Timer & Stopwatch planning status script missing: scripts/classroom-timer-stopwatch-planning-status.sh"
fi

section "Classroom Timer & Stopwatch Runtime Prototype"
if [[ -f scripts/classroom-timer-stopwatch-runtime-status.sh ]]; then
  timer_runtime_result=0
  timer_runtime_output="$(bash scripts/classroom-timer-stopwatch-runtime-status.sh 2>&1)" || timer_runtime_result=$?
  timer_runtime_pass="$(summary_count "${timer_runtime_output}" "PASS")"
  timer_runtime_warn="$(summary_count "${timer_runtime_output}" "WARN")"
  timer_runtime_fail="$(summary_count "${timer_runtime_output}" "FAIL")"

  if [[ "${timer_runtime_result}" != "0" ]]; then
    printf '%s\n' "${timer_runtime_output}"
    fail "Classroom Timer & Stopwatch runtime status failed"
  elif [[ -n "${timer_runtime_pass}" && -n "${timer_runtime_warn}" && -n "${timer_runtime_fail}" ]]; then
    printf 'Timer & Stopwatch Runtime: PASS %s / WARN %s / FAIL %s\n' "${timer_runtime_pass}" "${timer_runtime_warn}" "${timer_runtime_fail}"
    pass "Classroom Timer & Stopwatch runtime status completed"
  else
    pass "Classroom Timer & Stopwatch runtime status completed"
  fi
else
  warn "Classroom Timer & Stopwatch runtime status script missing: scripts/classroom-timer-stopwatch-runtime-status.sh"
fi

section "App Ecosystem Planning Lanes Program"
if [[ -f scripts/app-ecosystem-planning-lanes-status.sh ]]; then
  planning_lanes_result=0
  planning_lanes_output="$(bash scripts/app-ecosystem-planning-lanes-status.sh 2>&1)" || planning_lanes_result=$?
  planning_lanes_pass="$(summary_count "${planning_lanes_output}" "PASS")"
  planning_lanes_warn="$(summary_count "${planning_lanes_output}" "WARN")"
  planning_lanes_fail="$(summary_count "${planning_lanes_output}" "FAIL")"

  if [[ "${planning_lanes_result}" != "0" ]]; then
    printf '%s\n' "${planning_lanes_output}"
    fail "App ecosystem planning lanes status failed"
  elif [[ -n "${planning_lanes_pass}" && -n "${planning_lanes_warn}" && -n "${planning_lanes_fail}" ]]; then
    printf 'App Ecosystem Planning Lanes: PASS %s / WARN %s / FAIL %s\n' "${planning_lanes_pass}" "${planning_lanes_warn}" "${planning_lanes_fail}"
    pass "App ecosystem planning lanes status completed"
  else
    pass "App ecosystem planning lanes status completed"
  fi
else
  warn "App ecosystem planning lanes status script missing: scripts/app-ecosystem-planning-lanes-status.sh"
fi

section "App Runtime Approval Gate"
if [[ -f scripts/app-runtime-approval-gate-status.sh ]]; then
  approval_gate_result=0
  approval_gate_output="$(bash scripts/app-runtime-approval-gate-status.sh 2>&1)" || approval_gate_result=$?
  approval_gate_pass="$(summary_count "${approval_gate_output}" "PASS")"
  approval_gate_warn="$(summary_count "${approval_gate_output}" "WARN")"
  approval_gate_fail="$(summary_count "${approval_gate_output}" "FAIL")"

  if [[ "${approval_gate_result}" != "0" ]]; then
    printf '%s\n' "${approval_gate_output}"
    fail "App runtime approval gate status failed"
  elif [[ -n "${approval_gate_pass}" && -n "${approval_gate_warn}" && -n "${approval_gate_fail}" ]]; then
    printf 'App Runtime Approval Gate: PASS %s / WARN %s / FAIL %s\n' "${approval_gate_pass}" "${approval_gate_warn}" "${approval_gate_fail}"
    pass "App runtime approval gate status completed"
  else
    pass "App runtime approval gate status completed"
  fi
else
  warn "App runtime approval gate status script missing: scripts/app-runtime-approval-gate-status.sh"
fi

section "Curriculum Source Readiness Foundation"
if [[ -f scripts/curriculum-source-readiness-status.sh ]]; then
  curriculum_source_readiness_result=0
  curriculum_source_readiness_output="$(bash scripts/curriculum-source-readiness-status.sh 2>&1)" || curriculum_source_readiness_result=$?
  curriculum_source_readiness_pass="$(summary_count "${curriculum_source_readiness_output}" "PASS")"
  curriculum_source_readiness_warn="$(summary_count "${curriculum_source_readiness_output}" "WARN")"
  curriculum_source_readiness_fail="$(summary_count "${curriculum_source_readiness_output}" "FAIL")"

  if [[ "${curriculum_source_readiness_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_source_readiness_output}"
    fail "Curriculum Source Readiness status failed"
  elif [[ -n "${curriculum_source_readiness_pass}" && -n "${curriculum_source_readiness_warn}" && -n "${curriculum_source_readiness_fail}" ]]; then
    printf 'Curriculum Source Readiness: PASS %s / WARN %s / FAIL %s\n' "${curriculum_source_readiness_pass}" "${curriculum_source_readiness_warn}" "${curriculum_source_readiness_fail}"
    pass "Curriculum Source Readiness status completed"
  else
    pass "Curriculum Source Readiness status completed"
  fi
else
  warn "Curriculum Source Readiness status script missing: scripts/curriculum-source-readiness-status.sh"
fi

section "Curriculum Builder Registry Lane Status (Aggregate)"
if [[ -f scripts/curriculum-builder-registry-lane-status.sh ]]; then
  curriculum_registry_lane_result=0
  curriculum_registry_lane_output="$(bash scripts/curriculum-builder-registry-lane-status.sh 2>&1)" || curriculum_registry_lane_result=$?
  curriculum_registry_lane_pass="$(summary_count "${curriculum_registry_lane_output}" "PASS")"
  curriculum_registry_lane_warn="$(summary_count "${curriculum_registry_lane_output}" "WARN")"
  curriculum_registry_lane_fail="$(summary_count "${curriculum_registry_lane_output}" "FAIL")"

  if [[ "${curriculum_registry_lane_result}" != "0" ]]; then
    printf '%s\n' "${curriculum_registry_lane_output}"
    fail "Curriculum Builder Registry lane status failed"
  elif [[ -n "${curriculum_registry_lane_pass}" && -n "${curriculum_registry_lane_warn}" && -n "${curriculum_registry_lane_fail}" ]]; then
    printf 'Curriculum Builder Registry Lane: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_lane_pass}" "${curriculum_registry_lane_warn}" "${curriculum_registry_lane_fail}"
    pass "Curriculum Builder Registry lane status completed"
  else
    pass "Curriculum Builder Registry lane status completed"
  fi
else
  warn "Curriculum Builder Registry lane status script missing: scripts/curriculum-builder-registry-lane-status.sh"
fi

section "Curriculum Registry v0 Manual Metadata Foundation"
if [[ -f scripts/curriculum-registry-v0-status.sh ]]; then
  curriculum_registry_v0_result=0
  curriculum_registry_v0_output="$(bash scripts/curriculum-registry-v0-status.sh 2>&1)" || curriculum_registry_v0_result=$?
  curriculum_registry_v0_pass="$(summary_count "${curriculum_registry_v0_output}" "PASS")"
  curriculum_registry_v0_warn="$(summary_count "${curriculum_registry_v0_output}" "WARN")"
  curriculum_registry_v0_fail="$(summary_count "${curriculum_registry_v0_output}" "FAIL")"

  if [[ "${curriculum_registry_v0_result}" != "0" ]]; then
    printf 'Curriculum Registry v0 Manual Metadata Foundation: status command completed\n'
    printf '%s\n' "${curriculum_registry_v0_output}"
    fail "Curriculum Registry v0 status failed"
  elif [[ -n "${curriculum_registry_v0_pass}" && -n "${curriculum_registry_v0_warn}" && -n "${curriculum_registry_v0_fail}" ]]; then
    printf 'Curriculum Registry v0 Manual Metadata Foundation: PASS %s / WARN %s / FAIL %s\n' "${curriculum_registry_v0_pass}" "${curriculum_registry_v0_warn}" "${curriculum_registry_v0_fail}"
    pass "Curriculum Registry v0 status completed"
  else
    printf 'Curriculum Registry v0 Manual Metadata Foundation: status command completed\n'
    pass "Curriculum Registry v0 status completed"
  fi
else
  warn "Curriculum Registry v0 status script missing: scripts/curriculum-registry-v0-status.sh"
fi

section "Curriculum Output Contract v0 Bounded Validator Foundation"
if [[ -f scripts/curriculum-output-contract-v0-status.sh ]]; then
  curriculum_output_contract_v0_result=0
  curriculum_output_contract_v0_output="$(bash scripts/curriculum-output-contract-v0-status.sh 2>&1)" || curriculum_output_contract_v0_result=$?
  curriculum_output_contract_v0_pass="$(summary_count "${curriculum_output_contract_v0_output}" "PASS")"
  curriculum_output_contract_v0_warn="$(summary_count "${curriculum_output_contract_v0_output}" "WARN")"
  curriculum_output_contract_v0_fail="$(summary_count "${curriculum_output_contract_v0_output}" "FAIL")"

  if [[ "${curriculum_output_contract_v0_result}" != "0" ]]; then
    printf 'Curriculum Output Contract v0 Bounded Validator Foundation: status command completed\n'
    printf '%s\n' "${curriculum_output_contract_v0_output}"
    fail "Curriculum Output Contract v0 status failed"
  elif [[ -n "${curriculum_output_contract_v0_pass}" && -n "${curriculum_output_contract_v0_warn}" && -n "${curriculum_output_contract_v0_fail}" ]]; then
    printf 'Curriculum Output Contract v0 Bounded Validator Foundation: PASS %s / WARN %s / FAIL %s\n' "${curriculum_output_contract_v0_pass}" "${curriculum_output_contract_v0_warn}" "${curriculum_output_contract_v0_fail}"
    pass "Curriculum Output Contract v0 status completed"
  else
    printf 'Curriculum Output Contract v0 Bounded Validator Foundation: status command completed\n'
    pass "Curriculum Output Contract v0 status completed"
  fi
else
  warn "Curriculum Output Contract v0 status script missing: scripts/curriculum-output-contract-v0-status.sh"
fi

section "Curriculum Registry–Contract Binding v0 Foundation"
if [[ -f scripts/curriculum-binding-v0-status.sh ]]; then
  curriculum_binding_v0_result=0
  curriculum_binding_v0_output="$(bash scripts/curriculum-binding-v0-status.sh 2>&1)" || curriculum_binding_v0_result=$?
  curriculum_binding_v0_pass="$(summary_count "${curriculum_binding_v0_output}" "PASS")"
  curriculum_binding_v0_warn="$(summary_count "${curriculum_binding_v0_output}" "WARN")"
  curriculum_binding_v0_fail="$(summary_count "${curriculum_binding_v0_output}" "FAIL")"

  if [[ "${curriculum_binding_v0_result}" != "0" ]]; then
    printf 'Curriculum Registry–Contract Binding v0 Foundation: status command completed\n'
    printf '%s\n' "${curriculum_binding_v0_output}"
    fail "Curriculum Binding v0 status failed"
  elif [[ -n "${curriculum_binding_v0_pass}" && -n "${curriculum_binding_v0_warn}" && -n "${curriculum_binding_v0_fail}" ]]; then
    printf 'Curriculum Registry–Contract Binding v0 Foundation: PASS %s / WARN %s / FAIL %s\n' "${curriculum_binding_v0_pass}" "${curriculum_binding_v0_warn}" "${curriculum_binding_v0_fail}"
    pass "Curriculum Binding v0 status completed"
  else
    printf 'Curriculum Registry–Contract Binding v0 Foundation: status command completed\n'
    pass "Curriculum Binding v0 status completed"
  fi
else
  warn "Curriculum Binding v0 status script missing: scripts/curriculum-binding-v0-status.sh"
fi

section "Teacher App Designer / Canvas LLM Local-First Foundation"
if [[ -f scripts/teacher-app-designer-canvas-llm-status.sh ]]; then
  teacher_app_designer_canvas_llm_result=0
  teacher_app_designer_canvas_llm_output="$(bash scripts/teacher-app-designer-canvas-llm-status.sh 2>&1)" || teacher_app_designer_canvas_llm_result=$?
  teacher_app_designer_canvas_llm_pass="$(summary_count "${teacher_app_designer_canvas_llm_output}" "PASS")"
  teacher_app_designer_canvas_llm_warn="$(summary_count "${teacher_app_designer_canvas_llm_output}" "WARN")"
  teacher_app_designer_canvas_llm_fail="$(summary_count "${teacher_app_designer_canvas_llm_output}" "FAIL")"

  if [[ "${teacher_app_designer_canvas_llm_result}" != "0" ]]; then
    printf 'Teacher App Designer / Canvas LLM Local-First Foundation: status command completed\n'
    printf '%s\n' "${teacher_app_designer_canvas_llm_output}"
    fail "Teacher App Designer / Canvas LLM foundation status failed"
  elif [[ -n "${teacher_app_designer_canvas_llm_pass}" && -n "${teacher_app_designer_canvas_llm_warn}" && -n "${teacher_app_designer_canvas_llm_fail}" ]]; then
    printf 'Teacher App Designer / Canvas LLM Local-First Foundation: PASS %s / WARN %s / FAIL %s\n' "${teacher_app_designer_canvas_llm_pass}" "${teacher_app_designer_canvas_llm_warn}" "${teacher_app_designer_canvas_llm_fail}"
    pass "Teacher App Designer / Canvas LLM foundation status completed"
  else
    printf 'Teacher App Designer / Canvas LLM Local-First Foundation: status command completed\n'
    pass "Teacher App Designer / Canvas LLM foundation status completed"
  fi
else
  warn "Teacher App Designer / Canvas LLM status script missing: scripts/teacher-app-designer-canvas-llm-status.sh"
fi

end_section_summary "Lesson Planning Status"

group_banner "Future-Safety / Parked Work"
begin_section_summary

section "Document Indexing Command Detail Polish"
if [[ -f scripts/document-indexing-command-detail-status.sh ]]; then
  document_indexing_command_detail_result=0
  document_indexing_command_detail_output="$(bash scripts/document-indexing-command-detail-status.sh 2>&1)" || document_indexing_command_detail_result=$?
  document_indexing_command_detail_pass="$(summary_count "${document_indexing_command_detail_output}" "PASS")"
  document_indexing_command_detail_warn="$(summary_count "${document_indexing_command_detail_output}" "WARN")"
  document_indexing_command_detail_fail="$(summary_count "${document_indexing_command_detail_output}" "FAIL")"

  if [[ "${document_indexing_command_detail_result}" != "0" ]]; then
    printf 'Document Indexing Command Detail Polish: status command completed\n'
    printf '%s\n' "${document_indexing_command_detail_output}"
    fail "Document Indexing command detail polish status failed"
  elif [[ -n "${document_indexing_command_detail_pass}" && -n "${document_indexing_command_detail_warn}" && -n "${document_indexing_command_detail_fail}" ]]; then
    printf 'Document Indexing Command Detail Polish: PASS %s / WARN %s / FAIL %s\n' "${document_indexing_command_detail_pass}" "${document_indexing_command_detail_warn}" "${document_indexing_command_detail_fail}"
    pass "Document Indexing command detail polish status completed"
  else
    printf 'Document Indexing Command Detail Polish: status command completed\n'
    pass "Document Indexing command detail polish status completed"
  fi
else
  warn "Document Indexing command detail status script missing: scripts/document-indexing-command-detail-status.sh"
fi

section "Safe Local Document Indexing Plan"
if [[ -f scripts/document-indexing-plan-status.sh ]]; then
  document_indexing_result=0
  document_indexing_output="$(bash scripts/document-indexing-plan-status.sh 2>&1)" || document_indexing_result=$?
  document_indexing_pass="$(summary_count "${document_indexing_output}" "PASS")"
  document_indexing_warn="$(summary_count "${document_indexing_output}" "WARN")"
  document_indexing_fail="$(summary_count "${document_indexing_output}" "FAIL")"

  if [[ "${document_indexing_result}" != "0" ]]; then
    printf 'Safe Local Document Indexing Plan: status command completed\n'
    printf '%s\n' "${document_indexing_output}"
    fail "document indexing plan status failed"
  elif [[ -n "${document_indexing_pass}" && -n "${document_indexing_warn}" && -n "${document_indexing_fail}" ]]; then
    printf 'Safe Local Document Indexing Plan: PASS %s / WARN %s / FAIL %s\n' "${document_indexing_pass}" "${document_indexing_warn}" "${document_indexing_fail}"
    pass "document indexing plan status completed"
  else
    printf 'Safe Local Document Indexing Plan: status command completed\n'
    pass "document indexing plan status completed"
  fi
else
  warn "document indexing plan status script missing: scripts/document-indexing-plan-status.sh"
fi

section "Local Document Indexing Follow-Up"
if [[ -f scripts/local-document-indexing-follow-up-status.sh ]]; then
  local_document_indexing_followup_result=0
  local_document_indexing_followup_output="$(bash scripts/local-document-indexing-follow-up-status.sh 2>&1)" || local_document_indexing_followup_result=$?
  local_document_indexing_followup_pass="$(summary_count "${local_document_indexing_followup_output}" "PASS")"
  local_document_indexing_followup_warn="$(summary_count "${local_document_indexing_followup_output}" "WARN")"
  local_document_indexing_followup_fail="$(summary_count "${local_document_indexing_followup_output}" "FAIL")"

  if [[ "${local_document_indexing_followup_result}" != "0" ]]; then
    printf 'Local Document Indexing Follow-Up: status command completed\n'
    printf '%s\n' "${local_document_indexing_followup_output}"
    fail "local document indexing follow-up status failed"
  elif [[ -n "${local_document_indexing_followup_pass}" && -n "${local_document_indexing_followup_warn}" && -n "${local_document_indexing_followup_fail}" ]]; then
    printf 'Local Document Indexing Follow-Up: PASS %s / WARN %s / FAIL %s\n' "${local_document_indexing_followup_pass}" "${local_document_indexing_followup_warn}" "${local_document_indexing_followup_fail}"
    pass "local document indexing follow-up status completed"
  else
    printf 'Local Document Indexing Follow-Up: status command completed\n'
    pass "local document indexing follow-up status completed"
  fi
else
  warn "local document indexing follow-up status script missing: scripts/local-document-indexing-follow-up-status.sh"
fi

section "Project Memory Cleanup"
if [[ -f scripts/project-memory-cleanup-status.sh ]]; then
  project_memory_cleanup_result=0
  project_memory_cleanup_output="$(bash scripts/project-memory-cleanup-status.sh 2>&1)" || project_memory_cleanup_result=$?
  project_memory_cleanup_pass="$(summary_count "${project_memory_cleanup_output}" "PASS")"
  project_memory_cleanup_warn="$(summary_count "${project_memory_cleanup_output}" "WARN")"
  project_memory_cleanup_fail="$(summary_count "${project_memory_cleanup_output}" "FAIL")"

  if [[ "${project_memory_cleanup_result}" != "0" ]]; then
    printf 'Project Memory Cleanup: status command completed\n'
    printf '%s\n' "${project_memory_cleanup_output}"
    fail "project memory cleanup status failed"
  elif [[ -n "${project_memory_cleanup_pass}" && -n "${project_memory_cleanup_warn}" && -n "${project_memory_cleanup_fail}" ]]; then
    printf 'Project Memory Cleanup: PASS %s / WARN %s / FAIL %s\n' "${project_memory_cleanup_pass}" "${project_memory_cleanup_warn}" "${project_memory_cleanup_fail}"
    pass "project memory cleanup status completed"
  else
    printf 'Project Memory Cleanup: status command completed\n'
    pass "project memory cleanup status completed"
  fi
else
  warn "project memory cleanup status script missing: scripts/project-memory-cleanup-status.sh"
fi

section "Testing/Checklist Consolidation"
if [[ -f scripts/testing-checklist-consolidation-status.sh ]]; then
  testing_checklist_result=0
  testing_checklist_output="$(bash scripts/testing-checklist-consolidation-status.sh 2>&1)" || testing_checklist_result=$?
  testing_checklist_pass="$(summary_count "${testing_checklist_output}" "PASS")"
  testing_checklist_warn="$(summary_count "${testing_checklist_output}" "WARN")"
  testing_checklist_fail="$(summary_count "${testing_checklist_output}" "FAIL")"

  if [[ "${testing_checklist_result}" != "0" ]]; then
    printf 'Testing/Checklist Consolidation: status command completed\n'
    printf '%s\n' "${testing_checklist_output}"
    fail "testing checklist consolidation status failed"
  elif [[ -n "${testing_checklist_pass}" && -n "${testing_checklist_warn}" && -n "${testing_checklist_fail}" ]]; then
    printf 'Testing/Checklist Consolidation: PASS %s / WARN %s / FAIL %s\n' "${testing_checklist_pass}" "${testing_checklist_warn}" "${testing_checklist_fail}"
    pass "testing checklist consolidation status completed"
  else
    printf 'Testing/Checklist Consolidation: status command completed\n'
    pass "testing checklist consolidation status completed"
  fi
else
  warn "testing checklist consolidation status script missing: scripts/testing-checklist-consolidation-status.sh"
fi

section "Command/Check Bundle Reference Polish"
if [[ -f scripts/command-check-bundle-reference-status.sh ]]; then
  command_check_bundle_reference_result=0
  command_check_bundle_reference_output="$(bash scripts/command-check-bundle-reference-status.sh 2>&1)" || command_check_bundle_reference_result=$?
  command_check_bundle_reference_pass="$(summary_count "${command_check_bundle_reference_output}" "PASS")"
  command_check_bundle_reference_warn="$(summary_count "${command_check_bundle_reference_output}" "WARN")"
  command_check_bundle_reference_fail="$(summary_count "${command_check_bundle_reference_output}" "FAIL")"

  if [[ "${command_check_bundle_reference_result}" != "0" ]]; then
    printf 'Command/Check Bundle Reference Polish: status command completed\n'
    printf '%s\n' "${command_check_bundle_reference_output}"
    fail "command check bundle reference polish status failed"
  elif [[ -n "${command_check_bundle_reference_pass}" && -n "${command_check_bundle_reference_warn}" && -n "${command_check_bundle_reference_fail}" ]]; then
    printf 'Command/Check Bundle Reference Polish: PASS %s / WARN %s / FAIL %s\n' "${command_check_bundle_reference_pass}" "${command_check_bundle_reference_warn}" "${command_check_bundle_reference_fail}"
    pass "command check bundle reference polish status completed"
  else
    printf 'Command/Check Bundle Reference Polish: status command completed\n'
    pass "command check bundle reference polish status completed"
  fi
else
  warn "command check bundle reference status script missing: scripts/command-check-bundle-reference-status.sh"
fi

section "Checklist-Driven Prompt Template Tightening"
if [[ -f scripts/checklist-driven-prompt-template-status.sh ]]; then
  checklist_prompt_template_result=0
  checklist_prompt_template_output="$(bash scripts/checklist-driven-prompt-template-status.sh 2>&1)" || checklist_prompt_template_result=$?
  checklist_prompt_template_pass="$(summary_count "${checklist_prompt_template_output}" "PASS")"
  checklist_prompt_template_warn="$(summary_count "${checklist_prompt_template_output}" "WARN")"
  checklist_prompt_template_fail="$(summary_count "${checklist_prompt_template_output}" "FAIL")"

  if [[ "${checklist_prompt_template_result}" != "0" ]]; then
    printf 'Checklist-Driven Prompt Template Tightening: status command completed\n'
    printf '%s\n' "${checklist_prompt_template_output}"
    fail "checklist-driven prompt template tightening status failed"
  elif [[ -n "${checklist_prompt_template_pass}" && -n "${checklist_prompt_template_warn}" && -n "${checklist_prompt_template_fail}" ]]; then
    printf 'Checklist-Driven Prompt Template Tightening: PASS %s / WARN %s / FAIL %s\n' "${checklist_prompt_template_pass}" "${checklist_prompt_template_warn}" "${checklist_prompt_template_fail}"
    pass "checklist-driven prompt template tightening status completed"
  else
    printf 'Checklist-Driven Prompt Template Tightening: status command completed\n'
    pass "checklist-driven prompt template tightening status completed"
  fi
else
  warn "checklist-driven prompt template status script missing: scripts/checklist-driven-prompt-template-status.sh"
fi

section "PR Lifecycle Guardrail Consolidation"
if [[ -f scripts/pr-lifecycle-guardrail-status.sh ]]; then
  pr_lifecycle_guardrail_result=0
  pr_lifecycle_guardrail_output="$(bash scripts/pr-lifecycle-guardrail-status.sh 2>&1)" || pr_lifecycle_guardrail_result=$?
  pr_lifecycle_guardrail_pass="$(summary_count "${pr_lifecycle_guardrail_output}" "PASS")"
  pr_lifecycle_guardrail_warn="$(summary_count "${pr_lifecycle_guardrail_output}" "WARN")"
  pr_lifecycle_guardrail_fail="$(summary_count "${pr_lifecycle_guardrail_output}" "FAIL")"

  if [[ "${pr_lifecycle_guardrail_result}" != "0" ]]; then
    printf 'PR Lifecycle Guardrail Consolidation: status command completed\n'
    printf '%s\n' "${pr_lifecycle_guardrail_output}"
    fail "PR lifecycle guardrail consolidation status failed"
  elif [[ -n "${pr_lifecycle_guardrail_pass}" && -n "${pr_lifecycle_guardrail_warn}" && -n "${pr_lifecycle_guardrail_fail}" ]]; then
    printf 'PR Lifecycle Guardrail Consolidation: PASS %s / WARN %s / FAIL %s\n' "${pr_lifecycle_guardrail_pass}" "${pr_lifecycle_guardrail_warn}" "${pr_lifecycle_guardrail_fail}"
    pass "PR lifecycle guardrail consolidation status completed"
  else
    printf 'PR Lifecycle Guardrail Consolidation: status command completed\n'
    pass "PR lifecycle guardrail consolidation status completed"
  fi
else
  warn "PR lifecycle guardrail status script missing: scripts/pr-lifecycle-guardrail-status.sh"
fi

section "Branch Hygiene and Cleanup Reference"
if [[ -f scripts/branch-hygiene-cleanup-status.sh ]]; then
  branch_hygiene_cleanup_result=0
  branch_hygiene_cleanup_output="$(bash scripts/branch-hygiene-cleanup-status.sh 2>&1)" || branch_hygiene_cleanup_result=$?
  branch_hygiene_cleanup_pass="$(summary_count "${branch_hygiene_cleanup_output}" "PASS")"
  branch_hygiene_cleanup_warn="$(summary_count "${branch_hygiene_cleanup_output}" "WARN")"
  branch_hygiene_cleanup_fail="$(summary_count "${branch_hygiene_cleanup_output}" "FAIL")"

  if [[ "${branch_hygiene_cleanup_result}" != "0" ]]; then
    printf 'Branch Hygiene and Cleanup Reference: status command completed\n'
    printf '%s\n' "${branch_hygiene_cleanup_output}"
    fail "branch hygiene and cleanup reference status failed"
  elif [[ -n "${branch_hygiene_cleanup_pass}" && -n "${branch_hygiene_cleanup_warn}" && -n "${branch_hygiene_cleanup_fail}" ]]; then
    printf 'Branch Hygiene and Cleanup Reference: PASS %s / WARN %s / FAIL %s\n' "${branch_hygiene_cleanup_pass}" "${branch_hygiene_cleanup_warn}" "${branch_hygiene_cleanup_fail}"
    pass "branch hygiene and cleanup reference status completed"
  else
    printf 'Branch Hygiene and Cleanup Reference: status command completed\n'
    pass "branch hygiene and cleanup reference status completed"
  fi
else
  warn "branch hygiene cleanup status script missing: scripts/branch-hygiene-cleanup-status.sh"
fi

section "Local Main Proof Report Polish"
if [[ -f scripts/local-main-proof-report-status.sh ]]; then
  local_main_proof_report_result=0
  local_main_proof_report_output="$(bash scripts/local-main-proof-report-status.sh 2>&1)" || local_main_proof_report_result=$?
  local_main_proof_report_pass="$(summary_count "${local_main_proof_report_output}" "PASS")"
  local_main_proof_report_warn="$(summary_count "${local_main_proof_report_output}" "WARN")"
  local_main_proof_report_fail="$(summary_count "${local_main_proof_report_output}" "FAIL")"

  if [[ "${local_main_proof_report_result}" != "0" ]]; then
    printf 'Local Main Proof Report Polish: status command completed\n'
    printf '%s\n' "${local_main_proof_report_output}"
    fail "local main proof report polish status failed"
  elif [[ -n "${local_main_proof_report_pass}" && -n "${local_main_proof_report_warn}" && -n "${local_main_proof_report_fail}" ]]; then
    printf 'Local Main Proof Report Polish: PASS %s / WARN %s / FAIL %s\n' "${local_main_proof_report_pass}" "${local_main_proof_report_warn}" "${local_main_proof_report_fail}"
    pass "local main proof report polish status completed"
  else
    printf 'Local Main Proof Report Polish: status command completed\n'
    pass "local main proof report polish status completed"
  fi
else
  warn "local main proof report status script missing: scripts/local-main-proof-report-status.sh"
fi

section "Workflow Docs Cross-Link Polish"
if [[ -f scripts/workflow-docs-cross-link-status.sh ]]; then
  workflow_docs_cross_link_result=0
  workflow_docs_cross_link_output="$(bash scripts/workflow-docs-cross-link-status.sh 2>&1)" || workflow_docs_cross_link_result=$?
  workflow_docs_cross_link_pass="$(summary_count "${workflow_docs_cross_link_output}" "PASS")"
  workflow_docs_cross_link_warn="$(summary_count "${workflow_docs_cross_link_output}" "WARN")"
  workflow_docs_cross_link_fail="$(summary_count "${workflow_docs_cross_link_output}" "FAIL")"

  if [[ "${workflow_docs_cross_link_result}" != "0" ]]; then
    printf 'Workflow Docs Cross-Link Polish: status command completed\n'
    printf '%s\n' "${workflow_docs_cross_link_output}"
    fail "workflow docs cross-link polish status failed"
  elif [[ -n "${workflow_docs_cross_link_pass}" && -n "${workflow_docs_cross_link_warn}" && -n "${workflow_docs_cross_link_fail}" ]]; then
    printf 'Workflow Docs Cross-Link Polish: PASS %s / WARN %s / FAIL %s\n' "${workflow_docs_cross_link_pass}" "${workflow_docs_cross_link_warn}" "${workflow_docs_cross_link_fail}"
    pass "workflow docs cross-link polish status completed"
  else
    printf 'Workflow Docs Cross-Link Polish: status command completed\n'
    pass "workflow docs cross-link polish status completed"
  fi
else
  warn "workflow docs cross-link status script missing: scripts/workflow-docs-cross-link-status.sh"
fi

section "Workflow Docs Navigation Status Summary"
if [[ -f scripts/workflow-docs-navigation-status-summary.sh ]]; then
  workflow_docs_navigation_result=0
  workflow_docs_navigation_output="$(bash scripts/workflow-docs-navigation-status-summary.sh 2>&1)" || workflow_docs_navigation_result=$?
  workflow_docs_navigation_pass="$(summary_count "${workflow_docs_navigation_output}" "PASS")"
  workflow_docs_navigation_warn="$(summary_count "${workflow_docs_navigation_output}" "WARN")"
  workflow_docs_navigation_fail="$(summary_count "${workflow_docs_navigation_output}" "FAIL")"

  if [[ "${workflow_docs_navigation_result}" != "0" ]]; then
    printf 'Workflow Docs Navigation Status Summary: status command completed\n'
    printf '%s\n' "${workflow_docs_navigation_output}"
    fail "workflow docs navigation status summary failed"
  elif [[ -n "${workflow_docs_navigation_pass}" && -n "${workflow_docs_navigation_warn}" && -n "${workflow_docs_navigation_fail}" ]]; then
    printf 'Workflow Docs Navigation Status Summary: PASS %s / WARN %s / FAIL %s\n' "${workflow_docs_navigation_pass}" "${workflow_docs_navigation_warn}" "${workflow_docs_navigation_fail}"
    pass "workflow docs navigation status summary completed"
  else
    printf 'Workflow Docs Navigation Status Summary: status command completed\n'
    pass "workflow docs navigation status summary completed"
  fi
else
  warn "workflow docs navigation status script missing: scripts/workflow-docs-navigation-status-summary.sh"
fi

section "Prompt Pack Maintenance Checklist"
if [[ -f scripts/prompt-pack-maintenance-status.sh ]]; then
  prompt_pack_maintenance_result=0
  prompt_pack_maintenance_output="$(bash scripts/prompt-pack-maintenance-status.sh 2>&1)" || prompt_pack_maintenance_result=$?
  prompt_pack_maintenance_pass="$(summary_count "${prompt_pack_maintenance_output}" "PASS")"
  prompt_pack_maintenance_warn="$(summary_count "${prompt_pack_maintenance_output}" "WARN")"
  prompt_pack_maintenance_fail="$(summary_count "${prompt_pack_maintenance_output}" "FAIL")"

  if [[ "${prompt_pack_maintenance_result}" != "0" ]]; then
    printf 'Prompt Pack Maintenance Checklist: status command completed\n'
    printf '%s\n' "${prompt_pack_maintenance_output}"
    fail "prompt pack maintenance checklist status failed"
  elif [[ -n "${prompt_pack_maintenance_pass}" && -n "${prompt_pack_maintenance_warn}" && -n "${prompt_pack_maintenance_fail}" ]]; then
    printf 'Prompt Pack Maintenance Checklist: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_maintenance_pass}" "${prompt_pack_maintenance_warn}" "${prompt_pack_maintenance_fail}"
    pass "prompt pack maintenance checklist status completed"
  else
    printf 'Prompt Pack Maintenance Checklist: status command completed\n'
    pass "prompt pack maintenance checklist status completed"
  fi
else
  warn "prompt pack maintenance status script missing: scripts/prompt-pack-maintenance-status.sh"
fi

section "Prompt Pack Reference Index"
if [[ -f scripts/prompt-pack-reference-index-status.sh ]]; then
  prompt_pack_reference_index_result=0
  prompt_pack_reference_index_output="$(bash scripts/prompt-pack-reference-index-status.sh 2>&1)" || prompt_pack_reference_index_result=$?
  prompt_pack_reference_index_pass="$(summary_count "${prompt_pack_reference_index_output}" "PASS")"
  prompt_pack_reference_index_warn="$(summary_count "${prompt_pack_reference_index_output}" "WARN")"
  prompt_pack_reference_index_fail="$(summary_count "${prompt_pack_reference_index_output}" "FAIL")"

  if [[ "${prompt_pack_reference_index_result}" != "0" ]]; then
    printf 'Prompt Pack Reference Index: status command completed\n'
    printf '%s\n' "${prompt_pack_reference_index_output}"
    fail "prompt pack reference index status failed"
  elif [[ -n "${prompt_pack_reference_index_pass}" && -n "${prompt_pack_reference_index_warn}" && -n "${prompt_pack_reference_index_fail}" ]]; then
    printf 'Prompt Pack Reference Index: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_reference_index_pass}" "${prompt_pack_reference_index_warn}" "${prompt_pack_reference_index_fail}"
    pass "prompt pack reference index status completed"
  else
    printf 'Prompt Pack Reference Index: status command completed\n'
    pass "prompt pack reference index status completed"
  fi
else
  warn "prompt pack reference index status script missing: scripts/prompt-pack-reference-index-status.sh"
fi

section "Prompt Pack Stale-Reference Audit"
if [[ -f scripts/prompt-pack-stale-reference-audit-status.sh ]]; then
  prompt_pack_stale_reference_result=0
  prompt_pack_stale_reference_output="$(bash scripts/prompt-pack-stale-reference-audit-status.sh 2>&1)" || prompt_pack_stale_reference_result=$?
  prompt_pack_stale_reference_pass="$(summary_count "${prompt_pack_stale_reference_output}" "PASS")"
  prompt_pack_stale_reference_warn="$(summary_count "${prompt_pack_stale_reference_output}" "WARN")"
  prompt_pack_stale_reference_fail="$(summary_count "${prompt_pack_stale_reference_output}" "FAIL")"

  if [[ "${prompt_pack_stale_reference_result}" != "0" ]]; then
    printf 'Prompt Pack Stale-Reference Audit: status command completed\n'
    printf '%s\n' "${prompt_pack_stale_reference_output}"
    fail "prompt pack stale-reference audit status failed"
  elif [[ -n "${prompt_pack_stale_reference_pass}" && -n "${prompt_pack_stale_reference_warn}" && -n "${prompt_pack_stale_reference_fail}" ]]; then
    printf 'Prompt Pack Stale-Reference Audit: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_stale_reference_pass}" "${prompt_pack_stale_reference_warn}" "${prompt_pack_stale_reference_fail}"
    pass "prompt pack stale-reference audit status completed"
  else
    printf 'Prompt Pack Stale-Reference Audit: status command completed\n'
    pass "prompt pack stale-reference audit status completed"
  fi
else
  warn "prompt pack stale-reference audit status script missing: scripts/prompt-pack-stale-reference-audit-status.sh"
fi

section "Prompt Pack Freshness Report Polish"
if [[ -f scripts/prompt-pack-freshness-report-status.sh ]]; then
  prompt_pack_freshness_report_result=0
  prompt_pack_freshness_report_output="$(bash scripts/prompt-pack-freshness-report-status.sh 2>&1)" || prompt_pack_freshness_report_result=$?
  prompt_pack_freshness_report_pass="$(summary_count "${prompt_pack_freshness_report_output}" "PASS")"
  prompt_pack_freshness_report_warn="$(summary_count "${prompt_pack_freshness_report_output}" "WARN")"
  prompt_pack_freshness_report_fail="$(summary_count "${prompt_pack_freshness_report_output}" "FAIL")"

  if [[ "${prompt_pack_freshness_report_result}" != "0" ]]; then
    printf 'Prompt Pack Freshness Report Polish: status command completed\n'
    printf '%s\n' "${prompt_pack_freshness_report_output}"
    fail "prompt pack freshness report polish status failed"
  elif [[ -n "${prompt_pack_freshness_report_pass}" && -n "${prompt_pack_freshness_report_warn}" && -n "${prompt_pack_freshness_report_fail}" ]]; then
    printf 'Prompt Pack Freshness Report Polish: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_freshness_report_pass}" "${prompt_pack_freshness_report_warn}" "${prompt_pack_freshness_report_fail}"
    pass "prompt pack freshness report polish status completed"
  else
    printf 'Prompt Pack Freshness Report Polish: status command completed\n'
    pass "prompt pack freshness report polish status completed"
  fi
else
  warn "prompt pack freshness report status script missing: scripts/prompt-pack-freshness-report-status.sh"
fi

section "Prompt Pack Handoff Summary"
if [[ -f scripts/prompt-pack-handoff-summary-status.sh ]]; then
  prompt_pack_handoff_summary_result=0
  prompt_pack_handoff_summary_output="$(bash scripts/prompt-pack-handoff-summary-status.sh 2>&1)" || prompt_pack_handoff_summary_result=$?
  prompt_pack_handoff_summary_pass="$(summary_count "${prompt_pack_handoff_summary_output}" "PASS")"
  prompt_pack_handoff_summary_warn="$(summary_count "${prompt_pack_handoff_summary_output}" "WARN")"
  prompt_pack_handoff_summary_fail="$(summary_count "${prompt_pack_handoff_summary_output}" "FAIL")"

  if [[ "${prompt_pack_handoff_summary_result}" != "0" ]]; then
    printf 'Prompt Pack Handoff Summary: status command completed\n'
    printf '%s\n' "${prompt_pack_handoff_summary_output}"
    fail "prompt pack handoff summary status failed"
  elif [[ -n "${prompt_pack_handoff_summary_pass}" && -n "${prompt_pack_handoff_summary_warn}" && -n "${prompt_pack_handoff_summary_fail}" ]]; then
    printf 'Prompt Pack Handoff Summary: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_handoff_summary_pass}" "${prompt_pack_handoff_summary_warn}" "${prompt_pack_handoff_summary_fail}"
    pass "prompt pack handoff summary status completed"
  else
    printf 'Prompt Pack Handoff Summary: status command completed\n'
    pass "prompt pack handoff summary status completed"
  fi
else
  warn "prompt pack handoff summary status script missing: scripts/prompt-pack-handoff-summary-status.sh"
fi

section "Prompt Pack Stack Completion Marker"
if [[ -f scripts/prompt-pack-stack-completion-status.sh ]]; then
  prompt_pack_stack_completion_result=0
  prompt_pack_stack_completion_output="$(bash scripts/prompt-pack-stack-completion-status.sh 2>&1)" || prompt_pack_stack_completion_result=$?
  prompt_pack_stack_completion_pass="$(summary_count "${prompt_pack_stack_completion_output}" "PASS")"
  prompt_pack_stack_completion_warn="$(summary_count "${prompt_pack_stack_completion_output}" "WARN")"
  prompt_pack_stack_completion_fail="$(summary_count "${prompt_pack_stack_completion_output}" "FAIL")"

  if [[ "${prompt_pack_stack_completion_result}" != "0" ]]; then
    printf 'Prompt Pack Stack Completion Marker: status command completed\n'
    printf '%s\n' "${prompt_pack_stack_completion_output}"
    fail "prompt pack stack completion marker status failed"
  elif [[ -n "${prompt_pack_stack_completion_pass}" && -n "${prompt_pack_stack_completion_warn}" && -n "${prompt_pack_stack_completion_fail}" ]]; then
    printf 'Prompt Pack Stack Completion Marker: PASS %s / WARN %s / FAIL %s\n' "${prompt_pack_stack_completion_pass}" "${prompt_pack_stack_completion_warn}" "${prompt_pack_stack_completion_fail}"
    pass "prompt pack stack completion marker status completed"
  else
    printf 'Prompt Pack Stack Completion Marker: status command completed\n'
    pass "prompt pack stack completion marker status completed"
  fi
else
  warn "prompt pack stack completion status script missing: scripts/prompt-pack-stack-completion-status.sh"
fi

end_section_summary "Future-Safety / Parked Work"

group_banner "Appearance & Vibe Foundation Status"
begin_section_summary
printf 'Foundation stack complete for now. Live wallpaper/photo curator implementation not started.\n'

section "Appearance & Vibe Wallpaper/Photo Curator Plan"
if [[ -f scripts/wallpaper-photo-curator-plan-status.sh ]]; then
  wallpaper_curator_result=0
  wallpaper_curator_output="$(bash scripts/wallpaper-photo-curator-plan-status.sh 2>&1)" || wallpaper_curator_result=$?
  wallpaper_curator_pass="$(summary_count "${wallpaper_curator_output}" "PASS")"
  wallpaper_curator_warn="$(summary_count "${wallpaper_curator_output}" "WARN")"
  wallpaper_curator_fail="$(summary_count "${wallpaper_curator_output}" "FAIL")"

  if [[ "${wallpaper_curator_result}" != "0" ]]; then
    printf 'Appearance & Vibe Wallpaper/Photo Curator Plan: status command completed\n'
    printf '%s\n' "${wallpaper_curator_output}"
    fail "wallpaper photo curator plan status failed"
  elif [[ -n "${wallpaper_curator_pass}" && -n "${wallpaper_curator_warn}" && -n "${wallpaper_curator_fail}" ]]; then
    printf 'Appearance & Vibe Wallpaper/Photo Curator Plan: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_curator_pass}" "${wallpaper_curator_warn}" "${wallpaper_curator_fail}"
    pass "wallpaper photo curator plan status completed"
  else
    printf 'Appearance & Vibe Wallpaper/Photo Curator Plan: status command completed\n'
    pass "wallpaper photo curator plan status completed"
  fi
else
  warn "wallpaper photo curator plan status script missing: scripts/wallpaper-photo-curator-plan-status.sh"
fi

section "Wallpaper/Photo Folder Design"
if [[ -f scripts/wallpaper-photo-folder-design-status.sh ]]; then
  wallpaper_folder_design_result=0
  wallpaper_folder_design_output="$(bash scripts/wallpaper-photo-folder-design-status.sh 2>&1)" || wallpaper_folder_design_result=$?
  wallpaper_folder_design_pass="$(summary_count "${wallpaper_folder_design_output}" "PASS")"
  wallpaper_folder_design_warn="$(summary_count "${wallpaper_folder_design_output}" "WARN")"
  wallpaper_folder_design_fail="$(summary_count "${wallpaper_folder_design_output}" "FAIL")"

  if [[ "${wallpaper_folder_design_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Folder Design: status command completed\n'
    printf '%s\n' "${wallpaper_folder_design_output}"
    fail "wallpaper photo folder design status failed"
  elif [[ -n "${wallpaper_folder_design_pass}" && -n "${wallpaper_folder_design_warn}" && -n "${wallpaper_folder_design_fail}" ]]; then
    printf 'Wallpaper/Photo Folder Design: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_folder_design_pass}" "${wallpaper_folder_design_warn}" "${wallpaper_folder_design_fail}"
    pass "wallpaper photo folder design status completed"
  else
    printf 'Wallpaper/Photo Folder Design: status command completed\n'
    pass "wallpaper photo folder design status completed"
  fi
else
  warn "wallpaper photo folder design status script missing: scripts/wallpaper-photo-folder-design-status.sh"
fi

section "Wallpaper/Photo Dry-Run Folder Validator"
if [[ -f scripts/wallpaper-photo-dry-run-folder-validator.sh ]]; then
  wallpaper_dry_run_result=0
  wallpaper_dry_run_output="$(bash scripts/wallpaper-photo-dry-run-folder-validator.sh 2>&1)" || wallpaper_dry_run_result=$?
  wallpaper_dry_run_pass="$(summary_count "${wallpaper_dry_run_output}" "PASS")"
  wallpaper_dry_run_warn="$(summary_count "${wallpaper_dry_run_output}" "WARN")"
  wallpaper_dry_run_fail="$(summary_count "${wallpaper_dry_run_output}" "FAIL")"

  if [[ "${wallpaper_dry_run_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Dry-Run Folder Validator: status command completed\n'
    printf '%s\n' "${wallpaper_dry_run_output}"
    fail "wallpaper photo dry-run folder validator failed"
  elif [[ -n "${wallpaper_dry_run_pass}" && -n "${wallpaper_dry_run_warn}" && -n "${wallpaper_dry_run_fail}" ]]; then
    printf 'Wallpaper/Photo Dry-Run Folder Validator: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_dry_run_pass}" "${wallpaper_dry_run_warn}" "${wallpaper_dry_run_fail}"
    pass "wallpaper photo dry-run folder validator completed"
  else
    printf 'Wallpaper/Photo Dry-Run Folder Validator: status command completed\n'
    pass "wallpaper photo dry-run folder validator completed"
  fi
else
  warn "wallpaper photo dry-run folder validator script missing: scripts/wallpaper-photo-dry-run-folder-validator.sh"
fi

section "Wallpaper/Photo Folder Creation Helper"
if [[ -f scripts/wallpaper-photo-folder-creation-status.sh ]]; then
  wallpaper_folder_creation_result=0
  wallpaper_folder_creation_output="$(bash scripts/wallpaper-photo-folder-creation-status.sh 2>&1)" || wallpaper_folder_creation_result=$?
  wallpaper_folder_creation_pass="$(summary_count "${wallpaper_folder_creation_output}" "PASS")"
  wallpaper_folder_creation_warn="$(summary_count "${wallpaper_folder_creation_output}" "WARN")"
  wallpaper_folder_creation_fail="$(summary_count "${wallpaper_folder_creation_output}" "FAIL")"

  if [[ "${wallpaper_folder_creation_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Folder Creation Helper: status command completed\n'
    printf '%s\n' "${wallpaper_folder_creation_output}"
    fail "wallpaper photo folder creation status failed"
  elif [[ -n "${wallpaper_folder_creation_pass}" && -n "${wallpaper_folder_creation_warn}" && -n "${wallpaper_folder_creation_fail}" ]]; then
    printf 'Wallpaper/Photo Folder Creation Helper: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_folder_creation_pass}" "${wallpaper_folder_creation_warn}" "${wallpaper_folder_creation_fail}"
    pass "wallpaper photo folder creation status completed"
  else
    printf 'Wallpaper/Photo Folder Creation Helper: status command completed\n'
    pass "wallpaper photo folder creation status completed"
  fi
else
  warn "wallpaper photo folder creation status script missing: scripts/wallpaper-photo-folder-creation-status.sh"
fi

section "Wallpaper/Photo Metadata Schema"
if [[ -f scripts/wallpaper-photo-metadata-status.sh ]]; then
  wallpaper_metadata_result=0
  wallpaper_metadata_output="$(bash scripts/wallpaper-photo-metadata-status.sh 2>&1)" || wallpaper_metadata_result=$?
  wallpaper_metadata_pass="$(summary_count "${wallpaper_metadata_output}" "PASS")"
  wallpaper_metadata_warn="$(summary_count "${wallpaper_metadata_output}" "WARN")"
  wallpaper_metadata_fail="$(summary_count "${wallpaper_metadata_output}" "FAIL")"

  if [[ "${wallpaper_metadata_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Metadata Schema: status command completed\n'
    printf '%s\n' "${wallpaper_metadata_output}"
    fail "wallpaper photo metadata status failed"
  elif [[ -n "${wallpaper_metadata_pass}" && -n "${wallpaper_metadata_warn}" && -n "${wallpaper_metadata_fail}" ]]; then
    printf 'Wallpaper/Photo Metadata Schema: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_metadata_pass}" "${wallpaper_metadata_warn}" "${wallpaper_metadata_fail}"
    pass "wallpaper photo metadata status completed"
  else
    printf 'Wallpaper/Photo Metadata Schema: status command completed\n'
    pass "wallpaper photo metadata status completed"
  fi
else
  warn "wallpaper photo metadata status script missing: scripts/wallpaper-photo-metadata-status.sh"
fi

section "Wallpaper/Photo Temp Queue Rules"
if [[ -f scripts/wallpaper-photo-temp-queue-status.sh ]]; then
  wallpaper_temp_queue_result=0
  wallpaper_temp_queue_output="$(bash scripts/wallpaper-photo-temp-queue-status.sh 2>&1)" || wallpaper_temp_queue_result=$?
  wallpaper_temp_queue_pass="$(summary_count "${wallpaper_temp_queue_output}" "PASS")"
  wallpaper_temp_queue_warn="$(summary_count "${wallpaper_temp_queue_output}" "WARN")"
  wallpaper_temp_queue_fail="$(summary_count "${wallpaper_temp_queue_output}" "FAIL")"

  if [[ "${wallpaper_temp_queue_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Temp Queue Rules: status command completed\n'
    printf '%s\n' "${wallpaper_temp_queue_output}"
    fail "wallpaper photo temp queue status failed"
  elif [[ -n "${wallpaper_temp_queue_pass}" && -n "${wallpaper_temp_queue_warn}" && -n "${wallpaper_temp_queue_fail}" ]]; then
    printf 'Wallpaper/Photo Temp Queue Rules: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_temp_queue_pass}" "${wallpaper_temp_queue_warn}" "${wallpaper_temp_queue_fail}"
    pass "wallpaper photo temp queue status completed"
  else
    printf 'Wallpaper/Photo Temp Queue Rules: status command completed\n'
    pass "wallpaper photo temp queue status completed"
  fi
else
  warn "wallpaper photo temp queue status script missing: scripts/wallpaper-photo-temp-queue-status.sh"
fi

section "Wallpaper/Photo Queue File Format"
if [[ -f scripts/wallpaper-photo-queue-file-status.sh ]]; then
  wallpaper_queue_file_result=0
  wallpaper_queue_file_output="$(bash scripts/wallpaper-photo-queue-file-status.sh 2>&1)" || wallpaper_queue_file_result=$?
  wallpaper_queue_file_pass="$(summary_count "${wallpaper_queue_file_output}" "PASS")"
  wallpaper_queue_file_warn="$(summary_count "${wallpaper_queue_file_output}" "WARN")"
  wallpaper_queue_file_fail="$(summary_count "${wallpaper_queue_file_output}" "FAIL")"

  if [[ "${wallpaper_queue_file_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Queue File Format: status command completed\n'
    printf '%s\n' "${wallpaper_queue_file_output}"
    fail "wallpaper photo queue file status failed"
  elif [[ -n "${wallpaper_queue_file_pass}" && -n "${wallpaper_queue_file_warn}" && -n "${wallpaper_queue_file_fail}" ]]; then
    printf 'Wallpaper/Photo Queue File Format: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_queue_file_pass}" "${wallpaper_queue_file_warn}" "${wallpaper_queue_file_fail}"
    pass "wallpaper photo queue file status completed"
  else
    printf 'Wallpaper/Photo Queue File Format: status command completed\n'
    pass "wallpaper photo queue file status completed"
  fi
else
  warn "wallpaper photo queue file status script missing: scripts/wallpaper-photo-queue-file-status.sh"
fi

section "Wallpaper/Photo Approve/Dismiss UI Design"
if [[ -f scripts/wallpaper-photo-approve-dismiss-ui-status.sh ]]; then
  wallpaper_approve_dismiss_ui_result=0
  wallpaper_approve_dismiss_ui_output="$(bash scripts/wallpaper-photo-approve-dismiss-ui-status.sh 2>&1)" || wallpaper_approve_dismiss_ui_result=$?
  wallpaper_approve_dismiss_ui_pass="$(summary_count "${wallpaper_approve_dismiss_ui_output}" "PASS")"
  wallpaper_approve_dismiss_ui_warn="$(summary_count "${wallpaper_approve_dismiss_ui_output}" "WARN")"
  wallpaper_approve_dismiss_ui_fail="$(summary_count "${wallpaper_approve_dismiss_ui_output}" "FAIL")"

  if [[ "${wallpaper_approve_dismiss_ui_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Approve/Dismiss UI Design: status command completed\n'
    printf '%s\n' "${wallpaper_approve_dismiss_ui_output}"
    fail "wallpaper photo approve dismiss UI status failed"
  elif [[ -n "${wallpaper_approve_dismiss_ui_pass}" && -n "${wallpaper_approve_dismiss_ui_warn}" && -n "${wallpaper_approve_dismiss_ui_fail}" ]]; then
    printf 'Wallpaper/Photo Approve/Dismiss UI Design: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_approve_dismiss_ui_pass}" "${wallpaper_approve_dismiss_ui_warn}" "${wallpaper_approve_dismiss_ui_fail}"
    pass "wallpaper photo approve dismiss UI status completed"
  else
    printf 'Wallpaper/Photo Approve/Dismiss UI Design: status command completed\n'
    pass "wallpaper photo approve dismiss UI status completed"
  fi
else
  warn "wallpaper photo approve dismiss UI status script missing: scripts/wallpaper-photo-approve-dismiss-ui-status.sh"
fi

section "Wallpaper/Photo Image Processing Rules"
if [[ -f scripts/wallpaper-photo-image-processing-status.sh ]]; then
  wallpaper_image_processing_result=0
  wallpaper_image_processing_output="$(bash scripts/wallpaper-photo-image-processing-status.sh 2>&1)" || wallpaper_image_processing_result=$?
  wallpaper_image_processing_pass="$(summary_count "${wallpaper_image_processing_output}" "PASS")"
  wallpaper_image_processing_warn="$(summary_count "${wallpaper_image_processing_output}" "WARN")"
  wallpaper_image_processing_fail="$(summary_count "${wallpaper_image_processing_output}" "FAIL")"

  if [[ "${wallpaper_image_processing_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Image Processing Rules: status command completed\n'
    printf '%s\n' "${wallpaper_image_processing_output}"
    fail "wallpaper photo image processing status failed"
  elif [[ -n "${wallpaper_image_processing_pass}" && -n "${wallpaper_image_processing_warn}" && -n "${wallpaper_image_processing_fail}" ]]; then
    printf 'Wallpaper/Photo Image Processing Rules: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_image_processing_pass}" "${wallpaper_image_processing_warn}" "${wallpaper_image_processing_fail}"
    pass "wallpaper photo image processing status completed"
  else
    printf 'Wallpaper/Photo Image Processing Rules: status command completed\n'
    pass "wallpaper photo image processing status completed"
  fi
else
  warn "wallpaper photo image processing status script missing: scripts/wallpaper-photo-image-processing-status.sh"
fi

section "Wallpaper/Photo Local Scheduler Plan"
if [[ -f scripts/wallpaper-photo-local-scheduler-status.sh ]]; then
  wallpaper_local_scheduler_result=0
  wallpaper_local_scheduler_output="$(bash scripts/wallpaper-photo-local-scheduler-status.sh 2>&1)" || wallpaper_local_scheduler_result=$?
  wallpaper_local_scheduler_pass="$(summary_count "${wallpaper_local_scheduler_output}" "PASS")"
  wallpaper_local_scheduler_warn="$(summary_count "${wallpaper_local_scheduler_output}" "WARN")"
  wallpaper_local_scheduler_fail="$(summary_count "${wallpaper_local_scheduler_output}" "FAIL")"

  if [[ "${wallpaper_local_scheduler_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Local Scheduler Plan: status command completed\n'
    printf '%s\n' "${wallpaper_local_scheduler_output}"
    fail "wallpaper photo local scheduler status failed"
  elif [[ -n "${wallpaper_local_scheduler_pass}" && -n "${wallpaper_local_scheduler_warn}" && -n "${wallpaper_local_scheduler_fail}" ]]; then
    printf 'Wallpaper/Photo Local Scheduler Plan: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_local_scheduler_pass}" "${wallpaper_local_scheduler_warn}" "${wallpaper_local_scheduler_fail}"
    pass "wallpaper photo local scheduler status completed"
  else
    printf 'Wallpaper/Photo Local Scheduler Plan: status command completed\n'
    pass "wallpaper photo local scheduler status completed"
  fi
else
  warn "wallpaper photo local scheduler status script missing: scripts/wallpaper-photo-local-scheduler-status.sh"
fi

section "Wallpaper/Photo Source Fetcher Plan"
if [[ -f scripts/wallpaper-photo-source-fetcher-plan-status.sh ]]; then
  wallpaper_source_fetcher_result=0
  wallpaper_source_fetcher_output="$(bash scripts/wallpaper-photo-source-fetcher-plan-status.sh 2>&1)" || wallpaper_source_fetcher_result=$?
  wallpaper_source_fetcher_pass="$(summary_count "${wallpaper_source_fetcher_output}" "PASS")"
  wallpaper_source_fetcher_warn="$(summary_count "${wallpaper_source_fetcher_output}" "WARN")"
  wallpaper_source_fetcher_fail="$(summary_count "${wallpaper_source_fetcher_output}" "FAIL")"

  if [[ "${wallpaper_source_fetcher_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Source Fetcher Plan: status command completed\n'
    printf '%s\n' "${wallpaper_source_fetcher_output}"
    fail "wallpaper photo source fetcher plan status failed"
  elif [[ -n "${wallpaper_source_fetcher_pass}" && -n "${wallpaper_source_fetcher_warn}" && -n "${wallpaper_source_fetcher_fail}" ]]; then
    printf 'Wallpaper/Photo Source Fetcher Plan: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_source_fetcher_pass}" "${wallpaper_source_fetcher_warn}" "${wallpaper_source_fetcher_fail}"
    pass "wallpaper photo source fetcher plan status completed"
  else
    printf 'Wallpaper/Photo Source Fetcher Plan: status command completed\n'
    pass "wallpaper photo source fetcher plan status completed"
  fi
else
  warn "wallpaper photo source fetcher plan status script missing: scripts/wallpaper-photo-source-fetcher-plan-status.sh"
fi

section "Wallpaper/Photo Source Allowlist Foundation"
if [[ -f scripts/wallpaper-photo-source-allowlist-status.sh ]]; then
  wallpaper_source_allowlist_result=0
  wallpaper_source_allowlist_output="$(bash scripts/wallpaper-photo-source-allowlist-status.sh 2>&1)" || wallpaper_source_allowlist_result=$?
  wallpaper_source_allowlist_pass="$(summary_count "${wallpaper_source_allowlist_output}" "PASS")"
  wallpaper_source_allowlist_warn="$(summary_count "${wallpaper_source_allowlist_output}" "WARN")"
  wallpaper_source_allowlist_fail="$(summary_count "${wallpaper_source_allowlist_output}" "FAIL")"

  if [[ "${wallpaper_source_allowlist_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Source Allowlist Foundation: status command completed\n'
    printf '%s\n' "${wallpaper_source_allowlist_output}"
    fail "wallpaper photo source allowlist foundation status failed"
  elif [[ -n "${wallpaper_source_allowlist_pass}" && -n "${wallpaper_source_allowlist_warn}" && -n "${wallpaper_source_allowlist_fail}" ]]; then
    printf 'Wallpaper/Photo Source Allowlist Foundation: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_source_allowlist_pass}" "${wallpaper_source_allowlist_warn}" "${wallpaper_source_allowlist_fail}"
    pass "wallpaper photo source allowlist foundation status completed"
  else
    printf 'Wallpaper/Photo Source Allowlist Foundation: status command completed\n'
    pass "wallpaper photo source allowlist foundation status completed"
  fi
else
  warn "wallpaper photo source allowlist status script missing: scripts/wallpaper-photo-source-allowlist-status.sh"
fi

section "Wallpaper/Photo Simulated Discovery"
if [[ -f scripts/wallpaper-photo-simulated-discovery-status.sh ]]; then
  wallpaper_simulated_discovery_result=0
  wallpaper_simulated_discovery_output="$(bash scripts/wallpaper-photo-simulated-discovery-status.sh 2>&1)" || wallpaper_simulated_discovery_result=$?
  wallpaper_simulated_discovery_pass="$(summary_count "${wallpaper_simulated_discovery_output}" "PASS")"
  wallpaper_simulated_discovery_warn="$(summary_count "${wallpaper_simulated_discovery_output}" "WARN")"
  wallpaper_simulated_discovery_fail="$(summary_count "${wallpaper_simulated_discovery_output}" "FAIL")"

  if [[ "${wallpaper_simulated_discovery_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Simulated Discovery: status command completed\n'
    printf '%s\n' "${wallpaper_simulated_discovery_output}"
    fail "wallpaper photo simulated discovery status failed"
  elif [[ -n "${wallpaper_simulated_discovery_pass}" && -n "${wallpaper_simulated_discovery_warn}" && -n "${wallpaper_simulated_discovery_fail}" ]]; then
    printf 'Wallpaper/Photo Simulated Discovery: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_simulated_discovery_pass}" "${wallpaper_simulated_discovery_warn}" "${wallpaper_simulated_discovery_fail}"
    pass "wallpaper photo simulated discovery status completed"
  else
    printf 'Wallpaper/Photo Simulated Discovery: status command completed\n'
    pass "wallpaper photo simulated discovery status completed"
  fi
else
  warn "wallpaper photo simulated discovery status script missing: scripts/wallpaper-photo-simulated-discovery-status.sh"
fi

section "Wallpaper/Photo Review UI Prototype"
if [[ -f scripts/wallpaper-photo-review-ui-prototype-status.sh ]]; then
  wallpaper_review_ui_result=0
  wallpaper_review_ui_output="$(bash scripts/wallpaper-photo-review-ui-prototype-status.sh 2>&1)" || wallpaper_review_ui_result=$?
  wallpaper_review_ui_pass="$(summary_count "${wallpaper_review_ui_output}" "PASS")"
  wallpaper_review_ui_warn="$(summary_count "${wallpaper_review_ui_output}" "WARN")"
  wallpaper_review_ui_fail="$(summary_count "${wallpaper_review_ui_output}" "FAIL")"

  if [[ "${wallpaper_review_ui_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Review UI Prototype: status command completed\n'
    printf '%s\n' "${wallpaper_review_ui_output}"
    fail "wallpaper photo review UI prototype status failed"
  elif [[ -n "${wallpaper_review_ui_pass}" && -n "${wallpaper_review_ui_warn}" && -n "${wallpaper_review_ui_fail}" ]]; then
    printf 'Wallpaper/Photo Review UI Prototype: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_review_ui_pass}" "${wallpaper_review_ui_warn}" "${wallpaper_review_ui_fail}"
    pass "wallpaper photo review UI prototype status completed"
  else
    printf 'Wallpaper/Photo Review UI Prototype: status command completed\n'
    pass "wallpaper photo review UI prototype status completed"
  fi
else
  warn "wallpaper photo review UI prototype status script missing: scripts/wallpaper-photo-review-ui-prototype-status.sh"
fi

section "Wallpaper/Photo Image Processor Foundation"
if [[ -f scripts/wallpaper-photo-image-processor-foundation-status.sh ]]; then
  wallpaper_image_processor_result=0
  wallpaper_image_processor_output="$(bash scripts/wallpaper-photo-image-processor-foundation-status.sh 2>&1)" || wallpaper_image_processor_result=$?
  wallpaper_image_processor_pass="$(summary_count "${wallpaper_image_processor_output}" "PASS")"
  wallpaper_image_processor_warn="$(summary_count "${wallpaper_image_processor_output}" "WARN")"
  wallpaper_image_processor_fail="$(summary_count "${wallpaper_image_processor_output}" "FAIL")"

  if [[ "${wallpaper_image_processor_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Image Processor Foundation: status command completed\n'
    printf '%s\n' "${wallpaper_image_processor_output}"
    fail "wallpaper photo image processor foundation status failed"
  elif [[ -n "${wallpaper_image_processor_pass}" && -n "${wallpaper_image_processor_warn}" && -n "${wallpaper_image_processor_fail}" ]]; then
    printf 'Wallpaper/Photo Image Processor Foundation: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_image_processor_pass}" "${wallpaper_image_processor_warn}" "${wallpaper_image_processor_fail}"
    pass "wallpaper photo image processor foundation status completed"
  else
    printf 'Wallpaper/Photo Image Processor Foundation: status command completed\n'
    pass "wallpaper photo image processor foundation status completed"
  fi
else
  warn "wallpaper photo image processor foundation status script missing: scripts/wallpaper-photo-image-processor-foundation-status.sh"
fi

section "Wallpaper/Photo Scheduler Foundation"
if [[ -f scripts/wallpaper-photo-scheduler-foundation-status.sh ]]; then
  wallpaper_scheduler_foundation_result=0
  wallpaper_scheduler_foundation_output="$(bash scripts/wallpaper-photo-scheduler-foundation-status.sh 2>&1)" || wallpaper_scheduler_foundation_result=$?
  wallpaper_scheduler_foundation_pass="$(summary_count "${wallpaper_scheduler_foundation_output}" "PASS")"
  wallpaper_scheduler_foundation_warn="$(summary_count "${wallpaper_scheduler_foundation_output}" "WARN")"
  wallpaper_scheduler_foundation_fail="$(summary_count "${wallpaper_scheduler_foundation_output}" "FAIL")"

  if [[ "${wallpaper_scheduler_foundation_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Scheduler Foundation: status command completed\n'
    printf '%s\n' "${wallpaper_scheduler_foundation_output}"
    fail "wallpaper photo scheduler foundation status failed"
  elif [[ -n "${wallpaper_scheduler_foundation_pass}" && -n "${wallpaper_scheduler_foundation_warn}" && -n "${wallpaper_scheduler_foundation_fail}" ]]; then
    printf 'Wallpaper/Photo Scheduler Foundation: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_scheduler_foundation_pass}" "${wallpaper_scheduler_foundation_warn}" "${wallpaper_scheduler_foundation_fail}"
    pass "wallpaper photo scheduler foundation status completed"
  else
    printf 'Wallpaper/Photo Scheduler Foundation: status command completed\n'
    pass "wallpaper photo scheduler foundation status completed"
  fi
else
  warn "wallpaper photo scheduler foundation status script missing: scripts/wallpaper-photo-scheduler-foundation-status.sh"
fi

section "Wallpaper/Photo Notification Foundation"
if [[ -f scripts/wallpaper-photo-notification-foundation-status.sh ]]; then
  wallpaper_notification_foundation_result=0
  wallpaper_notification_foundation_output="$(bash scripts/wallpaper-photo-notification-foundation-status.sh 2>&1)" || wallpaper_notification_foundation_result=$?
  wallpaper_notification_foundation_pass="$(summary_count "${wallpaper_notification_foundation_output}" "PASS")"
  wallpaper_notification_foundation_warn="$(summary_count "${wallpaper_notification_foundation_output}" "WARN")"
  wallpaper_notification_foundation_fail="$(summary_count "${wallpaper_notification_foundation_output}" "FAIL")"

  if [[ "${wallpaper_notification_foundation_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Notification Foundation: status command completed\n'
    printf '%s\n' "${wallpaper_notification_foundation_output}"
    fail "wallpaper photo notification foundation status failed"
  elif [[ -n "${wallpaper_notification_foundation_pass}" && -n "${wallpaper_notification_foundation_warn}" && -n "${wallpaper_notification_foundation_fail}" ]]; then
    printf 'Wallpaper/Photo Notification Foundation: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_notification_foundation_pass}" "${wallpaper_notification_foundation_warn}" "${wallpaper_notification_foundation_fail}"
    pass "wallpaper photo notification foundation status completed"
  else
    printf 'Wallpaper/Photo Notification Foundation: status command completed\n'
    pass "wallpaper photo notification foundation status completed"
  fi
else
  warn "wallpaper photo notification foundation status script missing: scripts/wallpaper-photo-notification-foundation-status.sh"
fi

section "Wallpaper/Photo Rotation Handoff and Safety Audit"
if [[ -f scripts/wallpaper-photo-rotation-handoff-safety-status.sh ]]; then
  wallpaper_rotation_handoff_result=0
  wallpaper_rotation_handoff_output="$(bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh 2>&1)" || wallpaper_rotation_handoff_result=$?
  wallpaper_rotation_handoff_pass="$(summary_count "${wallpaper_rotation_handoff_output}" "PASS")"
  wallpaper_rotation_handoff_warn="$(summary_count "${wallpaper_rotation_handoff_output}" "WARN")"
  wallpaper_rotation_handoff_fail="$(summary_count "${wallpaper_rotation_handoff_output}" "FAIL")"

  if [[ "${wallpaper_rotation_handoff_result}" != "0" ]]; then
    printf 'Wallpaper/Photo Rotation Handoff and Safety Audit: status command completed\n'
    printf '%s\n' "${wallpaper_rotation_handoff_output}"
    fail "wallpaper photo rotation handoff safety status failed"
  elif [[ -n "${wallpaper_rotation_handoff_pass}" && -n "${wallpaper_rotation_handoff_warn}" && -n "${wallpaper_rotation_handoff_fail}" ]]; then
    printf 'Wallpaper/Photo Rotation Handoff and Safety Audit: PASS %s / WARN %s / FAIL %s\n' "${wallpaper_rotation_handoff_pass}" "${wallpaper_rotation_handoff_warn}" "${wallpaper_rotation_handoff_fail}"
    pass "wallpaper photo rotation handoff safety status completed"
  else
    printf 'Wallpaper/Photo Rotation Handoff and Safety Audit: status command completed\n'
    pass "wallpaper photo rotation handoff safety status completed"
  fi
else
  warn "wallpaper photo rotation handoff safety status script missing: scripts/wallpaper-photo-rotation-handoff-safety-status.sh"
fi

end_section_summary "Appearance & Vibe Foundation Status"

group_banner "Developer / Cursor Workflow Status"
begin_section_summary

section "Cursor Workflow"
if [[ -f scripts/cursor-workflow-status.sh ]]; then
  cursor_result=0
  cursor_output="$(bash scripts/cursor-workflow-status.sh 2>&1)" || cursor_result=$?
  cursor_pass="$(summary_count "${cursor_output}" "PASS")"
  cursor_warn="$(summary_count "${cursor_output}" "WARN")"
  cursor_fail="$(summary_count "${cursor_output}" "FAIL")"

  if [[ "${cursor_result}" != "0" ]]; then
    printf 'Cursor Workflow: status command completed\n'
    printf '%s\n' "${cursor_output}"
    fail "cursor workflow status failed"
  elif [[ -n "${cursor_pass}" && -n "${cursor_warn}" && -n "${cursor_fail}" ]]; then
    printf 'Cursor Workflow: PASS %s / WARN %s / FAIL %s\n' "${cursor_pass}" "${cursor_warn}" "${cursor_fail}"
    pass "cursor workflow status completed"
  else
    printf 'Cursor Workflow: status command completed\n'
    pass "cursor workflow status completed"
  fi
else
  warn "cursor workflow status script missing: scripts/cursor-workflow-status.sh"
fi

section "Cursor Operating Modes and Proposal Governance"
if [[ -f scripts/cursor-operating-modes-status.sh ]]; then
  cursor_modes_result=0
  cursor_modes_output="$(bash scripts/cursor-operating-modes-status.sh 2>&1)" || cursor_modes_result=$?
  cursor_modes_pass="$(summary_count "${cursor_modes_output}" "PASS")"
  cursor_modes_warn="$(summary_count "${cursor_modes_output}" "WARN")"
  cursor_modes_fail="$(summary_count "${cursor_modes_output}" "FAIL")"

  if [[ "${cursor_modes_result}" != "0" ]]; then
    printf '%s\n' "${cursor_modes_output}"
    fail "cursor operating modes status failed"
  elif [[ -n "${cursor_modes_pass}" && -n "${cursor_modes_warn}" && -n "${cursor_modes_fail}" ]]; then
    printf 'Cursor Operating Modes: PASS %s / WARN %s / FAIL %s\n' "${cursor_modes_pass}" "${cursor_modes_warn}" "${cursor_modes_fail}"
    pass "cursor operating modes status completed"
  else
    pass "cursor operating modes status completed"
  fi
else
  warn "cursor operating modes status script missing: scripts/cursor-operating-modes-status.sh"
fi

section "Autonomous Build Engine Governance"
if [[ -f scripts/autonomous-build-engine-status.sh ]]; then
  autonomous_build_engine_result=0
  autonomous_build_engine_output="$(bash scripts/autonomous-build-engine-status.sh 2>&1)" || autonomous_build_engine_result=$?
  autonomous_build_engine_pass="$(summary_count "${autonomous_build_engine_output}" "PASS")"
  autonomous_build_engine_warn="$(summary_count "${autonomous_build_engine_output}" "WARN")"
  autonomous_build_engine_fail="$(summary_count "${autonomous_build_engine_output}" "FAIL")"

  if [[ "${autonomous_build_engine_result}" != "0" ]]; then
    printf '%s\n' "${autonomous_build_engine_output}"
    fail "Autonomous Build Engine status failed"
  elif [[ -n "${autonomous_build_engine_pass}" && -n "${autonomous_build_engine_warn}" && -n "${autonomous_build_engine_fail}" ]]; then
    printf 'Autonomous Build Engine: PASS %s / WARN %s / FAIL %s\n' "${autonomous_build_engine_pass}" "${autonomous_build_engine_warn}" "${autonomous_build_engine_fail}"
    pass "Autonomous Build Engine status completed"
  else
    pass "Autonomous Build Engine status completed"
  fi
else
  warn "Autonomous Build Engine status script missing: scripts/autonomous-build-engine-status.sh"
fi

section "Governance Lane Status (Aggregate)"
if [[ -f scripts/governance-lane-status.sh ]]; then
  governance_lane_result=0
  governance_lane_output="$(bash scripts/governance-lane-status.sh 2>&1)" || governance_lane_result=$?
  governance_lane_pass="$(summary_count "${governance_lane_output}" "PASS")"
  governance_lane_warn="$(summary_count "${governance_lane_output}" "WARN")"
  governance_lane_fail="$(summary_count "${governance_lane_output}" "FAIL")"

  if [[ "${governance_lane_result}" != "0" ]]; then
    printf '%s\n' "${governance_lane_output}"
    fail "Governance lane status failed"
  elif [[ -n "${governance_lane_pass}" && -n "${governance_lane_warn}" && -n "${governance_lane_fail}" ]]; then
    printf 'Governance Lane: PASS %s / WARN %s / FAIL %s\n' "${governance_lane_pass}" "${governance_lane_warn}" "${governance_lane_fail}"
    pass "Governance lane status completed"
  else
    pass "Governance lane status completed"
  fi
else
  warn "Governance lane status script missing: scripts/governance-lane-status.sh"
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

end_section_summary "Developer / Cursor Workflow Status"

group_banner "Recommendation"
begin_section_summary

section "Build Queue / Next Recommended Action"
if [[ -f scripts/chief-of-staff-next-action.sh ]]; then
  next_action_result=0
  next_action_output="$(bash scripts/chief-of-staff-next-action.sh 2>&1)" || next_action_result=$?
  next_action_fail="$(printf '%s\n' "${next_action_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"
  if [[ "${next_action_result}" != "0" || "${next_action_fail}" -gt 0 ]]; then
    printf '%s\n' "${next_action_output}"
    fail "next-action recommendation failed"
  else
    pass "next-action recommendation completed"
    printf '%s\n' "${next_action_output}" | sed -n '/^Recommended Next Action$/,/^Summary$/p' | sed '/^Summary$/d'
  fi
elif [[ -f docs/build-queue.md ]]; then
  next_pr="$(awk '
    /^## Next PR[[:space:]]*$/ { in_next = 1; next }
    in_next && NF > 0 { print; exit }
  ' docs/build-queue.md)"
  if [[ -n "${next_pr}" ]]; then
    pass "next recommended PR found"
    printf '\n>>> Next recommended PR: %s <<<\n\n' "${next_pr}"
    printf 'Next recommended PR: %s\n' "${next_pr}"
    printf 'Run the matching status helper after dashboard if you are starting that build.\n'
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

end_section_summary "Recommendation"

group_banner "Final Health Summary"
begin_section_summary

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
printf 'Health: %s/%s checks passing\n' "${PASS_COUNT}" "$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))"

end_section_summary "Final Health Summary"

if (( CRITICAL_FAILURE > 0 )); then
  exit 1
fi

exit 0
