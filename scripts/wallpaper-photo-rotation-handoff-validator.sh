#!/usr/bin/env bash
# Dry-run rotation handoff validation only. No file moves, network calls, or file operations.
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

default_report_file="assistant/appearance-vibe/wallpaper-photo-curator/sample-rotation-handoff-readiness-report.json"
report_file="${1:-${default_report_file}}"

section 'Wallpaper/Photo Rotation Handoff Dry-Run Validator'
cat <<'EOF'
Status: simulated rotation handoff validation only
Handoff enabled: no
File moves: no
File copies: no
File deletions: no
Folder scans: no
Queue writes: no
Wallpaper changes: no
Photos changes: no
Network calls: no
Image processing: no
Scheduler implemented: no
Notifications sent: no
Reddit integration: no
Devvit integration: no
EOF

if [[ ! -f "${report_file}" ]]; then
  fail "rotation handoff readiness report file missing: ${report_file}"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

pass "rotation handoff readiness report file exists: ${report_file}"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 required for rotation handoff validation"
  section 'Summary'
  printf 'PASS: %s\n' "${PASS_COUNT}"
  printf 'WARN: %s\n' "${WARN_COUNT}"
  printf 'FAIL: %s\n' "${FAIL_COUNT}"
  exit 1
fi

validation_output="$(python3 - "${report_file}" <<'PY'
import json
import re
import sys

report_file = sys.argv[1]

VALID_GATE_STATUSES = {
    "foundation_complete",
    "planning_only",
    "not_implemented",
    "future_approval_required",
}
VALID_RISK_LEVELS = {
    "low",
    "medium",
    "high",
    "blocked_until_approved",
}
REQUIRED_GATE_FIELDS = [
    "gate_id",
    "name",
    "status",
    "required_before_handoff",
    "notes",
]
REQUIRED_AUDIT_FIELDS = [
    "audit_id",
    "area",
    "status",
    "risk_level",
    "notes",
]
TOP_FALSE_FLAGS = [
    "handoff_enabled",
    "file_moves",
    "file_copies",
    "file_deletions",
    "folder_scans",
    "queue_writes",
    "wallpaper_changes",
    "photos_changes",
    "network_calls",
]
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|avif)(\b|/|$)", re.I)
SECRET_RE = re.compile(
    r"(api[_-]?key|oauth|bearer\s+token|secret|password|credential|access_token|refresh_token)",
    re.I,
)

results = []

def emit(level, message):
    results.append((level, message))

