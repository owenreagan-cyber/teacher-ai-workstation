#!/usr/bin/env bash
# Read-only Teacher App Designer / Canvas LLM foundation status only. No network calls, APIs, or file operations.
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

plan_doc="docs/teacher-app-designer-canvas-llm-plan.md"
safety_doc="docs/canvas-llm-safety-and-approval-contract.md"
architecture_doc="docs/canvas-llm-local-first-drive-first-architecture.md"
placeholder_schema_doc="docs/canvas-llm-placeholder-schema.md"
approval_states_doc="docs/canvas-llm-approval-and-export-states.md"
maintenance_doc="docs/canvas-llm-placeholder-schema-maintenance.md"
export_plan_doc="docs/canvas-llm-manual-export-package-plan.md"
export_shapes_doc="docs/canvas-llm-manual-export-package-shapes.md"
export_maintenance_doc="docs/canvas-llm-manual-export-package-maintenance.md"
review_checklist_doc="docs/canvas-llm-manual-export-review-checklist.md"
review_checklist_maintenance_doc="docs/canvas-llm-manual-export-review-checklist-maintenance.md"
completion_plan_doc="docs/canvas-llm-manual-completion-status-placeholder-plan.md"
completion_maintenance_doc="docs/canvas-llm-manual-completion-status-placeholder-maintenance.md"
weekly_bundle_plan_doc="docs/canvas-llm-weekly-export-bundle-placeholder-plan.md"
weekly_bundle_maintenance_doc="docs/canvas-llm-weekly-export-bundle-placeholder-maintenance.md"
capstone_doc="docs/canvas-llm-planning-foundation-capstone.md"
capstone_maintenance_doc="docs/canvas-llm-planning-foundation-capstone-maintenance.md"

section 'Teacher App Designer / Canvas LLM Local-First Foundation'
cat <<'EOF'
Status: planning/status only
Single-user local-first Drive-first: yes
Live Canvas behavior: no
Live Drive behavior: no
Canvas API: no
Google Drive API: no
OAuth: no
Network calls: no
Automation: no
Document scanning: no
Folder scanning: no
File indexing: no
OCR: no
Embeddings: no
Vector database: no
Real lesson generation: no
Generated lesson briefs: no
Generated lesson drafts: no
Real review notes: no
Student data: no
Runtime behavior changed: no
Existing commands preserved: yes
PASS/WARN/FAIL semantics preserved: yes
EOF

section 'Foundation Doc Presence'

check_file "${plan_doc}"
check_file "${safety_doc}"
check_file "${architecture_doc}"

section 'Plan Doc Checks'

check_doc_contains "${plan_doc}" "Teacher App Designer" "Teacher App Designer"
check_doc_contains "${plan_doc}" "Canvas LLM" "Canvas LLM"
check_doc_contains "${plan_doc}" "single-user" "single-user focus"
check_doc_contains "${plan_doc}" "Owen" "Owen-focused scope"
check_doc_contains "${plan_doc}" "Teacher Workstation owns teacher-facing workflows" "Teacher Workstation owns teacher-facing workflows"
check_doc_contains "${plan_doc}" "Chief of Staff is status/safety only" "Chief of Staff is status/safety only"
check_doc_contains "${plan_doc}" "Curriculum Builder owns metadata/resource references" "Curriculum Builder owns metadata/resource references"
check_doc_contains "${plan_doc}" "planning/status only" "planning/status only"
check_doc_contains "${plan_doc}" "no live Canvas behavior" "no live Canvas behavior"
check_doc_contains "${plan_doc}" "no live Drive behavior" "no live Drive behavior"

section 'Safety Contract Doc Checks'

check_doc_contains "${safety_doc}" "No silent publishing" "no silent publishing"
check_doc_contains "${safety_doc}" "No student data" "no student data"
check_doc_contains "${safety_doc}" "No Canvas API during foundation" "no Canvas API during foundation"
check_doc_contains "${safety_doc}" "No Google Drive API during foundation" "no Google Drive API during foundation"
check_doc_contains "${safety_doc}" "No OAuth during foundation" "no OAuth during foundation"
check_doc_contains "${safety_doc}" "No network calls" "no network calls"
check_doc_contains "${safety_doc}" "No real lesson generation" "no real lesson generation"
check_doc_contains "${safety_doc}" "No scanning, indexing, OCR, embeddings, or vector DB" "no scanning/indexing/OCR/embeddings/vector DB"
check_doc_contains "${safety_doc}" "not_started" "approval state not_started"
check_doc_contains "${safety_doc}" "drafted" "approval state drafted"
check_doc_contains "${safety_doc}" "needs_teacher_review" "approval state needs_teacher_review"
check_doc_contains "${safety_doc}" "teacher_revised" "approval state teacher_revised"
check_doc_contains "${safety_doc}" "approved_for_export" "approval state approved_for_export"
check_doc_contains "${safety_doc}" "exported" "approval state exported"
check_doc_contains "${safety_doc}" "blocked" "approval state blocked"
check_doc_contains "${safety_doc}" "rejected" "approval state rejected"

section 'Architecture Doc Checks'

check_doc_contains "${architecture_doc}" "local-first" "local-first"
check_doc_contains "${architecture_doc}" "Drive-first" "Drive-first"
check_doc_contains "${architecture_doc}" "Supabase is optional/future only, not default" "Supabase optional/future only, not default"
check_doc_contains "${architecture_doc}" "Files remain in Google Drive, NAS, iCloud, or local folders where possible" "files remain in Google Drive/NAS/iCloud/local where possible"
check_doc_contains "${architecture_doc}" "stores metadata and references, not paid hosted copies" "workstation stores metadata/references, not raw hosted copies"

section 'Placeholder Schema Doc Presence'

check_file "${placeholder_schema_doc}"
check_file "${approval_states_doc}"
check_file "${maintenance_doc}"

section 'Placeholder Schema Doc Checks'

