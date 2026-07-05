#!/usr/bin/env bash
# Shared fast-smoke tier boundary helpers for status scripts.
# Smoke must stay fast: no dashboard, validate-all, coherence, vault M*, or deep suites.
# See docs/validation-tiers.md and tests/smoke-chief-of-staff-cli-boundary-test.sh.
#
# Usage (from a status script with pass/fail defined):
#   source scripts/validation-smoke-tier-boundary.sh
#   check_smoke_excludes_deep_validation 'teacher-knowledge-vault-m0' 'Teacher Knowledge Vault M0'

check_smoke_excludes_deep_validation() {
  local pattern="$1"
  local label="$2"
  local smoke_file="tests/smoke-chief-of-staff-cli.sh"
  local boundary_test="tests/smoke-chief-of-staff-cli-boundary-test.sh"
  local executable_lines

  if [[ ! -f "${smoke_file}" ]]; then
    fail "smoke file missing: ${smoke_file}"
    return
  fi
  if [[ ! -f "${boundary_test}" ]]; then
    fail "smoke boundary test missing: ${boundary_test}"
    return
  fi

  executable_lines="$(grep -v '^[[:space:]]*#' "${smoke_file}" \
    | grep -E 'bin/chief-of-staff|bash (scripts|tests)/' \
    | grep -v 'Boundary guard')"

  if printf '%s\n' "${executable_lines}" | grep -q -F -e "${pattern}"; then
    fail "smoke must not invoke deep validation: ${label}"
  else
    pass "smoke excludes deep validation: ${label} (fast-smoke tier)"
  fi
}