try:
    with open(report_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except json.JSONDecodeError as exc:
    emit("FAIL", f"rotation handoff readiness report JSON does not parse: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)
except OSError as exc:
    emit("FAIL", f"cannot read rotation handoff readiness report file: {exc}")
    for level, message in results:
        print(f"{level}: {message}")
    sys.exit(0)

emit("PASS", "rotation handoff readiness report JSON parses")

if data.get("mode") != "simulated":
    emit("FAIL", "top-level mode must be simulated")
else:
    emit("PASS", "top-level mode is simulated")

for flag in TOP_FALSE_FLAGS:
    if data.get(flag) is not False:
        emit("FAIL", f"top-level {flag} must be false")
    else:
        emit("PASS", f"top-level {flag} is false")

gates = data.get("readiness_gates")
if not isinstance(gates, list):
    emit("FAIL", "top-level readiness_gates missing or not an array")
    gates = []

audit_items = data.get("safety_audit_items")
if not isinstance(audit_items, list):
    emit("FAIL", "top-level safety_audit_items missing or not an array")
    audit_items = []

if len(gates) < 10:
    emit("FAIL", f"readiness_gates must contain at least 10 gates, found {len(gates)}")
else:
    emit("PASS", f"readiness_gates contains {len(gates)} gates")

if len(audit_items) < 15:
    emit("FAIL", f"safety_audit_items must contain at least 15 items, found {len(audit_items)}")
else:
    emit("PASS", f"safety_audit_items contains {len(audit_items)} items")

report_blob = json.dumps(data)
if "reddit.com" in report_blob.lower():
    emit("FAIL", "readiness report must not contain reddit.com")
else:
    emit("PASS", "readiness report does not contain reddit.com")

if IMAGE_EXT_RE.search(report_blob):
    emit("FAIL", "readiness report must not contain image file extensions")
else:
    emit("PASS", "readiness report does not contain image file extensions")

if SECRET_RE.search(report_blob):
    emit("FAIL", "readiness report must not contain obvious secrets/API keys/OAuth tokens")
else:
    emit("PASS", "readiness report does not contain obvious secrets/API keys/OAuth tokens")

gate_valid = {}
for index, gate in enumerate(gates, start=1):
    label = f"gate {index}"
    gate_id = gate.get("gate_id", f"gate-{index}") if isinstance(gate, dict) else f"gate-{index}"
    gate_label = f"{label} ({gate_id})"
    failures = []

    if not isinstance(gate, dict):
        emit("FAIL", f"{gate_label}: not an object")
        continue

    for field in REQUIRED_GATE_FIELDS:
        if field not in gate:
            failures.append(f"missing field {field}")

    status = gate.get("status")
    if status not in VALID_GATE_STATUSES:
        failures.append(f"invalid status: {status!r}")

    if gate.get("required_before_handoff") is not True:
        failures.append("required_before_handoff must be true")

    area = gate.get("name", "unknown")
    gate_valid[area] = gate_valid.get(area, True) and not failures

    gate_blob = json.dumps(gate)
    if "reddit.com" in gate_blob.lower():
        failures.append("gate must not contain reddit.com")
    if IMAGE_EXT_RE.search(gate_blob):
        failures.append("gate must not contain image file extension")
    if SECRET_RE.search(gate_blob):
        failures.append("gate must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{gate_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{gate_label}: valid")

audit_valid = {}
for index, item in enumerate(audit_items, start=1):
    label = f"audit item {index}"
    audit_id = item.get("audit_id", f"audit-{index}") if isinstance(item, dict) else f"audit-{index}"
    item_label = f"{label} ({audit_id})"
    failures = []

    if not isinstance(item, dict):
        emit("FAIL", f"{item_label}: not an object")
        continue

    for field in REQUIRED_AUDIT_FIELDS:
        if field not in item:
            failures.append(f"missing field {field}")

    status = item.get("status")
    if status not in VALID_GATE_STATUSES:
        failures.append(f"invalid status: {status!r}")

    risk = item.get("risk_level")
    if risk not in VALID_RISK_LEVELS:
        failures.append(f"invalid risk_level: {risk!r}")

    area = item.get("area", "unknown")
    audit_valid[area] = audit_valid.get(area, True) and not failures

    item_blob = json.dumps(item)
    if "reddit.com" in item_blob.lower():
        failures.append("audit item must not contain reddit.com")
    if IMAGE_EXT_RE.search(item_blob):
        failures.append("audit item must not contain image file extension")
    if SECRET_RE.search(item_blob):
        failures.append("audit item must not contain obvious secrets/API keys/OAuth tokens")

    if failures:
        emit("FAIL", f"{item_label}: {'; '.join(failures)}")
    else:
        emit("PASS", f"{item_label}: valid")

for area, valid in sorted(gate_valid.items()):
    if valid:
        emit("PASS", f"readiness gate group '{area}': valid")
    else:
        emit("FAIL", f"readiness gate group '{area}': invalid")

for area, valid in sorted(audit_valid.items()):
    if valid:
        emit("PASS", f"safety audit area '{area}': valid")
    else:
        emit("FAIL", f"safety audit area '{area}': invalid")

for level, message in results:
    print(f"{level}: {message}")
PY
)" || true

section 'Readiness and Safety Items Checked'

while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
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
      printf '%s\n' "${line}"
      ;;
  esac
done <<< "${validation_output}"

pass 'simulated/local-only validation only'
pass 'no handoff occurred'
pass 'no files were moved, copied, deleted, or scanned'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
