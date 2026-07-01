#!/usr/bin/env bash
# Read-only Curriculum Builder foundation status only. No network calls, scanning, or file indexing.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

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

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_doc_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "${file}" ]]; then
    fail "${file} must mention ${label}"
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
    fail "cannot syntax check missing file: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_help_contains() {
  local flag="$1"
  if bin/chief-of-staff --help | grep -F -- "${flag}" >/dev/null; then
    pass "help contains ${flag}"
  else
    fail "help must contain ${flag}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

plan_doc="docs/curriculum-builder-local-first-foundation-plan.md"
storage_strategy_doc="docs/curriculum-source-storage-strategy.md"
registry_plan_doc="docs/curriculum-resource-registry-plan.md"
planning_stack_summary_doc="docs/curriculum-builder-planning-stack-summary.md"
next_phase_decision_doc="docs/curriculum-builder-next-phase-decision.md"
decision_intake_template_doc="docs/curriculum-builder-decision-intake-template.md"
approval_gate_doc="docs/curriculum-builder-approval-gate.md"
planning_closeout_doc="docs/curriculum-builder-planning-closeout.md"
maintainer_handoff_doc="docs/curriculum-builder-maintainer-handoff.md"
future_pr_checklist_doc="docs/curriculum-builder-future-pr-checklist.md"
canonical_planning_index_doc="docs/curriculum-builder-canonical-planning-index.md"
next_stage_readiness_audit_doc="docs/curriculum-builder-next-stage-readiness-audit.md"
manual_registry_schema_plan_doc="docs/curriculum-builder-manual-registry-schema-plan.md"
dashboard_doc="docs/chief-of-staff-dashboard.md"
dashboard_section_summary_doc="docs/dashboard-section-summary-polish.md"
phase_1_audit_doc="docs/phase-1-chief-of-staff-status-audit.md"

section "Curriculum Builder Local-First Foundation Plan"
cat <<'EOF'
Status: documentation/status only
Implementation: no
Schema file: no
Validator: no
Document scanning: no
Folder scanning: no
File indexing: no
OCR: no
Embeddings: no
Vector database: no
Lesson generation: no
Student data: no
Network calls: no
APIs: no
OAuth: no
Automation: no
Live integrations: no
Background jobs: no
Scheduler: no
EOF

section "Foundation Plan Doc Checks"

check_file "${plan_doc}"

if [[ -f "${plan_doc}" ]]; then
  check_doc_contains "${plan_doc}" "Curriculum Builder Local-First Foundation Plan" "Curriculum Builder Local-First Foundation Plan"
  check_doc_contains "${plan_doc}" "Google Drive" "Google Drive storage source"
  check_doc_contains "${plan_doc}" "NAS" "NAS storage source"
  check_doc_contains "${plan_doc}" "iCloud" "iCloud storage source"
  check_doc_contains "${plan_doc}" "local folders" "local folders storage source"
  check_doc_contains "${plan_doc}" "metadata" "metadata storage model"
  check_doc_contains "${plan_doc}" "references" "source references model"
  check_doc_contains "${plan_doc}" "no document scanning" "no document scanning boundary"
  check_doc_contains "${plan_doc}" "no folder scanning" "no folder scanning boundary"
  check_doc_contains "${plan_doc}" "no file indexing" "no file indexing boundary"
  check_doc_contains "${plan_doc}" "no OCR" "no OCR boundary"
  check_doc_contains "${plan_doc}" "no embeddings" "no embeddings boundary"
  check_doc_contains "${plan_doc}" "no vector database" "no vector database boundary"
  check_doc_contains "${plan_doc}" "no lesson generation" "no lesson generation boundary"
  check_doc_contains "${plan_doc}" "no student data" "no student data boundary"
  check_doc_contains "${plan_doc}" "no network calls" "no network calls boundary"
  check_doc_contains "${plan_doc}" "Chief of Staff" "Chief of Staff role"
  check_doc_contains "${plan_doc}" "status/orchestration/reference layer" "Chief of Staff status/orchestration/reference layer"
  check_doc_contains "${plan_doc}" "does not own curriculum files" "Chief of Staff does not own curriculum files"
  check_doc_contains "${plan_doc}" "lesson-planning workflows may reference the registry" "lesson-planning registry reference planning"
  check_doc_contains "${plan_doc}" "not duplicate every raw curriculum file" "no paid duplicate raw file copies"
fi

section "Curriculum Source Storage Strategy Doc Checks"

check_file "${storage_strategy_doc}"

if [[ -f "${storage_strategy_doc}" ]]; then
  check_doc_contains "${storage_strategy_doc}" "Curriculum Source Storage Strategy" "Curriculum Source Storage Strategy"
  check_doc_contains "${storage_strategy_doc}" "Google Drive" "Google Drive storage source"
  check_doc_contains "${storage_strategy_doc}" "NAS" "NAS storage source"
  check_doc_contains "${storage_strategy_doc}" "iCloud" "iCloud storage source"
  check_doc_contains "${storage_strategy_doc}" "local folders" "local folders storage source"
  check_doc_contains "${storage_strategy_doc}" "metadata" "metadata storage model"
  check_doc_contains "${storage_strategy_doc}" "references" "source references model"
  check_doc_contains "${storage_strategy_doc}" "source-reference model" "source-reference model"
  check_doc_contains "${storage_strategy_doc}" "Teacher Workstation" "Teacher Workstation role"
  check_doc_contains "${storage_strategy_doc}" "Chief of Staff" "Chief of Staff role"
  check_doc_contains "${storage_strategy_doc}" "does not own raw curriculum files" "Chief of Staff does not own raw curriculum files"
  check_doc_contains "${storage_strategy_doc}" "no document scanning" "no document scanning boundary"
  check_doc_contains "${storage_strategy_doc}" "no folder scanning" "no folder scanning boundary"
  check_doc_contains "${storage_strategy_doc}" "no file indexing" "no file indexing boundary"
  check_doc_contains "${storage_strategy_doc}" "no OCR" "no OCR boundary"
  check_doc_contains "${storage_strategy_doc}" "no embeddings" "no embeddings boundary"
  check_doc_contains "${storage_strategy_doc}" "no vector database" "no vector database boundary"
  check_doc_contains "${storage_strategy_doc}" "no lesson generation" "no lesson generation boundary"
  check_doc_contains "${storage_strategy_doc}" "no student data" "no student data boundary"
  check_doc_contains "${storage_strategy_doc}" "no network calls" "no network calls boundary"
  check_doc_contains "${storage_strategy_doc}" "no APIs" "no APIs boundary"
  check_doc_contains "${storage_strategy_doc}" "no OAuth" "no OAuth boundary"
  check_doc_contains "${storage_strategy_doc}" "no automation" "no automation boundary"
fi

section "Curriculum Resource Registry Plan Doc Checks"

