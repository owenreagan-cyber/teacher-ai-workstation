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

check_doc_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "${file}" ]]; then
    fail "cannot check missing doc: ${file}"
    return
  fi
  if grep -Fq "${phrase}" "${file}"; then
    pass "doc mentions ${label}"
  else
    fail "${file} must mention ${label}"
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

section "Teacher Planning Command Detail Polish Files"
for path in \
  docs/teacher-planning-command-detail-polish.md \
  scripts/teacher-planning-command-detail-status.sh; do
  check_required_file "${path}"
done

section "Lesson Review Command Detail Polish Files"
for path in \
  docs/lesson-review-command-detail-polish.md \
  scripts/lesson-review-command-detail-status.sh; do
  check_required_file "${path}"
done

section "Review Notes Command Detail Polish Files"
for path in \
  docs/review-notes-command-detail-polish.md \
  scripts/review-notes-command-detail-status.sh; do
  check_required_file "${path}"
done

section "Document Indexing Command Detail Polish Files"
for path in \
  docs/document-indexing-command-detail-polish.md \
  scripts/document-indexing-command-detail-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Command Detail Summary Files"
for path in \
  docs/teacher-workflow-command-detail-summary.md \
  scripts/teacher-workflow-command-detail-summary-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Safe-Output Examples Files"
for path in \
  docs/teacher-workflow-safe-output-examples.md \
  scripts/teacher-workflow-safe-output-examples-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Safe-Output Checker Files"
for path in \
  docs/teacher-workflow-safe-output-checker.md \
  scripts/teacher-workflow-safe-output-checker-status.sh; do
  check_required_file "${path}"
done

section "Teacher Workflow Output Examples Completion Marker Files"
for path in \
  docs/teacher-workflow-output-examples-completion-marker.md \
  scripts/teacher-workflow-output-examples-completion-status.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/teacher-workflow-output-examples-completion-status.sh

section "Lesson-Planning Template Readiness Polish Files"
for path in \
  docs/lesson-planning-template-readiness-polish.md \
  scripts/lesson-planning-template-readiness-status.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/lesson-planning-template-readiness-status.sh

section "Curriculum Builder Local-First Foundation Files"
for path in \
  docs/curriculum-builder-local-first-foundation-plan.md \
  docs/curriculum-source-storage-strategy.md \
  docs/curriculum-resource-registry-plan.md \
  docs/curriculum-builder-planning-stack-summary.md \
  docs/curriculum-builder-next-phase-decision.md \
  docs/curriculum-builder-decision-intake-template.md \
  docs/curriculum-builder-approval-gate.md \
  docs/curriculum-builder-planning-closeout.md \
  docs/curriculum-builder-maintainer-handoff.md \
  docs/curriculum-builder-future-pr-checklist.md \
  docs/curriculum-builder-canonical-planning-index.md \
  docs/curriculum-builder-output-contract-foundation.md \
  docs/curriculum-builder-static-source-registry-plan.md \
  docs/curriculum-builder-section-completion-audit.md \
  scripts/curriculum-builder-foundation-status.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-foundation-status.sh

section "Curriculum Registry v0 Foundation Files"
for path in \
  docs/curriculum-registry-v0.md \
  assistant/curriculum-builder/registry/v0/registry.json \
  assistant/curriculum-builder/registry/v0/registry-schema.json \
  assistant/curriculum-builder/registry/v0/README.md \
  scripts/curriculum-registry-v0-validator.sh \
  scripts/curriculum-registry-v0-status.sh \
  tests/curriculum-registry-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-registry-v0-validator.sh
check_bash_syntax scripts/curriculum-registry-v0-status.sh
check_bash_syntax tests/curriculum-registry-v0-test.sh

section "Curriculum Output Contract v0 Foundation Files"
for path in \
  docs/curriculum-output-contract-v0.md \
  assistant/curriculum-builder/output-contract/v0/contract-envelope-schema.json \
  assistant/curriculum-builder/output-contract/v0/direct-instruction-slide-deck-schema.json \
  assistant/curriculum-builder/output-contract/v0/contracts/sample-di-slide-deck-001.json \
  assistant/curriculum-builder/output-contract/v0/placeholder-manifest.json \
  assistant/curriculum-builder/output-contract/v0/README.md \
  scripts/curriculum-output-contract-v0-validator.sh \
  scripts/curriculum-output-contract-v0-status.sh \
  tests/curriculum-output-contract-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-output-contract-v0-validator.sh
check_bash_syntax scripts/curriculum-output-contract-v0-status.sh
check_bash_syntax tests/curriculum-output-contract-v0-test.sh

section "Teacher Script Contract v0 Foundation Files"
for path in \
  docs/curriculum-teacher-script-contract-v0.md \
  assistant/curriculum-builder/output-contract/v0/teacher-script-contract-schema.json \
  assistant/curriculum-builder/output-contract/v0/contracts/sample-teacher-script-001.json \
  tests/curriculum-teacher-script-contract-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax tests/curriculum-teacher-script-contract-v0-test.sh

