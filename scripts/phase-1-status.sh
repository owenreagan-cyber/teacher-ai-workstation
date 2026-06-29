#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
COMPARE_0E=0
CRITICAL_BLOCKER=0

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
  CRITICAL_BLOCKER=1
  printf 'FAIL: %s\n' "$1"
}

usage() {
  cat <<'EOF'
Phase 1 Chief of Staff Status

Usage:
  bash scripts/phase-1-status.sh
  bash scripts/phase-1-status.sh --compare-0e

This script is read-only. It does not call APIs, use secrets, access Gmail/Drive,
or create, modify, delete, or move files.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compare-0e)
      COMPARE_0E=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  fail "not inside a Git repository"
  repo_root="$(pwd -P)"
fi

cd "${repo_root}"

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_required_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "required current/core file exists: ${path}"
  else
    fail "required current/core file missing: ${path}"
  fi
}

check_optional_file() {
  local path="$1"
  local label="$2"
  if [[ -f "${path}" ]]; then
    pass "${label}: ${path}"
  else
    warn "${label} missing or not started: ${path}"
  fi
}

check_optional_dir() {
  local path="$1"
  local label="$2"
  if [[ -d "${path}" ]]; then
    pass "${label}: ${path}"
  else
    warn "${label} missing or not started: ${path}"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "${path}" ]]; then
    warn "${label}: cannot check missing file ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    warn "${label} not found in ${path}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    warn "skipping syntax check for missing script: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_python_syntax_optional() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    warn "skipping Python syntax check for missing script: ${path}"
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    warn "python3 missing; skipping Python syntax check for ${path}"
    return
  fi

  if PYTHONPYCACHEPREFIX=/private/tmp/teacher-ai-pycache python3 -m py_compile "${path}"; then
    pass "python syntax ok: ${path}"
  else
    fail "python syntax failed: ${path}"
  fi
}

check_json_syntax_optional() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    warn "skipping JSON check for missing config: ${path}"
    return
  fi

  if ! command -v node >/dev/null 2>&1; then
    warn "node missing; skipping JSON check for ${path}"
    return
  fi

  if node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "${path}"; then
    pass "JSON syntax ok: ${path}"
  else
    fail "JSON syntax failed: ${path}"
  fi
}

run_optional_command() {
  local label="$1"
  local severity="$2"
  local output=""
  shift 2

  if output="$("$@" 2>&1)"; then
    pass "${label}"
  else
    if [[ "${severity}" == "fail" ]]; then
      fail "${label} failed"
    else
      warn "${label} returned nonzero; review manually"
    fi
    if [[ -n "${output}" ]]; then
      printf '%s\n' "${output}" | sed 's/^/      /'
    fi
  fi
}

printf '\nPhase 1 Chief of Staff Status Audit\n'
printf '====================================\n'
printf 'Repo root: %s\n' "${repo_root}"
printf 'Read-only: yes\n'

if (( COMPARE_0E == 1 )); then
  section "Phase 0E Transition Check"
  if [[ -f scripts/verify-phase-0e.sh ]]; then
    run_optional_command "Phase 0E verifier passes" "fail" bash scripts/verify-phase-0e.sh
  else
    fail "Phase 0E verifier missing: scripts/verify-phase-0e.sh"
  fi
fi

section "Tier 1: Current/Core Files"
for path in \
  bin/chief-of-staff \
  assistant/chief-of-staff.md \
  assistant/permissions.md \
  assistant/failure-recovery-policy.md \
  assistant/memory/projects.md \
  assistant/intake/README.md; do
  check_required_file "${path}"
done

