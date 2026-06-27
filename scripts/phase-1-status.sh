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
  printf 'Next recommended PR: Chief of Staff command launcher / status dashboard.\n'
fi

if (( COMPARE_0E == 1 && CRITICAL_BLOCKER == 0 )); then
  printf '\nPhase 0E complete; Phase 1 readiness audit complete.\n'
fi

if (( FAIL_COUNT > 0 )); then
  exit 1
fi

exit 0