section "Worksheet Contract v0 Foundation Files"
for path in \
  docs/curriculum-worksheet-contract-v0.md \
  assistant/curriculum-builder/output-contract/v0/worksheet-contract-schema.json \
  assistant/curriculum-builder/output-contract/v0/contracts/sample-worksheet-001.json \
  tests/curriculum-worksheet-contract-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax tests/curriculum-worksheet-contract-v0-test.sh

section "Review Game Contract v0 Foundation Files"
for path in \
  docs/curriculum-review-game-contract-v0.md \
  assistant/curriculum-builder/output-contract/v0/review-game-contract-schema.json \
  assistant/curriculum-builder/output-contract/v0/contracts/sample-review-game-001.json \
  tests/curriculum-review-game-contract-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax tests/curriculum-review-game-contract-v0-test.sh

section "Canvas Package Contract v0 Foundation Files"
for path in \
  docs/curriculum-canvas-package-contract-v0.md \
  assistant/curriculum-builder/output-contract/v0/canvas-export-package-contract-schema.json \
  assistant/curriculum-builder/output-contract/v0/contracts/sample-canvas-package-001.json \
  tests/curriculum-canvas-package-contract-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax tests/curriculum-canvas-package-contract-v0-test.sh

section "Curriculum Builder v1 Foundation Files"
check_required_file docs/curriculum-builder-v1-foundation.md
check_required_file tests/curriculum-contract-suite-v0-test.sh
check_bash_syntax tests/curriculum-contract-suite-v0-test.sh

section "Master Build Roadmap Files"
check_required_file docs/master-build-roadmap.md
check_required_file docs/teacher-workstation-capability-map.md
check_required_file docs/ai-tool-routing-matrix.md
check_required_file docs/3d-builder-workshop-agent-roadmap.md
master_roadmap_doc="docs/master-build-roadmap.md"
check_doc_contains "${master_roadmap_doc}" "Teacher Workstation Health Monitor" "master roadmap mentions Health Monitor"
check_doc_contains "${master_roadmap_doc}" "Teacher Workstation System Updater" "master roadmap mentions System Updater"
check_doc_contains "${master_roadmap_doc}" "3D Builder Workshop Agent" "master roadmap mentions 3D Builder Workshop Agent"
check_doc_contains "${master_roadmap_doc}" "Lovable Classroom App Builder" "master roadmap mentions Lovable integration"
check_doc_contains "${master_roadmap_doc}" "Widget and Shortcut Builder" "master roadmap mentions Widget and Shortcut Builder"
check_doc_contains "${master_roadmap_doc}" "Mac Workstation Experience" "master roadmap mentions Mac Workstation Experience"
check_doc_contains "${master_roadmap_doc}" "Canvas Manual Restart" "master roadmap mentions Canvas Manual Restart"
check_doc_contains "${master_roadmap_doc}" "Staged integration model" "master roadmap mentions staged integration model"
capability_map_doc="docs/teacher-workstation-capability-map.md"
check_doc_contains "${capability_map_doc}" "Integrations and Automation (Staged)" "capability map mentions staged integrations"

section "Chief of Staff v1 Agent Core (Program B1) Files"
for path in \
  docs/chief-of-staff-v1-foundation.md \
  docs/chief-of-staff-agent-core.md \
  docs/chief-of-staff-operating-model.md \
  docs/chief-of-staff-proof-workflow.md \
  docs/chief-of-staff-command-index-v1.md \
  assistant/chief-of-staff/v1/command-surface-manifest.json \
  assistant/chief-of-staff/v1/README.md \
  scripts/chief-of-staff-commands.sh \
  scripts/chief-of-staff-v1-foundation-status.sh \
  scripts/chief-of-staff-command-index-v1-status.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/chief-of-staff-commands.sh
check_bash_syntax scripts/chief-of-staff-v1-foundation-status.sh
check_bash_syntax scripts/chief-of-staff-command-index-v1-status.sh
agent_core_doc="docs/chief-of-staff-agent-core.md"
check_doc_contains "${agent_core_doc}" "must not become" "agent core non-ownership boundaries"
check_doc_contains docs/chief-of-staff-v1-foundation.md "complete_v1_b" "v1 foundation closure status"
check_doc_contains docs/chief-of-staff-v1-program-b-closure.md "complete_v1_b" "program b closure status"
if grep -Fq -- '--commands' bin/chief-of-staff; then
  pass "chief-of-staff exposes --commands"
else
  fail "chief-of-staff missing --commands"
fi
if grep -Fq -- '--chief-of-staff-v1-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --chief-of-staff-v1-status"
else
  fail "chief-of-staff missing --chief-of-staff-v1-status"