section "Tier 2: Planned Or Optional Readiness"
check_optional_file "assistant/memory/active-priorities.md" "active priorities memory"
check_optional_file "assistant/training/writing-samples/approved-samples.md" "approved writing samples"
check_optional_file "docs/phase-1-chief-of-staff-status-audit.md" "Phase 1 audit doc"
check_optional_file "docs/developer-mode-readiness.md" "Developer Mode readiness doc"
check_optional_file "docs/build-queue.md" "build queue doc"
check_optional_file "docs/phase-1-readiness-checklist.md" "Phase 1 readiness checklist"
check_optional_file "docs/chief-of-staff-roadmap.md" "Chief of Staff roadmap"
check_optional_file "docs/reddit-api-status.md" "Reddit API status doc"
check_optional_file "docs/spotify-vibe-playlists.md" "Spotify playlist doc"
check_optional_file "docs/vibe-panel-roadmap.md" "Vibe Panel roadmap"
check_optional_file "docs/3d-printing-roadmap.md" "3D printing roadmap"
check_optional_file "docs/open-threads.md" "open threads doc"
check_optional_dir "assistant/intake/raw" "raw intake holding folder"
check_optional_dir "assistant/intake/quarantine-files" "quarantine file folder"
check_optional_dir "assistant/intake/approved-files" "approved file folder"

section "Functional Checks"
if [[ -x bin/chief-of-staff || -f bin/chief-of-staff ]]; then
  run_optional_command "Chief of Staff CLI lists workflows" "fail" bin/chief-of-staff --list-workflows
else
  fail "Chief of Staff CLI is missing or unreadable: bin/chief-of-staff"
fi

if [[ -f bin/chief-of-staff ]] && grep -q -- '--intake-status' bin/chief-of-staff; then
  run_optional_command "intake status command runs" "warn" bin/chief-of-staff --intake-status
else
  warn "no intake status command found in bin/chief-of-staff"
fi

if [[ -f bin/chief-of-staff ]] && grep -q -- '--memory-status' bin/chief-of-staff; then
  run_optional_command "memory status command runs" "warn" bin/chief-of-staff --memory-status
else
  warn "no memory status command found in bin/chief-of-staff"
fi

section "Memory Currency Checks"
check_text "assistant/memory/active-priorities.md" "Phase 0E" "active priorities mentions Phase 0E"
check_text "assistant/memory/active-priorities.md" "Phase 1" "active priorities mentions Phase 1"
check_text "assistant/memory/active-priorities.md" "Chief of Staff" "active priorities mentions Chief of Staff"
check_text "assistant/memory/projects.md" "Phase 0E" "project memory mentions Phase 0E"
check_text "assistant/memory/projects.md" "Phase 1" "project memory mentions Phase 1"
check_text "assistant/memory/projects.md" "Developer Mode|Chief of Staff" "project memory mentions Developer Mode or Chief of Staff"

section "Future/Planned Work Signals"
check_text "docs/chief-of-staff-roadmap.md" "local folder indexing|Selected local folder indexing" "local indexing remains planned"
check_text "docs/chief-of-staff-roadmap.md" "Google Drive|Drive" "Drive integration remains documented as later"
check_text "docs/chief-of-staff-roadmap.md" "Gmail|email" "Gmail/email integration remains documented as later"
check_text "docs/open-threads.md" "Reddit API approval is pending|Reddit API approval pending" "Reddit API approval remains open"
check_text "docs/open-threads.md" "Spotify.*not automated|Spotify automation pending" "Spotify automation remains open"
check_text "docs/open-threads.md" "Vibe Panel.*scaffold|Vibe Panel.*pending" "Vibe Panel remains scaffold/pending"

section "Chief of Staff Command Launcher Files"
for path in \
  docs/chief-of-staff-command-launcher-refinement.md \
  docs/dashboard-polish-command-grouping-follow-up.md \
  scripts/command-launcher-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Temp Queue Rules Files"
for path in \
  docs/wallpaper-photo-temp-queue-rules.md \
  scripts/wallpaper-photo-temp-queue-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Queue File Format Files"
for path in \
  docs/wallpaper-photo-queue-file-format.md \
  assistant/appearance-vibe/wallpaper-photo-curator/queue-file-format.json \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-queue.json \
  scripts/wallpaper-photo-queue-file-validator.sh \
  scripts/wallpaper-photo-queue-file-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Approve/Dismiss UI Design Files"
