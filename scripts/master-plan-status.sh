#!/usr/bin/env bash
# Read-only master plan persistence status. Documentation/status only.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_dir() { [[ -d "$1" ]] && pass "directory exists: $1" || fail "directory missing: $1"; }
check_doc_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "doc mentions ${label}" || fail "${file} must mention ${label}"
}
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Master Plan Persistence Status'
cat <<'EOF'
Status: master_plan_persistence_status_complete
Classification: documentation/status only
Runtime activation: no
Production registry writes: blocked
Canvas API/OAuth/live reads/writes: blocked
Supabase/Firebase new usage: blocked
PASS does not authorize implementation: yes
EOF

section 'Master Plan Documents'
for path in \
  docs/master-plan/README.md \
  docs/master-plan/teacher-ai-workstation-master-plan.md \
  docs/master-plan/build-state-checklist.md \
  docs/master-plan/current-focus.md \
  docs/master-plan/decision-log.md \
  docs/master-plan/uploaded-artifacts-summary.md \
  docs/master-plan/approved-boundaries.md \
  docs/master-plan/roadmap-index.md \
  docs/master-plan/backlog-and-parking-lot.md \
  docs/master-plan/credit-conservation-plan.md \
  docs/master-plan/local-first-data-architecture.md; do
  check_file "${path}"
done

section 'Planning Inbox'
check_dir docs/planning-inbox
check_file docs/planning-inbox/README.md
check_file docs/planning-inbox/chat-sweep-notes.md
check_file docs/planning-inbox/upload-sweep-notes.md
check_file docs/planning-inbox/unconfirmed-ideas.md
check_doc_contains docs/planning-inbox/README.md "non-authoritative" "planning inbox non-authority"

section 'Program Roadmap Folders'
for path in \
  docs/programs/chief-of-staff/README.md \
  docs/programs/canvas-llm/README.md \
  docs/programs/canvas-llm/canvas-llm-phase-plan.md \
  docs/programs/canvas-llm/canvas-knowledge-sweep-plan.md \
  docs/programs/canvas-llm/canvas-self-healing-plan.md \
  docs/programs/curriculum-library/README.md \
  docs/programs/curriculum-library/local-first-curriculum-library-plan.md \
  docs/programs/curriculum-library/source-reference-registry-plan.md \
  docs/programs/lesson-builder/README.md \
  docs/programs/medical-center/README.md \
  docs/programs/medical-center/medical-center-phase-plan.md \
  docs/programs/morning-brief/README.md \
  docs/programs/morning-brief/morning-brief-phase-plan.md \
  docs/programs/classroom-apps/README.md \
  docs/programs/local-llm/README.md \
  docs/programs/widgets-and-workshop/README.md; do
  check_file "${path}"
done

section 'Required Track Representation'
check_doc_contains docs/programs/chief-of-staff/README.md "status, orchestration, safety, readiness" "Chief of Staff role"
check_doc_contains docs/programs/canvas-llm/README.md "Canvas API/OAuth/live writes: blocked" "Canvas LLM blocked integrations"
check_doc_contains docs/programs/canvas-llm/canvas-self-healing-plan.md "planned track" "Canvas self-healing planned track"
check_doc_contains docs/programs/curriculum-library/README.md "Teacher Knowledge Vault" "Teacher Knowledge Vault representation"
check_doc_contains docs/programs/curriculum-library/local-first-curriculum-library-plan.md "local-first metadata/reference architecture" "Curriculum Library local-first architecture"
check_doc_contains docs/programs/medical-center/README.md "Medical Center" "Medical Center representation"
check_doc_contains docs/programs/morning-brief/README.md "Morning Brief" "Morning Brief representation"
check_doc_contains docs/programs/classroom-apps/README.md "Classroom apps" "classroom apps representation"
check_doc_contains docs/programs/local-llm/README.md "no install, no download, no inference" "local LLM non-activation"
check_doc_contains docs/programs/widgets-and-workshop/README.md "no install, no Mac changes" "widgets/workshop non-activation"