fi
for cos_flag in --daily-status --closeout --approval-queue --blocker-queue --mode-status; do
  if grep -Fq -- "${cos_flag}" bin/chief-of-staff; then
    pass "chief-of-staff exposes ${cos_flag}"
  else
    fail "chief-of-staff missing ${cos_flag}"
  fi
done

section "Chief of Staff v1 Agent Core (Program B) Files"
for path in \
  docs/chief-of-staff-daily-operations.md \
  docs/chief-of-staff-closeout-workflow.md \
  docs/chief-of-staff-approval-blocker-queues.md \
  docs/chief-of-staff-mode-status.md \
  docs/chief-of-staff-v1-program-b-closure.md \
  scripts/chief-of-staff-daily-status.sh \
  scripts/chief-of-staff-closeout.sh \
  scripts/chief-of-staff-approval-queue.sh \
  scripts/chief-of-staff-blocker-queue.sh \
  scripts/chief-of-staff-mode-status.sh \
  tests/chief-of-staff-daily-operations-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/chief-of-staff-daily-status.sh
check_bash_syntax scripts/chief-of-staff-closeout.sh
check_bash_syntax scripts/chief-of-staff-approval-queue.sh
check_bash_syntax scripts/chief-of-staff-blocker-queue.sh
check_bash_syntax scripts/chief-of-staff-mode-status.sh
check_bash_syntax tests/chief-of-staff-daily-operations-test.sh

section "Teacher Workstation Health Monitor (Program H) Files"
for path in \
  docs/teacher-workstation-health-monitor.md \
  docs/teacher-workstation-health-monitor-foundation.md \
  scripts/teacher-workstation-health-status.sh \
  tests/teacher-workstation-health-monitor-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/teacher-workstation-health-status.sh
check_bash_syntax tests/teacher-workstation-health-monitor-test.sh
check_doc_contains docs/teacher-workstation-health-monitor-foundation.md "complete_v1_h" "health monitor closure status"
check_doc_contains docs/teacher-workstation-health-monitor.md "observes and reports" "health monitor observe-only boundary"
if grep -Fq -- '--system-health' bin/chief-of-staff; then
  pass "chief-of-staff exposes --system-health"
else
  fail "chief-of-staff missing --system-health"
fi
if grep -Fq -- '--workstation-health' bin/chief-of-staff; then
  pass "chief-of-staff exposes --workstation-health"
else
  fail "chief-of-staff missing --workstation-health"
fi

section "Teacher Workstation System Updater (Program I) Files"
for path in \
  docs/teacher-workstation-system-updater.md \
  docs/teacher-workstation-system-updater-foundation.md \
  scripts/teacher-workstation-system-updater-status.sh \
  scripts/teacher-workstation-system-update-plan.sh \
  tests/teacher-workstation-system-updater-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/teacher-workstation-system-updater-status.sh
check_bash_syntax scripts/teacher-workstation-system-update-plan.sh
check_bash_syntax tests/teacher-workstation-system-updater-test.sh
check_doc_contains docs/teacher-workstation-system-updater-foundation.md "complete_v1_i" "system updater closure status"
check_doc_contains docs/teacher-workstation-system-updater.md "recommends and plans only" "system updater read-only boundary"
if grep -Fq -- '--system-update-check' bin/chief-of-staff; then
  pass "chief-of-staff exposes --system-update-check"
else
  fail "chief-of-staff missing --system-update-check"
fi
if grep -Fq -- '--system-update-plan' bin/chief-of-staff; then
  pass "chief-of-staff exposes --system-update-plan"
else
  fail "chief-of-staff missing --system-update-plan"
fi

section "AI Tool Routing Matrix (Operational Surface) Files"
for path in \
  docs/ai-tool-routing-operational-surface.md \
  docs/ai-tool-routing-foundation.md \
  scripts/ai-tool-routing-status.sh \
  tests/ai-tool-routing-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/ai-tool-routing-status.sh
check_bash_syntax tests/ai-tool-routing-status-test.sh
check_doc_contains docs/ai-tool-routing-foundation.md "complete_v1_r" "ai tool routing closure status"
check_doc_contains docs/ai-tool-routing-operational-surface.md "read-only routing visibility" "routing read-only boundary"
if grep -Fq -- '--model-routing-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --model-routing-status"
else
  fail "chief-of-staff missing --model-routing-status"
fi

section "Local LLM / Ollama Workstation (Program D1) Files"
for path in \
  docs/local-llm-workstation-status-foundation.md \
  docs/local-llm-non-activation-boundaries.md \
  docs/local-llm-ollama-readiness-plan.md \
  scripts/local-llm-workstation-status.sh \
  tests/local-llm-workstation-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/local-llm-workstation-status.sh
check_bash_syntax tests/local-llm-workstation-status-test.sh
check_doc_contains docs/local-llm-workstation-status-foundation.md "complete_v1_d1" "local llm closure status"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Ollama install: blocked" "local llm ollama install blocked"
if grep -Fq -- '--local-llm-workstation-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --local-llm-workstation-status"
else
  fail "chief-of-staff missing --local-llm-workstation-status"
