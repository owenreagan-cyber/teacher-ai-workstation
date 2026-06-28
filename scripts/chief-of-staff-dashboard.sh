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
printf 'Dashboard reading order: health -> workflows -> command launcher -> lesson sections -> recommendation\n'

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

section "Build Queue / Next Recommended Action"
if [[ -f docs/build-queue.md ]]; then
  next_pr="$(awk '
    /^## Next PR[[:space:]]*$/ { in_next = 1; next }
    in_next && NF > 0 { print; exit }
  ' docs/build-queue.md)"
  if [[ -n "${next_pr}" ]]; then
    pass "next recommended PR found"
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

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
printf 'Health: %s/%s checks passing\n' "${PASS_COUNT}" "$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))"

if (( CRITICAL_FAILURE > 0 )); then
  exit 1
fi

exit 0
