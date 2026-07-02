#!/usr/bin/env bash
# Lightweight operating checks for validation/proof orchestration commands.
# Must never invoke smoke, validate-all with smoke, or full proof-run (smoke/dashboard).
#
# Execution model:
#   operating test -> individual commands -> lightweight proof (git baseline only)
set -euo pipefail

if [[ -n "${COS_OPERATING_TEST_RUNNING:-}" ]]; then
  echo "FAIL: recursive chief-of-staff-v1-operating-test.sh detected"
  exit 1
fi
export COS_OPERATING_TEST_RUNNING=1

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

OPERATING_TMP=""

cleanup() {
  if [[ -n "${OPERATING_TMP}" ]]; then
    rm -f "${OPERATING_TMP}"
  fi
}
trap cleanup EXIT

echo "Running Chief of Staff v1 operating command tests..."

for cmd in --next-action --commands; do
  OPERATING_TMP="$(mktemp "${TMPDIR:-/tmp}/chief-of-staff-v1-${cmd#--}.XXXXXX")"
  bin/chief-of-staff "${cmd}" >"${OPERATING_TMP}" 2>&1 || {
    echo "FAIL: ${cmd} exited nonzero"
    cat "${OPERATING_TMP}"
    exit 1
  }
  grep -q '^FAIL: 0$' "${OPERATING_TMP}" || {
    echo "FAIL: ${cmd} reported failures"
    cat "${OPERATING_TMP}"
    exit 1
  }
  rm -f "${OPERATING_TMP}"
  OPERATING_TMP=""
done

OPERATING_TMP="$(mktemp "${TMPDIR:-/tmp}/chief-of-staff-v1-validate-all.XXXXXX")"
bin/chief-of-staff --validate-all >"${OPERATING_TMP}" 2>&1 || {
  echo "FAIL: --validate-all exited nonzero"
  cat "${OPERATING_TMP}"
  exit 1
}
grep -q '^FAIL: 0$' "${OPERATING_TMP}" || {
  echo "FAIL: --validate-all reported failures"
  cat "${OPERATING_TMP}"
  exit 1
}
rm -f "${OPERATING_TMP}"
OPERATING_TMP=""

OPERATING_TMP="$(mktemp "${TMPDIR:-/tmp}/chief-of-staff-v1-proof-run.XXXXXX")"
COS_PROOF_SKIP_DASHBOARD=1 COS_PROOF_SKIP_VALIDATE=1 COS_PROOF_SKIP_SMOKE=1 \
  bin/chief-of-staff --proof-run >"${OPERATING_TMP}" 2>&1 || {
  echo "FAIL: --proof-run exited nonzero"
  cat "${OPERATING_TMP}"
  exit 1
}
grep -q 'Proof status: complete' "${OPERATING_TMP}" || {
  echo "FAIL: proof-run missing complete status"
  cat "${OPERATING_TMP}"
  exit 1
}
rm -f "${OPERATING_TMP}"
OPERATING_TMP=""

echo "PASS: Chief of Staff v1 operating command tests passed."