fi

section "Mac Workstation Experience (Program E1) Files"
for path in \
  docs/mac-workstation-experience-foundation.md \
  docs/mac-workstation-non-activation-boundaries.md \
  docs/mac-workstation-readiness-plan.md \
  scripts/mac-workstation-experience-status.sh \
  tests/mac-workstation-experience-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/mac-workstation-experience-status.sh
check_bash_syntax tests/mac-workstation-experience-status-test.sh
check_doc_contains docs/mac-workstation-experience-foundation.md "complete_v1_e1" "mac workstation closure status"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Mac system changes: blocked" "mac system changes blocked"
if grep -Fq -- '--mac-workstation-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --mac-workstation-status"
else
  fail "chief-of-staff missing --mac-workstation-status"
fi

section "Widget and Shortcut Builder (Program F1) Files"
for path in \
  docs/widget-shortcut-builder-catalog-foundation.md \
  docs/widget-shortcut-builder-non-activation-boundaries.md \
  docs/widget-shortcut-builder-readiness-plan.md \
  docs/widget-shortcut-builder-fake-catalog-index.md \
  assistant/widget-shortcut/samples/fake-widget-shortcut-catalog.json \
  scripts/widget-shortcut-builder-status.sh \
  tests/widget-shortcut-builder-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/widget-shortcut-builder-status.sh
check_bash_syntax tests/widget-shortcut-builder-status-test.sh
check_doc_contains docs/widget-shortcut-builder-catalog-foundation.md "complete_v1_f1" "widget shortcut closure status"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Widget install: blocked" "widget install blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Shortcut execution: blocked" "shortcut execution blocked"
if grep -Fq -- '--widget-shortcut-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --widget-shortcut-status"
else
  fail "chief-of-staff missing --widget-shortcut-status"
fi

section "Classroom App Lab (Prototype Rescue Foundation) Files"
for path in \
  docs/classroom-app-lab-prototype-rescue-foundation.md \
  docs/classroom-app-lab-non-activation-boundaries.md \
  docs/classroom-app-lab-readiness-plan.md \
  docs/classroom-app-lab-fake-prototype-inventory-template.md \
  docs/classroom-app-lab-vs-lovable-lane-boundary.md \
  docs/proposals/blocked/classroom-utility-apps-external-ideas.md \
  scripts/classroom-app-lab-status.sh \
  tests/classroom-app-lab-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/classroom-app-lab-status.sh
check_bash_syntax tests/classroom-app-lab-status-test.sh
check_doc_contains docs/classroom-app-lab-prototype-rescue-foundation.md "complete_v1_cal1" "classroom app lab closure status"
check_doc_contains docs/classroom-app-lab-non-activation-boundaries.md "Zip extraction: blocked" "classroom app lab zip extraction blocked"
if grep -Fq -- '--classroom-app-lab-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --classroom-app-lab-status"
else
  fail "chief-of-staff missing --classroom-app-lab-status"
fi

section "Lovable Classroom App Builder (Program G1) Files"
for path in \
  docs/lovable-classroom-app-builder-foundation.md \
  docs/lovable-classroom-app-builder-non-activation-boundaries.md \
  docs/lovable-classroom-app-builder-readiness-plan.md \
  scripts/lovable-classroom-app-builder-status.sh \
  tests/lovable-classroom-app-builder-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/lovable-classroom-app-builder-status.sh
check_bash_syntax tests/lovable-classroom-app-builder-status-test.sh
check_doc_contains docs/lovable-classroom-app-builder-foundation.md "complete_v1_g1" "lovable closure status"
check_doc_contains docs/lovable-classroom-app-builder-non-activation-boundaries.md "Lovable API: blocked" "lovable api blocked"
if grep -Fq -- '--lovable-status' bin/chief-of-staff; then pass "chief-of-staff exposes --lovable-status"; else fail "chief-of-staff missing --lovable-status"; fi

section "3D Builder Workshop Agent (Program J1) Files"
for path in docs/3d-builder-workshop-agent-foundation.md docs/3d-builder-workshop-agent-non-activation-boundaries.md scripts/3d-builder-workshop-agent-status.sh tests/3d-builder-workshop-agent-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/3d-builder-workshop-agent-status.sh
grep -Fq -- '--3d-builder-status' bin/chief-of-staff && pass "chief-of-staff exposes --3d-builder-status" || fail "chief-of-staff missing --3d-builder-status"

section "Cursor Operating Modes and Proposal Governance Files"
for path in \
  docs/cursor-operating-modes-and-approval-gates.md \
  docs/teacher-workstation-domain-boundaries.md \
  docs/proposals/index.md \
  docs/proposals/README.md \
  scripts/cursor-operating-modes-status.sh \
  tests/cursor-operating-modes-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/cursor-operating-modes-status.sh