section 'Boundaries And Architecture'
check_doc_contains docs/master-plan/build-state-checklist.md "Reality audit status: evidence-backed as of 2026-07-06" "evidence-backed checklist banner"
check_doc_contains docs/master-plan/build-state-checklist.md "master_plan_reality_audit_build_state_complete" "reality audit closure marker"
check_doc_contains docs/master-plan/build-state-checklist.md "## Status Legend" "status legend"
check_doc_contains docs/master-plan/build-state-checklist.md "## Major Track Reality Audit" "major track reality audit"
check_doc_contains docs/master-plan/build-state-checklist.md "BUILT" "BUILT status label"
check_doc_contains docs/master-plan/build-state-checklist.md "PARTIAL" "PARTIAL status label"
check_doc_contains docs/master-plan/build-state-checklist.md "DOCS-ONLY" "DOCS-ONLY status label"
check_doc_contains docs/master-plan/build-state-checklist.md "PLANNED" "PLANNED status label"
check_doc_contains docs/master-plan/build-state-checklist.md "BLOCKED" "BLOCKED status label"
check_doc_contains docs/master-plan/build-state-checklist.md "DEPRECATED" "DEPRECATED status label"
check_doc_contains docs/master-plan/build-state-checklist.md "UNKNOWN / NEEDS REPO AUDIT" "UNKNOWN status label"
check_doc_contains docs/master-plan/build-state-checklist.md "Chief of Staff | **PARTIAL**" "Chief of Staff reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Teacher Knowledge Vault / Curriculum Library | **PARTIAL**" "Teacher Knowledge Vault reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM | **DOCS-ONLY**" "Canvas LLM reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM Phase 0 standards foundation" "Canvas LLM Phase 0 reality note"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM Phase 1 fake/local validator" "Canvas LLM Phase 1 reality note"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas self-healing | **PLANNED**" "Canvas self-healing reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Lesson Builder / Lesson Planning | **PARTIAL**" "Lesson Builder reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Medical Center / System Health | **PARTIAL**" "Medical Center reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Morning Brief / Morning Updates | **PLANNED**" "Morning Brief reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Classroom Apps | **PARTIAL**" "Classroom Apps reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Local LLM | **DOCS-ONLY**" "Local LLM reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Widgets / Workshop / 3D workspace | **PARTIAL**" "Widgets workshop reality status"
check_doc_contains docs/master-plan/build-state-checklist.md "Supabase / Firebase | **DEPRECATED**" "Supabase Firebase deprecated status"
check_doc_contains docs/master-plan/build-state-checklist.md "Credit conservation / validation discipline | **BUILT**" "credit conservation built status"
check_doc_contains docs/master-plan/approved-boundaries.md "Production registry writes or active \`--write\`" "blocked production writes"
check_doc_contains docs/master-plan/approved-boundaries.md "Canvas API/OAuth/live reads/writes/publishing" "blocked Canvas integration"
check_doc_contains docs/master-plan/approved-boundaries.md "Student data" "student data boundary"
check_doc_contains docs/master-plan/local-first-data-architecture.md "Supabase: deprecated and blocked for new work" "Supabase deprecation"
check_doc_contains docs/master-plan/local-first-data-architecture.md "Firebase: deprecated and blocked for new work" "Firebase deprecation"
check_doc_contains docs/master-plan/local-first-data-architecture.md "local JSON, YAML, Markdown, or CSV registries" "local-first registry formats"
check_doc_contains docs/master-plan/credit-conservation-plan.md "targeted repo inspection" "credit-conserving inspection"
check_doc_contains docs/master-plan/credit-conservation-plan.md "validate-all only when required" "validate-all conservation"
check_doc_contains docs/master-plan/build-state-checklist.md "PASS output does not authorize implementation" "PASS semantics"
check_doc_contains docs/master-plan/current-focus.md "Reality Snapshot" "current focus reality snapshot"
check_doc_contains docs/master-plan/roadmap-index.md "Evidence-backed track statuses live in" "roadmap index evidence-backed note"
check_doc_contains docs/master-plan/backlog-and-parking-lot.md "Canvas self-healing runtime" "parking lot Canvas self-healing blocked"

section 'Command Integration'
check_file scripts/master-plan-status.sh
bash -n scripts/master-plan-status.sh && pass "bash syntax ok: scripts/master-plan-status.sh" || fail "bash syntax failed: scripts/master-plan-status.sh"
check_help_contains "--master-plan-status"
check_doc_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--master-plan-status"' "manifest master plan status command"
check_doc_contains docs/build-queue.md "master_plan_persistence_status_complete" "build queue master plan closure"
check_doc_contains docs/build-queue.md "master_plan_reality_audit_build_state_complete" "build queue reality audit closure"
check_doc_contains docs/build-queue.md "canvas_llm_phase_0_standards_foundation_complete" "build queue Canvas Phase 0 closure"
check_doc_contains docs/build-queue.md "canvas_llm_phase_1_fake_local_validator_complete" "build queue Canvas Phase 1 closure"
check_doc_contains assistant/memory/active-priorities.md "Master plan persistence and program roadmap consolidation: complete" "active priorities master plan closure"
check_doc_contains assistant/memory/active-priorities.md "Master plan reality audit and build-state checklist hardening: complete" "active priorities reality audit closure"
check_doc_contains assistant/memory/active-priorities.md "Canvas LLM Phase 0 standards foundation: complete" "active priorities Canvas Phase 0 closure"
check_doc_contains assistant/memory/active-priorities.md "Canvas LLM Phase 1 fake/local validator: complete" "active priorities Canvas Phase 1 closure"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
