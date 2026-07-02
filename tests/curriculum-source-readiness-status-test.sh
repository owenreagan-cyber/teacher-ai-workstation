#!/usr/bin/env bash
# Tests for Curriculum Source Readiness foundation status and validator guardrails.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Source Readiness status tests..."

status_script="scripts/curriculum-source-readiness-status.sh"
validator="scripts/curriculum-source-readiness-validate.sh"
inventory="assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json"
negative_dir="assistant/curriculum-builder/samples/curriculum-source-readiness/negative"

tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-source-readiness.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: readiness status script exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: readiness status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'fake_fixture_only' "${tmp}" || { echo "FAIL: missing fake_fixture_only banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'Real curriculum ingestion: blocked' "${tmp}" || { echo "FAIL: missing blocked ingestion banner"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'negative fixture rejected' "${tmp}" || { echo "FAIL: missing negative fixture checks"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

val_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-source-readiness-val.XXXXXX")"
bash "${validator}" "${inventory}" >"${val_tmp}" 2>&1 || {
  echo "FAIL: validator exited nonzero on canonical inventory"
  cat "${val_tmp}"
  rm -f "${val_tmp}"
  exit 1
}
grep -q 'inventory validation succeeded' "${val_tmp}" || { echo "FAIL: canonical inventory validation failed"; cat "${val_tmp}"; rm -f "${val_tmp}"; exit 1; }
rm -f "${val_tmp}"

for neg in \
  negative-ingestion-allowed.json \
  negative-student-data-allowed.json \
  negative-real-content-allowed.json \
  negative-production-write-allowed.json \
  negative-drive-url.json \
  negative-absolute-path.json \
  negative-student-field.json; do
  neg_path="${negative_dir}/${neg}"
  if bash "${validator}" "${neg_path}" >/dev/null 2>&1; then
    echo "FAIL: negative fixture should fail validation: ${neg}"
    exit 1
  fi
done
echo "PASS: all negative fixtures rejected by validator"

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/csr-live-before.XXXXXX")"
  cp assistant/curriculum-builder/registry/v0/registry.json "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${before}"; then
    echo "FAIL: readiness status mutated live registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

if [[ -f "${inventory}" ]]; then
  before_inv="$(mktemp "${TMPDIR:-/tmp}/csr-inventory-before.XXXXXX")"
  cp "${inventory}" "${before_inv}"
  bash "${status_script}" >/dev/null 2>&1
  bash "${validator}" "${inventory}" >/dev/null 2>&1
  if ! cmp -s "${inventory}" "${before_inv}"; then
    echo "FAIL: readiness scripts mutated fake inventory"
    rm -f "${before_inv}"
    exit 1
  fi
  rm -f "${before_inv}"
fi

if grep -Fq -- '--curriculum-source-write)' bin/chief-of-staff 2>/dev/null; then
  echo "FAIL: chief-of-staff must not implement --curriculum-source-write"
  exit 1
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/curriculum-source-readiness-cli.XXXXXX")"
bin/chief-of-staff --curriculum-source-readiness-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-source-readiness-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI readiness status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-source-readiness-status'; then
  echo "FAIL: --help missing --curriculum-source-readiness-status"
  exit 1
fi

if ! grep -Fq -- '"--curriculum-source-readiness-status"' assistant/chief-of-staff/v1/command-surface-manifest.json; then
  echo "FAIL: manifest missing --curriculum-source-readiness-status"
  exit 1
fi

echo "PASS: Curriculum Source Readiness status tests passed."