check_bash_syntax tests/cursor-operating-modes-status-test.sh
check_doc_contains docs/cursor-operating-modes-and-approval-gates.md "Maximum Autonomous Execution Mode" "operating modes doc autonomous execution"
check_doc_contains docs/teacher-workstation-domain-boundaries.md "Parent Communication Agents" "domain boundaries doc parent communication"
grep -Fq -- '--cursor-operating-modes-status' bin/chief-of-staff && pass "chief-of-staff exposes --cursor-operating-modes-status" || fail "chief-of-staff missing --cursor-operating-modes-status"

section "Curriculum Builder Metadata Contract Schemas (Programs A4–A7) Files"
for path in \
  docs/curriculum-builder-canonical-contract-schemas.md \
  docs/curriculum-resource-contract-schema.md \
  docs/curriculum-source-reference-contract-schema.md \
  docs/curriculum-review-state-contract-schema.md \
  docs/curriculum-lesson-link-contract-schema.md \
  docs/curriculum-builder-contract-boundaries.md \
  assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json \
  scripts/curriculum-builder-contract-schemas-status.sh \
  tests/curriculum-builder-contract-schemas-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-contract-schemas-status.sh
check_doc_contains docs/curriculum-builder-canonical-contract-schemas.md "complete_a4_a7_metadata_contracts" "contract schemas closure status"
grep -Fq -- '--curriculum-contracts-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-contracts-status" || fail "chief-of-staff missing --curriculum-contracts-status"

section "Curriculum Builder Registry v0.2 Manual Entry Dry-Run (CB-IMPL-1) Files"
for path in \
  docs/curriculum-builder-registry-v0-2-manual-entry-dry-run.md \
  docs/curriculum-builder-registry-v0-2-dry-run-boundaries.md \
  docs/curriculum-builder-registry-v0-2-validation-rules.md \
  assistant/curriculum-builder/samples/registry-v0-2-dry-run/example-candidate-valid.json \
  assistant/curriculum-builder/samples/registry-v0-2-dry-run/example-candidate-valid-002.json \
  scripts/curriculum-builder-registry-v0-2-dry-run.sh \
  scripts/curriculum-builder-registry-v0-2-status.sh \
  tests/curriculum-builder-registry-v0-2-dry-run-test.sh \
  tests/curriculum-builder-registry-v0-2-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-registry-v0-2-dry-run.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-status.sh
check_bash_syntax tests/curriculum-builder-registry-v0-2-dry-run-test.sh
check_bash_syntax tests/curriculum-builder-registry-v0-2-status-test.sh
check_doc_contains docs/curriculum-builder-registry-v0-2-manual-entry-dry-run.md "complete_cb_impl_1_dry_run" "registry v0.2 dry-run closure status"
grep -Fq -- '--curriculum-registry-dry-run-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-dry-run-status" || fail "chief-of-staff missing --curriculum-registry-dry-run-status"

section "Curriculum Builder Registry v0.2 Local Foundation Lane (CB-IMPL-2–4) Files"
for path in \
  docs/curriculum-builder-registry-v0-2-local-records-foundation.md \
  docs/curriculum-builder-registry-v0-2-record-boundaries.md \
  docs/curriculum-builder-registry-v0-2-renderer-foundation.md \
  docs/curriculum-builder-registry-v0-2-retrieval-hooks-foundation.md \
  docs/curriculum-builder-registry-v0-2-lane-closure.md \
  assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json \
  scripts/curriculum-builder-registry-v0-2-local-records-validate.sh \
  scripts/curriculum-builder-registry-v0-2-local-records-status.sh \
  scripts/curriculum-builder-registry-v0-2-render-preview.sh \
  scripts/curriculum-builder-registry-v0-2-renderer-status.sh \
  scripts/curriculum-builder-registry-v0-2-retrieval-check.sh \
  scripts/curriculum-builder-registry-v0-2-retrieval-status.sh \
  tests/curriculum-builder-registry-v0-2-local-records-test.sh \
  tests/curriculum-builder-registry-v0-2-renderer-test.sh \
  tests/curriculum-builder-registry-v0-2-retrieval-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-registry-v0-2-local-records-validate.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-local-records-status.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-render-preview.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-renderer-status.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-retrieval-check.sh
check_bash_syntax scripts/curriculum-builder-registry-v0-2-retrieval-status.sh
check_doc_contains docs/curriculum-builder-registry-v0-2-lane-closure.md "complete_cb_impl_2_3_4_local_foundation_lane" "lane closure status"
grep -Fq -- '--curriculum-registry-records-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-records-status" || fail "chief-of-staff missing --curriculum-registry-records-status"
grep -Fq -- '--curriculum-registry-renderer-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-renderer-status" || fail "chief-of-staff missing --curriculum-registry-renderer-status"
grep -Fq -- '--curriculum-registry-retrieval-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-retrieval-status" || fail "chief-of-staff missing --curriculum-registry-retrieval-status"

