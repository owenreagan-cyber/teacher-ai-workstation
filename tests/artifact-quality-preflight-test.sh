#!/usr/bin/env bash
# Tests for Instructional Artifact Quality preflight validators.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running artifact quality preflight tests..."

python3 tests/artifact_quality/test_preflight.py || {
  echo "FAIL: artifact quality preflight unit tests failed"
  exit 1
}

fixtures_root="fixtures/artifact-quality"
for bucket in passing warning failing; do
  [[ -d "${fixtures_root}/${bucket}" ]] || {
    echo "FAIL: missing fixture bucket ${bucket}"
    exit 1
  }
done

pass_out="$(mktemp "${TMPDIR:-/tmp}/artifact-pass.XXXXXX")"
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --input "${fixtures_root}/passing/worksheet-letter.pdf" >"${pass_out}" 2>&1
grep -q 'FINAL STATUS: PASS' "${pass_out}" || {
  echo "FAIL: passing fixture did not PASS"
  cat "${pass_out}"
  rm -f "${pass_out}"
  exit 1
}
rm -f "${pass_out}"

warn_out="$(mktemp "${TMPDIR:-/tmp}/artifact-warn.XXXXXX")"
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --input "${fixtures_root}/warning/low-utilization.pdf" >"${warn_out}" 2>&1 || true
grep -q 'FINAL STATUS: WARN' "${warn_out}" || {
  echo "FAIL: warning fixture did not WARN"
  cat "${warn_out}"
  rm -f "${warn_out}"
  exit 1
}
rm -f "${warn_out}"

fail_out="$(mktemp "${TMPDIR:-/tmp}/artifact-fail.XXXXXX")"
set +e
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --input "${fixtures_root}/failing/a4-page.pdf" >"${fail_out}" 2>&1
fail_code=$?
set -e
[[ "${fail_code}" -ne 0 ]] || {
  echo "FAIL: failing fixture must exit nonzero"
  cat "${fail_out}"
  rm -f "${fail_out}"
  exit 1
}
grep -q 'FINAL STATUS: FAIL' "${fail_out}" || {
  echo "FAIL: failing fixture did not report FAIL"
  cat "${fail_out}"
  rm -f "${fail_out}"
  exit 1
}
rm -f "${fail_out}"

compare_out="$(mktemp "${TMPDIR:-/tmp}/artifact-compare.XXXXXX")"
python3 scripts/artifact_quality/run_preflight.py \
  --profile teacher-key-letter \
  --subject shurley \
  --student "${fixtures_root}/passing/guided-notes-two-page.pdf" \
  --teacher "${fixtures_root}/passing/teacher-key-two-page.pdf" >"${compare_out}" 2>&1
grep -q 'Student and teacher pagination match' "${compare_out}" || {
  echo "FAIL: student/key comparison missing expected PASS line"
  cat "${compare_out}"
  rm -f "${compare_out}"
  exit 1
}
rm -f "${compare_out}"

echo "PASS: artifact quality preflight tests complete"
