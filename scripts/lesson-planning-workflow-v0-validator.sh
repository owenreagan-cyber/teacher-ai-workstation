#!/usr/bin/env bash
# Read-only Lesson Planning Workflow v0 validation only. No generation, network calls, or writes.
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

default_workflow_file="assistant/lesson-planning/workflow/v0/sample-lesson-workflow-001.json"
workflow_file="${1:-${default_workflow_file}}"

section 'Lesson Planning Workflow v0 Read-Only Validator'
cat <<'EOF'
Status: read-only validation only
Lesson generation: no
Generated briefs: no
Generated drafts: no
Real review notes: no
Student data: no
LLM calls: no
APIs: no
OAuth: no
Network calls: no
Retrieval: no
Renderers: no
EOF

if [[ ! -f "${workflow_file}" ]]; then
  fail "workflow file missing: ${workflow_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "workflow file exists: ${workflow_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for workflow validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${workflow_file}" <<'PY'
import json
import re
import sys

workflow_file = sys.argv[1]

PLANNING_STATUSES = {"idea", "drafted", "reviewed", "ready", "archived"}
REVIEW_STATUSES = {"not_reviewed", "metadata_only", "teacher_reviewed", "needs_review"}
REQUIRED_WORKFLOW_FIELDS = [
    "workflow_id", "title", "lesson_slug", "planning_status", "review_status",
    "human_review_required", "generation_enabled", "workflow_steps",
    "local_first_safety_flags", "notes", "activation_status",
]
REQUIRED_SAFETY_FLAGS = {
    "metadata_only", "no_student_data", "placeholder_only",
    "human_review_required", "no_generation", "no_llm_calls",
}
ID_PATTERN = re.compile(r"^sample-lesson-workflow-[a-z0-9-]+$")
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")
STEP_ID_PATTERN = re.compile(r"^step-[0-9]{2}$")
HTTP_PATTERN = re.compile(r"https?://", re.IGNORECASE)
STUDENT_NAME_PATTERN = re.compile(
    r"\b(student name|real student|pupil name)\b", re.IGNORECASE
)

errors = []
warnings = []

with open(workflow_file, encoding="utf-8") as handle:
    try:
        data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        sys.exit(0)

if not isinstance(data, dict):
    errors.append("workflow root must be an object")

if data.get("workflow_version") != "0.1.0":
    errors.append("workflow_version must be 0.1.0")

if data.get("workflow_status") != "active_v0":
    errors.append("workflow_status must be active_v0")

if data.get("metadata_only") is not True:
    errors.append("metadata_only must be true")

if data.get("read_only") is not True:
    errors.append("read_only must be true")

if data.get("human_review_required") is not True:
    errors.append("root human_review_required must be true")

if data.get("generation_enabled") is not False:
    errors.append("root generation_enabled must be false")

workflows = data.get("workflows")
if not isinstance(workflows, list):
    errors.append("workflows must be an array")
    workflows = []

if len(workflows) != 1:
    errors.append(f"workflow v0 requires exactly 1 fictional workflow (got {len(workflows)})")

seen_ids = set()
for index, workflow in enumerate(workflows):
    label = f"workflows[{index}]"
    if not isinstance(workflow, dict):
        errors.append(f"{label} must be an object")
        continue

    for field in REQUIRED_WORKFLOW_FIELDS:
        if field not in workflow:
            errors.append(f"{label} missing required field: {field}")

    extra = set(workflow.keys()) - set(REQUIRED_WORKFLOW_FIELDS)
    if extra:
        errors.append(f"{label} has unexpected fields: {sorted(extra)}")

    workflow_id = workflow.get("workflow_id", "")
    if not isinstance(workflow_id, str) or not ID_PATTERN.match(workflow_id):
        errors.append(f"{label} workflow_id invalid: {workflow_id!r}")
    elif workflow_id in seen_ids:
        errors.append(f"{label} duplicate workflow_id: {workflow_id}")
    else:
        seen_ids.add(workflow_id)

    title = workflow.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{label} title must be non-empty string")
    elif "placeholder" not in title.lower():
        warnings.append(f"{label} title should contain Placeholder for v0 fictional data")

    lesson_slug = workflow.get("lesson_slug", "")
    if not isinstance(lesson_slug, str) or not SLUG_PATTERN.match(lesson_slug):
        errors.append(f"{label} lesson_slug invalid: {lesson_slug!r}")

    planning_status = workflow.get("planning_status")
    if planning_status not in PLANNING_STATUSES:
        errors.append(f"{label} invalid planning_status: {planning_status!r}")

    review_status = workflow.get("review_status")
    if review_status not in REVIEW_STATUSES:
        errors.append(f"{label} invalid review_status: {review_status!r}")

    if workflow.get("human_review_required") is not True:
        errors.append(f"{label} human_review_required must be true")

    if workflow.get("generation_enabled") is not False:
        errors.append(f"{label} generation_enabled must be false")

    if workflow.get("activation_status") != "lesson_planning_v0":
        errors.append(f"{label} activation_status must be lesson_planning_v0")

    flags = workflow.get("local_first_safety_flags")
    if not isinstance(flags, list):
        errors.append(f"{label} local_first_safety_flags must be an array")
    else:
        flag_set = set(flags)
        missing = REQUIRED_SAFETY_FLAGS - flag_set
        if missing:
            errors.append(f"{label} missing safety flags: {sorted(missing)}")

    notes = workflow.get("notes", "")
    if not isinstance(notes, str):
        errors.append(f"{label} notes must be a string")
    elif STUDENT_NAME_PATTERN.search(notes):
        errors.append(f"{label} notes must not contain student-name phrases")

    steps = workflow.get("workflow_steps")
    if not isinstance(steps, list):
        errors.append(f"{label} workflow_steps must be an array")
        steps = []

    if len(steps) != 6:
        errors.append(f"{label} workflow_steps must contain exactly 6 steps (got {len(steps)})")

    seen_step_ids = set()
    for step_index, step in enumerate(steps):
        step_label = f"{label}.workflow_steps[{step_index}]"
        if not isinstance(step, dict):
            errors.append(f"{step_label} must be an object")
            continue

        for step_field in ("step_id", "label", "chief_of_staff_command", "read_only"):
            if step_field not in step:
                errors.append(f"{step_label} missing required field: {step_field}")

        step_id = step.get("step_id", "")
        if not isinstance(step_id, str) or not STEP_ID_PATTERN.match(step_id):
            errors.append(f"{step_label} step_id invalid: {step_id!r}")
        elif step_id in seen_step_ids:
            errors.append(f"{step_label} duplicate step_id: {step_id}")
        else:
            seen_step_ids.add(step_id)

        command = step.get("chief_of_staff_command", "")
        if not isinstance(command, str) or "bin/chief-of-staff" not in command:
            errors.append(f"{step_label} chief_of_staff_command must reference bin/chief-of-staff")

        if step.get("read_only") is not True:
            errors.append(f"{step_label} read_only must be true")

        blob = json.dumps(step)
        if HTTP_PATTERN.search(blob):
            errors.append(f"{step_label} must not contain http(s) URLs")

blob = json.dumps(data)
if HTTP_PATTERN.search(blob):
    errors.append("workflow document must not contain http(s) URLs")
if STUDENT_NAME_PATTERN.search(blob):
    errors.append("workflow document must not contain student-name phrases")

for warning in warnings:
    print(f"WARN: {warning}")
for error in errors:
    print(f"FAIL: {error}")

if not errors:
    print("PASS: workflow document structure valid")
    print("PASS: fictional placeholder workflow validated")
PY
)"

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
  esac
done <<< "${validation_output}"

pass 'no write action attempted'
pass 'no lesson generation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