section "Autonomous Build Engine Governance Files"
for path in \
  docs/cursor-autonomous-build-engine.md \
  docs/cursor-autonomous-build-engine-sprint-queue-template.md \
  docs/cursor-autonomous-build-engine-level-2-batch-playbook.md \
  docs/mac-workstation-e1-vs-wallpaper-lane-map.md \
  docs/curriculum-builder-contract-activation-checklist-owen.md \
  docs/curriculum-builder-registry-expected-warns.md \
  docs/whole-system-master-roadmap-build-state-report.md \
  scripts/autonomous-build-engine-status.sh \
  tests/autonomous-build-engine-status-test.sh \
  tests/lane-review-hardening-guardrails-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/autonomous-build-engine-status.sh
check_bash_syntax tests/autonomous-build-engine-status-test.sh
check_bash_syntax tests/lane-review-hardening-guardrails-test.sh
check_doc_contains docs/cursor-autonomous-build-engine.md "complete_autonomous_build_engine_governance" "autonomous build engine closure"
grep -Fq -- '--autonomous-build-engine-status' bin/chief-of-staff && pass "chief-of-staff exposes --autonomous-build-engine-status" || fail "chief-of-staff missing --autonomous-build-engine-status"

section "Governance Lane Aggregate Status Files"
for path in \
  scripts/governance-lane-status.sh \
  tests/governance-lane-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/governance-lane-status.sh
check_bash_syntax tests/governance-lane-status-test.sh
grep -Fq -- '--governance-lane-status' bin/chief-of-staff && pass "chief-of-staff exposes --governance-lane-status" || fail "chief-of-staff missing --governance-lane-status"

section "Workstation Ops Lane Aggregate Status Files"
for path in \
  scripts/workstation-ops-lane-status.sh \
  tests/workstation-ops-lane-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/workstation-ops-lane-status.sh
check_bash_syntax tests/workstation-ops-lane-status-test.sh
grep -Fq -- '--workstation-ops-lane-status' bin/chief-of-staff && pass "chief-of-staff exposes --workstation-ops-lane-status" || fail "chief-of-staff missing --workstation-ops-lane-status"

section "Backlog Non-Mutation Guardrail Tests"
check_required_file tests/backlog-non-mutation-guardrails-test.sh
check_bash_syntax tests/backlog-non-mutation-guardrails-test.sh

section "Curriculum Builder Production Registry Workflow Planning Files"
for path in \
  docs/curriculum-builder-production-registry-workflow-planning-brief.md \
  scripts/curriculum-builder-production-registry-planning-status.sh \
  tests/curriculum-builder-production-registry-planning-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-production-registry-planning-status.sh
check_bash_syntax tests/curriculum-builder-production-registry-planning-status-test.sh
check_doc_contains docs/curriculum-builder-production-registry-workflow-planning-brief.md "complete_production_registry_planning_brief" "production registry planning brief closure status"
grep -Fq -- '--curriculum-production-registry-planning-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-production-registry-planning-status" || fail "chief-of-staff missing --curriculum-production-registry-planning-status"

section "Owen Production Registry Checklist Tracker Files"
for path in \
  docs/curriculum-builder-production-registry-owen-checklist-tracker.md \
  scripts/curriculum-builder-production-registry-owen-checklist-status.sh \
  tests/curriculum-builder-production-registry-owen-checklist-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-production-registry-owen-checklist-status.sh
check_bash_syntax tests/curriculum-builder-production-registry-owen-checklist-status-test.sh
check_doc_contains docs/curriculum-builder-production-registry-owen-checklist-tracker.md "not_complete_awaiting_owen" "owen checklist tracker closure"
grep -Fq -- '--curriculum-production-registry-owen-checklist-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-production-registry-owen-checklist-status" || fail "chief-of-staff missing --curriculum-production-registry-owen-checklist-status"

section "Production Registry Governance Foundation Files"
for path in \
  docs/curriculum-builder-production-registry-governance-foundation.md \
  docs/curriculum-builder-production-registry-path-options.md \
  docs/curriculum-builder-production-registry-review-state-model.md \
  docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md \
  docs/curriculum-builder-local-first-storage-reference-model.md \
  docs/curriculum-builder-production-registry-owen-decision-worksheet.md \
  docs/curriculum-builder-production-registry-post-decision-implementation-map.md \
  docs/curriculum-builder-metadata-pilot-planning-boundary.md \
  docs/curriculum-builder-manual-metadata-boundary.md \
  assistant/curriculum-builder/registry/candidate-v0-2-production/README.md \
  assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel \
  scripts/curriculum-builder-production-registry-governance-status.sh \
  tests/curriculum-builder-production-registry-governance-status-test.sh \
  tests/curriculum-builder-production-registry-governance-guardrails-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-production-registry-governance-status.sh