check_file "${registry_plan_doc}"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "metadata-only" "metadata-only registry concept"
  check_doc_contains "${registry_plan_doc}" "Curriculum Resource Registry" "Curriculum Resource Registry"
  check_doc_contains "${registry_plan_doc}" "Google Drive" "Google Drive storage source"
  check_doc_contains "${registry_plan_doc}" "NAS" "NAS storage source"
  check_doc_contains "${registry_plan_doc}" "iCloud" "iCloud storage source"
  check_doc_contains "${registry_plan_doc}" "local folders" "local folders storage source"
  check_doc_contains "${registry_plan_doc}" "Teacher Workstation" "Teacher Workstation role"
  check_doc_contains "${registry_plan_doc}" "Chief of Staff" "Chief of Staff role"
  check_doc_contains "${registry_plan_doc}" "does not own raw curriculum files" "Chief of Staff does not own raw curriculum files"
  check_doc_contains "${registry_plan_doc}" "source_system" "source_system field"
  check_doc_contains "${registry_plan_doc}" "source_path_or_url" "source_path_or_url field"
  check_doc_contains "${registry_plan_doc}" "resource_type" "resource_type field"
  check_doc_contains "${registry_plan_doc}" "teacher_only" "teacher_only field"
  check_doc_contains "${registry_plan_doc}" "student_facing" "student_facing field"
  check_doc_contains "${registry_plan_doc}" "review_status" "review_status field"
  check_doc_contains "${registry_plan_doc}" "approval_status" "approval_status field"
  check_doc_contains "${registry_plan_doc}" "content_hash" "content_hash field"
  check_doc_contains "${registry_plan_doc}" "planning only" "planning only status marker"
  check_doc_contains "${registry_plan_doc}" "no active schema" "no active schema boundary"
  check_doc_contains "${registry_plan_doc}" "no active database" "no active database boundary"
  check_doc_contains "${registry_plan_doc}" "no document scanning" "no document scanning boundary"
  check_doc_contains "${registry_plan_doc}" "no folder scanning" "no folder scanning boundary"
  check_doc_contains "${registry_plan_doc}" "no file indexing" "no file indexing boundary"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary"
  check_doc_contains "${registry_plan_doc}" "no vector database" "no vector database boundary"
  check_doc_contains "${registry_plan_doc}" "no lesson generation" "no lesson generation boundary"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary"
  check_doc_contains "${registry_plan_doc}" "no APIs" "no APIs boundary"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary"
  check_doc_contains "${registry_plan_doc}" "no automation" "no automation boundary"
fi

section "Curriculum Registry Static Field Inventory Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Static Registry Field Inventory Note" "Static Registry Field Inventory Note"
  check_doc_contains "${registry_plan_doc}" "Field Group Rules" "Field Group Rules"
  check_doc_contains "${registry_plan_doc}" "Future Validation Expectations" "Future Validation Expectations"
  check_doc_contains "${registry_plan_doc}" "Explicit Non-Activation" "Explicit Non-Activation subsection"
  check_doc_contains "${registry_plan_doc}" "planning only" "planning only activation status"
  check_doc_contains "${registry_plan_doc}" "contains_student_data" "contains_student_data field"
  check_doc_contains "${registry_plan_doc}" "safety_status" "safety_status field"
  check_doc_contains "${registry_plan_doc}" "hash_algorithm" "hash_algorithm field"
  check_doc_contains "${registry_plan_doc}" "display_title" "display_title field"
  check_doc_contains "${registry_plan_doc}" "no database tables" "no database tables boundary"
  check_doc_contains "${registry_plan_doc}" "no registry data files" "no registry data files boundary"
  check_doc_contains "${registry_plan_doc}" "no validators" "no validators boundary"
  check_doc_contains "${registry_plan_doc}" "no importers" "no importers boundary"
  check_doc_contains "${registry_plan_doc}" "no scanners" "no scanners boundary"
  check_doc_contains "${registry_plan_doc}" "no crawlers" "no crawlers boundary"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary"
  check_doc_contains "${registry_plan_doc}" "no hashing" "no hashing boundary"
  check_doc_contains "${registry_plan_doc}" "no vector search" "no vector search boundary"
  check_doc_contains "${registry_plan_doc}" "answer_key" "answer_key field in static inventory"
  check_doc_contains "${registry_plan_doc}" "assessment_related" "assessment_related field in static inventory"
  check_doc_contains "${registry_plan_doc}" "linked_pacing_item" "linked_pacing_item field in static inventory"
  check_doc_contains "${registry_plan_doc}" "linked_lesson_template" "linked_lesson_template field in static inventory"
  check_doc_contains "${registry_plan_doc}" "linked_canvas_item" "linked_canvas_item field in static inventory"
fi

section "Curriculum Registry Safety Status Values Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Static Registry Safety and Status Values Note" "Static Registry Safety and Status Values Note"
  check_doc_contains "${registry_plan_doc}" "Safety Transition Rules" "Safety Transition Rules"
  check_doc_contains "${registry_plan_doc}" "Teacher-Only and Student-Facing Boundary" "Teacher-Only and Student-Facing Boundary"
  check_doc_contains "${registry_plan_doc}" "Status Values Are Not Workflows" "Status Values Are Not Workflows"
  check_doc_contains "${registry_plan_doc}" "teacher_only" "teacher_only safety field"
  check_doc_contains "${registry_plan_doc}" "student_facing" "student_facing safety field"
  check_doc_contains "${registry_plan_doc}" "answer_key" "answer_key safety field"
  check_doc_contains "${registry_plan_doc}" "assessment_related" "assessment_related safety field"
  check_doc_contains "${registry_plan_doc}" "contains_student_data" "contains_student_data safety field"
  check_doc_contains "${registry_plan_doc}" "external_sharing_allowed" "external_sharing_allowed safety field"
  check_doc_contains "${registry_plan_doc}" "review_status" "review_status safety field"
  check_doc_contains "${registry_plan_doc}" "approval_status" "approval_status safety field"
  check_doc_contains "${registry_plan_doc}" "usage_status" "usage_status safety field"
  check_doc_contains "${registry_plan_doc}" "metadata_status" "metadata_status safety field"
  check_doc_contains "${registry_plan_doc}" "safety_status" "safety_status safety field"
  check_doc_contains "${registry_plan_doc}" "activation_status" "activation_status safety field"
  check_doc_contains "${registry_plan_doc}" "not_reviewed" "not_reviewed status value"
  check_doc_contains "${registry_plan_doc}" "metadata_only" "metadata_only status value"
  check_doc_contains "${registry_plan_doc}" "teacher_reviewed" "teacher_reviewed status value"
  check_doc_contains "${registry_plan_doc}" "approved_for_planning" "approved_for_planning status value"
  check_doc_contains "${registry_plan_doc}" "approved_student_facing" "approved_student_facing status value"
  check_doc_contains "${registry_plan_doc}" "restricted" "restricted status value"
  check_doc_contains "${registry_plan_doc}" "blocked" "blocked status value"
  check_doc_contains "${registry_plan_doc}" "retired" "retired status value"
  check_doc_contains "${registry_plan_doc}" "do_not_use" "do_not_use status value"
  check_doc_contains "${registry_plan_doc}" "planning_only" "planning_only activation value"
  check_doc_contains "${registry_plan_doc}" "no active schema" "no active schema boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no database tables" "no database tables boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no registry data files" "no registry data files boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no validators" "no validators boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no review workflows" "no review workflows boundary"
  check_doc_contains "${registry_plan_doc}" "no approval workflows" "no approval workflows boundary"
  check_doc_contains "${registry_plan_doc}" "no real review notes" "no real review notes boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no automated safety classifiers" "no automated safety classifiers boundary"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary in safety note"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary in safety note"