for path in \
  docs/wallpaper-photo-approve-dismiss-ui-design.md \
  scripts/wallpaper-photo-approve-dismiss-ui-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Image Processing Rules Files"
for path in \
  docs/wallpaper-photo-image-processing-rules.md \
  scripts/wallpaper-photo-image-processing-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Local Scheduler Plan Files"
for path in \
  docs/wallpaper-photo-local-automation-scheduler-plan.md \
  scripts/wallpaper-photo-local-scheduler-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Source Fetcher Plan Files"
for path in \
  docs/wallpaper-photo-approved-source-fetcher-plan.md \
  scripts/wallpaper-photo-source-fetcher-plan-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Source Allowlist Foundation Files"
for path in \
  docs/wallpaper-photo-source-allowlist-foundation.md \
  assistant/appearance-vibe/wallpaper-photo-curator/source-allowlist-schema.json \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-source-allowlist.json \
  scripts/wallpaper-photo-source-allowlist-validator.sh \
  scripts/wallpaper-photo-source-allowlist-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Simulated Discovery Files"
for path in \
  docs/wallpaper-photo-simulated-approved-source-discovery-plan.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-discovery-report.json \
  scripts/wallpaper-photo-simulated-discovery-validator.sh \
  scripts/wallpaper-photo-simulated-discovery-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Review UI Prototype Files"
for path in \
  docs/wallpaper-photo-live-local-review-ui-prototype-plan.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-review-ui-state.json \
  scripts/wallpaper-photo-review-ui-state-validator.sh \
  scripts/wallpaper-photo-review-ui-prototype-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Image Processor Foundation Files"
for path in \
  docs/wallpaper-photo-image-processor-foundation.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-image-processing-plan.json \
  scripts/wallpaper-photo-image-processing-plan-validator.sh \
  scripts/wallpaper-photo-image-processor-foundation-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Scheduler Foundation Files"
for path in \
  docs/wallpaper-photo-scheduler-foundation.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-scheduler-run-plan.json \
  scripts/wallpaper-photo-scheduler-run-plan-validator.sh \
  scripts/wallpaper-photo-scheduler-foundation-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Notification Foundation Files"
for path in \
  docs/wallpaper-photo-notification-foundation.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-notification-plan.json \
  scripts/wallpaper-photo-notification-plan-validator.sh \
  scripts/wallpaper-photo-notification-foundation-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Rotation Handoff and Safety Audit Files"
for path in \
  docs/wallpaper-photo-rotation-handoff-safety-audit.md \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-rotation-handoff-readiness-report.json \
  scripts/wallpaper-photo-rotation-handoff-validator.sh \
  scripts/wallpaper-photo-rotation-handoff-safety-status.sh; do
  check_required_file "${path}"
done

section "Return to Chief of Staff Core Files"
for path in \
  docs/return-to-chief-of-staff-core.md \
  scripts/return-to-chief-of-staff-core-status.sh; do
  check_required_file "${path}"
done

section "Lesson Review Workflow Polish Files"
for path in \
  docs/lesson-review-workflow-polish.md \
  scripts/lesson-review-workflow-polish-status.sh; do
  check_required_file "${path}"
done

section "Review Notes Workflow Polish Files"
for path in \
  docs/review-notes-workflow-polish.md \
  scripts/review-notes-workflow-polish-status.sh; do
  check_required_file "${path}"
done

section "Local Document Indexing Follow-Up Files"
for path in \
  docs/local-document-indexing-follow-up.md \
  scripts/local-document-indexing-follow-up-status.sh; do
  check_required_file "${path}"
done

section "Project Memory Cleanup Files"
for path in \
  docs/project-memory-cleanup.md \
  scripts/project-memory-cleanup-status.sh; do
  check_required_file "${path}"
done

section "Testing/Checklist Consolidation Files"
for path in \
  docs/testing-checklist-consolidation.md \
  scripts/testing-checklist-consolidation-status.sh; do
  check_required_file "${path}"
done

section "Command/Check Bundle Reference Polish Files"
for path in \
  docs/command-check-bundle-reference-polish.md \
  scripts/command-check-bundle-reference-status.sh; do
  check_required_file "${path}"