check_bash_syntax tests/curriculum-builder-production-registry-governance-status-test.sh
check_bash_syntax tests/curriculum-builder-production-registry-governance-guardrails-test.sh
check_doc_contains docs/curriculum-builder-production-registry-governance-foundation.md "complete_cb_prod_gov_foundation" "governance foundation closure"
check_doc_contains docs/curriculum-builder-production-registry-owen-decision-worksheet.md "Documenting an option does not approve it" "decision worksheet non-approval"
grep -Fq -- '--curriculum-production-registry-governance-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-production-registry-governance-status" || fail "chief-of-staff missing --curriculum-production-registry-governance-status"

section "Curriculum Source Readiness Foundation Files"
for path in \
  docs/curriculum-source-readiness-and-intake-boundary-plan.md \
  docs/curriculum-source-readiness-fake-inventory-index.md \
  assistant/curriculum-builder/samples/curriculum-source-readiness/curriculum-source-metadata.schema.json \
  assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json \
  scripts/curriculum-source-readiness-validate.sh \
  scripts/curriculum-source-readiness-status.sh \
  tests/curriculum-source-readiness-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-source-readiness-validate.sh
check_bash_syntax scripts/curriculum-source-readiness-status.sh
check_bash_syntax tests/curriculum-source-readiness-status-test.sh
check_doc_contains docs/curriculum-source-readiness-and-intake-boundary-plan.md "complete_curriculum_source_readiness_plan" "curriculum source readiness closure"
grep -Fq -- '--curriculum-source-readiness-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-source-readiness-status" || fail "chief-of-staff missing --curriculum-source-readiness-status"

section "Curriculum Builder Registry Hardening Bundle Files"
for path in \
  docs/curriculum-builder-registry-authority-map.md \
  scripts/curriculum-builder-registry-lane-status.sh \
  scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh \
  tests/curriculum-builder-registry-lane-status-test.sh \
  tests/curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-builder-registry-lane-status.sh
check_bash_syntax scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh
check_bash_syntax tests/curriculum-builder-registry-lane-status-test.sh
check_bash_syntax tests/curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh
check_doc_contains docs/curriculum-builder-registry-authority-map.md "complete_registry_authority_map" "registry authority map closure"
grep -Fq -- '--curriculum-registry-lane-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-lane-status" || fail "chief-of-staff missing --curriculum-registry-lane-status"
grep -Fq -- '--curriculum-registry-a4-a7-fixture-schema-status' bin/chief-of-staff && pass "chief-of-staff exposes --curriculum-registry-a4-a7-fixture-schema-status" || fail "chief-of-staff missing --curriculum-registry-a4-a7-fixture-schema-status"

section "Curriculum Registry–Contract Binding v0 Foundation Files"
for path in \
  docs/curriculum-binding-v0.md \
  assistant/curriculum-builder/binding/v0/README.md \
  assistant/curriculum-builder/binding/v0/binding-manifest.json \
  scripts/curriculum-binding-v0-validator.sh \
  scripts/curriculum-binding-v0-lookup.sh \
  scripts/curriculum-binding-v0-status.sh \
  tests/curriculum-binding-v0-test.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/curriculum-binding-v0-validator.sh
check_bash_syntax scripts/curriculum-binding-v0-lookup.sh
check_bash_syntax scripts/curriculum-binding-v0-status.sh
check_bash_syntax tests/curriculum-binding-v0-test.sh

section "Renderer Foundation v1 Files"
for path in \
  docs/renderer-v1-foundation.md \
  docs/renderer-input-readiness-v0.md \
  docs/renderer-foundation-v0.md \
  assistant/renderer/v0/renderer-manifest.json \
  assistant/renderer/v0/README.md \
  assistant/renderer-foundation/v0/sample-renderer-manifests.json \
  scripts/renderer-foundation-status.sh \
  scripts/renderer-foundation-v0-validator.sh \
  scripts/renderer-input-readiness-v0-validator.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/renderer-foundation-status.sh
check_bash_syntax scripts/renderer-foundation-v0-validator.sh
check_bash_syntax scripts/renderer-input-readiness-v0-validator.sh