fi

section "Curriculum Registry Manual Entry Workflow Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Manual-First Registry Entry Workflow Note" "Manual-First Registry Entry Workflow Note"
  check_doc_contains "${registry_plan_doc}" "Manual Entry Stages" "Manual Entry Stages"
  check_doc_contains "${registry_plan_doc}" "Manual Entry Field Order" "Manual Entry Field Order"
  check_doc_contains "${registry_plan_doc}" "Conservative Defaults" "Conservative Defaults"
  check_doc_contains "${registry_plan_doc}" "Manual-First Rules" "Manual-First Rules"
  check_doc_contains "${registry_plan_doc}" "Future Human Review Expectations" "Future Human Review Expectations"
  check_doc_contains "${registry_plan_doc}" "manually recorded metadata references" "manually recorded metadata references"
  check_doc_contains "${registry_plan_doc}" "source_label" "source_label manual entry field"
  check_doc_contains "${registry_plan_doc}" "No scanning" "no scanning boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no crawling" "no crawling boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no automatic discovery" "no automatic discovery boundary"
  check_doc_contains "${registry_plan_doc}" "No API calls" "no API calls boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no parsing" "no parsing boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no active review workflow" "no active review workflow boundary"
  check_doc_contains "${registry_plan_doc}" "no active approval workflow" "no active approval workflow boundary"
  check_doc_contains "${registry_plan_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no live integrations" "no live integrations boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "not_approved" "not_approved default status"
  check_doc_contains "${registry_plan_doc}" "Teacher Workstation" "Teacher Workstation manual entry role"
  check_doc_contains "${registry_plan_doc}" "does not own raw curriculum files" "Chief of Staff does not own raw curriculum files in manual workflow"
  check_doc_contains "${registry_plan_doc}" "source_system" "source_system manual entry field"
  check_doc_contains "${registry_plan_doc}" "source_path_or_url" "source_path_or_url manual entry field"
  check_doc_contains "${registry_plan_doc}" "teacher_only" "teacher_only manual entry field"
  check_doc_contains "${registry_plan_doc}" "student_facing" "student_facing manual entry field"
  check_doc_contains "${registry_plan_doc}" "answer_key" "answer_key manual entry field"
  check_doc_contains "${registry_plan_doc}" "assessment_related" "assessment_related manual entry field"
  check_doc_contains "${registry_plan_doc}" "contains_student_data" "contains_student_data manual entry field"
  check_doc_contains "${registry_plan_doc}" "review_status" "review_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "approval_status" "approval_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "usage_status" "usage_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "metadata_status" "metadata_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "safety_status" "safety_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "activation_status" "activation_status manual entry field"
  check_doc_contains "${registry_plan_doc}" "not_reviewed" "not_reviewed manual entry default"
  check_doc_contains "${registry_plan_doc}" "planning_only" "planning_only manual entry default"
  check_doc_contains "${registry_plan_doc}" "Chief of Staff" "Chief of Staff manual entry role"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary in manual workflow"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary in manual workflow"
fi

section "Curriculum Registry Metadata Backup Export Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Metadata-Only Backup and Export Planning Note" "Metadata-Only Backup and Export Planning Note"
  check_doc_contains "${registry_plan_doc}" "Metadata-Only Scope" "Metadata-Only Scope"
  check_doc_contains "${registry_plan_doc}" "Explicitly Out of Scope" "Explicitly Out of Scope"
  check_doc_contains "${registry_plan_doc}" "Future Export Shape Options" "Future Export Shape Options"
  check_doc_contains "${registry_plan_doc}" "Future Backup Destinations" "Future Backup Destinations"
  check_doc_contains "${registry_plan_doc}" "Future Export Safety Rules" "Future Export Safety Rules"
  check_doc_contains "${registry_plan_doc}" "metadata only" "metadata only backup scope"
  check_doc_contains "${registry_plan_doc}" "source references" "source references backup scope"
  check_doc_contains "${registry_plan_doc}" "no raw files" "no raw files boundary"
  check_doc_contains "${registry_plan_doc}" "no backup scripts" "no backup scripts boundary"
  check_doc_contains "${registry_plan_doc}" "no export scripts" "no export scripts boundary"
  check_doc_contains "${registry_plan_doc}" "no archive bundles" "no archive bundles boundary"
  check_doc_contains "${registry_plan_doc}" "no file caches" "no file caches boundary"
  check_doc_contains "${registry_plan_doc}" "no raw file copying" "no raw file copying boundary"
  check_doc_contains "${registry_plan_doc}" "no Drive mirroring" "no Drive mirroring boundary"
  check_doc_contains "${registry_plan_doc}" "no NAS mirroring" "no NAS mirroring boundary"
  check_doc_contains "${registry_plan_doc}" "no iCloud mirroring" "no iCloud mirroring boundary"
  check_doc_contains "${registry_plan_doc}" "no scanning" "no scanning boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no indexing" "no indexing boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in backup note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in backup note"
  check_doc_contains "${registry_plan_doc}" "Explicit Non-Activation" "Explicit Non-Activation in backup note"
  check_doc_contains "${registry_plan_doc}" "Google Drive" "Google Drive in backup note"
  check_doc_contains "${registry_plan_doc}" "NAS" "NAS in backup note"
  check_doc_contains "${registry_plan_doc}" "iCloud" "iCloud in backup note"
  check_doc_contains "${registry_plan_doc}" "local folders" "local folders in backup note"
  check_doc_contains "${registry_plan_doc}" "no hashing" "no hashing boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no APIs" "no APIs boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no automation" "no automation boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no background jobs" "no background jobs boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in backup note"
  check_doc_contains "${registry_plan_doc}" "no live integrations" "no live integrations boundary in backup note"
fi

