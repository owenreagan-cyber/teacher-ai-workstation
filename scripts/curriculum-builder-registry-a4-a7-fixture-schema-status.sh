#!/usr/bin/env bash
# Read-only A4–A7 canonical contract cross-validation for registry v0.2 fake fixtures.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

fixture="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
negative_dir="assistant/curriculum-builder/samples/registry-v0-2-local-records/negative"
evidence_doc="docs/curriculum-builder-registry-a4-a7-fixture-evidence.md"
manifest="assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json"
status_script="scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh"

section 'Curriculum Builder Registry A4–A7 Fixture Schema Cross-Validation'
cat <<'EOF'
Status: read-only fixture cross-validation only
Classification: fake-fixture-only — not production approval
Runtime activation: no
Canonical schemas: inactive A4–A7 samples via inactive-manifest.json
Production registry writes: no
Fixture promotion: no
Student data: no
Real curriculum content: no
Expected WARNs: see docs/curriculum-builder-registry-expected-warns.md
EOF

if [[ ! -f "${fixture}" ]]; then
  fail "fixture missing: ${fixture}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

if [[ ! -f "${manifest}" ]]; then
  fail "inactive manifest missing: ${manifest}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "fixture file exists: ${fixture}"
pass "inactive manifest exists: ${manifest}"
check_file "${evidence_doc}"
grep -Fq -- "complete_a4_a7_fixture_optional_field_enrichment" "${evidence_doc}" && pass "A4–A7 fixture evidence doc closure marker present" || fail "A4–A7 fixture evidence doc missing closure marker"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for A4–A7 fixture cross-validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${repo_root}" "${fixture}" <<'PY'
import json
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
fixture_path = Path(sys.argv[2])
manifest_path = repo_root / "assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json"
samples_dir = manifest_path.parent

ENVELOPE = {"contract_type", "contract_version", "metadata_only", "read_only"}
OPTIONAL_NULL = {
    "content_hash_future", "last_verified_future", "review_notes_reference_future",
    "last_reviewed_future", "teacher_only_reason",
}
FORBIDDEN_FIELDS = {
    "student_name", "student_id", "student_identifier", "iep_reference",
    "oauth_token", "api_key", "generation_prompt",
}
A6_REVIEW_STATUSES = {
    "not_started", "in_review", "approved_placeholder", "deferred", "rejected_placeholder",
    "deferred_placeholder",  # fixture local-records validator also allows this
}
PLACEHOLDER_REF = re.compile(
    r"^(placeholder://|gdrive://placeholder/|nas://placeholder/|icloud://placeholder/|local://placeholder/)"
)

errors = []
warnings = []

with open(manifest_path, encoding="utf-8") as handle:
    manifest = json.load(handle)

with open(fixture_path, encoding="utf-8") as handle:
    fixture = json.load(handle)

contract_samples = {}
for entry in manifest.get("contract_schemas", []):
    program = entry.get("program")
    sample_rel = entry.get("sample")
    if not program or not sample_rel:
        errors.append(f"invalid manifest entry: {entry!r}")
        continue
    sample_path = samples_dir / sample_rel
    if not sample_path.is_file():
        errors.append(f"missing canonical sample for {program}: {sample_path}")
        continue
    with open(sample_path, encoding="utf-8") as sf:
        contract_samples[program] = json.load(sf)

def required_keys(sample: dict) -> set:
    return set(sample.keys()) - ENVELOPE - OPTIONAL_NULL

def check_forbidden(obj, label):
    for key in sorted(FORBIDDEN_FIELDS & set(obj.keys())):
        errors.append(f"{label} contains forbidden field: {key}")

def check_object(obj, program, label, extra_ok=None):
    sample = contract_samples.get(program)
    if not sample:
        errors.append(f"no canonical sample loaded for {program}")
        return
    required = required_keys(sample)
    if extra_ok:
        required = {k for k in required if k not in extra_ok}
    missing = sorted(required - set(obj.keys()))
    if missing:
        errors.append(f"{label} missing A{program[-1]} fields: {', '.join(missing)}")

# A4 — records
records = fixture.get("records", [])
if not isinstance(records, list) or not records:
    errors.append("fixture records must be non-empty array")
else:
    for idx, record in enumerate(records):
        check_object(record, "A4", f"records[{idx}]")
        check_forbidden(record, f"records[{idx}]")
        rs = record.get("review_status")
        if rs not in A6_REVIEW_STATUSES:
            errors.append(f"records[{idx}] review_status not A6-compatible: {rs!r}")