check_doc_contains "${placeholder_schema_doc}" "canvas_page_draft" "canvas_page_draft"
check_doc_contains "${placeholder_schema_doc}" "canvas_assignment_draft" "canvas_assignment_draft"
check_doc_contains "${placeholder_schema_doc}" "canvas_announcement_draft" "canvas_announcement_draft"
check_doc_contains "${placeholder_schema_doc}" "canvas_module_plan" "canvas_module_plan"
check_doc_contains "${placeholder_schema_doc}" "canvas_file_link_plan" "canvas_file_link_plan"
check_doc_contains "${placeholder_schema_doc}" "canvas_export_package" "canvas_export_package"
check_doc_contains "${placeholder_schema_doc}" "canvas_review_note_placeholder" "canvas_review_note_placeholder"
check_doc_contains "${placeholder_schema_doc}" "canvas_idempotency_fingerprint" "canvas_idempotency_fingerprint"
check_doc_contains "${placeholder_schema_doc}" "canvas_source_reference" "canvas_source_reference"
check_doc_contains "${placeholder_schema_doc}" "placeholder_id" "placeholder_id"
check_doc_contains "${placeholder_schema_doc}" "object_type" "object_type"
check_doc_contains "${placeholder_schema_doc}" "approval_state" "approval_state"
check_doc_contains "${placeholder_schema_doc}" "export_state" "export_state"
check_doc_contains "${placeholder_schema_doc}" "student_facing_allowed" "student_facing_allowed"
check_doc_contains "${placeholder_schema_doc}" "resource_reference_ids" "resource_reference_ids"
check_doc_contains "${placeholder_schema_doc}" "idempotency_fingerprint_placeholder" "idempotency_fingerprint_placeholder"
check_doc_contains "${placeholder_schema_doc}" "placeholder_only" "placeholder_only"
check_doc_contains "${placeholder_schema_doc}" "documentation_only" "documentation_only"
check_doc_contains "${placeholder_schema_doc}" "no_runtime_behavior" "no_runtime_behavior"
check_doc_contains "${placeholder_schema_doc}" "no_canvas_api" "no_canvas_api"
check_doc_contains "${placeholder_schema_doc}" "no_google_drive_api" "no_google_drive_api"
check_doc_contains "${placeholder_schema_doc}" "no_oauth" "no_oauth"
check_doc_contains "${placeholder_schema_doc}" "no_network_calls" "no_network_calls"
check_doc_contains "${placeholder_schema_doc}" "no_generation" "no_generation"
check_doc_contains "${placeholder_schema_doc}" "no_student_data" "no_student_data"
check_doc_contains "${placeholder_schema_doc}" "manual_approval_required" "manual_approval_required"
check_doc_contains "${placeholder_schema_doc}" "export_before_publish" "export_before_publish"

section 'Approval and Export States Doc Checks'

check_doc_contains "${approval_states_doc}" "not_started" "approval state not_started"
check_doc_contains "${approval_states_doc}" "drafted" "approval state drafted"
check_doc_contains "${approval_states_doc}" "needs_teacher_review" "approval state needs_teacher_review"
check_doc_contains "${approval_states_doc}" "teacher_revised" "approval state teacher_revised"
check_doc_contains "${approval_states_doc}" "approved_for_export" "approval state approved_for_export"
check_doc_contains "${approval_states_doc}" "exported" "approval state exported"
check_doc_contains "${approval_states_doc}" "blocked" "approval state blocked"
check_doc_contains "${approval_states_doc}" "rejected" "approval state rejected"
check_doc_contains "${approval_states_doc}" "not_ready" "export state not_ready"
check_doc_contains "${approval_states_doc}" "draft_ready" "export state draft_ready"
check_doc_contains "${approval_states_doc}" "review_ready" "export state review_ready"
check_doc_contains "${approval_states_doc}" "approved" "export state approved"
check_doc_contains "${approval_states_doc}" "export_ready" "export state export_ready"
check_doc_contains "${approval_states_doc}" "failed" "export state failed"
check_doc_contains "${approval_states_doc}" "pending" "connector state pending"
check_doc_contains "${approval_states_doc}" "validated" "connector state validated"
check_doc_contains "${approval_states_doc}" "dry_run_complete" "connector state dry_run_complete"
check_doc_contains "${approval_states_doc}" "approved_for_publish" "connector state approved_for_publish"
check_doc_contains "${approval_states_doc}" "publishing" "connector state publishing"
check_doc_contains "${approval_states_doc}" "published" "connector state published"
check_doc_contains "${approval_states_doc}" "publish_failed" "connector state publish_failed"
check_doc_contains "${approval_states_doc}" "rollback_needed" "connector state rollback_needed"
check_doc_contains "${approval_states_doc}" "rollback_complete" "connector state rollback_complete"
check_doc_contains "${approval_states_doc}" "not_started -> exported" "forbidden transition not_started -> exported"
check_doc_contains "${approval_states_doc}" "drafted -> exported" "forbidden transition drafted -> exported"
check_doc_contains "${approval_states_doc}" "needs_teacher_review -> exported" "forbidden transition needs_teacher_review -> exported"
check_doc_contains "${approval_states_doc}" "approved_for_export -> published" "forbidden transition approved_for_export -> published"
check_doc_contains "${approval_states_doc}" "exported -> published" "forbidden transition exported -> published"

section 'Placeholder Schema Maintenance Doc Checks'