done

section "Checklist-Driven Prompt Template Tightening Files"
for path in \
  docs/checklist-driven-prompt-template-tightening.md \
  scripts/checklist-driven-prompt-template-status.sh; do
  check_required_file "${path}"
done

section "PR Lifecycle Guardrail Consolidation Files"
for path in \
  docs/pr-lifecycle-guardrail-consolidation.md \
  scripts/pr-lifecycle-guardrail-status.sh; do
  check_required_file "${path}"
done

section "Branch Hygiene and Cleanup Reference Files"
for path in \
  docs/branch-hygiene-cleanup-reference.md \
  scripts/branch-hygiene-cleanup-status.sh; do
  check_required_file "${path}"
done

section "Local Main Proof Report Polish Files"
for path in \
  docs/local-main-proof-report-polish.md \
  scripts/local-main-proof-report-status.sh; do
  check_required_file "${path}"
done

section "Workflow Docs Cross-Link Polish Files"
for path in \
  docs/workflow-docs-cross-link-polish.md \
  scripts/workflow-docs-cross-link-status.sh; do
  check_required_file "${path}"
done

section "Workflow Docs Navigation Status Summary Files"
for path in \
  docs/workflow-docs-navigation-status-summary.md \
  scripts/workflow-docs-navigation-status-summary.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Maintenance Checklist Files"
for path in \
  docs/prompt-pack-maintenance-checklist.md \
  scripts/prompt-pack-maintenance-status.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Reference Index Files"
for path in \
  docs/prompt-pack-reference-index.md \
  scripts/prompt-pack-reference-index-status.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Stale-Reference Audit Files"
for path in \
  docs/prompt-pack-stale-reference-audit.md \
  scripts/prompt-pack-stale-reference-audit-status.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Freshness Report Polish Files"
for path in \
  docs/prompt-pack-freshness-report-polish.md \
  scripts/prompt-pack-freshness-report-status.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Handoff Summary Files"
for path in \
  docs/prompt-pack-handoff-summary.md \
  scripts/prompt-pack-handoff-summary-status.sh; do
  check_required_file "${path}"
done

section "Prompt Pack Stack Completion Marker Files"
for path in \
  docs/prompt-pack-stack-completion-marker.md \
  scripts/prompt-pack-stack-completion-status.sh; do
  check_required_file "${path}"
done

section "Core Teacher Workstation Planning Cleanup Files"
for path in \
  docs/core-teacher-workstation-planning-cleanup.md \
  scripts/core-teacher-workstation-planning-cleanup-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Quick-Reference Polish Files"
for path in \
  docs/teacher-workflow-quick-reference-polish.md \
  scripts/teacher-workflow-quick-reference-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Status Summary Files"
for path in \
  docs/teacher-workflow-status-summary.md \
  scripts/teacher-workflow-status-summary.sh; do
  check_required_file "${path}"
done

section "Teacher Planning Command Organization Files"
for path in \
  docs/teacher-planning-command-organization.md \
  scripts/teacher-planning-command-organization-status.sh; do
  check_required_file "${path}"
done

section "Dashboard Section Summary Polish Files"
for path in \
  docs/dashboard-section-summary-polish.md \
  scripts/dashboard-section-summary-status.sh; do
  check_required_file "${path}"
done

section "Chief of Staff Workflow Quick-Start Guide Files"
for path in \
  docs/chief-of-staff-workflow-quick-start-guide.md \
  scripts/chief-of-staff-workflow-quick-start-status.sh; do
  check_required_file "${path}"
done

section "Chief of Staff Help Examples Polish Files"
for path in \
  docs/chief-of-staff-help-examples-polish.md \
  scripts/chief-of-staff-help-examples-status.sh; do
  check_required_file "${path}"
done

section "Chief of Staff Command Map Cleanup Files"
for path in \
  docs/chief-of-staff-command-map-cleanup.md \
  scripts/chief-of-staff-command-map-status.sh; do
  check_required_file "${path}"
