#!/usr/bin/env bash
# Regression guard: fast-smoke tier boundary and vault preservation skip semantics.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running validation performance boundary tests..."

if [[ ! -f tests/smoke-chief-of-staff-cli-boundary-test.sh ]]; then
  echo "FAIL: missing smoke boundary test"
  exit 1
fi
bash tests/smoke-chief-of-staff-cli-boundary-test.sh

if [[ ! -f scripts/validation-smoke-tier-boundary.sh ]]; then
  echo "FAIL: missing validation-smoke-tier-boundary helper"
  exit 1
fi
bash -n scripts/validation-smoke-tier-boundary.sh

# Helper must not false-fail on boundary-guard comment lines in smoke.
tmp="$(mktemp "${TMPDIR:-/tmp}/validation-smoke-boundary-helper.XXXXXX")"
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); }
# shellcheck source=scripts/validation-smoke-tier-boundary.sh
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'whole-system-coherence' 'Whole-system coherence status'
rm -f "${tmp}"
if [[ "${FAIL_COUNT}" -ne 0 ]]; then
  echo "FAIL: validation-smoke-tier-boundary helper false-positive on whole-system-coherence guard"
  exit 1
fi
echo "PASS: validation-smoke-tier-boundary helper accepts smoke boundary guard lines"

start=$(date +%s)
COS_TKV_SKIP_PRESERVATION=1 bash scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh >/dev/null 2>&1 || {
  echo "FAIL: M7e status failed with COS_TKV_SKIP_PRESERVATION=1"
  exit 1
}
elapsed=$(( $(date +%s) - start ))
if [[ "${elapsed}" -gt 30 ]]; then
  echo "FAIL: M7e aggregate preservation skip took ${elapsed}s (expected under 30s)"
  exit 1
fi
echo "PASS: M7e preservation skip completes quickly (${elapsed}s)"

if grep -Fq 'export COS_TKV_SKIP_PRESERVATION=1' scripts/chief-of-staff-dashboard.sh \
  && grep -Fq 'export COS_TKV_SKIP_PRESERVATION=1' scripts/chief-of-staff-validate-all.sh; then
  echo "PASS: dashboard and validate-all export COS_TKV_SKIP_PRESERVATION"
else
  echo "FAIL: dashboard or validate-all missing COS_TKV_SKIP_PRESERVATION export"
  exit 1
fi

echo "PASS: validation performance boundary tests passed."