section "Curriculum Registry Validator Planning Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Local Registry Validator Planning Note" "Local Registry Validator Planning Note"
  check_doc_contains "${registry_plan_doc}" "Future Validator Scope" "Future Validator Scope"
  check_doc_contains "${registry_plan_doc}" "Future Required Field Expectations" "Future Required Field Expectations"
  check_doc_contains "${registry_plan_doc}" "Future Allowed Value Checks" "Future Allowed Value Checks"
  check_doc_contains "${registry_plan_doc}" "Future Safety Consistency Checks" "Future Safety Consistency Checks"
  check_doc_contains "${registry_plan_doc}" "Future Reference Shape Checks" "Future Reference Shape Checks"
  check_doc_contains "${registry_plan_doc}" "Future PASS/WARN/FAIL Semantics" "Future PASS/WARN/FAIL Semantics"
  check_doc_contains "${registry_plan_doc}" "Validator Non-Goals" "Validator Non-Goals"
  check_doc_contains "${registry_plan_doc}" "required metadata fields" "required metadata fields validator scope"
  check_doc_contains "${registry_plan_doc}" "no active validator" "no active validator boundary"
  check_doc_contains "${registry_plan_doc}" "no registry data file" "no registry data file boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no new command" "no new command boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no dashboard checks" "no dashboard checks boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "**PASS**:" "future validator PASS semantics"
  check_doc_contains "${registry_plan_doc}" "**WARN**:" "future validator WARN semantics"
  check_doc_contains "${registry_plan_doc}" "**FAIL**:" "future validator FAIL semantics"
  check_doc_contains "${registry_plan_doc}" "active validators" "active validators non-activation marker"
  check_doc_contains "${registry_plan_doc}" "no active schema" "no active schema boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in validator note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in validator note"
  check_doc_contains "${registry_plan_doc}" "source_path_or_url" "source_path_or_url validator field"
  check_doc_contains "${registry_plan_doc}" "metadata_status" "metadata_status validator field"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no hashing" "no hashing boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no APIs" "no APIs boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no automation" "no automation boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in validator note"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary in validator note"
fi

section "Curriculum Registry Placeholder Metadata Shape Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Placeholder Metadata Shape Note" "Placeholder Metadata Shape Note"
  check_doc_contains "${registry_plan_doc}" "Placeholder Record Shape" "Placeholder Record Shape"
  check_doc_contains "${registry_plan_doc}" "Placeholder CSV Column Shape" "Placeholder CSV Column Shape"
  check_doc_contains "${registry_plan_doc}" "Placeholder Status Posture" "Placeholder Status Posture"
  check_doc_contains "${registry_plan_doc}" "Placeholder Safety Rules" "Placeholder Safety Rules"
  check_doc_contains "${registry_plan_doc}" "Future Implementation Guardrails" "Future Implementation Guardrails"
  check_doc_contains "${registry_plan_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in placeholder note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in placeholder note"
  check_doc_contains "${registry_plan_doc}" "Explicit Non-Activation" "Explicit Non-Activation in placeholder note"
  check_doc_contains "${registry_plan_doc}" "fake placeholder examples only" "fake placeholder examples only marker"
  check_doc_contains "${registry_plan_doc}" "placeholder-resource-001" "placeholder-resource-001 example id"
  check_doc_contains "${registry_plan_doc}" "placeholder://source/reference" "placeholder source reference example"
  check_doc_contains "${registry_plan_doc}" "manual_reference" "manual_reference placeholder source_system"
  check_doc_contains "${registry_plan_doc}" "planning_only" "planning_only placeholder status"
  check_doc_contains "${registry_plan_doc}" "not_reviewed" "not_reviewed placeholder status"
  check_doc_contains "${registry_plan_doc}" "not_approved" "not_approved placeholder status"
  check_doc_contains "${registry_plan_doc}" "metadata_status" "metadata_status placeholder field"
  check_doc_contains "${registry_plan_doc}" "safety_status" "safety_status placeholder field"
  check_doc_contains "${registry_plan_doc}" "activation_status" "activation_status placeholder field"
  check_doc_contains "${registry_plan_doc}" "contains_student_data" "contains_student_data placeholder field"
  check_doc_contains "${registry_plan_doc}" "student_facing" "student_facing placeholder field"
  check_doc_contains "${registry_plan_doc}" "teacher_only" "teacher_only placeholder field"
  check_doc_contains "${registry_plan_doc}" "source_path_or_url" "source_path_or_url placeholder field"
  check_doc_contains "${registry_plan_doc}" "resource_type" "resource_type placeholder field"
  check_doc_contains "${registry_plan_doc}" "not a schema" "not a schema boundary"
  check_doc_contains "${registry_plan_doc}" "not a registry data file" "not a registry data file boundary"
  check_doc_contains "${registry_plan_doc}" "not seed data" "not seed data boundary"
  check_doc_contains "${registry_plan_doc}" "not a real curriculum resource" "not a real curriculum resource boundary"
  check_doc_contains "${registry_plan_doc}" "no active schema" "no active schema boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no registry data files" "no registry data files boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no seed data" "no seed data boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no real curriculum resource records" "no real curriculum resource records boundary"
  check_doc_contains "${registry_plan_doc}" "no active validators" "no active validators boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no new commands" "no new commands boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no hashing" "no hashing boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no APIs" "no APIs boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no automation" "no automation boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in placeholder note"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary in placeholder note"
fi

section "Curriculum Registry Implementation Approval Gate Checks"

