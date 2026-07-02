#!/usr/bin/env bash
# Tests for Curriculum Builder Registry v0.2 local fake records (CB-IMPL-2).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry v0.2 local records tests..."

validator="scripts/curriculum-builder-registry-v0-2-local-records-validate.sh"
fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-records.XXXXXX")"
bash "${validator}" "${fixture}" >"${tmp}" 2>&1 || {
  echo "FAIL: local records validator exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: validator reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no_production_write: true' "${tmp}" || { echo "FAIL: missing no_production_write"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

bad_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-records-bad.XXXXXX.json")"
python3 - "${fixture}" "${bad_tmp}" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as f:
    data = json.load(f)
data["records"][0]["resource_id"] = "real-school-id-001"
data["records"][0]["source_reference"] = "https://drive.google.com/real"
with open(dst, "w", encoding="utf-8") as f:
    json.dump(data, f)
PY

bad_out="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-records-bad-out.XXXXXX")"
bash "${validator}" "${bad_tmp}" >"${bad_out}" 2>&1 || true
if ! grep -q 'FAIL:' "${bad_out}"; then
  echo "FAIL: validator did not reject invalid fixture"
  cat "${bad_out}"
  rm -f "${bad_tmp}" "${bad_out}"
  exit 1
fi
rm -f "${bad_tmp}" "${bad_out}"

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-live-before.XXXXXX")"
  cp assistant/curriculum-builder/registry/v0/registry.json "${before}"
  bash "${validator}" "${fixture}" >/dev/null 2>&1
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${before}"; then
    echo "FAIL: validator mutated live registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-v02-records-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-records-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: --curriculum-registry-records-status exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI status reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

echo "PASS: Curriculum Builder Registry v0.2 local records tests passed."