done

section "Chief of Staff Dashboard Readability Pass Files"
for path in \
  docs/chief-of-staff-dashboard-readability-pass.md \
  scripts/chief-of-staff-dashboard-readability-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Metadata Schema Files"
for path in \
  docs/wallpaper-photo-metadata-schema.md \
  assistant/appearance-vibe/wallpaper-photo-curator/README.md \
  assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json \
  assistant/appearance-vibe/wallpaper-photo-curator/sample-records.json \
  scripts/wallpaper-photo-metadata-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Manual Folder Creation Helper Files"
for path in \
  docs/wallpaper-photo-manual-folder-creation-helper.md \
  scripts/wallpaper-photo-create-folders.sh \
  scripts/wallpaper-photo-folder-creation-status.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Dry-Run Folder Validator Files"
for path in \
  docs/wallpaper-photo-dry-run-folder-validator.md \
  scripts/wallpaper-photo-dry-run-folder-validator.sh; do
  check_required_file "${path}"
done

section "Wallpaper/Photo Rotation Folder Design Files"
for path in \
  docs/wallpaper-photo-rotation-folder-design.md \
  scripts/wallpaper-photo-folder-design-status.sh; do
  check_required_file "${path}"
done

section "Appearance & Vibe Wallpaper/Photo Curator Plan Files"
for path in \
  docs/appearance-vibe-wallpaper-photo-curator-plan.md \
  scripts/wallpaper-photo-curator-plan-status.sh; do
  check_required_file "${path}"
done

section "Safe Local Document Indexing Plan Files"
for path in \
  docs/safe-local-document-indexing-plan.md \
  scripts/document-indexing-plan-status.sh; do
  check_required_file "${path}"
done

section "Review Notes Template Files"
for path in \
  docs/review-notes-template.md \
  assistant/lesson-planning/review-notes/README.md \
  scripts/review-notes-template-status.sh; do
  check_required_file "${path}"
done

section "Single-Slug Lesson Review Files"
for path in \
  docs/single-slug-lesson-review-view.md \
  scripts/lesson-review-view.sh; do
  check_required_file "${path}"
done

section "Lesson Review Checklist Files"
for path in \
  docs/safe-local-lesson-review-checklist.md \
  scripts/lesson-review-checklist-status.sh; do
  check_required_file "${path}"
done

section "Cursor Workflow Files"
for path in \
  .cursor/rules/teacher-ai-workstation.mdc \
  docs/cursor-workflow-operating-system.md \
  docs/cursor-prompt-template.md \
  docs/cursor-pr-review-checklist.md \
  scripts/cursor-workflow-status.sh; do
  check_required_file "${path}"
done