if [[ -f "${registry_plan_doc}" ]]; then
  check_doc_contains "${registry_plan_doc}" "Registry Implementation Approval Gate Note" "Registry Implementation Approval Gate Note"
  check_doc_contains "${registry_plan_doc}" "Implementation Requires Explicit Future Approval" "Implementation Requires Explicit Future Approval"
  check_doc_contains "${registry_plan_doc}" "Required Future PR Questions" "Required Future PR Questions"
  check_doc_contains "${registry_plan_doc}" "Approval Categories" "Approval Categories"
  check_doc_contains "${registry_plan_doc}" "Default Decision Rules" "Default Decision Rules"
  check_doc_contains "${registry_plan_doc}" "Future Readiness Checklist" "Future Readiness Checklist"
  check_doc_contains "${registry_plan_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in approval gate note"
  check_doc_contains "${registry_plan_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in approval gate note"
  check_doc_contains "${registry_plan_doc}" "Explicit Non-Activation" "Explicit Non-Activation in approval gate note"
  check_doc_contains "${registry_plan_doc}" "explicit approval" "explicit approval gate marker"
  check_doc_contains "${registry_plan_doc}" "docs_only_approved" "docs_only_approved approval category"
  check_doc_contains "${registry_plan_doc}" "schema_implementation_requested" "schema_implementation_requested approval category"
  check_doc_contains "${registry_plan_doc}" "metadata_file_requested" "metadata_file_requested approval category"
  check_doc_contains "${registry_plan_doc}" "fake_placeholder_records_requested" "fake_placeholder_records_requested approval category"
  check_doc_contains "${registry_plan_doc}" "real_registry_records_requested" "real_registry_records_requested approval category"
  check_doc_contains "${registry_plan_doc}" "validator_requested" "validator_requested approval category"
  check_doc_contains "${registry_plan_doc}" "command_requested" "command_requested approval category"
  check_doc_contains "${registry_plan_doc}" "export_requested" "export_requested approval category"
  check_doc_contains "${registry_plan_doc}" "backup_requested" "backup_requested approval category"
  check_doc_contains "${registry_plan_doc}" "connector_requested" "connector_requested approval category"
  check_doc_contains "${registry_plan_doc}" "lesson_planning_reference_requested" "lesson_planning_reference_requested approval category"
  check_doc_contains "${registry_plan_doc}" "generation_requested" "generation_requested approval category"
  check_doc_contains "${registry_plan_doc}" "blocked_without_explicit_approval" "blocked_without_explicit_approval approval category"
  check_doc_contains "${registry_plan_doc}" "no student data" "no student data boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no raw file ownership transfer" "no raw file ownership transfer boundary"
  check_doc_contains "${registry_plan_doc}" "no generation behavior" "no generation behavior boundary"
  check_doc_contains "${registry_plan_doc}" "no active schema" "no active schema boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no registry data files" "no registry data files boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no fake registry data files" "no fake registry data files boundary"
  check_doc_contains "${registry_plan_doc}" "no sample records" "no sample records boundary"
  check_doc_contains "${registry_plan_doc}" "no real curriculum resource records" "no real curriculum resource records boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no active validators" "no active validators boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no new commands" "no new commands boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no dashboard sections" "no dashboard sections boundary"
  check_doc_contains "${registry_plan_doc}" "no file reads" "no file reads boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no hashing" "no hashing boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no OCR" "no OCR boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no embeddings" "no embeddings boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no APIs" "no APIs boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no OAuth" "no OAuth boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no network calls" "no network calls boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no automation" "no automation boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no background jobs" "no background jobs boundary in approval gate note"
  check_doc_contains "${registry_plan_doc}" "no schedulers" "no schedulers boundary"
  check_doc_contains "${registry_plan_doc}" "no lesson generation" "no lesson generation boundary"
  check_doc_contains "${registry_plan_doc}" "no live integrations" "no live integrations boundary in approval gate note"
fi

section "Curriculum Builder Planning Stack Summary Checks"

check_file "${planning_stack_summary_doc}"

if [[ -f "${planning_stack_summary_doc}" ]]; then
  check_doc_contains "${planning_stack_summary_doc}" "Curriculum Builder Planning Stack Summary" "Curriculum Builder Planning Stack Summary"
  check_doc_contains "${planning_stack_summary_doc}" "Planning Stack Index" "Planning Stack Index"
  check_doc_contains "${planning_stack_summary_doc}" "Storage and Ownership Summary" "Storage and Ownership Summary"
  check_doc_contains "${planning_stack_summary_doc}" "Registry Boundary Summary" "Registry Boundary Summary"
  check_doc_contains "${planning_stack_summary_doc}" "Current Allowed Work" "Current Allowed Work"
  check_doc_contains "${planning_stack_summary_doc}" "Current Blocked Work Without Explicit Approval" "Current Blocked Work Without Explicit Approval"
  check_doc_contains "${planning_stack_summary_doc}" "Future PR Decision Path" "Future PR Decision Path"
  check_doc_contains "${planning_stack_summary_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "Explicit Non-Activation" "Explicit Non-Activation in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "docs/curriculum-builder-local-first-foundation-plan.md" "foundation plan doc reference"
  check_doc_contains "${planning_stack_summary_doc}" "docs/curriculum-source-storage-strategy.md" "source storage strategy doc reference"
  check_doc_contains "${planning_stack_summary_doc}" "docs/curriculum-resource-registry-plan.md" "registry plan doc reference"
  check_doc_contains "${planning_stack_summary_doc}" "Static Registry Field Inventory Note" "Static Registry Field Inventory Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Static Registry Safety and Status Values Note" "Static Registry Safety and Status Values Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Manual-First Registry Entry Workflow Note" "Manual-First Registry Entry Workflow Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Metadata-Only Backup and Export Planning Note" "Metadata-Only Backup and Export Planning Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Local Registry Validator Planning Note" "Local Registry Validator Planning Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Placeholder Metadata Shape Note" "Placeholder Metadata Shape Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Registry Implementation Approval Gate Note" "Registry Implementation Approval Gate Note reference"
  check_doc_contains "${planning_stack_summary_doc}" "Google Drive" "Google Drive storage source"
  check_doc_contains "${planning_stack_summary_doc}" "NAS" "NAS storage source"
  check_doc_contains "${planning_stack_summary_doc}" "iCloud" "iCloud storage source"
  check_doc_contains "${planning_stack_summary_doc}" "local folders" "local folders storage source"
  check_doc_contains "${planning_stack_summary_doc}" "metadata/status/reference records only" "metadata/status/reference records only boundary"
  check_doc_contains "${planning_stack_summary_doc}" "does not own raw curriculum files" "Chief of Staff does not own raw curriculum files"
  check_doc_contains "${planning_stack_summary_doc}" "no student data" "no student data boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no active schema" "no active schema boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no database tables" "no database tables boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no registry data files" "no registry data files boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no fake registry data files" "no fake registry data files boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no real registry records" "no real registry records boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no active validators" "no active validators boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no new commands" "no new commands boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no dashboard sections" "no dashboard sections boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no file reads" "no file reads boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no hashing" "no hashing boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no scanning" "no scanning boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no indexing" "no indexing boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no OCR" "no OCR boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no embeddings" "no embeddings boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no APIs" "no APIs boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no OAuth" "no OAuth boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no network calls" "no network calls boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no automation" "no automation boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no background jobs" "no background jobs boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no schedulers" "no schedulers boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no lesson generation" "no lesson generation boundary in planning stack summary"
  check_doc_contains "${planning_stack_summary_doc}" "no live integrations" "no live integrations boundary in planning stack summary"
fi

section "Curriculum Builder Next Phase Decision Checks"

check_file "${next_phase_decision_doc}"

