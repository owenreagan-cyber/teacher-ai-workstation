#!/usr/bin/env bash
# Negative tests for first-record production registry validator.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running first-record validator negative tests..."

validator="scripts/curriculum-builder-production-registry-first-record-validate.sh"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
fixture_dir="assistant/curriculum-builder/samples/first-record-planning/negative"

[[ -x "${validator}" || -f "${validator}" ]] || { echo "FAIL: validator missing"; exit 1; }

run_negative() {
  local fixture="$1"
  local label="$2"
  local tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/cb-first-record-neg.XXXXXX")"
  if bash "${validator}" "${fixture}" >"${tmp}" 2>&1; then
    echo "FAIL: ${label} should fail validation"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  fi
  if grep -q 'first production registry record validation succeeded' "${tmp}"; then
    echo "FAIL: ${label} incorrectly succeeded"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  fi
  rm -f "${tmp}"
  echo "PASS: ${label} rejected"
}

for fixture in \
  "${fixture_dir}/negative-two-records.json" \
  "${fixture_dir}/negative-wrong-record-id.json" \
  "${fixture_dir}/negative-url-in-notes.json"; do
  [[ -f "${fixture}" ]] || { echo "FAIL: missing negative fixture ${fixture}"; exit 1; }
done

run_negative "${fixture_dir}/negative-two-records.json" "two-records fixture"
run_negative "${fixture_dir}/negative-wrong-record-id.json" "wrong-record-id fixture"
run_negative "${fixture_dir}/negative-url-in-notes.json" "url-in-notes fixture"

val_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-first-record-pos.XXXXXX")"
bash "${validator}" "${production_registry_path}" >"${val_tmp}" 2>&1 || {
  echo "FAIL: canonical production registry validator exited nonzero"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
grep -q 'first production registry record validation succeeded' "${val_tmp}" || {
  echo "FAIL: canonical production registry must validate"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
rm -f "${val_tmp}"

echo "PASS: First-record validator negative tests passed."
