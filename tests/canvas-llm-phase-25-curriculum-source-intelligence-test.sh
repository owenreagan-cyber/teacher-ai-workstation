#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 25 curriculum source intelligence tests..."
M=scripts/canvas_llm_phase25/resolve_resources.py
V=scripts/canvas_llm_phase25/validate_resolution.py
T=$(mktemp -d "${TMPDIR:-/tmp}/phase25.XXXXXX")
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" "$V" \
  scripts/canvas_llm_phase25/models.py \
  scripts/canvas_llm_phase25/registry.py \
  scripts/canvas_llm_phase25/correction_memory.py \
  scripts/canvas_llm_phase25/requirements.py \
  scripts/canvas_llm_phase25/resolver.py \
  scripts/canvas_llm_phase25/integration.py

DEMO="$T/phase25-demo.json"
python3 "$M" build-demo --week Q1W5 --predictions fixtures/canvas-llm/phase-25/phase24-predicted-week.json --registry fixtures/canvas-llm/phase-25/resource-registry.json --corrections fixtures/canvas-llm/phase-25/resource-corrections.json --out "$DEMO"

python3 - "$DEMO" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["weekCode"] == "Q1W5"
assert payload["validation"]["failCount"] == 0
assert payload["validation"]["warnCount"] == 2
assert payload["phase23Preview"]["deploymentState"] == "preview-only"
assert payload["phase23Preview"]["approvalState"] == "draft"
assert payload["containsStudentData"] is False
print("PASS packet shape")
PY

python3 "$V" "$DEMO" | grep -q '^WARN: due-time.unresolved Canvas assignment due-time convention remains owner-unresolved$'
python3 "$V" "$DEMO" | grep -q '^WARN: math-test-cadence.unresolved Math test cadence remains owner-unresolved$'
python3 "$V" "$DEMO" | grep -q '^PASS: reading.checkout14 Checkout 14 is absent without warning$'
python3 "$V" "$DEMO" | grep -q '^PASS: power-up.review-queue Power Up mapping remains a review item without becoming a global warning$'
python3 "$V" "$DEMO" | grep -q '^FAIL: 0$'

python3 - "$DEMO" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

resolved = payload["resolvedResources"]
review = payload["reviewQueue"]

def find_method(method, resource_type=None):
    for item in resolved:
        if item["resolutionMethod"] == method:
            if resource_type is None or item["requirement"]["resourceType"] == resource_type:
                return item
    raise AssertionError((method, resource_type))

exact = find_method("exact-verified-match", "student-book")
assert exact["resource"]["resourceId"] == "SM5-L18-STUDENT-BOOK"
assert any("duplicate" in c["availabilityStatus"] or "moved" in c["availabilityStatus"] for c in exact["ignoredCandidates"])

even_sheet = find_method("approved-parity-or-family-match", "homework-recording-sheet")
assert even_sheet["resource"]["resourceId"] == "SM5-EVEN-HW-RECORDING-SHEET"

owner_corr = find_method("owner-approved-correction", "worksheet")
assert owner_corr["resource"]["resourceId"] == "SM5-LESSON-1-20-WORKSHEET"

lesson_range = find_method("approved-lesson-range-match", "worksheet")
assert lesson_range["resource"]["resourceId"] == "SM5-LESSON-1-20-WORKSHEET"

assessment_family = find_method("approved-parity-or-family-match", "fluency-directions")
assert assessment_family["resource"]["resourceId"] == "RM4-FLUENCY-DIRECTIONS"

subject_wide = [item for item in resolved if item["requirement"]["resourceType"] == "page-resource"]
assert subject_wide

power_up = find_method("unresolved", "power-up")
assert power_up["resource"] is None
assert power_up["reviewState"] == "missing"

blocked = [item for item in review if item["status"] == "Blocked"]
assert blocked
teacher_only = [item for item in review if item["status"] == "Teacher-Only"]
assert teacher_only

conflicts = [item for item in review if item["status"] == "Conflicting"]
assert conflicts

needs_review = [item for item in review if item["status"] == "Needs Review"]
assert needs_review

phase23 = payload["phase23Preview"]
assert phase23["deploymentState"] == "preview-only"
assert phase23["approvalState"] == "draft"
assert all("Checkout 14" not in json.dumps(item, ensure_ascii=False) for item in phase23["assessmentReminders"])
assert all("power-up" not in json.dumps(item, ensure_ascii=False).lower() for item in phase23["pages"])
print("PASS resolution rules")
PY

STATE="$T/resource-corrections.json"
PHASE25_LOCAL_ROOT="$T/local-root" python3 - "$STATE" <<'PY'
import json
import sys
from pathlib import Path
from scripts.canvas_llm_phase25.correction_memory import load_correction_state, save_resource_correction

path = Path(sys.argv[1])
state = load_correction_state(path)
assert state["status"] == "saved"
saved = save_resource_correction(
    {
        "subject": "math",
        "weekCode": "Q1W5",
        "day": "Monday",
        "requiredResourceClass": "student-book",
        "predictedResourceId": "SM5-L18-STUDENT-BOOK-LEGACY",
        "approvedResourceId": "SM5-L18-STUDENT-BOOK",
        "correctionScope": "this lesson",
        "timestamp": "2026-07-11T00:00:00Z",
        "reason": "Legacy alias maps to canonical book",
        "sourceRule": "teacher.resource.override",
        "revision": 1,
    },
    0,
    path,
)
assert saved["status"] == "saved"
conflict = save_resource_correction(
    {
        "subject": "math",
        "weekCode": "Q1W5",
        "day": "Monday",
        "requiredResourceClass": "student-book",
        "predictedResourceId": "SM5-L18-STUDENT-BOOK-LEGACY",
        "approvedResourceId": "SM5-L18-STUDENT-BOOK",
        "correctionScope": "this lesson",
        "timestamp": "2026-07-11T00:00:00Z",
        "reason": "Legacy alias maps to canonical book",
        "sourceRule": "teacher.resource.override",
        "revision": 2,
    },
    0,
    path,
)
assert conflict["status"] == "conflict"
bad = path.parent / "broken.json"
bad.write_text("{broken-json", encoding="utf-8")
quarantined = load_correction_state(bad)
assert quarantined["status"] == "error"
print("PASS correction memory")
PY

if git ls-files '.local/*' | grep -q .; then
  echo "FAIL: tracked .local artifact found"
  exit 1
fi

echo "PASS: no .local artifacts tracked"
echo "PASS: Phase 25 curriculum source intelligence tests complete"
