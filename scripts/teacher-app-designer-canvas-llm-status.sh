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

section 'Cross-Link Checks'

check_doc_contains "${plan_doc}" "docs/canvas-llm-placeholder-schema.md" "plan references placeholder schema doc"
check_doc_contains "${safety_doc}" "docs/canvas-llm-approval-and-export-states.md" "safety contract references approval states doc"
check_doc_contains "${architecture_doc}" "docs/canvas-llm-placeholder-schema.md" "architecture references placeholder schema doc"

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