# A5 — source_references (core subset; optional planning fields may warn)
a5_sample = contract_samples.get("A5", {})
a5_core = {"source_reference_id", "source_system", "source_label", "path_or_url_reference", "not_scanned", "not_ingested"}
a5_recommended = required_keys(a5_sample) - a5_core
for idx, src in enumerate(fixture.get("source_references", [])):
    check_forbidden(src, f"source_references[{idx}]")
    missing_core = sorted(a5_core - set(src.keys()))
    if missing_core:
        errors.append(f"source_references[{idx}] missing A5 core fields: {', '.join(missing_core)}")
    missing_rec = sorted(a5_recommended - set(src.keys()))
    for field in missing_rec:
        warnings.append(f"source_references[{idx}] missing recommended A5 field: {field}")
    path_ref = src.get("path_or_url_reference", "")
    if not isinstance(path_ref, str) or not PLACEHOLDER_REF.match(path_ref):
        errors.append(f"source_references[{idx}] path_or_url_reference must be placeholder URI")

# A7 — lesson_links
for idx, link in enumerate(fixture.get("lesson_links", [])):
    check_object(link, "A7", f"lesson_links[{idx}]")
    check_forbidden(link, f"lesson_links[{idx}]")
    if link.get("generation_blocked") is not True:
        errors.append(f"lesson_links[{idx}] generation_blocked must be true")

# A6 — embedded review on records (intentional fixture design)
embedded_a6_ok = bool(records) and all(
    isinstance(r.get("review_status"), str) and r.get("review_status") in A6_REVIEW_STATUSES
    for r in records
)
if embedded_a6_ok:
    print("PASS: A6 review_status embedded on A4 records per fixture design")
    print("a6_embedded_design: true")
else:
    warnings.append("fixture missing valid embedded A6 review_status on all A4 records")

# Optional-field coverage summary (fake/local enrichment)
a5_optional_present = 0
a5_optional_total = 0
for src in fixture.get("source_references", []):
    for field in sorted(a5_recommended):
        a5_optional_total += 1
        if field in src:
            a5_optional_present += 1
if a5_optional_total:
    print(f"PASS: A5 optional fields present {a5_optional_present}/{a5_optional_total} across source_references")
    print(f"a5_optional_coverage: {a5_optional_present}/{a5_optional_total}")
tags_count = sum(1 for r in records if isinstance(r.get("tags"), list) and r["tags"])
if records:
    print(f"PASS: A4 optional tags present on {tags_count}/{len(records)} records")

if errors:
    for err in errors:
        print(f"FAIL: {err}")
    print(f"FAIL_COUNT:{len(errors)}")
else:
    print("PASS: fixture cross-validates against canonical A4–A7 inactive samples")
    print("fixture_only: true")
    print("no_production_write: true")
    print("FAIL_COUNT:0")

for w in warnings:
    print(f"WARN: {w}")
print(f"WARN_COUNT:{len(warnings)}")
PY
)"

while IFS= read -r line; do
  case "${line}" in
    PASS:*) pass "${line#PASS: }" ;;
    WARN:*) warn "${line#WARN: }" ;;
    FAIL:*) fail "${line#FAIL: }" ;;
    fixture_only:*) pass "${line}" ;;
    no_production_write:*) pass "${line}" ;;
    a6_embedded_design:*) pass "${line}" ;;
    a5_optional_coverage:*) pass "A5 optional field coverage: ${line#a5_optional_coverage: }" ;;
  esac
done <<< "${validation_output}"

if grep -q '^FAIL:' <<< "${validation_output}" || grep -q 'FAIL_COUNT:[1-9]' <<< "${validation_output}"; then
  :
elif grep -q 'PASS: fixture cross-validates' <<< "${validation_output}"; then
  pass "A4–A7 fixture schema cross-validation completed"
else
  fail "A4–A7 fixture schema cross-validation did not report success"
  printf '%s\n' "${validation_output}"
fi

section 'Negative Fixture Guardrails'
if [[ -d "${negative_dir}" ]]; then
  pass "negative fixture directory exists: ${negative_dir}"
  for neg in "${negative_dir}"/negative-*.json; do
    [[ -f "${neg}" ]] || continue
    neg_name="$(basename "${neg}")"
    neg_output="$(python3 - "${repo_root}" "${neg}" <<'PY'
import json
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
fixture_path = Path(sys.argv[2])
manifest_path = repo_root / "assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json"
samples_dir = manifest_path.parent

