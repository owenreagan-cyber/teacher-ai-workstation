#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

next_action="scripts/chief-of-staff-next-action.sh"

echo "Running Chief of Staff next-action tests..."

if ! bash "${next_action}" >/tmp/chief-of-staff-next-action.out 2>&1; then
  echo "FAIL: next-action script failed"
  cat /tmp/chief-of-staff-next-action.out
  exit 1
fi

grep -q 'Recommended major program:' /tmp/chief-of-staff-next-action.out || {
  echo "FAIL: next-action missing major program line"
  cat /tmp/chief-of-staff-next-action.out
  exit 1
}

grep -q 'Chief of Staff v1' /tmp/chief-of-staff-next-action.out || {
  echo "FAIL: next-action missing Chief of Staff v1 recommendation"
  cat /tmp/chief-of-staff-next-action.out
  exit 1
}

grep -q 'frozen' /tmp/chief-of-staff-next-action.out || {
  echo "FAIL: next-action missing canvas frozen status"
  cat /tmp/chief-of-staff-next-action.out
  exit 1
}

grep -q '^FAIL: 0$' /tmp/chief-of-staff-next-action.out || {
  echo "FAIL: next-action reported failures"
  cat /tmp/chief-of-staff-next-action.out
  exit 1
}

bin/chief-of-staff --next-action >/tmp/chief-of-staff-next-action-cos.out
grep -q 'Recommended major program:' /tmp/chief-of-staff-next-action-cos.out || {
  echo "FAIL: chief-of-staff --next-action missing major program"
  cat /tmp/chief-of-staff-next-action-cos.out
  exit 1
}

echo "PASS: Chief of Staff next-action tests passed."