if [[ -f "${next_phase_decision_doc}" ]]; then
  check_doc_contains "${next_phase_decision_doc}" "Curriculum Builder Next-Phase Decision Note" "Curriculum Builder Next-Phase Decision Note"
  check_doc_contains "${next_phase_decision_doc}" "Current Planning Stack Status" "Current Planning Stack Status"
  check_doc_contains "${next_phase_decision_doc}" "Recommended Next-Phase Decision" "Recommended Next-Phase Decision"
  check_doc_contains "${next_phase_decision_doc}" "Allowed Next Paths" "Allowed Next Paths"
  check_doc_contains "${next_phase_decision_doc}" "Blocked Without Explicit Approval" "Blocked Without Explicit Approval"
  check_doc_contains "${next_phase_decision_doc}" "Decision Questions for the Next PR" "Decision Questions for the Next PR"
  check_doc_contains "${next_phase_decision_doc}" "Safe Default" "Safe Default"
  check_doc_contains "${next_phase_decision_doc}" "Relationship to Teacher Workstation" "Relationship to Teacher Workstation in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "Relationship to Chief of Staff" "Relationship to Chief of Staff in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "Explicit Non-Activation" "Explicit Non-Activation in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "pause implementation" "pause implementation recommendation"
  check_doc_contains "${next_phase_decision_doc}" "documentation/status-only" "documentation/status-only boundary"
  check_doc_contains "${next_phase_decision_doc}" "explicit approval" "explicit approval requirement"
  check_doc_contains "${next_phase_decision_doc}" "schema planning only" "schema planning only path"
  check_doc_contains "${next_phase_decision_doc}" "fake placeholder fixture planning only" "fake placeholder fixture planning only path"
  check_doc_contains "${next_phase_decision_doc}" "local validator planning only" "local validator planning only path"
  check_doc_contains "${next_phase_decision_doc}" "metadata export/import planning only" "metadata export/import planning only path"
  check_doc_contains "${next_phase_decision_doc}" "Teacher Workstation reference planning only" "Teacher Workstation reference planning only path"
  check_doc_contains "${next_phase_decision_doc}" "Stop Curriculum Builder work for now" "Stop Curriculum Builder work for now path"
  check_doc_contains "${next_phase_decision_doc}" "no active schema" "no active schema boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no database tables" "no database tables boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no registry data files" "no registry data files boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no fake registry data files" "no fake registry data files boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no real registry records" "no real registry records boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no active validators" "no active validators boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no new commands" "no new commands boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no dashboard sections" "no dashboard sections boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no file reads" "no file reads boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no hashing" "no hashing boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no scanning" "no scanning boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no indexing" "no indexing boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no OCR" "no OCR boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no embeddings" "no embeddings boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no APIs" "no APIs boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no OAuth" "no OAuth boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no network calls" "no network calls boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no automation" "no automation boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no background jobs" "no background jobs boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no schedulers" "no schedulers boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no generated lesson briefs" "no generated lesson briefs boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no generated lesson drafts" "no generated lesson drafts boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no lesson generation" "no lesson generation boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no student data" "no student data boundary in next phase decision"
  check_doc_contains "${next_phase_decision_doc}" "no live integrations" "no live integrations boundary in next phase decision"
fi

section "Curriculum Builder Decision Intake Template Checks"

check_file "${decision_intake_template_doc}"

if [[ -f "${decision_intake_template_doc}" ]]; then
  check_doc_contains "${decision_intake_template_doc}" "Curriculum Builder Decision Intake Template" "Curriculum Builder Decision Intake Template"
  check_doc_contains "${decision_intake_template_doc}" "decision title" "decision title template field"
  check_doc_contains "${decision_intake_template_doc}" "requested path" "requested path template field"
  check_doc_contains "${decision_intake_template_doc}" "approval level" "approval level template field"
  check_doc_contains "${decision_intake_template_doc}" "proposed next PR scope" "proposed next PR scope template field"
  check_doc_contains "${decision_intake_template_doc}" "explicitly allowed work" "explicitly allowed work template field"
  check_doc_contains "${decision_intake_template_doc}" "explicitly blocked work" "explicitly blocked work template field"
  check_doc_contains "${decision_intake_template_doc}" "storage impact" "storage impact template field"
  check_doc_contains "${decision_intake_template_doc}" "registry impact" "registry impact template field"
  check_doc_contains "${decision_intake_template_doc}" "Teacher Workstation impact" "Teacher Workstation impact template field"
  check_doc_contains "${decision_intake_template_doc}" "Chief of Staff impact" "Chief of Staff impact template field"
  check_doc_contains "${decision_intake_template_doc}" "dashboard/status impact" "dashboard/status impact template field"
  check_doc_contains "${decision_intake_template_doc}" "rollback plan" "rollback plan template field"
  check_doc_contains "${decision_intake_template_doc}" "validation commands" "validation commands template field"
  check_doc_contains "${decision_intake_template_doc}" "final approval checkbox" "final approval checkbox template field"
  check_doc_contains "${decision_intake_template_doc}" "Non-Activation confirmation" "Non-Activation confirmation template field"
  check_doc_contains "${decision_intake_template_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary"
  check_doc_contains "${decision_intake_template_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary"
  check_doc_contains "${decision_intake_template_doc}" "no lesson generation" "no lesson generation boundary in intake template"
  check_doc_contains "${decision_intake_template_doc}" "no student data" "no student data boundary in intake template"
  check_doc_contains "${decision_intake_template_doc}" "no raw curriculum file duplication" "no raw curriculum file duplication boundary"
fi

section "Curriculum Builder Approval Gate Checks"

check_file "${approval_gate_doc}"

if [[ -f "${approval_gate_doc}" ]]; then
  check_doc_contains "${approval_gate_doc}" "Curriculum Builder Approval Gate" "Curriculum Builder Approval Gate"
  check_doc_contains "${approval_gate_doc}" "approval gate" "approval gate marker"
  check_doc_contains "${approval_gate_doc}" "completed decision intake requirement" "completed decision intake requirement"
  check_doc_contains "${approval_gate_doc}" "implementation blocked until approval" "implementation blocked until approval"
  check_doc_contains "${approval_gate_doc}" "future implementation entry criteria" "future implementation entry criteria"
  check_doc_contains "${approval_gate_doc}" "required validation" "required validation marker"
  check_doc_contains "${approval_gate_doc}" "final local main proof" "final local main proof"
  check_doc_contains "${approval_gate_doc}" "rollback expectations" "rollback expectations"
  check_doc_contains "${approval_gate_doc}" "Teacher Workstation relationship" "Teacher Workstation relationship"
  check_doc_contains "${approval_gate_doc}" "Chief of Staff relationship" "Chief of Staff relationship"
  check_doc_contains "${approval_gate_doc}" "curriculum registry relationship" "curriculum registry relationship"
  check_doc_contains "${approval_gate_doc}" "Non-Activation confirmation" "Non-Activation confirmation in approval gate"
  check_doc_contains "${approval_gate_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary in approval gate"
  check_doc_contains "${approval_gate_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary in approval gate"
  check_doc_contains "${approval_gate_doc}" "no automation/live integrations" "no automation/live integrations boundary"
  check_doc_contains "${approval_gate_doc}" "no lesson generation" "no lesson generation boundary in approval gate"
  check_doc_contains "${approval_gate_doc}" "no student data" "no student data boundary in approval gate"
  check_doc_contains "${approval_gate_doc}" "no storage migration/raw file duplication" "no storage migration/raw file duplication boundary"
