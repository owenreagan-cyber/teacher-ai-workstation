#!/usr/bin/env bash
# Read-only Curriculum Output Contract v0 validation only. No generation, rendering, or network calls.
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

default_contract_root="assistant/curriculum-builder/output-contract/v0"
contract_root="${1:-${default_contract_root}}"
registry_file="assistant/curriculum-builder/registry/v0/registry.json"

section 'Curriculum Output Contract v0 Read-Only Validator'
cat <<'EOF'
Status: read-only contract validation only
Lesson generation: no
Renderers: no
HTML/PDF generation: no
Canvas package building: no
Ingestion: no
Scanning: no
OCR: no
Embeddings: no
RAG: no
Vector database: no
APIs: no
OAuth: no
Network calls: no
Student data: no
Contract writes: no
EOF

if [[ ! -d "${contract_root}" ]]; then
  fail "contract root missing: ${contract_root}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "contract root exists: ${contract_root}"

if [[ ! -f "${registry_file}" ]]; then
  fail "registry file missing for reference checks: ${registry_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "registry file exists for reference checks: ${registry_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for contract validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${contract_root}" "${registry_file}" <<'PY'
import json
import os
import re
import sys

contract_root = sys.argv[1]
registry_file = sys.argv[2]

CONTRACT_TYPES = {
    "direct_instruction_slide_deck_contract",
    "worksheet_contract",
    "review_game_contract",
    "teacher_script_contract",
    "canvas_export_package_contract",
}
STUDENT_FACING = {"true", "false", "unknown"}
REQUIRED_SAFETY_FLAGS = {
    "metadata_only",
    "no_student_data",
    "not_generated",
    "not_rendered",
    "manual_entry",
    "placeholder_only",
    "no_external_resolution",
}
PLACEHOLDER_REQUIRED = {
    "contract_version", "contract_status", "metadata_only", "read_only",
    "contract_id", "contract_type", "title", "placeholder_status",
    "registry_references", "local_first_safety_flags", "planning_notes",
    "created_by_manual_entry", "activation_status",
}
DI_REQUIRED = {
    "contract_version", "contract_status", "metadata_only", "read_only",
    "contract_id", "contract_type", "title", "subject", "grade_band", "course",
    "unit", "lesson", "registry_references", "teacher_only", "student_facing_allowed",
    "delivery_mode", "slide_count", "slide_outline_placeholders",
    "local_first_safety_flags", "planning_notes", "created_by_manual_entry",
    "activation_status",
}
TS_REQUIRED = {
    "contract_version", "contract_status", "metadata_only", "read_only",
    "contract_id", "contract_type", "title", "subject", "grade_band", "course",
    "unit", "lesson", "registry_references", "teacher_only", "student_facing_allowed",
    "review_state", "approval_status", "lesson_context", "script_sections",
    "local_first_safety_flags", "non_activation_flags", "pedagogy_extensions",
    "metadata_extensions", "planning_notes", "created_by_manual_entry",
    "activation_status",
}
REVIEW_STATES = {
    "not_reviewed", "metadata_only", "teacher_reviewed", "needs_update", "retired",
}
APPROVAL_STATUSES = {
    "not_approved", "placeholder_approved", "blocked_placeholder", "approved", "rejected",
}
REQUIRED_NON_ACTIVATION_FLAGS = {
    "not_generated", "not_rendered", "no_runtime_execution",
    "no_dynamic_variables", "no_student_name_injection",
}
BLOCKED_FIELDS = {
    "html_content", "slide_html", "generated_content", "generated_slides",
    "pdf_path", "canvas_package_uri", "rendered_output", "lesson_draft",
    "embedding_status", "ocr_status", "parsed_text", "generated_script",
    "dynamic_variables", "student_name_injection", "personalized_content",
}
ID_PATTERN = re.compile(r"^sample-contract-[a-z0-9-]+$")
REGISTRY_ID_PATTERN = re.compile(r"^sample-[a-z0-9-]+$")
SLIDE_ID_PATTERN = re.compile(r"^slide-[0-9]{2}$")
SECTION_ID_PATTERN = re.compile(r"^section-[0-9]{2}$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
HTML_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z]", re.IGNORECASE)
STUDENT_NAME_PATTERN = re.compile(
    r"\b(student name|real student|pupil name)\b", re.IGNORECASE
)

errors = []
warnings = []


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def validate_registry_refs(label, refs, registry_ids):
    if not isinstance(refs, list):
        errors.append(f"{label} registry_references must be an array")
        return
    for ref in refs:
        if not isinstance(ref, str) or not REGISTRY_ID_PATTERN.match(ref):
            errors.append(f"{label} invalid registry reference: {ref!r}")
        elif ref not in registry_ids:
            errors.append(f"{label} registry reference not found in Registry v0: {ref}")


def validate_common_envelope(label, data, *, placeholder=False):
    extra = set(data.keys()) & BLOCKED_FIELDS
    if extra:
        errors.append(f"{label} contains blocked generation/render fields: {sorted(extra)}")

    if data.get("contract_version") != "0.1.0":
        errors.append(f"{label} contract_version must be 0.1.0")

    if data.get("metadata_only") is not True:
        errors.append(f"{label} metadata_only must be true")

    if data.get("read_only") is not True:
        errors.append(f"{label} read_only must be true")

    contract_id = data.get("contract_id", "")
    if not isinstance(contract_id, str) or not ID_PATTERN.match(contract_id):
        errors.append(f"{label} invalid contract_id: {contract_id!r}")

    contract_type = data.get("contract_type")
    if contract_type not in CONTRACT_TYPES:
        errors.append(f"{label} invalid contract_type: {contract_type!r}")

    title = data.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{label} title must be non-empty string")
    elif "placeholder" not in title.lower():
        warnings.append(f"{label} title should contain Placeholder for v0 fictional data")

    flags = data.get("local_first_safety_flags")
    if not isinstance(flags, list) or not all(isinstance(item, str) for item in flags):
        errors.append(f"{label} local_first_safety_flags must be string array")
    else:
        missing = REQUIRED_SAFETY_FLAGS - set(flags)
        if missing:
            errors.append(f"{label} missing required safety flags: {sorted(missing)}")

    if data.get("created_by_manual_entry") is not True:
        errors.append(f"{label} created_by_manual_entry must be true")

    combined = json.dumps(data)
    if HTTP_PATTERN.search(combined):
        errors.append(f"{label} must not contain http(s) URLs")
    if HTML_PATTERN.search(combined):
        errors.append(f"{label} must not contain HTML-like content")
    if STUDENT_NAME_PATTERN.search(combined):
        errors.append(f"{label} appears to contain student-identifying text")

    if placeholder:
        if data.get("contract_status") != "placeholder_v0":
            errors.append(f"{label} contract_status must be placeholder_v0")
        if data.get("placeholder_status") != "planning_only":
            errors.append(f"{label} placeholder_status must be planning_only")
        if data.get("activation_status") != "contract_v0_placeholder":
            errors.append(f"{label} activation_status must be contract_v0_placeholder")
    else:
        if data.get("contract_status") != "active_v0":
            errors.append(f"{label} contract_status must be active_v0")
        if data.get("activation_status") != "contract_v0":
            errors.append(f"{label} activation_status must be contract_v0")


def validate_placeholder(label, data, registry_ids):
    for field in PLACEHOLDER_REQUIRED:
        if field not in data:
            errors.append(f"{label} missing required field: {field}")

    validate_common_envelope(label, data, placeholder=True)
    validate_registry_refs(label, data.get("registry_references", []), registry_ids)

    blocked_type_fields = {
        "delivery_mode", "slide_count", "slide_outline_placeholders",
        "subject", "grade_band", "course", "unit", "lesson",
        "teacher_only", "student_facing_allowed", "review_state", "approval_status",
        "lesson_context", "script_sections", "non_activation_flags",
        "pedagogy_extensions", "metadata_extensions",
    }
    present = set(data.keys()) & blocked_type_fields
    if present:
        errors.append(f"{label} placeholder must not include canonical-only fields: {sorted(present)}")


def validate_di_contract(label, data, registry_ids):
    for field in DI_REQUIRED:
        if field not in data:
            errors.append(f"{label} missing required field: {field}")

    extra = set(data.keys()) - DI_REQUIRED
    if extra:
        errors.append(f"{label} unexpected fields: {sorted(extra)}")

    validate_common_envelope(label, data, placeholder=False)

    if data.get("contract_type") != "direct_instruction_slide_deck_contract":
        errors.append(f"{label} contract_type must be direct_instruction_slide_deck_contract")

    if data.get("delivery_mode") != "direct_instruction":
        errors.append(f"{label} delivery_mode must be direct_instruction")

    refs = data.get("registry_references", [])
    validate_registry_refs(label, refs, registry_ids)
    if isinstance(refs, list) and len(refs) < 1:
        errors.append(f"{label} canonical contract requires at least one registry reference")

    teacher_only = data.get("teacher_only")
    if not isinstance(teacher_only, bool):
        errors.append(f"{label} teacher_only must be boolean")

    student_facing = data.get("student_facing_allowed")
    if student_facing not in STUDENT_FACING:
        errors.append(f"{label} invalid student_facing_allowed: {student_facing!r}")
    if teacher_only is True and student_facing == "true":
        errors.append(f"{label} teacher_only true cannot pair with student_facing_allowed true")

    slide_count = data.get("slide_count")
    slides = data.get("slide_outline_placeholders")
    if not isinstance(slide_count, int) or slide_count < 1 or slide_count > 20:
        errors.append(f"{label} slide_count must be integer 1-20")
    if not isinstance(slides, list) or not slides:
        errors.append(f"{label} slide_outline_placeholders must be non-empty array")
    elif isinstance(slide_count, int) and len(slides) != slide_count:
        errors.append(f"{label} slide_count must match slide_outline_placeholders length")
    else:
        seen_slide_ids = set()
        for index, slide in enumerate(slides):
            slide_label = f"{label} slide_outline_placeholders[{index}]"
            if not isinstance(slide, dict):
                errors.append(f"{slide_label} must be an object")
                continue
            for key in ("slide_id", "title_placeholder", "notes_placeholder"):
                if key not in slide:
                    errors.append(f"{slide_label} missing {key}")
            slide_id = slide.get("slide_id", "")
            if not isinstance(slide_id, str) or not SLIDE_ID_PATTERN.match(slide_id):
                errors.append(f"{slide_label} invalid slide_id: {slide_id!r}")
            elif slide_id in seen_slide_ids:
                errors.append(f"{slide_label} duplicate slide_id: {slide_id}")
            else:
                seen_slide_ids.add(slide_id)
            for text_key in ("title_placeholder", "notes_placeholder"):
                value = slide.get(text_key, "")
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{slide_label} {text_key} must be non-empty string")
                elif "placeholder" not in value.lower():
                    warnings.append(f"{slide_label} {text_key} should include placeholder wording")


def validate_teacher_script_contract(label, data, registry_records):
    for field in TS_REQUIRED:
        if field not in data:
            errors.append(f"{label} missing required field: {field}")

    extra = set(data.keys()) - TS_REQUIRED
    if extra:
        errors.append(f"{label} unexpected fields: {sorted(extra)}")

    validate_common_envelope(label, data, placeholder=False)

    if data.get("contract_type") != "teacher_script_contract":
        errors.append(f"{label} contract_type must be teacher_script_contract")

    refs = data.get("registry_references", [])
    validate_registry_refs(label, refs, set(registry_records.keys()))
    if isinstance(refs, list) and len(refs) < 1:
        errors.append(f"{label} canonical contract requires at least one registry reference")

    teacher_only = data.get("teacher_only")
    if teacher_only is not True:
        errors.append(f"{label} teacher_only must be true for teacher script contracts")

    student_facing = data.get("student_facing_allowed")
    if student_facing not in STUDENT_FACING:
        errors.append(f"{label} invalid student_facing_allowed: {student_facing!r}")
    if student_facing == "true":
        errors.append(f"{label} teacher script contract must not be student_facing_allowed true")

    review_state = data.get("review_state")
    if review_state not in REVIEW_STATES:
        errors.append(f"{label} invalid review_state: {review_state!r}")

    approval_status = data.get("approval_status")
    if approval_status not in APPROVAL_STATUSES:
        errors.append(f"{label} invalid approval_status: {approval_status!r}")

    non_activation = data.get("non_activation_flags")
    if not isinstance(non_activation, list) or not all(isinstance(item, str) for item in non_activation):
        errors.append(f"{label} non_activation_flags must be string array")
    else:
        missing = REQUIRED_NON_ACTIVATION_FLAGS - set(non_activation)
        if missing:
            errors.append(f"{label} missing required non_activation_flags: {sorted(missing)}")

    for ext_field in ("pedagogy_extensions", "metadata_extensions"):
        value = data.get(ext_field)
        if not isinstance(value, dict):
            errors.append(f"{label} {ext_field} must be an object")

    lesson_context = data.get("lesson_context")
    if not isinstance(lesson_context, dict):
        errors.append(f"{label} lesson_context must be an object")
    else:
        for key in ("pacing_reference", "delivery_mode", "focus_topic"):
            if key not in lesson_context:
                errors.append(f"{label} lesson_context missing {key}")
        if lesson_context.get("delivery_mode") != "direct_instruction":
            errors.append(f"{label} lesson_context delivery_mode must be direct_instruction")
        focus_topic = lesson_context.get("focus_topic", "")
        if not isinstance(focus_topic, str) or not focus_topic.strip():
            errors.append(f"{label} lesson_context focus_topic must be non-empty string")
        elif "placeholder" not in focus_topic.lower():
            warnings.append(f"{label} lesson_context focus_topic should include placeholder wording")

    sections = data.get("script_sections")
    if not isinstance(sections, list) or not sections:
        errors.append(f"{label} script_sections must be non-empty array")
    else:
        seen_section_ids = set()
        section_text_fields = (
            "section_label", "teacher_script", "teacher_prompt",
            "student_response_expectation", "check_for_understanding",
            "timing_or_pacing_hint", "materials_or_prep_note",
        )
        for index, section in enumerate(sections):
            section_label = f"{label} script_sections[{index}]"
            if not isinstance(section, dict):
                errors.append(f"{section_label} must be an object")
                continue
            for key in ("section_id", *section_text_fields):
                if key not in section:
                    errors.append(f"{section_label} missing {key}")
            section_id = section.get("section_id", "")
            if not isinstance(section_id, str) or not SECTION_ID_PATTERN.match(section_id):
                errors.append(f"{section_label} invalid section_id: {section_id!r}")
            elif section_id in seen_section_ids:
                errors.append(f"{section_label} duplicate section_id: {section_id}")
            else:
                seen_section_ids.add(section_id)
            for text_key in section_text_fields:
                value = section.get(text_key, "")
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{section_label} {text_key} must be non-empty string")
                elif "placeholder" not in value.lower():
                    warnings.append(f"{section_label} {text_key} should include placeholder wording")


def get_canonical_contract_paths(manifest):
    canonical_contracts = manifest.get("canonical_contracts")
    if isinstance(canonical_contracts, list) and canonical_contracts:
        return canonical_contracts
    canonical_contract = manifest.get("canonical_contract")
    if isinstance(canonical_contract, str):
        return [canonical_contract]
    return []


def load_all_contract_paths(manifest):
    paths = get_canonical_contract_paths(manifest)
    placeholders = manifest.get("placeholder_contracts", [])
    if isinstance(placeholders, list):
        paths.extend(placeholders)
    return paths


try:
    registry_data = load_json(registry_file)
except json.JSONDecodeError as exc:
    print(f"FAIL: invalid registry JSON: {exc}")
    sys.exit(0)

registry_ids = {
    record.get("registry_id")
    for record in registry_data.get("records", [])
    if isinstance(record, dict) and isinstance(record.get("registry_id"), str)
}
registry_records = {
    record.get("registry_id"): record
    for record in registry_data.get("records", [])
    if isinstance(record, dict) and isinstance(record.get("registry_id"), str)
}

manifest_path = os.path.join(contract_root, "placeholder-manifest.json")
if not os.path.isfile(manifest_path):
    errors.append(f"manifest missing: {manifest_path}")
else:
    manifest = load_json(manifest_path)
    canonical_rels = get_canonical_contract_paths(manifest)
    placeholder_rels = manifest.get("placeholder_contracts", [])
    if not isinstance(canonical_rels, list) or len(canonical_rels) != 2:
        errors.append("manifest must list exactly 2 canonical contracts")
    if not isinstance(placeholder_rels, list) or len(placeholder_rels) != 3:
        errors.append("manifest must list exactly 3 placeholder contracts")

    for canonical_rel in canonical_rels:
        canonical_path = os.path.join(contract_root, canonical_rel)
        label = f"canonical:{canonical_rel}"
        if not os.path.isfile(canonical_path):
            errors.append(f"canonical contract file missing: {canonical_rel}")
            continue
        contract_data = load_json(canonical_path)
        contract_type = contract_data.get("contract_type")
        if contract_type == "direct_instruction_slide_deck_contract":
            validate_di_contract(label, contract_data, registry_ids)
        elif contract_type == "teacher_script_contract":
            validate_teacher_script_contract(label, contract_data, registry_records)
        else:
            errors.append(f"{label} unsupported canonical contract_type: {contract_type!r}")

    if isinstance(placeholder_rels, list):
        for rel in placeholder_rels:
            path = os.path.join(contract_root, rel)
            label = f"placeholder:{rel}"
            if not os.path.isfile(path):
                errors.append(f"{label} file missing")
                continue
            pdata = load_json(path)
            validate_placeholder(label, pdata, registry_ids)

for warning in warnings:
    print(f"WARN: {warning}")

for error in errors:
    print(f"FAIL: {error}")

if not errors:
    print("PASS: output contract v0 manifest valid")
    print("PASS: canonical direct instruction slide deck contract valid")
    print("PASS: canonical teacher script contract valid")
    print(f"PASS: validated {len(placeholder_rels) if isinstance(placeholder_rels, list) else 0} placeholder contracts")
    print("PASS: registry reference checks completed against Registry v0")
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