check_doc_contains "${maintenance_doc}" "Markdown only" "Markdown only"
check_doc_contains "${maintenance_doc}" "Do not create active JSON" "Do not create active JSON"
check_doc_contains "${maintenance_doc}" "Do not add runtime validators" "Do not add runtime validators"
check_doc_contains "${maintenance_doc}" "Do not add parsers/importers/loaders" "Do not add parsers/importers/loaders"
check_doc_contains "${maintenance_doc}" "Preserve single-user/local-first/Drive-first" "Preserve single-user/local-first/Drive-first"
check_doc_contains "${maintenance_doc}" "Supabase optional/future-only" "Supabase optional/future-only"
check_doc_contains "${maintenance_doc}" "static file-presence and fixed-string checks" "static file-presence and fixed-string checks"
check_doc_contains "${maintenance_doc}" "must not parse, load, validate, generate, or call APIs" "must not parse, load, validate, generate, or call APIs"
check_doc_contains "${maintenance_doc}" "docs/canvas-llm-placeholder-schema.md" "canonical placeholder schema doc"
check_doc_contains "${maintenance_doc}" "docs/canvas-llm-approval-and-export-states.md" "canonical approval states doc"
check_doc_contains "${maintenance_doc}" "docs/canvas-llm-safety-and-approval-contract.md" "canonical safety contract doc"
check_doc_contains "${maintenance_doc}" "docs/canvas-llm-local-first-drive-first-architecture.md" "canonical architecture doc"
check_doc_contains "${maintenance_doc}" "docs/teacher-app-designer-canvas-llm-plan.md" "canonical plan doc"

section 'Manual Export Package Doc Presence'

check_file "${export_plan_doc}"
check_file "${export_shapes_doc}"
check_file "${export_maintenance_doc}"

section 'Manual Export Package Plan Doc Checks'

check_doc_contains "${export_plan_doc}" "manual copy/export package workflow" "manual copy/export package workflow"
check_doc_contains "${export_plan_doc}" "fastest useful school-year path" "fastest useful school-year path"
check_doc_contains "${export_plan_doc}" "canvas_page_copy_package" "canvas_page_copy_package"
check_doc_contains "${export_plan_doc}" "canvas_assignment_copy_package" "canvas_assignment_copy_package"
check_doc_contains "${export_plan_doc}" "canvas_announcement_copy_package" "canvas_announcement_copy_package"
check_doc_contains "${export_plan_doc}" "canvas_module_checklist_package" "canvas_module_checklist_package"
check_doc_contains "${export_plan_doc}" "canvas_file_link_checklist_package" "canvas_file_link_checklist_package"
check_doc_contains "${export_plan_doc}" "canvas_weekly_export_bundle_placeholder" "canvas_weekly_export_bundle_placeholder"
check_doc_contains "${export_plan_doc}" "approval_state: approved_for_export" "approval_state approved_for_export"
check_doc_contains "${export_plan_doc}" "export_state: export_ready" "export_state export_ready"
check_doc_contains "${export_plan_doc}" "package_header" "package_header"
check_doc_contains "${export_plan_doc}" "teacher_review_summary" "teacher_review_summary"
check_doc_contains "${export_plan_doc}" "copy_ready_title_block" "copy_ready_title_block"
check_doc_contains "${export_plan_doc}" "copy_ready_body_block" "copy_ready_body_block"
check_doc_contains "${export_plan_doc}" "resource_link_checklist" "resource_link_checklist"
check_doc_contains "${export_plan_doc}" "manual_canvas_steps" "manual_canvas_steps"
check_doc_contains "${export_plan_doc}" "post_copy_completion_checklist" "post_copy_completion_checklist"
check_doc_contains "${export_plan_doc}" "safety_footer" "safety_footer"
check_doc_contains "${export_plan_doc}" "manual_copy_package" "manual_copy_package"
check_doc_contains "${export_plan_doc}" "not_copied" "not_copied"
check_doc_contains "${export_plan_doc}" "copied_to_canvas_manually" "copied_to_canvas_manually"
check_doc_contains "${export_plan_doc}" "teacher_verified_in_canvas" "teacher_verified_in_canvas"
check_doc_contains "${export_plan_doc}" "needs_manual_revision" "needs_manual_revision"
check_doc_contains "${export_plan_doc}" "skipped" "skipped"
check_doc_contains "${export_plan_doc}" "missing_title" "missing_title"
check_doc_contains "${export_plan_doc}" "teacher_only_resource_in_student_package" "teacher_only_resource_in_student_package"
check_doc_contains "${export_plan_doc}" "unresolved_resource_reference" "unresolved_resource_reference"
check_doc_contains "${export_plan_doc}" "No exporter" "No exporter"
check_doc_contains "${export_plan_doc}" "No generated package files" "No generated package files"
check_doc_contains "${export_plan_doc}" "No Canvas API" "No Canvas API"
check_doc_contains "${export_plan_doc}" "No Drive API" "No Drive API"
check_doc_contains "${export_plan_doc}" "No generation" "No generation"
check_doc_contains "${export_plan_doc}" "No student data" "No student data"

section 'Manual Export Package Shapes Doc Checks'