section "Teacher App Designer / Canvas LLM Foundation Files"
for path in \
  docs/teacher-app-designer-canvas-llm-plan.md \
  docs/canvas-llm-safety-and-approval-contract.md \
  docs/canvas-llm-local-first-drive-first-architecture.md \
  docs/canvas-llm-placeholder-schema.md \
  docs/canvas-llm-approval-and-export-states.md \
  docs/canvas-llm-placeholder-schema-maintenance.md \
  docs/canvas-llm-manual-export-package-plan.md \
  docs/canvas-llm-manual-export-package-shapes.md \
  docs/canvas-llm-manual-export-package-maintenance.md \
  docs/canvas-llm-manual-export-review-checklist.md \
  docs/canvas-llm-manual-export-review-checklist-maintenance.md \
  docs/canvas-llm-manual-completion-status-placeholder-plan.md \
  docs/canvas-llm-manual-completion-status-placeholder-maintenance.md \
  docs/canvas-llm-weekly-export-bundle-placeholder-plan.md \
  docs/canvas-llm-weekly-export-bundle-placeholder-maintenance.md \
  docs/canvas-llm-planning-foundation-capstone.md \
  docs/canvas-llm-planning-foundation-capstone-maintenance.md \
  docs/canvas-llm-planning-foundation-closure-audit.md \
  docs/canvas-llm-planning-foundation-closure-audit-maintenance.md \
  docs/canvas-llm-planning-foundation-index.md \
  docs/canvas-llm-planning-foundation-freeze.md \
  docs/canvas-llm-frozen-foundation-handoff-snapshot.md \
  docs/canvas-llm-frozen-foundation-handoff-snapshot-maintenance.md \
  docs/canvas-llm-stop-marker-curriculum-builder-return.md \
  docs/canvas-llm-stop-marker-curriculum-builder-return-maintenance.md \
  docs/canvas-llm-section-completion-audit.md \
  scripts/teacher-app-designer-canvas-llm-status.sh; do
  check_required_file "${path}"
done
check_bash_syntax scripts/teacher-app-designer-canvas-llm-status.sh

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
  .cursor/rules/teacher-ai-workstation-senior-engineer.mdc \
  docs/cursor-workflow-operating-system.md \
  docs/cursor-prompt-template.md \
  docs/cursor-pr-review-checklist.md \
  docs/implementation-approval-gate.md \
  docs/engineering-constitution.md \
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
check_bash_syntax "scripts/teacher-planning-command-detail-status.sh"
check_bash_syntax "scripts/lesson-review-command-detail-status.sh"
check_bash_syntax "scripts/review-notes-command-detail-status.sh"
check_bash_syntax "scripts/document-indexing-command-detail-status.sh"
check_bash_syntax "scripts/teacher-workflow-command-detail-summary-status.sh"
check_bash_syntax "scripts/teacher-workflow-safe-output-examples-status.sh"
check_bash_syntax "scripts/teacher-workflow-safe-output-checker-status.sh"
check_bash_syntax "scripts/teacher-workflow-output-examples-completion-status.sh"
check_bash_syntax "scripts/lesson-planning-template-readiness-status.sh"
check_bash_syntax "scripts/curriculum-builder-foundation-status.sh"
check_bash_syntax "scripts/renderer-foundation-status.sh"
check_bash_syntax "scripts/renderer-foundation-v0-validator.sh"
check_bash_syntax "scripts/renderer-input-readiness-v0-validator.sh"
check_bash_syntax "scripts/teacher-app-designer-canvas-llm-status.sh"
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
check_bash_syntax "scripts/cursor-operating-modes-status.sh"
check_bash_syntax "scripts/curriculum-builder-contract-schemas-status.sh"
check_bash_syntax "scripts/phase-1-status.sh"
check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/verify-phase-0e.sh"
check_bash_syntax "scripts/phase-0e-summary.sh"
check_python_syntax_optional "scripts/image-review-status.py"
check_json_syntax_optional "configs/spotify-vibe-playlists.json"

phase_1_audit_doc="docs/phase-1-chief-of-staff-status-audit.md"

section "Repo-Wide Parked Tracks Status Map Checks"

check_doc_contains "${phase_1_audit_doc}" "Repo-Wide Parked Tracks and Active Status Map" "Repo-Wide Parked Tracks and Active Status Map section"
check_doc_contains "${phase_1_audit_doc}" "Curriculum Builder parked" "Curriculum Builder parked"
check_doc_contains "${phase_1_audit_doc}" "Lesson-planning placeholder readiness parked" "Lesson-planning placeholder readiness parked"
check_doc_contains "${phase_1_audit_doc}" "foundation complete for now; live curator not started" "Appearance & Vibe foundation complete; live curator not started"
check_doc_contains "${phase_1_audit_doc}" "Dashboard remains a read-only status surface" "dashboard read-only status surface"
check_doc_contains "${phase_1_audit_doc}" "Current source-of-truth commands" "current source-of-truth commands"
check_doc_contains "${phase_1_audit_doc}" "Do not restart parked work" "do not restart parked work"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

section "Recommendation"
if (( CRITICAL_BLOCKER > 0 )); then
  printf 'Fix critical Chief of Staff CLI, memory, intake, or script problems before the next build PR.\n'
else
  printf 'Next recommended posture: lesson-planning placeholder readiness is complete for now; follow-ons are documentation/status-only unless explicitly approved; static template schema planning remains planning-only and must not activate schema/validator behavior.\n'
fi

if (( COMPARE_0E == 1 && CRITICAL_BLOCKER == 0 )); then
  printf '\nPhase 0E complete; Phase 1 readiness audit complete.\n'
fi

if (( FAIL_COUNT > 0 )); then
  exit 1
fi

exit 0