section "Syntax Checks"
check_bash_syntax "scripts/command-launcher-status.sh"
check_bash_syntax "scripts/wallpaper-photo-temp-queue-status.sh"
check_bash_syntax "scripts/wallpaper-photo-queue-file-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-queue-file-status.sh"
check_bash_syntax "scripts/wallpaper-photo-approve-dismiss-ui-status.sh"
check_bash_syntax "scripts/wallpaper-photo-image-processing-status.sh"
check_bash_syntax "scripts/wallpaper-photo-local-scheduler-status.sh"
check_bash_syntax "scripts/wallpaper-photo-source-fetcher-plan-status.sh"
check_bash_syntax "scripts/wallpaper-photo-source-allowlist-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-source-allowlist-status.sh"
check_bash_syntax "scripts/wallpaper-photo-simulated-discovery-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-simulated-discovery-status.sh"
check_bash_syntax "scripts/wallpaper-photo-review-ui-state-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-review-ui-prototype-status.sh"
check_bash_syntax "scripts/wallpaper-photo-image-processing-plan-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-image-processor-foundation-status.sh"
check_bash_syntax "scripts/wallpaper-photo-scheduler-run-plan-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-scheduler-foundation-status.sh"
check_bash_syntax "scripts/wallpaper-photo-notification-plan-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-notification-foundation-status.sh"
check_bash_syntax "scripts/wallpaper-photo-rotation-handoff-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-rotation-handoff-safety-status.sh"
check_bash_syntax "scripts/return-to-chief-of-staff-core-status.sh"
check_bash_syntax "scripts/lesson-review-workflow-polish-status.sh"
check_bash_syntax "scripts/review-notes-workflow-polish-status.sh"
check_bash_syntax "scripts/local-document-indexing-follow-up-status.sh"
check_bash_syntax "scripts/project-memory-cleanup-status.sh"
check_bash_syntax "scripts/testing-checklist-consolidation-status.sh"
check_bash_syntax "scripts/command-check-bundle-reference-status.sh"
check_bash_syntax "scripts/checklist-driven-prompt-template-status.sh"
check_bash_syntax "scripts/pr-lifecycle-guardrail-status.sh"
check_bash_syntax "scripts/branch-hygiene-cleanup-status.sh"
check_bash_syntax "scripts/local-main-proof-report-status.sh"
check_bash_syntax "scripts/workflow-docs-cross-link-status.sh"
check_bash_syntax "scripts/workflow-docs-navigation-status-summary.sh"
check_bash_syntax "scripts/prompt-pack-maintenance-status.sh"
check_bash_syntax "scripts/prompt-pack-reference-index-status.sh"
check_bash_syntax "scripts/prompt-pack-stale-reference-audit-status.sh"
check_bash_syntax "scripts/prompt-pack-freshness-report-status.sh"
check_bash_syntax "scripts/prompt-pack-handoff-summary-status.sh"
check_bash_syntax "scripts/prompt-pack-stack-completion-status.sh"
check_bash_syntax "scripts/core-teacher-workstation-planning-cleanup-status.sh"
check_bash_syntax "scripts/teacher-workflow-quick-reference-status.sh"
check_bash_syntax "scripts/teacher-workflow-status-summary.sh"
check_bash_syntax "scripts/teacher-planning-command-organization-status.sh"
check_bash_syntax "scripts/dashboard-section-summary-status.sh"
check_bash_syntax "scripts/chief-of-staff-workflow-quick-start-status.sh"
check_bash_syntax "scripts/chief-of-staff-help-examples-status.sh"
check_bash_syntax "scripts/chief-of-staff-command-map-status.sh"
check_bash_syntax "scripts/chief-of-staff-dashboard-readability-status.sh"
check_bash_syntax "scripts/wallpaper-photo-metadata-status.sh"
check_bash_syntax "scripts/wallpaper-photo-create-folders.sh"
check_bash_syntax "scripts/wallpaper-photo-folder-creation-status.sh"
check_bash_syntax "scripts/wallpaper-photo-dry-run-folder-validator.sh"
check_bash_syntax "scripts/wallpaper-photo-folder-design-status.sh"
check_bash_syntax "scripts/wallpaper-photo-curator-plan-status.sh"
check_bash_syntax "scripts/document-indexing-plan-status.sh"
check_bash_syntax "scripts/review-notes-template-status.sh"
check_bash_syntax "scripts/lesson-review-view.sh"
check_bash_syntax "scripts/lesson-review-checklist-status.sh"
check_bash_syntax "scripts/cursor-workflow-status.sh"
check_bash_syntax "scripts/phase-1-status.sh"
check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/verify-phase-0e.sh"
check_bash_syntax "scripts/phase-0e-summary.sh"
check_python_syntax_optional "scripts/image-review-status.py"
check_json_syntax_optional "configs/spotify-vibe-playlists.json"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

section "Recommendation"
if (( CRITICAL_BLOCKER > 0 )); then
  printf 'Fix critical Chief of Staff CLI, memory, intake, or script problems before the next build PR.\n'
else
  printf 'Next recommended PR: Teacher planning command detail polish.\n'
fi

if (( COMPARE_0E == 1 && CRITICAL_BLOCKER == 0 )); then
  printf '\nPhase 0E complete; Phase 1 readiness audit complete.\n'
fi

if (( FAIL_COUNT > 0 )); then
  exit 1
fi

exit 0
