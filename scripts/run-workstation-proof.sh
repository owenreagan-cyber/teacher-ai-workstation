#!/usr/bin/env bash
# Read-only local proof runner. No network, GitHub API, or uploads.
#
# Execution model:
#   proof-run -> validate-all (no smoke) -> smoke once -> dashboard tail -> proof summary
#   Must never call chief-of-staff-v1-operating-test.sh.
#
# Environment:
#   COS_PROOF_ALREADY_RUNNING   Set internally; nested proof-run fails immediately.
#   COS_PROOF_SKIP_VALIDATE=1   Skip validate-all stage (operating tests use this).
#   COS_PROOF_SKIP_SMOKE=1      Skip smoke stage (operating tests use this).
#   COS_PROOF_SKIP_DASHBOARD=1  Skip dashboard tail stage.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
PROOF_FAILURE=0
PROOF_TMP=""

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
  PROOF_FAILURE=1
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

cleanup() {
  if [[ -n "${PROOF_TMP}" ]]; then
    rm -f "${PROOF_TMP}"
  fi
}
trap cleanup EXIT

# Wrap only known slow operations. Gracefully runs without timeout on macOS when unavailable.
run_with_timeout() {
  local seconds="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "${seconds}" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "${seconds}" "$@"
  else
    "$@"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

if [[ -n "${COS_PROOF_ALREADY_RUNNING:-}" ]]; then
  fail "recursive proof-run detected"
  section 'Proof Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  printf 'Proof status: failed\n'
  exit 1
fi
export COS_PROOF_ALREADY_RUNNING=1

section 'Workstation Proof Runner'
cat <<'EOF'
Status: read-only local proof only
Network calls: no
GitHub API: no
Uploads: no
Lesson generation: no
EOF

section 'Git Baseline Proof'
branch="$(git branch --show-current 2>/dev/null || true)"
printf 'Branch: %s\n' "${branch:-unknown}"
printf 'HEAD: %s\n' "$(git log -1 --oneline 2>/dev/null || echo unknown)"
if [[ "${branch}" == "main" ]]; then
  pass "on main branch"
else
  warn "not on main branch"
fi
if [[ -z "$(git status --short 2>/dev/null || true)" ]]; then
  pass "working tree clean"
else
  warn "working tree has uncommitted changes"
  git status --short
fi

section 'Validation Orchestration'
if [[ "${COS_PROOF_SKIP_VALIDATE:-}" == "1" ]]; then
  pass "validate-all proof skipped (COS_PROOF_SKIP_VALIDATE=1)"
elif [[ -f scripts/chief-of-staff-validate-all.sh ]]; then
  if bash scripts/chief-of-staff-validate-all.sh; then
    pass "validate-all completed"
  else
    fail "validate-all failed"
  fi
else
  fail "validate-all script missing"
fi

section 'Smoke CLI Proof'
if [[ "${COS_PROOF_SKIP_SMOKE:-}" == "1" ]]; then
  pass "smoke CLI proof skipped (COS_PROOF_SKIP_SMOKE=1)"
else
  PROOF_TMP="$(mktemp "${TMPDIR:-/tmp}/run-workstation-proof-smoke.XXXXXX")"
  smoke_result=0
  if run_with_timeout 120 bash tests/smoke-chief-of-staff-cli.sh >"${PROOF_TMP}" 2>&1; then
    pass "smoke CLI proof passed"
  else
    smoke_result=$?
    cat "${PROOF_TMP}"
    if [[ "${smoke_result}" -eq 124 ]]; then
      fail "smoke CLI proof timed out after 120s"
    else
      fail "smoke CLI proof failed"
    fi
  fi
  rm -f "${PROOF_TMP}"
  PROOF_TMP=""
fi

if [[ "${COS_PROOF_SKIP_DASHBOARD:-}" != "1" ]]; then
  section 'Dashboard Snapshot (tail)'
  if [[ -f bin/chief-of-staff ]]; then
    dashboard_result=0
    dashboard_output="$(bin/chief-of-staff --dashboard 2>&1)" || dashboard_result=$?
    printf '%s\n' "${dashboard_output}" | tail -25
    dashboard_fail="$(printf '%s\n' "${dashboard_output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"
    if [[ "${dashboard_result}" != "0" || "${dashboard_fail}" -gt 0 ]]; then
      fail "dashboard proof failed"
    else
      pass "dashboard proof completed"
    fi
  else
    fail "chief-of-staff missing for dashboard proof"
  fi
else
  pass "dashboard proof skipped (COS_PROOF_SKIP_DASHBOARD=1)"
fi

section 'Branch Cleanup Confirmation'
stale_branches="$(git branch 2>/dev/null | grep -v '^\* main$' | grep -v '^  main$' || true)"
if [[ -z "${stale_branches}" ]]; then
  pass "no extra local branches besides main"
else
  warn "local branches present besides main"
  printf '%s\n' "${stale_branches}"
fi

section 'Proof Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
printf 'Proof status: %s\n' "$(if [[ "${PROOF_FAILURE}" -eq 0 ]]; then echo complete; else echo failed; fi)"

if [[ "${PROOF_FAILURE}" -gt 0 ]]; then
  exit 1
fi
exit 0
