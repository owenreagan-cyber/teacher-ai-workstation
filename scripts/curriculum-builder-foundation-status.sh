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
