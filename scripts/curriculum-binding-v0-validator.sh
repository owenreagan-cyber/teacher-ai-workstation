#!/usr/bin/env bash
# Read-only Registry–Contract Binding v0 validation only. No generation, resolution, or network calls.
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

default_binding_root="assistant/curriculum-builder/binding/v0"
binding_root="${1:-${default_binding_root}}"

section 'Curriculum Registry–Contract Binding v0 Read-Only Validator'
cat <<'EOF'
Status: read-only binding validation only
Lesson generation: no
Renderers: no
HTML/PDF generation: no
Canvas package building: no
Ingestion: no
Scanning: no
Folder crawling: no
OCR: no
Embeddings: no
RAG: no
Vector database: no
APIs: no
OAuth: no
Network calls: no
Drive/NAS/iCloud resolution: no
Student data: no
Registry writes: no
Contract writes: no
EOF

if [[ ! -d "${binding_root}" ]]; then
  fail "binding root missing: ${binding_root}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "binding root exists: ${binding_root}"

manifest_file="${binding_root}/binding-manifest.json"
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
  fail "python3 required for binding validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${binding_root}" "${manifest_file}" <<'PY'
import json
import os
import re
import sys

binding_root = sys.argv[1]
manifest_file = sys.argv[2]

REGISTRY_ID_PATTERN = re.compile(r"^sample-[a-z0-9-]+$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
ALIGNMENT_FIELDS = ("subject", "grade_band", "unit", "lesson")

errors = []
warnings = []


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
    placeholders = manifest.get("placeholder_contracts", [])
    if isinstance(placeholders, list):
        paths.extend(placeholders)
    for rel in paths:
        path = os.path.join(contract_root, rel)
        label = rel
        if not os.path.isfile(path):
            errors.append(f"contract file missing: {rel}")
            continue
        data = load_json(path)
        contracts.append((label, data))
    return contracts


with open(manifest_file, encoding="utf-8") as handle:
    binding_manifest = json.load(handle)

if binding_manifest.get("binding_version") != "0.1.0":
    errors.append("binding_version must be 0.1.0")
if binding_manifest.get("binding_status") != "active_v0":
    errors.append("binding_status must be active_v0")
if binding_manifest.get("metadata_only") is not True:
    errors.append("metadata_only must be true")
if binding_manifest.get("read_only") is not True:
    errors.append("read_only must be true")

registry_source = binding_manifest.get("registry_source")
contract_root_rel = binding_manifest.get("contract_root")
contract_manifest_rel = binding_manifest.get("contract_manifest")

if not isinstance(registry_source, str) or not os.path.isfile(registry_source):
    errors.append(f"registry source missing: {registry_source!r}")
    registry_data = {"records": []}
else:
    registry_data = load_json(registry_source)

if not isinstance(contract_root_rel, str) or not os.path.isdir(contract_root_rel):
    errors.append(f"contract root missing: {contract_root_rel!r}")
    contract_root_rel = contract_root_rel or ""
    contract_manifest = {}
else:
    contract_manifest_path = contract_manifest_rel
    if not isinstance(contract_manifest_path, str) or not os.path.isfile(contract_manifest_path):
        errors.append(f"contract manifest missing: {contract_manifest_rel!r}")
        contract_manifest = {}
    else:
        contract_manifest = load_json(contract_manifest_path)

registry_records = {}
for index, record in enumerate(registry_data.get("records", [])):
    if not isinstance(record, dict):
        errors.append(f"registry records[{index}] must be an object")
        continue
    registry_id = record.get("registry_id")
    if not isinstance(registry_id, str):
        errors.append(f"registry records[{index}] missing registry_id")
        continue
    registry_records[registry_id] = record

contracts = load_contracts(contract_root_rel, contract_manifest) if contract_root_rel else []

reverse_index = {registry_id: [] for registry_id in registry_records}
referenced_registry_ids = set()
contract_to_refs = {}

for label, contract in contracts:
    contract_id = contract.get("contract_id", label)
    refs = contract.get("registry_references", [])
    contract_to_refs[contract_id] = refs

    if not isinstance(refs, list):
        errors.append(f"{label} registry_references must be an array")
        continue

    for ref in refs:
        if not isinstance(ref, str) or not REGISTRY_ID_PATTERN.match(ref):
            errors.append(f"{label} malformed registry reference: {ref!r}")
            continue
        if HTTP_PATTERN.search(ref):
            errors.append(f"{label} registry reference must not contain http(s) URL: {ref}")
            continue
        if ref not in registry_records:
            errors.append(f"{label} registry reference not found in Registry v0: {ref}")
            continue
        referenced_registry_ids.add(ref)
        reverse_index.setdefault(ref, []).append(contract_id)

        if contract.get("contract_status") == "active_v0":
            record = registry_records[ref]
            for field in ALIGNMENT_FIELDS:
                contract_value = contract.get(field)
                record_value = record.get(field)
                if (
                    isinstance(contract_value, str)
                    and isinstance(record_value, str)
                    and contract_value
                    and record_value
                    and contract_value != record_value
                ):
                    warnings.append(
                        f"{label} {field} alignment mismatch for {ref}: "
                        f"contract={contract_value!r} registry={record_value!r}"
                    )

for registry_id, contract_ids in sorted(reverse_index.items()):
    if contract_ids:
        joined = ", ".join(sorted(contract_ids))
        print(f"PASS: registry_id {registry_id} referenced by contract(s): {joined}")

unreferenced = sorted(set(registry_records) - referenced_registry_ids)
if unreferenced:
    print(
        "PASS: registry records without contract references: "
        + ", ".join(unreferenced)
    )

for contract_id, refs in sorted(contract_to_refs.items()):
    if isinstance(refs, list):
        if refs:
            print(
                f"PASS: contract {contract_id} references registry_id(s): "
                + ", ".join(refs)
            )
        else:
            print(f"PASS: contract {contract_id} has no registry references")

for warning in warnings:
    print(f"WARN: {warning}")

for error in errors:
    print(f"FAIL: {error}")

if not errors:
    print("PASS: all contract registry references exist in Registry v0")
    print("PASS: no malformed registry references detected")
    print("PASS: binding reverse index built successfully")
    print(f"PASS: validated {len(contracts)} contracts against {len(registry_records)} registry records")
PY
)" || true

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
      ;;
    *)
      if [[ -n "${line}" ]]; then
        printf '%s\n' "${line}"
      fi
      ;;
  esac
done <<< "${validation_output}"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