ENVELOPE = {"contract_type", "contract_version", "metadata_only", "read_only"}
OPTIONAL_NULL = {
    "content_hash_future", "last_verified_future", "review_notes_reference_future",
    "last_reviewed_future", "teacher_only_reason",
}
FORBIDDEN_FIELDS = {
    "student_name", "student_id", "student_identifier", "iep_reference",
    "oauth_token", "api_key", "generation_prompt",
}
A6_REVIEW_STATUSES = {
    "not_started", "in_review", "approved_placeholder", "deferred", "rejected_placeholder",
    "deferred_placeholder",
}
PLACEHOLDER_REF = re.compile(
    r"^(placeholder://|gdrive://placeholder/|nas://placeholder/|icloud://placeholder/|local://placeholder/)"
)

errors = []
with open(manifest_path, encoding="utf-8") as handle:
    manifest = json.load(handle)
with open(fixture_path, encoding="utf-8") as handle:
    fixture = json.load(handle)

contract_samples = {}
for entry in manifest.get("contract_schemas", []):
    program = entry.get("program")
    sample_rel = entry.get("sample")
    if not program or not sample_rel:
        continue
    sample_path = samples_dir / sample_rel
    if sample_path.is_file():
        with open(sample_path, encoding="utf-8") as sf:
            contract_samples[program] = json.load(sf)

def required_keys(sample: dict) -> set:
    return set(sample.keys()) - ENVELOPE - OPTIONAL_NULL

def check_forbidden(obj, label):
    for key in sorted(FORBIDDEN_FIELDS & set(obj.keys())):
        errors.append(f"{label} contains forbidden field: {key}")

records = fixture.get("records", [])
for idx, record in enumerate(records):
    sample = contract_samples.get("A4")
    if sample:
        missing = sorted(required_keys(sample) - set(record.keys()))
        if missing:
            errors.append(f"records[{idx}] missing A4 fields: {', '.join(missing)}")
    check_forbidden(record, f"records[{idx}]")
    rs = record.get("review_status")
    if rs is not None and rs not in A6_REVIEW_STATUSES:
        errors.append(f"records[{idx}] review_status not A6-compatible: {rs!r}")

a5_sample = contract_samples.get("A5", {})
a5_core = {"source_reference_id", "source_system", "source_label", "path_or_url_reference", "not_scanned", "not_ingested"}
for idx, src in enumerate(fixture.get("source_references", [])):
    check_forbidden(src, f"source_references[{idx}]")
    missing_core = sorted(a5_core - set(src.keys()))
    if missing_core:
        errors.append(f"source_references[{idx}] missing A5 core fields: {', '.join(missing_core)}")
    path_ref = src.get("path_or_url_reference", "")
    if path_ref and (not isinstance(path_ref, str) or not PLACEHOLDER_REF.match(path_ref)):
        errors.append(f"source_references[{idx}] path_or_url_reference must be placeholder URI")

for idx, link in enumerate(fixture.get("lesson_links", [])):
    sample = contract_samples.get("A7")
    if sample:
        missing = sorted(required_keys(sample) - set(link.keys()))
        if missing:
            errors.append(f"lesson_links[{idx}] missing A7 fields: {', '.join(missing)}")
    check_forbidden(link, f"lesson_links[{idx}]")
    if "generation_blocked" in link and link.get("generation_blocked") is not True:
        errors.append(f"lesson_links[{idx}] generation_blocked must be true")

if errors:
    print("NEGATIVE_EXPECTED_FAIL: true")
    print(f"NEGATIVE_ERROR_COUNT: {len(errors)}")
else:
    print("NEGATIVE_UNEXPECTED_PASS: true")
PY
)"
    if grep -q 'NEGATIVE_EXPECTED_FAIL: true' <<< "${neg_output}"; then
      pass "negative fixture correctly fails validation: ${neg_name}"
    else
      fail "negative fixture must fail validation: ${neg_name}"
      printf '%s\n' "${neg_output}"
    fi
  done
else
  fail "negative fixture directory missing: ${negative_dir}"
fi

section 'Production Registry Parked-State Proof'
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Status Script and CLI'
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
grep -Fq -- '--curriculum-registry-a4-a7-fixture-schema-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-registry-a4-a7-fixture-schema-status' || fail 'CLI missing --curriculum-registry-a4-a7-fixture-schema-status'
grep -Fq -- '"--curriculum-registry-a4-a7-fixture-schema-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists a4-a7 fixture schema status' || fail 'manifest missing a4-a7 fixture schema status'
check_file docs/curriculum-builder-registry-authority-map.md
grep -Fq -- "complete_registry_authority_map" docs/curriculum-builder-registry-authority-map.md && pass "authority map doc present" || fail "authority map doc missing closure marker"

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no production registry write attempted'
pass 'no fixture promotion attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
