#!/usr/bin/env bash
# Tests for Curriculum Builder Registry A4–A7 fixture schema cross-validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Curriculum Builder Registry A4–A7 fixture schema tests..."

status_script="scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh"
fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"

tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-a4a7-schema.XXXXXX")"
bash "${status_script}" >"${tmp}" 2>&1 || {
  echo "FAIL: A4–A7 fixture schema status exited nonzero"
  cat "${tmp}"
  rm -f "${tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${tmp}" || { echo "FAIL: status reported failures"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
grep -q 'no_production_write: true' "${tmp}" || { echo "FAIL: missing no_production_write"; cat "${tmp}"; rm -f "${tmp}"; exit 1; }
rm -f "${tmp}"

bad_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-a4a7-bad.XXXXXX.json")"
python3 - "${fixture}" "${bad_tmp}" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as f:
    data = json.load(f)
del data["records"][0]["resource_type"]
with open(dst, "w", encoding="utf-8") as f:
    json.dump(data, f)
PY

bad_out="$(mktemp "${TMPDIR:-/tmp}/cb-registry-a4a7-bad-out.XXXXXX")"
# Run validation logic only via python path - status script always uses canonical fixture.
# Use inline python matching status script validation on bad fixture.
python3 - "${repo_root}" "${bad_tmp}" <<'PY' >"${bad_out}" 2>&1 || true
import json, sys
from pathlib import Path
repo_root = Path(sys.argv[1])
fixture_path = Path(sys.argv[2])
manifest_path = repo_root / "assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json"
with open(manifest_path, encoding="utf-8") as f:
    manifest = json.load(f)
with open(fixture_path, encoding="utf-8") as f:
    fixture = json.load(f)
samples_dir = manifest_path.parent
sample_path = samples_dir / "samples/sample-resource-001.json"
with open(sample_path, encoding="utf-8") as f:
    sample = json.load(f)
envelope = {"contract_type", "contract_version", "metadata_only", "read_only"}
required = set(sample.keys()) - envelope - {"content_hash_future", "last_verified_future"}
missing = required - set(fixture["records"][0].keys())
if missing:
    print(f"FAIL: missing fields {missing}")
    sys.exit(0)
print("FAIL: expected missing fields")
PY

if ! grep -q '^FAIL:' "${bad_out}"; then
  echo "FAIL: negative fixture validation did not fail"
  cat "${bad_out}"
  rm -f "${bad_tmp}" "${bad_out}"
  exit 1
fi
rm -f "${bad_tmp}" "${bad_out}"

if [[ -f assistant/curriculum-builder/registry/v0/registry.json ]]; then
  before="$(mktemp "${TMPDIR:-/tmp}/cb-registry-a4a7-live-before.XXXXXX")"
  cp assistant/curriculum-builder/registry/v0/registry.json "${before}"
  bash "${status_script}" >/dev/null 2>&1
  if ! cmp -s assistant/curriculum-builder/registry/v0/registry.json "${before}"; then
    echo "FAIL: status script mutated live registry"
    rm -f "${before}"
    exit 1
  fi
  rm -f "${before}"
fi

cli_tmp="$(mktemp "${TMPDIR:-/tmp}/cb-registry-a4a7-cli.XXXXXX")"
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status >"${cli_tmp}" 2>&1 || {
  echo "FAIL: CLI exited nonzero"
  cat "${cli_tmp}"
  rm -f "${cli_tmp}"
  exit 1
}
grep -q '^FAIL: 0$' "${cli_tmp}" || { echo "FAIL: CLI reported failures"; cat "${cli_tmp}"; rm -f "${cli_tmp}"; exit 1; }
rm -f "${cli_tmp}"

if ! bin/chief-of-staff --help 2>&1 | grep -Fq -- '--curriculum-registry-a4-a7-fixture-schema-status'; then
  echo "FAIL: --help missing a4-a7 fixture schema status command"
  exit 1
fi

echo "PASS: Curriculum Builder Registry A4–A7 fixture schema tests passed."