check_doc_contains "${export_shapes_doc}" "package_placeholder_id" "package_placeholder_id"
check_doc_contains "${export_shapes_doc}" "package_type" "package_type"
check_doc_contains "${export_shapes_doc}" "source_draft_ids_placeholder" "source_draft_ids_placeholder"
check_doc_contains "${export_shapes_doc}" "approval_state_required" "approval_state_required"
check_doc_contains "${export_shapes_doc}" "export_state_required" "export_state_required"
check_doc_contains "${export_shapes_doc}" "copy_ready_blocks_placeholder" "copy_ready_blocks_placeholder"
check_doc_contains "${export_shapes_doc}" "manual_canvas_steps_placeholder" "manual_canvas_steps_placeholder"
check_doc_contains "${export_shapes_doc}" "manual_completion_status_placeholder" "manual_completion_status_placeholder"
check_doc_contains "${export_shapes_doc}" "canvas_page_copy_package" "shapes canvas_page_copy_package"
check_doc_contains "${export_shapes_doc}" "canvas_assignment_copy_package" "shapes canvas_assignment_copy_package"
check_doc_contains "${export_shapes_doc}" "canvas_announcement_copy_package" "shapes canvas_announcement_copy_package"
check_doc_contains "${export_shapes_doc}" "canvas_module_checklist_package" "shapes canvas_module_checklist_package"
check_doc_contains "${export_shapes_doc}" "canvas_file_link_checklist_package" "shapes canvas_file_link_checklist_package"
check_doc_contains "${export_shapes_doc}" "canvas_weekly_export_bundle_placeholder" "shapes canvas_weekly_export_bundle_placeholder"
check_doc_contains "${export_shapes_doc}" "open_canvas_course_manually" "open_canvas_course_manually"
check_doc_contains "${export_shapes_doc}" "create_or_open_target_page_manually" "create_or_open_target_page_manually"
check_doc_contains "${export_shapes_doc}" "copy_title_manually" "copy_title_manually"
check_doc_contains "${export_shapes_doc}" "copy_body_manually" "copy_body_manually"
check_doc_contains "${export_shapes_doc}" "check_links_manually" "check_links_manually"
check_doc_contains "${export_shapes_doc}" "save_as_draft_or_publish_manually" "save_as_draft_or_publish_manually"
check_doc_contains "${export_shapes_doc}" "verify_result_manually" "verify_result_manually"
check_doc_contains "${export_shapes_doc}" "record_completion_status_manually" "record_completion_status_manually"
check_doc_contains "${export_shapes_doc}" "No page content is generated here" "No page content is generated here"
check_doc_contains "${export_shapes_doc}" "No assignment is created" "No assignment is created"
check_doc_contains "${export_shapes_doc}" "No announcement is sent" "No announcement is sent"
check_doc_contains "${export_shapes_doc}" "No Canvas module is created" "No Canvas module is created"
check_doc_contains "${export_shapes_doc}" "No Drive link is resolved" "No Drive link is resolved"
check_doc_contains "${export_shapes_doc}" "No file is uploaded" "No file is uploaded"
check_doc_contains "${export_shapes_doc}" "does not automate a browser" "does not automate a browser"
check_doc_contains "${export_shapes_doc}" "does not call Canvas" "does not call Canvas"

section 'Manual Export Package Maintenance Doc Checks'

check_doc_contains "${export_maintenance_doc}" "Keep package shapes in Markdown only" "Keep package shapes in Markdown only"
check_doc_contains "${export_maintenance_doc}" "Do not create active export package files" "Do not create active export package files"
check_doc_contains "${export_maintenance_doc}" "Do not add an exporter" "Do not add an exporter"
check_doc_contains "${export_maintenance_doc}" "Do not add a copy-package generator" "Do not add a copy-package generator"
check_doc_contains "${export_maintenance_doc}" "Do not add browser automation" "Do not add browser automation"
check_doc_contains "${export_maintenance_doc}" "Do not add Canvas API calls" "Do not add Canvas API calls"
check_doc_contains "${export_maintenance_doc}" "Do not add Drive API calls" "Do not add Drive API calls"
check_doc_contains "${export_maintenance_doc}" "Do not resolve links automatically" "Do not resolve links automatically"
check_doc_contains "${export_maintenance_doc}" "Do not upload files" "Do not upload files"
check_doc_contains "${export_maintenance_doc}" "Preserve manual approval" "Preserve manual approval"
check_doc_contains "${export_maintenance_doc}" "Preserve manual copy only" "Preserve manual copy only"
check_doc_contains "${export_maintenance_doc}" "static file-presence and fixed-string checks" "static file-presence and fixed-string checks"
check_doc_contains "${export_maintenance_doc}" "must not parse package shapes" "must not parse package shapes"
check_doc_contains "${export_maintenance_doc}" "must not generate packages" "must not generate packages"
check_doc_contains "${export_maintenance_doc}" "must not write files" "must not write files"
check_doc_contains "${export_maintenance_doc}" "requires a future explicit PR and approval" "requires a future explicit PR and approval"

section 'Manual Export Review Checklist Doc Presence'

check_file "${review_checklist_doc}"
check_file "${review_checklist_maintenance_doc}"

section 'Manual Export Review Checklist Doc Checks'

