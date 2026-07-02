#!/usr/bin/env bash
# Tests for Curriculum Builder Registry v0.2 manual entry dry-run validator.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry v0.2 dry-run validator tests..."

validator="scripts/curriculum-builder-registry-v0-2-dry-run.sh"
sample="assistant/curriculum-builder/samples/registry-v0-2-dry-run/example-candidate-valid.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-dry-run.XXXXXX")"
bash "${validator}" "${sample}" >"${tmp}" 2>&1 || {
  echo "FAIL: dry-run validator exited nonzero on valid sample"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || {
  echo "FAIL: dry-run validator reported failures on valid sample"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'dry-run validation only' "${tmp}" || {
  echo "FAIL: missing dry-run boundary header"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q 'would_write=false' "${tmp}" || {
  echo "FAIL: missing would_write=false proof"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
rm -f "${tmp}"

bad_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-bad.XXXXXX.json")"
cat >"${bad_tmp}" <<'EOF'
{
  "dry_run_version": "0.2.0",
  "dry_run_mode": "manual_entry_candidate",
  "metadata_only": true,
  "read_only": true,
  "no_registry_write": true,
  "would_write": false,
  "candidate_entry": {
    "resource_id": "real-school-record-001",
    "title": "Sample Worksheet",
    "resource_type": "worksheet",
    "subject": "Example Math Course",
    "grade_band": "Example Grade 5",
    "course": "Example Math Course",
    "unit": "Unit 1",
    "lesson": "Lesson 1",
    "topic": "Example Topic Placeholder",
    "source_reference_id": "example-source-001",
    "source_reference": "https://drive.google.com/real-link",
    "source_system": "google_drive",
    "teacher_only": false,
    "student_facing_allowed": true,
    "review_status": "approved_placeholder",
    "notes": "Invalid dry-run candidate for negative test."
  }
}
EOF

bad_out="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-bad-out.XXXXXX")"
bash "${validator}" "${bad_tmp}" >"${bad_out}" 2>&1 || true
if ! grep -q '^FAIL: [1-9]' "${bad_out}" && ! grep -q 'FAIL: resource_id invalid' "${bad_out}"; then
  echo "FAIL: dry-run validator did not reject invalid candidate"
  cat "${bad_out}"
  rm -f "${bad_tmp}" "${bad_out}"
  exit 1
fi
rm -f "${bad_tmp}" "${bad_out}"

registry_before="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-before.XXXXXX")"
if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  cp assistant/curriculum-builder/registry/v0/registry.json "${registry_before}"
fi
sample_before="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-sample-before.XXXXXX")"
cp "${sample}" "${sample_before}"

bash "${validator}" "${sample}" >/dev/null 2>&1

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${registry_before}"; then
    echo "FAIL: dry-run validator mutated live registry"
    rm -f "${registry_before}" "${sample_before}"
    exit 1
  fi
fi
if ! cmp -s "${sample}" "${sample_before}"; then
  echo "FAIL: dry-run validator mutated sample file"
  rm -f "${registry_before}" "${sample_before}"
  exit 1
fi
rm -f "${registry_before}" "${sample_before}"

echo "PASS: Curriculum Builder Registry v0.2 dry-run validator tests passed."