fi

section "Curriculum Builder Planning Closeout Checks"

check_file "${planning_closeout_doc}"

if [[ -f "${planning_closeout_doc}" ]]; then
  check_doc_contains "${planning_closeout_doc}" "Curriculum Builder Planning Closeout" "Curriculum Builder Planning Closeout"
  check_doc_contains "${planning_closeout_doc}" "planning stack summary" "planning stack summary in closeout"
  check_doc_contains "${planning_closeout_doc}" "local-first storage decision" "local-first storage decision in closeout"
  check_doc_contains "${planning_closeout_doc}" "metadata/reference-only registry direction" "metadata/reference-only registry direction in closeout"
  check_doc_contains "${planning_closeout_doc}" "completed planning artifacts" "completed planning artifacts in closeout"
  check_doc_contains "${planning_closeout_doc}" "current status commands" "current status commands in closeout"
  check_doc_contains "${planning_closeout_doc}" "safe next options" "safe next options in closeout"
  check_doc_contains "${planning_closeout_doc}" "pause implementation recommendation" "pause implementation recommendation in closeout"
  check_doc_contains "${planning_closeout_doc}" "Teacher Workstation role" "Teacher Workstation role in closeout"
  check_doc_contains "${planning_closeout_doc}" "Chief of Staff role" "Chief of Staff role in closeout"
  check_doc_contains "${planning_closeout_doc}" "Non-Activation list" "Non-Activation list in closeout"
  check_doc_contains "${planning_closeout_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary in closeout"
  check_doc_contains "${planning_closeout_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary in closeout"
  check_doc_contains "${planning_closeout_doc}" "no lesson generation" "no lesson generation boundary in closeout"
  check_doc_contains "${planning_closeout_doc}" "no student data" "no student data boundary in closeout"
fi

section "Curriculum Builder Maintainer Handoff Checks"

check_file "${maintainer_handoff_doc}"

if [[ -f "${maintainer_handoff_doc}" ]]; then
  check_doc_contains "${maintainer_handoff_doc}" "Curriculum Builder Maintainer Handoff" "Curriculum Builder Maintainer Handoff"
  check_doc_contains "${maintainer_handoff_doc}" "current state summary" "current state summary in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "latest completed PR reference" "latest completed PR reference in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "planning stack status" "planning stack status in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "local-first storage model" "local-first storage model in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "metadata/reference-only registry direction" "metadata/reference-only registry direction in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "Teacher Workstation relationship" "Teacher Workstation relationship in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "Chief of Staff relationship" "Chief of Staff relationship in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "approval gate requirement" "approval gate requirement in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "decision intake requirement" "decision intake requirement in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "current status commands" "current status commands in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "required validation commands" "required validation commands in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "final local main proof requirements" "final local main proof requirements in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "safe next PR categories" "safe next PR categories in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "blocked PR categories" "blocked PR categories in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "Non-Activation confirmation" "Non-Activation confirmation in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "no automation/live integrations" "no automation/live integrations boundary in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "no lesson generation" "no lesson generation boundary in maintainer handoff"
  check_doc_contains "${maintainer_handoff_doc}" "no student data" "no student data boundary in maintainer handoff"
fi

section "Curriculum Builder Future PR Checklist Checks"

check_file "${future_pr_checklist_doc}"

if [[ -f "${future_pr_checklist_doc}" ]]; then
  check_doc_contains "${future_pr_checklist_doc}" "Curriculum Builder Future PR Checklist" "Curriculum Builder Future PR Checklist"
  check_doc_contains "${future_pr_checklist_doc}" "PR title and type" "PR title and type checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "approval status" "approval status checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "decision intake link/status" "decision intake link/status checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "scope classification" "scope classification checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "files expected to change" "files expected to change checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "files that must not change" "files that must not change checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "commands that must remain unchanged" "commands that must remain unchanged checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "checks that must remain unchanged" "checks that must remain unchanged checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "PASS/WARN/FAIL preservation" "PASS/WARN/FAIL preservation checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "dashboard health preservation" "dashboard health preservation checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "storage impact" "storage impact checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "registry impact" "registry impact checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "Teacher Workstation impact" "Teacher Workstation impact checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "Chief of Staff impact" "Chief of Staff impact checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "validation commands" "validation commands checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "PR body requirements" "PR body requirements checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "merge requirements" "merge requirements checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "branch deletion verification" "branch deletion verification checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "final local main proof" "final local main proof checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "rollback notes" "rollback notes checklist field"
  check_doc_contains "${future_pr_checklist_doc}" "Non-Activation confirmation" "Non-Activation confirmation in future PR checklist"
  check_doc_contains "${future_pr_checklist_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary in future PR checklist"
  check_doc_contains "${future_pr_checklist_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary in future PR checklist"
  check_doc_contains "${future_pr_checklist_doc}" "no lesson generation" "no lesson generation boundary in future PR checklist"
  check_doc_contains "${future_pr_checklist_doc}" "no student data" "no student data boundary in future PR checklist"
  check_doc_contains "${future_pr_checklist_doc}" "no raw curriculum file duplication" "no raw curriculum file duplication boundary in future PR checklist"
fi

section "Curriculum Builder Canonical Planning Index Checks"

check_file "${canonical_planning_index_doc}"

if [[ -f "${canonical_planning_index_doc}" ]]; then
  check_doc_contains "${canonical_planning_index_doc}" "Curriculum Builder Canonical Planning Index" "Curriculum Builder Canonical Planning Index"
  check_doc_contains "${canonical_planning_index_doc}" "current state summary" "current state summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "planning stack purpose" "planning stack purpose in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "local-first architecture summary" "local-first architecture summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "storage model summary" "storage model summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "metadata/reference-only registry summary" "metadata/reference-only registry summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Teacher Workstation relationship" "Teacher Workstation relationship in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Chief of Staff relationship" "Chief of Staff relationship in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "approval gate summary" "approval gate summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "decision intake summary" "decision intake summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "maintainer handoff summary" "maintainer handoff summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "future PR checklist summary" "future PR checklist summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "current status commands" "current status commands in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "required validation commands" "required validation commands in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "final local main proof requirements" "final local main proof requirements in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "artifact map" "artifact map in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Start Here" "Start Here section in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Safe Next PR Routing" "Safe Next PR Routing section in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Do Not Start Here" "Do Not Start Here section in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "blocked work summary" "blocked work summary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "Non-Activation confirmation" "Non-Activation confirmation in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no scanning/indexing/OCR/embeddings" "no scanning/indexing/OCR/embeddings boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no APIs/OAuth/network calls" "no APIs/OAuth/network calls boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no automation/live integrations" "no automation/live integrations boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no lesson generation" "no lesson generation boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no student data" "no student data boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "no raw curriculum file duplication" "no raw curriculum file duplication boundary in canonical index"
  check_doc_contains "${canonical_planning_index_doc}" "docs/curriculum-builder-next-stage-readiness-audit.md" "next-stage readiness audit reference in canonical index"