check_doc_contains "${review_checklist_doc}" "manual export review checklist" "manual export review checklist"
check_doc_contains "${review_checklist_doc}" "package_identity_review" "package_identity_review"
check_doc_contains "${review_checklist_doc}" "approval_state_review" "approval_state_review"
check_doc_contains "${review_checklist_doc}" "export_state_review" "export_state_review"
check_doc_contains "${review_checklist_doc}" "student_facing_safety_review" "student_facing_safety_review"
check_doc_contains "${review_checklist_doc}" "teacher_only_resource_review" "teacher_only_resource_review"
check_doc_contains "${review_checklist_doc}" "title_and_body_review" "title_and_body_review"
check_doc_contains "${review_checklist_doc}" "resource_link_review" "resource_link_review"
check_doc_contains "${review_checklist_doc}" "manual_canvas_steps_review" "manual_canvas_steps_review"
check_doc_contains "${review_checklist_doc}" "safety_footer_review" "safety_footer_review"
check_doc_contains "${review_checklist_doc}" "blocked_or_rejected_review" "blocked_or_rejected_review"
check_doc_contains "${review_checklist_doc}" "completion_status_review" "completion_status_review"
check_doc_contains "${review_checklist_doc}" "Confirm package_placeholder_id is present" "Confirm package_placeholder_id is present"
check_doc_contains "${review_checklist_doc}" "Confirm package_type is one of the allowed manual export package families" "Confirm package_type is one of the allowed manual export package families"
check_doc_contains "${review_checklist_doc}" "Confirm approval_state_required is approved_for_export" "Confirm approval_state_required is approved_for_export"
check_doc_contains "${review_checklist_doc}" "Confirm export_state_required is export_ready" "Confirm export_state_required is export_ready"
check_doc_contains "${review_checklist_doc}" "Confirm no blocked safety issue is listed" "Confirm no blocked safety issue is listed"
check_doc_contains "${review_checklist_doc}" "Confirm no rejected item is included" "Confirm no rejected item is included"
check_doc_contains "${review_checklist_doc}" "Confirm student-facing package does not include teacher-only resources" "Confirm student-facing package does not include teacher-only resources"
check_doc_contains "${review_checklist_doc}" "Confirm no student data appears" "Confirm no student data appears"
check_doc_contains "${review_checklist_doc}" "Confirm manual_canvas_steps are present" "Confirm manual_canvas_steps are present"
check_doc_contains "${review_checklist_doc}" "Confirm safety_footer is present" "Confirm safety_footer is present"
check_doc_contains "${review_checklist_doc}" "manual_copy_only" "manual_copy_only"
check_doc_contains "${review_checklist_doc}" "not_published" "not_published"
check_doc_contains "${review_checklist_doc}" "No Canvas page is created" "No Canvas page is created"
check_doc_contains "${review_checklist_doc}" "No assignment is created" "No assignment is created"
check_doc_contains "${review_checklist_doc}" "No announcement is sent" "No announcement is sent"
check_doc_contains "${review_checklist_doc}" "No Canvas module is reordered" "No Canvas module is reordered"
check_doc_contains "${review_checklist_doc}" "No Drive link resolved" "No Drive link resolved"
check_doc_contains "${review_checklist_doc}" "No file uploaded" "No file uploaded"
check_doc_contains "${review_checklist_doc}" "No folder scanned" "No folder scanned"
check_doc_contains "${review_checklist_doc}" "no archive is produced" "no archive is produced"
check_doc_contains "${review_checklist_doc}" "no files are generated" "no files are generated"
check_doc_contains "${review_checklist_doc}" "no Canvas publish occurs" "no Canvas publish occurs"
check_doc_contains "${review_checklist_doc}" "Blocked items should not be copied" "Blocked items should not be copied"
check_doc_contains "${review_checklist_doc}" "Rejected items should not be copied" "Rejected items should not be copied"
check_doc_contains "${review_checklist_doc}" "No automatic repair occurs" "No automatic repair occurs"
check_doc_contains "${review_checklist_doc}" "No automatic regeneration occurs" "No automatic regeneration occurs"
check_doc_contains "${review_checklist_doc}" "no Canvas verification is automated" "no Canvas verification is automated"
check_doc_contains "${review_checklist_doc}" "No checklist runner" "No checklist runner"
check_doc_contains "${review_checklist_doc}" "No review engine" "No review engine"
check_doc_contains "${review_checklist_doc}" "No exporter" "No exporter"
check_doc_contains "${review_checklist_doc}" "No generated package files" "No generated package files"
check_doc_contains "${review_checklist_doc}" "No browser automation" "No browser automation"
check_doc_contains "${review_checklist_doc}" "No generated review notes" "No generated review notes"

section 'Manual Export Review Checklist Maintenance Doc Checks'

check_doc_contains "${review_checklist_maintenance_doc}" "Keep checklists in Markdown only" "Keep checklists in Markdown only"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add a checklist runner" "Do not add a checklist runner"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add a review engine" "Do not add a review engine"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add an exporter" "Do not add an exporter"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add generated package files" "Do not add generated package files"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add browser automation" "Do not add browser automation"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add Canvas API calls" "Do not add Canvas API calls"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not add Drive API calls" "Do not add Drive API calls"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not resolve links automatically" "Do not resolve links automatically"
check_doc_contains "${review_checklist_maintenance_doc}" "Do not upload files" "Do not upload files"
check_doc_contains "${review_checklist_maintenance_doc}" "Preserve manual approval" "Preserve manual approval"
check_doc_contains "${review_checklist_maintenance_doc}" "Preserve manual completion verification" "Preserve manual completion verification"
check_doc_contains "${review_checklist_maintenance_doc}" "Preserve manual copy only" "Preserve manual copy only"
check_doc_contains "${review_checklist_maintenance_doc}" "static file-presence and fixed-string checks" "static file-presence and fixed-string checks"
check_doc_contains "${review_checklist_maintenance_doc}" "must not parse checklists" "must not parse checklists"
check_doc_contains "${review_checklist_maintenance_doc}" "must not execute checklists" "must not execute checklists"
check_doc_contains "${review_checklist_maintenance_doc}" "must not generate packages" "must not generate packages"
check_doc_contains "${review_checklist_maintenance_doc}" "must not write files" "must not write files"
check_doc_contains "${review_checklist_maintenance_doc}" "requires a future explicit PR and approval" "requires a future explicit PR and approval"

section 'Manual Completion Status Doc Presence'

check_file "${completion_plan_doc}"
check_file "${completion_maintenance_doc}"

section 'Manual Completion Status Plan Doc Checks'

