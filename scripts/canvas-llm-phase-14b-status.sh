#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

require_file() {
  [[ -f "$1" ]] && pass "Phase 14B file exists: $1" || fail "Missing Phase 14B file: $1"
}

require_executable() {
  [[ -x "$1" ]] && pass "Phase 14B executable exists: $1" || fail "Missing executable Phase 14B file: $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

FETCHER="scripts/canvas-llm-approved-course-metadata-fetch.py"
STATUS="scripts/canvas-llm-phase-14b-status.sh"
DOC="docs/programs/canvas-llm/canvas-phase-14b-approved-course-metadata-fetch.md"
MANIFEST="config/canvas-llm/approved-canvas-course-manifest.json"
LOCAL_ROOT=".local/canvas-llm/approved-course-metadata"
LOCAL_MANIFEST="${LOCAL_ROOT}/manifest.json"

section "Canvas LLM Phase 14B: Read-Only Approved Course Metadata Fetch"
cat <<'STATUS_TEXT'
Status: canvas_llm_phase_14b_approved_course_metadata_fetch
Classification: approved read-only Canvas metadata fetch, ignored local raw metadata only
Canvas writes: blocked
File downloads and file contents: blocked
Page, announcement, and assignment bodies: blocked
Student data/users/enrollments/submissions/grades: blocked
Tracked school Canvas URL or token: blocked
STATUS_TEXT

section "Tracked Artifacts"
require_file "$MANIFEST"
require_executable "$FETCHER"
require_executable "$STATUS"
require_file "$DOC"
require_file "docs/programs/canvas-llm/canvas-llm-phase-plan.md"

PYCACHE_ROOT="${TMPDIR:-/tmp}/canvas-phase-14b-pycache"
mkdir -p "$PYCACHE_ROOT"

if PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" python3 -m py_compile "$FETCHER" >/tmp/canvas-phase-14b-pycompile.out 2>&1; then
  pass "Phase 14B fetcher Python compiles"
else
  fail "Phase 14B fetcher Python compile failed"
  cat /tmp/canvas-phase-14b-pycompile.out || true
fi

section "Phase 14A Manifest Continuity"
if manifest_output="$(scripts/canvas-llm-course-approval-manifest-validator.py 2>&1)"; then
  echo "$manifest_output"
  pass "Phase 14A manifest still validates"
else
  echo "$manifest_output"
  fail "Phase 14A manifest validator failed"
fi

section "Fetcher Static Safety"
for phrase in \
  "TOKEN_ENV_NAME = \"CANVAS_API_TOKEN\"" \
  "BASE_URL_ENV_NAME = \"CANVAS_BASE_URL\"" \
  "APPROVED_STAGING_ROOT = Path(\".local/canvas-llm/approved-course-metadata\")" \
  "ALLOWED_METADATA_CATEGORIES" \
  "BLOCKED_ENDPOINT_CLASSES" \
  "BODY_KEYS" \
  "method=\"GET\"" \
  "\"canvas_write\": False" \
  "\"file_downloads\": False" \
  "\"body_ingestion\": False" \
  "\"student_data\": False"
do
  if grep -Fq "$phrase" "$FETCHER"; then
    pass "fetcher proves ${phrase}"
  else
    fail "fetcher missing ${phrase}"
  fi
done

if "$FETCHER" validate >/tmp/canvas-phase-14b-fetcher-validate.out 2>&1; then
  pass "fetcher validate command succeeds"
else
  fail "fetcher validate command failed"
  cat /tmp/canvas-phase-14b-fetcher-validate.out || true
fi

for phrase in \
  "validation accepted 19 approved course IDs" \
  "validation accepted approved local staging path" \
  "live fetch requires explicit approval flag" \
  "token value is never printed" \
  "Canvas endpoint plan is read-only metadata-only"
do
  if grep -Fq "$phrase" /tmp/canvas-phase-14b-fetcher-validate.out; then
    pass "fetcher validation output proves: $phrase"
  else
    fail "fetcher validation output missing: $phrase"
  fi
done

section "Ignored Local Metadata Guard"
if git check-ignore -q "${LOCAL_ROOT}/manifest.json"; then
  pass "approved-course-metadata local manifest path is ignored"
else
  fail "approved-course-metadata local manifest path is not ignored"
fi

if [[ -z "$(git ls-files .local/canvas-llm)" ]]; then
  pass ".local Canvas metadata is not tracked"
else
  fail ".local Canvas metadata is tracked"
  git ls-files .local/canvas-llm || true
fi

if [[ -z "$(git status --short -- .local/canvas-llm || true)" ]]; then
  pass "ignored .local Canvas metadata does not appear in git status"
else
  fail "ignored .local Canvas metadata appeared in git status"
  git status --short -- .local/canvas-llm || true
fi

section "Tracked Token And School URL Guards"
if grep -R -E 'https://[^[:space:])`]+[.]instructure[.]com|[[:alnum:]_.-]+[.]instructure[.]com' "$FETCHER" "$STATUS" "$DOC" docs/programs/canvas-llm/canvas-llm-phase-plan.md >/tmp/canvas-phase-14b-url-scan.out 2>&1; then
  fail "tracked school Canvas URL found in Phase 14B files"
  cat /tmp/canvas-phase-14b-url-scan.out || true
else
  pass "Phase 14B tracked files do not contain school Canvas URL"
fi

python3 - "$FETCHER" "$STATUS" "$DOC" docs/programs/canvas-llm/canvas-llm-phase-plan.md >/tmp/canvas-phase-14b-secret-scan.out 2>&1 <<'PYSECRET'
import re
import sys
from pathlib import Path

patterns = [
    re.compile(r"\bsk-(?:proj|live|test|ant|svcacct|admin|user|org)-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bCANVAS_API_TOKEN\s*=\s*['\"][^'\"]+['\"]"),
]
hits = []
for file_name in sys.argv[1:]:
    text = Path(file_name).read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if "re.compile(" in line or "patterns = [" in line:
            continue
        for pattern in patterns:
            if pattern.search(line):
                hits.append(f"{file_name}:{line_number}:{line}")
if hits:
    print("\n".join(hits))
    sys.exit(1)
PYSECRET
if [[ $? -eq 0 ]]; then
  pass "no tracked token or bearer secret pattern found"
else
  fail "possible tracked token or bearer secret found"
  cat /tmp/canvas-phase-14b-secret-scan.out || true
fi

section "Fetched Metadata Validation"
if [[ ! -f "$LOCAL_MANIFEST" ]]; then
  warn "local Phase 14B metadata manifest has not been fetched yet: $LOCAL_MANIFEST"
else
  if python3 - "$MANIFEST" "$LOCAL_ROOT" <<'PYLOCAL'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
root = Path(sys.argv[2])
approved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
approved = {int(course["course_id"]): course for course in approved_manifest["courses"]}
top = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
course_ids = top.get("course_ids", [])
bad_ids = sorted(set(course_ids) - set(approved))
if bad_ids:
    raise SystemExit(f"unapproved course IDs in local fetch manifest: {bad_ids}")
missing_ids = sorted(set(approved) - set(course_ids))
if missing_ids:
    raise SystemExit(f"approved course IDs missing from local fetch manifest: {missing_ids}")

required_files = {
    "course_metadata.json",
    "folders_metadata.json",
    "files_metadata.json",
    "modules_metadata.json",
    "module_items_metadata.json",
    "pages_metadata.json",
    "announcements_metadata.json",
    "assignments_metadata.json",
    "manifest.json",
}
for course_id in course_ids:
    course_root = root / f"course-{course_id}"
    missing = sorted(name for name in required_files if not (course_root / name).is_file())
    if missing:
        raise SystemExit(f"course {course_id} missing files: {missing}")
    course_manifest = json.loads((course_root / "manifest.json").read_text(encoding="utf-8"))
    approved_course = approved[int(course_id)]
    for key in ("course_role", "school_year", "subject", "canonical_prefixes"):
        if course_manifest.get(key) != approved_course[key]:
            raise SystemExit(f"course {course_id} manifest does not preserve {key}")
    for safety_key in ("read_only", "metadata_only", "assignments_metadata_for_relationship_mapping_only", "pages_metadata_only", "announcements_metadata_only"):
        if course_manifest.get(safety_key) is not True:
            raise SystemExit(f"course {course_id} manifest missing true {safety_key}")
    for safety_key in ("body_ingestion", "file_downloads", "canvas_write", "student_data"):
        if course_manifest.get(safety_key) is not False:
            raise SystemExit(f"course {course_id} manifest missing false {safety_key}")

for path in root.rglob("*.json"):
    text = path.read_text(encoding="utf-8").lower()
    blocked_fragments = [
        '"body"', '"description"', '"message"', '"submission"', '"submissions"',
        '"enrollments"', '"grades"', '"users"', '"download_url"', '"syllabus_body"',
    ]
    hits = [fragment for fragment in blocked_fragments if fragment in text]
    if hits:
        raise SystemExit(f"blocked body/file/student-style key found in {path}: {hits}")

homeroom = [course for course in top["courses"] if "homeroom" in course["course_role"] or "newsletter" in course["course_role"]]
academic = [course for course in top["courses"] if "academic" in course["course_role"] or course["course_role"] == "current_operational_course"]
if len(homeroom) != 3:
    raise SystemExit(f"expected 3 homeroom/newsletter courses, found {len(homeroom)}")
if len(academic) != 15:
    raise SystemExit(f"expected 15 academic/current operational courses, found {len(academic)}")

print(f"Fetched course count: {len(course_ids)}")
print("Fetched course IDs: " + ", ".join(str(course_id) for course_id in course_ids))
print("Homeroom/newsletter course IDs: " + ", ".join(str(course["course_id"]) for course in homeroom))
print("Academic/current course IDs: " + ", ".join(str(course["course_id"]) for course in academic))
for course in top["courses"]:
    counts = course.get("counts", {})
    rendered = ", ".join(f"{key}={counts[key]}" for key in sorted(counts))
    print(f"Counts course {course['course_id']}: {rendered}")
PYLOCAL
  then
    pass "local fetched metadata validates against approved manifest and safety rules"
  else
    fail "local fetched metadata validation failed"
  fi
fi

section "Metadata-Only And No-Write Proof"
for phrase in \
  "page bodies" \
  "announcement bodies" \
  "assignment bodies" \
  "file downloads" \
  "Canvas writes remain blocked" \
  "metadata-only"
do
  if grep -Fqi "$phrase" "$DOC"; then
    pass "Phase 14B doc states guard: $phrase"
  else
    fail "Phase 14B doc missing guard: $phrase"
  fi
done

section "Phase 14A Continuity"
if phase14a_output="$(PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" bin/chief-of-staff --canvas-llm-phase-14a-status 2>&1)"; then
  echo "$phase14a_output" | tail -35
  if echo "$phase14a_output" | grep -q "FAIL: 0"; then
    pass "Phase 14A status still passes"
  else
    fail "Phase 14A status did not report FAIL: 0"
  fi
else
  echo "$phase14a_output"
  fail "Phase 14A status command failed"
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "$FAIL_COUNT" -ne 0 ]] && exit 1
exit 0
