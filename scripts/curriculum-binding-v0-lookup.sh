#!/usr/bin/env bash
# Read-only Registry–Contract Binding v0 lookup only. No resolution, writes, or network calls.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

binding_root="assistant/curriculum-builder/binding/v0"
manifest_file="${binding_root}/binding-manifest.json"
registry_id="${1:-}"

section 'Curriculum Registry–Contract Binding v0 Read-Only Lookup'
cat <<'EOF'
Status: read-only lookup only
Network calls: no
Drive/NAS/iCloud resolution: no
Scanning: no
Registry writes: no
Contract writes: no
EOF

if [[ ! -f "${manifest_file}" ]]; then
  fail "binding manifest missing: ${manifest_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "binding manifest exists: ${manifest_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for binding lookup"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

lookup_output="$(python3 - "${manifest_file}" "${registry_id}" <<'PY'
import json
import os
import re
import sys

manifest_file = sys.argv[1]
registry_id_filter = sys.argv[2]

REGISTRY_ID_PATTERN = re.compile(r"^sample-[a-z0-9-]+$")

errors = []


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_contracts(contract_root, manifest):
    contracts = []
    paths = []
    canonical_contracts = manifest.get("canonical_contracts")
    if isinstance(canonical_contracts, list) and canonical_contracts:
        paths.extend(canonical_contracts)
    else:
        canonical = manifest.get("canonical_contract")
        if isinstance(canonical, str):
            paths.append(canonical)
    for rel in manifest.get("placeholder_contracts", []) or []:
        paths.append(rel)
    for rel in paths:
        path = os.path.join(contract_root, rel)
        if not os.path.isfile(path):
            errors.append(f"contract file missing: {rel}")
            continue
        contracts.append(load_json(path))
    return contracts


binding_manifest = load_json(manifest_file)
registry_source = binding_manifest.get("registry_source")
contract_root = binding_manifest.get("contract_root")
contract_manifest_path = binding_manifest.get("contract_manifest")

registry_records = {}
if isinstance(registry_source, str) and os.path.isfile(registry_source):
    registry_data = load_json(registry_source)
    for record in registry_data.get("records", []):
        if isinstance(record, dict) and isinstance(record.get("registry_id"), str):
            registry_records[record["registry_id"]] = record

contracts = []
if (
    isinstance(contract_root, str)
    and os.path.isdir(contract_root)
    and isinstance(contract_manifest_path, str)
    and os.path.isfile(contract_manifest_path)
):
    contracts = load_contracts(contract_root, load_json(contract_manifest_path))

reverse_index = {rid: [] for rid in registry_records}
contract_refs = {}

for contract in contracts:
    contract_id = contract.get("contract_id", "unknown")
    refs = contract.get("registry_references", [])
    if not isinstance(refs, list):
        errors.append(f"{contract_id} registry_references must be an array")
        continue
    contract_refs[contract_id] = refs
    for ref in refs:
        if isinstance(ref, str) and ref in reverse_index:
            reverse_index[ref].append(contract_id)

if registry_id_filter:
    if not REGISTRY_ID_PATTERN.match(registry_id_filter):
        errors.append(f"malformed registry_id: {registry_id_filter!r}")
    elif registry_id_filter not in registry_records:
        errors.append(f"registry_id not found in Registry v0: {registry_id_filter}")
    else:
        matches = sorted(reverse_index.get(registry_id_filter, []))
        record = registry_records[registry_id_filter]
        print(f"PASS: registry lookup for {registry_id_filter}")
        print(
            f"PASS: registry record title: {record.get('title', 'unknown')}"
        )
        if matches:
            for contract_id in matches:
                contract = next(
                    (item for item in contracts if item.get("contract_id") == contract_id),
                    {},
                )
                contract_type = contract.get("contract_type", "unknown")
                print(
                    f"PASS: referenced by contract {contract_id} ({contract_type})"
                )
        else:
            print(
                f"PASS: no output contracts reference registry_id {registry_id_filter}"
            )
else:
    print("PASS: full binding lookup report")
    for contract_id in sorted(contract_refs):
        refs = contract_refs[contract_id]
        if refs:
            print(
                f"PASS: contract {contract_id} -> registry_id(s): "
                + ", ".join(refs)
            )
        else:
            print(f"PASS: contract {contract_id} -> registry_id(s): none")
    for registry_id in sorted(registry_records):
        contract_ids = sorted(reverse_index.get(registry_id, []))
        if contract_ids:
            print(
                f"PASS: registry_id {registry_id} <- contract(s): "
                + ", ".join(contract_ids)
            )

for error in errors:
    print(f"FAIL: {error}")

if not errors:
    print("PASS: binding lookup completed without failures")
PY
)" || true

lookup_fail=0
while IFS= read -r line; do
  case "${line}" in
    PASS:*)
      pass "${line#PASS: }"
      ;;
    WARN:*)
      warn "${line#WARN: }"
      ;;
    FAIL:*)
      fail "${line#FAIL: }"
      lookup_fail=1
      ;;
    *)
      if [[ -n "${line}" ]]; then
        printf '%s\n' "${line}"
      fi
      ;;
  esac
done <<< "${lookup_output}"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