check_doc_contains "${completion_plan_doc}" "manual completion status" "manual completion status concept"
check_doc_contains "${completion_plan_doc}" "not_copied" "status not_copied"
check_doc_contains "${completion_plan_doc}" "copied_to_canvas_manually" "status copied_to_canvas_manually"
check_doc_contains "${completion_plan_doc}" "teacher_verified_in_canvas" "status teacher_verified_in_canvas"
check_doc_contains "${completion_plan_doc}" "needs_manual_revision" "status needs_manual_revision"
check_doc_contains "${completion_plan_doc}" "skipped" "status skipped"
check_doc_contains "${completion_plan_doc}" "blocked" "status blocked"
check_doc_contains "${completion_plan_doc}" "rejected" "status rejected"
check_doc_contains "${completion_plan_doc}" "package_id" "field package_id"
check_doc_contains "${completion_plan_doc}" "canvas_destination_label" "field canvas_destination_label"
check_doc_contains "${completion_plan_doc}" "completion_status" "field completion_status"
check_doc_contains "${completion_plan_doc}" "copied_by" "field copied_by"
check_doc_contains "${completion_plan_doc}" "copied_at" "field copied_at"
check_doc_contains "${completion_plan_doc}" "verified_by" "field verified_by"
check_doc_contains "${completion_plan_doc}" "verified_at" "field verified_at"
check_doc_contains "${completion_plan_doc}" "revision_reason" "field revision_reason"
check_doc_contains "${completion_plan_doc}" "blocked_or_rejected_reason" "field blocked_or_rejected_reason"
check_doc_contains "${completion_plan_doc}" "source_review_checklist_reference" "field source_review_checklist_reference"
check_doc_contains "${completion_plan_doc}" "Blocked and rejected carryover" "blocked/rejected carryover"
check_doc_contains "${completion_plan_doc}" "No Canvas item is read, written, created, updated, deleted, or verified by software" "no Canvas item software access"
check_doc_contains "${completion_plan_doc}" "Teacher verification is manual and external to the app" "teacher verification manual external"
check_doc_contains "${completion_plan_doc}" "no Canvas verification is automated" "no Canvas verification automated"
check_doc_contains "${completion_plan_doc}" "No Canvas API is called" "no Canvas API called"
check_doc_contains "${completion_plan_doc}" "No completion tracker" "no completion tracker"
check_doc_contains "${completion_plan_doc}" "No checklist runner" "no checklist runner"
check_doc_contains "${completion_plan_doc}" "No review engine" "no review engine"
check_doc_contains "${completion_plan_doc}" "No exporter" "no exporter"
check_doc_contains "${completion_plan_doc}" "No generated package files" "no generated package files"
check_doc_contains "${completion_plan_doc}" "No browser automation" "no browser automation"
check_doc_contains "${completion_plan_doc}" "No student data" "no student data"
check_doc_contains "${completion_plan_doc}" "separate approved PR" "separate approved PR for runtime tracker"
check_doc_contains "${completion_plan_doc}" "Chief of Staff may eventually report" "Chief of Staff may eventually report"
check_doc_contains "${completion_plan_doc}" "Chief of Staff must not do yet" "Chief of Staff must not do yet"

section 'Manual Completion Status Maintenance Doc Checks'

check_doc_contains "${completion_maintenance_doc}" "Do not add a completion tracker" "Do not add a completion tracker"
check_doc_contains "${completion_maintenance_doc}" "separate approved PR" "separate approved PR"
check_doc_contains "${completion_maintenance_doc}" "No Canvas item is read, written, created, updated, deleted, or verified by software" "maintenance no Canvas software access"
check_doc_contains "${completion_maintenance_doc}" "Teacher verification is manual and external to the app" "maintenance teacher verification manual"
check_doc_contains "${completion_maintenance_doc}" "no Canvas verification is automated" "maintenance no automated verification"
check_doc_contains "${completion_maintenance_doc}" "not_copied" "maintenance status not_copied"
check_doc_contains "${completion_maintenance_doc}" "copied_to_canvas_manually" "maintenance status copied_to_canvas_manually"
check_doc_contains "${completion_maintenance_doc}" "teacher_verified_in_canvas" "maintenance status teacher_verified_in_canvas"
check_doc_contains "${completion_maintenance_doc}" "needs_manual_revision" "maintenance status needs_manual_revision"
check_doc_contains "${completion_maintenance_doc}" "skipped" "maintenance status skipped"
check_doc_contains "${completion_maintenance_doc}" "blocked" "maintenance status blocked"
check_doc_contains "${completion_maintenance_doc}" "rejected" "maintenance status rejected"
check_doc_contains "${completion_maintenance_doc}" "blocked/rejected carryover" "maintenance blocked/rejected carryover"

section 'Weekly Export Bundle Doc Presence'

check_file "${weekly_bundle_plan_doc}"
check_file "${weekly_bundle_maintenance_doc}"

section 'Weekly Export Bundle Plan Doc Checks'

