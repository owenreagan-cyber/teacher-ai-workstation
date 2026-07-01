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