fi

section "Curriculum Builder Next-Stage Readiness Audit Checks"

check_file "${next_stage_readiness_audit_doc}"

if [[ -f "${next_stage_readiness_audit_doc}" ]]; then
  check_doc_contains "${next_stage_readiness_audit_doc}" "Curriculum Builder Next-Stage Readiness Audit" "Curriculum Builder Next-Stage Readiness Audit title"
  check_doc_contains "${next_stage_readiness_audit_doc}" "Current status baseline" "current status baseline section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "What is already ready" "what is already ready section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "What is still planning-only" "what is still planning-only section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "What is explicitly not active" "what is explicitly not active section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "Safe next PR categories" "safe next PR categories section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "What must remain blocked" "what must remain blocked section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "Cursor self-check expectations" "Cursor self-check expectations section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "Required validation commands" "required validation commands section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "PR handoff template" "PR handoff template section"
  check_doc_contains "${next_stage_readiness_audit_doc}" "read-only proof surfaces" "read-only proof surfaces boundary"
  check_doc_contains "${next_stage_readiness_audit_doc}" "metadata/reference-only" "metadata/reference-only boundary"
  check_doc_contains "${next_stage_readiness_audit_doc}" "manual and static" "manual/static-first boundary"
  check_doc_contains "${next_stage_readiness_audit_doc}" "no document scanning" "no document scanning boundary in next-stage audit"
  check_doc_contains "${next_stage_readiness_audit_doc}" "no raw curriculum file duplication" "no raw curriculum file duplication boundary in next-stage audit"
  check_doc_contains "${next_stage_readiness_audit_doc}" "does not own raw curriculum files" "Chief of Staff does not own raw curriculum files in next-stage audit"
  check_doc_contains "${next_stage_readiness_audit_doc}" "docs/curriculum-builder-canonical-planning-index.md" "canonical planning index cross-link in next-stage audit"
  check_doc_contains "${next_stage_readiness_audit_doc}" "Non-Activation confirmation" "Non-Activation confirmation in next-stage audit"
fi

section "Curriculum Builder Manual Registry Schema Plan Checks"

check_file "${manual_registry_schema_plan_doc}"

if [[ -f "${manual_registry_schema_plan_doc}" ]]; then
  check_doc_contains "${manual_registry_schema_plan_doc}" "Curriculum Builder Manual Registry Schema Plan" "Curriculum Builder Manual Registry Schema Plan title"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Non-Activation Statement" "Non-Activation Statement section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Required Fields" "Required Fields section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Optional Fields" "Optional Fields section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Reserved Future Fields" "Reserved Future Fields section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Example Placeholder Rows" "Example Placeholder Rows section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Blocked Capabilities" "Blocked Capabilities section"
  check_doc_contains "${manual_registry_schema_plan_doc}" "registry_id" "registry_id required field"
  check_doc_contains "${manual_registry_schema_plan_doc}" "source_reference" "source_reference required field"
  check_doc_contains "${manual_registry_schema_plan_doc}" "teacher_only" "teacher_only safety field"
  check_doc_contains "${manual_registry_schema_plan_doc}" "gdrive://placeholder" "fictional placeholder source reference"
  check_doc_contains "${manual_registry_schema_plan_doc}" "no document scanning" "no document scanning boundary in schema plan"
  check_doc_contains "${manual_registry_schema_plan_doc}" "no student data" "no student data boundary in schema plan"
  check_doc_contains "${manual_registry_schema_plan_doc}" "docs/curriculum-builder-canonical-planning-index.md" "canonical planning index cross-link in schema plan"
  check_doc_contains "${manual_registry_schema_plan_doc}" "Non-Activation confirmation" "Non-Activation confirmation in schema plan"
fi

if [[ -f "${canonical_planning_index_doc}" ]]; then
  check_doc_contains "${canonical_planning_index_doc}" "docs/curriculum-builder-manual-registry-schema-plan.md" "manual registry schema plan reference in canonical index"
fi

section "Dashboard Planning Index Visibility Checks"

if [[ -f "${dashboard_doc}" ]]; then
  check_doc_contains "${dashboard_doc}" "Curriculum Builder Planning Index Visibility" "Curriculum Builder Planning Index Visibility in dashboard doc"
  check_doc_contains "${dashboard_doc}" "docs/curriculum-builder-canonical-planning-index.md" "canonical planning index reference in dashboard doc"
  check_doc_contains "${dashboard_doc}" "Curriculum Builder planning index" "Curriculum Builder planning index label in dashboard doc"
  check_doc_contains "${dashboard_doc}" "Approval gate required before implementation" "approval gate visibility in dashboard doc"
  check_doc_contains "${dashboard_doc}" "curriculum-builder-foundation-status" "curriculum builder status command in dashboard doc"
  check_doc_contains "${dashboard_doc}" "does not change dashboard behavior" "dashboard behavior preservation note"
fi

if [[ -f "${dashboard_section_summary_doc}" ]]; then
  check_doc_contains "${dashboard_section_summary_doc}" "Lesson Planning Status Planning Index" "Lesson Planning Status Planning Index in dashboard section summary doc"
  check_doc_contains "${dashboard_section_summary_doc}" "docs/curriculum-builder-canonical-planning-index.md" "canonical planning index reference in dashboard section summary doc"
fi

section "Phase 1 Curriculum Builder Status Closeout Checks"

if [[ -f "${phase_1_audit_doc}" ]]; then
  check_doc_contains "${phase_1_audit_doc}" "Curriculum Builder Planning Stack Closeout" "Curriculum Builder Planning Stack Closeout in Phase 1 audit"
  check_doc_contains "${phase_1_audit_doc}" "docs/curriculum-builder-canonical-planning-index.md" "canonical planning index in Phase 1 closeout"
  check_doc_contains "${phase_1_audit_doc}" "approval gate" "approval gate in Phase 1 closeout"
  check_doc_contains "${phase_1_audit_doc}" "decision intake" "decision intake in Phase 1 closeout"
  check_doc_contains "${phase_1_audit_doc}" "curriculum-builder-foundation-status" "curriculum builder foundation status command in Phase 1 closeout"
  check_doc_contains "${phase_1_audit_doc}" "chief-of-staff --dashboard" "dashboard command in Phase 1 closeout"
  check_doc_contains "${phase_1_audit_doc}" "No implementation behavior is active" "no active implementation behavior in Phase 1 closeout"
fi

section "Command Wiring Checks"

check_help_contains '--curriculum-builder-foundation-status'
check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"
check_bash_syntax "scripts/curriculum-builder-foundation-status.sh"

pass "no write action attempted"
pass "no folder scanning attempted"
pass "no network call attempted"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