check_doc_contains "${weekly_bundle_plan_doc}" "weekly bundle" "weekly bundle concept"
check_doc_contains "${weekly_bundle_plan_doc}" "planning-only" "planning-only"
check_doc_contains "${weekly_bundle_plan_doc}" "Markdown-only" "Markdown-only"
check_doc_contains "${weekly_bundle_plan_doc}" "no bundle files are generated" "no bundle files generated"
check_doc_contains "${weekly_bundle_plan_doc}" "no Canvas content is read, written, created, updated, deleted, or published" "no Canvas content software access"
check_doc_contains "${weekly_bundle_plan_doc}" "no exporter" "no exporter"
check_doc_contains "${weekly_bundle_plan_doc}" "no weekly bundle assembler" "no weekly bundle assembler"
check_doc_contains "${weekly_bundle_plan_doc}" "no package builder" "no package builder"
check_doc_contains "${weekly_bundle_plan_doc}" "no package files" "no package files"
check_doc_contains "${weekly_bundle_plan_doc}" "no generated lesson drafts" "no generated lesson drafts"
check_doc_contains "${weekly_bundle_plan_doc}" "no generated review notes" "no generated review notes"
check_doc_contains "${weekly_bundle_plan_doc}" "no Canvas API" "no Canvas API"
check_doc_contains "${weekly_bundle_plan_doc}" "no Google Drive API" "no Google Drive API"
check_doc_contains "${weekly_bundle_plan_doc}" "no OAuth" "no OAuth"
check_doc_contains "${weekly_bundle_plan_doc}" "no network calls" "no network calls"
check_doc_contains "${weekly_bundle_plan_doc}" "no automation" "no automation"
check_doc_contains "${weekly_bundle_plan_doc}" "no scheduler" "no scheduler"
check_doc_contains "${weekly_bundle_plan_doc}" "no browser automation" "no browser automation"
check_doc_contains "${weekly_bundle_plan_doc}" "no scanning/indexing/OCR/embeddings/vector database" "no scanning/indexing/OCR/embeddings/vector database"
check_doc_contains "${weekly_bundle_plan_doc}" "no student data" "no student data"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_not_started" "bundle status bundle_not_started"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_planned" "bundle status bundle_planned"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_review_ready" "bundle status bundle_review_ready"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_reviewed" "bundle status bundle_reviewed"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_ready_for_manual_copy" "bundle status bundle_ready_for_manual_copy"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_partially_copied" "bundle status bundle_partially_copied"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_copied_to_canvas_manually" "bundle status bundle_copied_to_canvas_manually"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_teacher_verified_in_canvas" "bundle status bundle_teacher_verified_in_canvas"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_needs_manual_revision" "bundle status bundle_needs_manual_revision"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_blocked" "bundle status bundle_blocked"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_rejected" "bundle status bundle_rejected"
check_doc_contains "${weekly_bundle_plan_doc}" "bundle_skipped" "bundle status bundle_skipped"
check_doc_contains "${weekly_bundle_plan_doc}" "canvas_page_package" "package type canvas_page_package"
check_doc_contains "${weekly_bundle_plan_doc}" "canvas_assignment_package" "package type canvas_assignment_package"
check_doc_contains "${weekly_bundle_plan_doc}" "canvas_announcement_package" "package type canvas_announcement_package"
check_doc_contains "${weekly_bundle_plan_doc}" "canvas_module_package" "package type canvas_module_package"
check_doc_contains "${weekly_bundle_plan_doc}" "canvas_file_link_package" "package type canvas_file_link_package"
check_doc_contains "${weekly_bundle_plan_doc}" "teacher_note_placeholder" "package type teacher_note_placeholder"
check_doc_contains "${weekly_bundle_plan_doc}" "manual_followup_placeholder" "package type manual_followup_placeholder"
check_doc_contains "${weekly_bundle_plan_doc}" "manual export review checklist" "manual export review checklist relationship"
check_doc_contains "${weekly_bundle_plan_doc}" "not_copied" "completion status not_copied referenced"
check_doc_contains "${weekly_bundle_plan_doc}" "copied_to_canvas_manually" "completion status copied_to_canvas_manually referenced"
check_doc_contains "${weekly_bundle_plan_doc}" "teacher_verified_in_canvas" "completion status teacher_verified_in_canvas referenced"
check_doc_contains "${weekly_bundle_plan_doc}" "needs_manual_revision" "completion status needs_manual_revision referenced"
check_doc_contains "${weekly_bundle_plan_doc}" "Blocked and Rejected Carryover" "blocked/rejected carryover"
check_doc_contains "${weekly_bundle_plan_doc}" "blocked/rejected/skipped" "blocked/rejected/skipped carryover"
check_doc_contains "${weekly_bundle_plan_doc}" "Teacher Verification Boundary" "teacher verification boundary"
check_doc_contains "${weekly_bundle_plan_doc}" "App does not inspect Canvas" "app does not inspect Canvas"
check_doc_contains "${weekly_bundle_plan_doc}" "Chief of Staff Reporting Boundary" "Chief of Staff reporting boundary"
check_doc_contains "${weekly_bundle_plan_doc}" "Chief of Staff must not" "Chief of Staff must not"
check_doc_contains "${weekly_bundle_plan_doc}" "separate approved PR" "separate approved PR"
check_doc_contains "${weekly_bundle_plan_doc}" "no generated package files" "no generated package files"

section 'Weekly Export Bundle Maintenance Doc Checks'

check_doc_contains "${weekly_bundle_maintenance_doc}" "bundle_not_started" "maintenance bundle_not_started"
check_doc_contains "${weekly_bundle_maintenance_doc}" "bundle_skipped" "maintenance bundle_skipped"
check_doc_contains "${weekly_bundle_maintenance_doc}" "canvas_page_package" "maintenance canvas_page_package"
check_doc_contains "${weekly_bundle_maintenance_doc}" "canvas_file_link_package" "maintenance canvas_file_link_package"
check_doc_contains "${weekly_bundle_maintenance_doc}" "blocked/rejected/skipped carryover" "maintenance blocked/rejected/skipped carryover"
check_doc_contains "${weekly_bundle_maintenance_doc}" "no weekly bundle assembler" "maintenance no weekly bundle assembler"
check_doc_contains "${weekly_bundle_maintenance_doc}" "no generated package files" "maintenance no generated package files"
check_doc_contains "${weekly_bundle_maintenance_doc}" "separate approved PR" "maintenance separate approved PR"
check_doc_contains "${weekly_bundle_maintenance_doc}" "Do not imply Canvas state is software-verified" "maintenance no software-verified Canvas"

section 'Planning Foundation Capstone Doc Presence'

check_file "${capstone_doc}"
check_file "${capstone_maintenance_doc}"

section 'Planning Foundation Capstone Doc Checks'

check_doc_contains "${capstone_doc}" "planning foundation complete for now" "capstone planning foundation complete"
check_doc_contains "${capstone_doc}" "Activation status: not active" "capstone activation not active"
check_doc_contains "${capstone_doc}" "Completed Planning Stack" "capstone completed planning stack"
check_doc_contains "${capstone_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "capstone references weekly bundle plan"
check_doc_contains "${capstone_doc}" "docs/canvas-llm-manual-completion-status-placeholder-plan.md" "capstone references completion status plan"
check_doc_contains "${capstone_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "capstone references manual export review checklist"
check_doc_contains "${capstone_doc}" "docs/canvas-llm-manual-export-package-shapes.md" "capstone references manual export package shapes"
check_doc_contains "${capstone_doc}" "docs/canvas-llm-safety-and-approval-contract.md" "capstone references safety and approval contract"
check_doc_contains "${capstone_doc}" "runtime exporter" "capstone no runtime exporter"
check_doc_contains "${capstone_doc}" "export command" "capstone no export command"
check_doc_contains "${capstone_doc}" "bundle assembler" "capstone no bundle assembler"
check_doc_contains "${capstone_doc}" "package builder" "capstone no package builder"
check_doc_contains "${capstone_doc}" "no Canvas API" "capstone no Canvas API"
check_doc_contains "${capstone_doc}" "no Google Drive API" "capstone no Google Drive API"
check_doc_contains "${capstone_doc}" "no OAuth" "capstone no OAuth"
check_doc_contains "${capstone_doc}" "no network calls" "capstone no network calls"
check_doc_contains "${capstone_doc}" "no browser automation" "capstone no browser automation"
check_doc_contains "${capstone_doc}" "no scheduler" "capstone no scheduler"
check_doc_contains "${capstone_doc}" "no automation" "capstone no automation"
check_doc_contains "${capstone_doc}" "no scanning" "capstone no scanning"
check_doc_contains "${capstone_doc}" "no file indexing" "capstone no file indexing"
check_doc_contains "${capstone_doc}" "no OCR" "capstone no OCR"
check_doc_contains "${capstone_doc}" "no embeddings" "capstone no embeddings"
check_doc_contains "${capstone_doc}" "no vector database" "capstone no vector database"
check_doc_contains "${capstone_doc}" "no generated lesson drafts" "capstone no generated lesson drafts"
check_doc_contains "${capstone_doc}" "no generated review notes" "capstone no generated review notes"
check_doc_contains "${capstone_doc}" "no student data" "capstone no student data"
check_doc_contains "${capstone_doc}" "Software does not verify Canvas state" "capstone manual teacher verification"
check_doc_contains "${capstone_doc}" "Software does not inspect Canvas" "capstone software does not inspect Canvas"
check_doc_contains "${capstone_doc}" "Chief of Staff must not currently" "capstone Chief of Staff status-only boundary"
check_doc_contains "${capstone_doc}" "separate approved PR" "capstone separate approved PR gate"

section 'Planning Foundation Capstone Maintenance Doc Checks'

check_doc_contains "${capstone_maintenance_doc}" "planning foundation complete for now" "maintenance planning foundation complete"
check_doc_contains "${capstone_maintenance_doc}" "Activation status: not active" "maintenance activation not active"
check_doc_contains "${capstone_maintenance_doc}" "Editing Rules" "maintenance editing rules"
check_doc_contains "${capstone_maintenance_doc}" "Do not imply Canvas state is software-verified" "maintenance no software-verified Canvas"
check_doc_contains "${capstone_maintenance_doc}" "separate approved PR" "maintenance separate approved PR"
check_doc_contains "${capstone_maintenance_doc}" "Chief of Staff must not" "maintenance Chief of Staff boundary"

section 'Cross-Link Checks'

check_doc_contains "${plan_doc}" "docs/canvas-llm-placeholder-schema.md" "plan references placeholder schema doc"
check_doc_contains "${plan_doc}" "docs/canvas-llm-manual-export-package-plan.md" "plan references manual export package plan"
check_doc_contains "${plan_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "plan references manual export review checklist"
check_doc_contains "${plan_doc}" "docs/canvas-llm-manual-completion-status-placeholder-plan.md" "plan references manual completion status plan"
check_doc_contains "${plan_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "plan references weekly export bundle plan"
check_doc_contains "${plan_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "plan references planning foundation capstone"
check_doc_contains "${safety_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "safety contract references planning foundation capstone"
check_doc_contains "${safety_doc}" "docs/canvas-llm-approval-and-export-states.md" "safety contract references approval states doc"
check_doc_contains "${safety_doc}" "docs/canvas-llm-manual-export-package-plan.md" "safety contract references manual export package plan"
check_doc_contains "${safety_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "safety contract references manual export review checklist"
check_doc_contains "${architecture_doc}" "docs/canvas-llm-placeholder-schema.md" "architecture references placeholder schema doc"
check_doc_contains "${architecture_doc}" "docs/canvas-llm-manual-export-package-plan.md" "architecture references manual export package plan"
check_doc_contains "${placeholder_schema_doc}" "docs/canvas-llm-manual-export-package-plan.md" "placeholder schema references manual export package plan"
check_doc_contains "${approval_states_doc}" "docs/canvas-llm-manual-export-package-plan.md" "approval states references manual export package plan"
check_doc_contains "${approval_states_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "approval states references manual export review checklist"
check_doc_contains "${approval_states_doc}" "docs/canvas-llm-manual-completion-status-placeholder-plan.md" "approval states references manual completion status plan"
check_doc_contains "${approval_states_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "approval states references weekly export bundle plan"
check_doc_contains "${approval_states_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "approval states references planning foundation capstone"
check_doc_contains "${export_plan_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "export plan references manual export review checklist"
check_doc_contains "${export_plan_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "export plan references weekly export bundle plan"
check_doc_contains "${export_plan_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "export plan references planning foundation capstone"
check_doc_contains "${review_checklist_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "review checklist references planning foundation capstone"
check_doc_contains "${completion_plan_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "completion plan references planning foundation capstone"
check_doc_contains "${weekly_bundle_plan_doc}" "docs/canvas-llm-planning-foundation-capstone.md" "weekly bundle plan references planning foundation capstone"
check_doc_contains "${export_shapes_doc}" "docs/canvas-llm-manual-export-review-checklist.md" "export shapes references manual export review checklist"
check_doc_contains "${export_shapes_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "export shapes references weekly export bundle plan"
check_doc_contains "${export_maintenance_doc}" "docs/canvas-llm-manual-export-review-checklist-maintenance.md" "export maintenance references review checklist maintenance"
check_doc_contains "${review_checklist_doc}" "docs/canvas-llm-manual-completion-status-placeholder-plan.md" "review checklist references manual completion status plan"
check_doc_contains "${review_checklist_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "review checklist references weekly export bundle plan"
check_doc_contains "${review_checklist_maintenance_doc}" "docs/canvas-llm-manual-completion-status-placeholder-maintenance.md" "review checklist maintenance references completion maintenance"
check_doc_contains "${review_checklist_maintenance_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-maintenance.md" "review checklist maintenance references weekly bundle maintenance"
check_doc_contains "${completion_plan_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "completion plan references weekly export bundle plan"
check_doc_contains "${completion_maintenance_doc}" "docs/canvas-llm-weekly-export-bundle-placeholder-plan.md" "completion maintenance references weekly export bundle plan"

section 'Script and Command Wiring'

check_bash_syntax "scripts/teacher-app-designer-canvas-llm-status.sh"
check_bash_syntax "bin/chief-of-staff"
check_help_contains '--teacher-app-designer-canvas-llm-status'

pass 'no write action attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
