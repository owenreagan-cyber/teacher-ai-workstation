#!/usr/bin/env bash
# Canvas LLM Phase 9B read-only sandbox API metadata fetch execution status.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"
}

check_executable() {
  [[ -x "$1" ]] && pass "executable exists: $1" || fail "executable missing: $1"
}

check_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    fail "$file missing for $label"
    return
  fi
  grep -F -- "$phrase" "$file" >/dev/null && pass "file mentions $label" || fail "$file must mention $label"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

fetcher="scripts/canvas-llm-sandbox-metadata-fetch.py"
phase9a_status="scripts/canvas-llm-phase-9a-status.sh"

section "Canvas LLM Phase 9B Read-Only Sandbox API Metadata Fetch"
cat <<'STATUS'
Status: canvas_llm_phase_9b_sandbox_api_metadata_fetch_ready
Classification: separately approved read-only sandbox metadata fetch execution
Approved course ID: 24399 only
Approved Canvas source: local CANVAS_BASE_URL environment variable only
Approved token source: local CANVAS_API_TOKEN environment variable only
Tracked school URL: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 9B Artifacts"
check_file ".gitignore"
check_executable "${fetcher}"
check_executable "${phase9a_status}"
python3 -m py_compile "${fetcher}" >/dev/null 2>&1 && pass "Phase 9B fetcher Python compiles" || fail "Phase 9B fetcher Python compile failed"
grep -F ".local/canvas-llm/" .gitignore >/dev/null && pass ".local/canvas-llm/ is ignored" || fail ".local/canvas-llm/ must be ignored"

section "Fetcher Static Guards"
check_contains "${fetcher}" 'APPROVED_COURSE_ID = "24399"' "approved course ID 24399"
check_contains "${fetcher}" 'TOKEN_ENV_NAME = "CANVAS_API_TOKEN"' "token env name only"
check_contains "${fetcher}" 'BASE_URL_ENV_NAME = "CANVAS_BASE_URL"' "base URL env name only"
check_contains "${fetcher}" 'APPROVAL_FLAG = "--i-understand-this-uses-read-only-canvas-api"' "explicit live approval flag"
check_contains "${fetcher}" 'method="GET"' "GET-only request method"
check_contains "${fetcher}" "SAFE_KEYS_BY_ENDPOINT" "safe metadata key allowlist"
check_contains "${fetcher}" "BLOCKED_ENDPOINT_CLASSES" "blocked endpoint class list"
check_contains "${fetcher}" "student_data" "student data safety flag"
check_contains "${fetcher}" "real_curriculum_body_ingestion" "real curriculum body ingestion flag"
check_contains "${fetcher}" "token value is not printed" "token value not printed"
check_contains "${fetcher}" ".local/canvas-llm/sandbox-metadata/course-24399" "approved local staging path"

section "Plan And Validate Commands"
if "${fetcher}" plan >/tmp/canvas-phase-9b-plan.out 2>&1; then
  pass "plan command succeeds without live API access"
else
  fail "plan command failed"
  cat /tmp/canvas-phase-9b-plan.out || true
fi

for phrase in \
  '"course_id": "24399"' \
  '"metadata_only": true' \
  '"read_only": true' \
  '"canvas_write": false' \
  '"student_data": false' \
  '"real_curriculum_body_ingestion": false' \
  '"token_value_printed": false' \
  '"token_env_name": "CANVAS_API_TOKEN"' \
  '"base_url_env_name": "CANVAS_BASE_URL"'
do
  grep -F -- "$phrase" /tmp/canvas-phase-9b-plan.out >/dev/null && pass "plan output proves $phrase" || fail "plan output missing $phrase"
done

if "${fetcher}" validate >/tmp/canvas-phase-9b-validate.out 2>&1; then
  pass "validate command succeeds without live API access"
else
  fail "validate command failed"
  cat /tmp/canvas-phase-9b-validate.out || true
fi
grep -F "token value is never printed" /tmp/canvas-phase-9b-validate.out >/dev/null && pass "validate confirms token is never printed" || fail "validate must confirm token is never printed"

section "Course And Approval Guards"
if "${fetcher}" --course-id 99999 plan >/tmp/canvas-phase-9b-wrong-course.out 2>&1; then
  fail "wrong course ID was accepted"
else
  pass "wrong course ID rejected"
fi
grep -F "course ID must be 24399" /tmp/canvas-phase-9b-wrong-course.out >/dev/null && pass "wrong course rejection message is explicit" || fail "wrong course rejection message missing"

if "${fetcher}" live-fetch >/tmp/canvas-phase-9b-live-no-flag.out 2>&1; then
  fail "live fetch without approval flag was accepted"
else
  pass "live fetch without approval flag blocked"
fi
grep -F "live fetch requires explicit approval flag" /tmp/canvas-phase-9b-live-no-flag.out >/dev/null && pass "approval flag requirement is explicit" || fail "approval flag requirement missing"

section "Tracked Secret And URL Guards"
if grep -R "thalesacademy\.instructure\.com" .gitignore "${fetcher}" scripts/canvas-llm-phase-9b-status.sh >/tmp/canvas-phase-9b-url-grep.out 2>&1; then
  fail "tracked school Canvas URL found in Phase 9B tracked files"
  cat /tmp/canvas-phase-9b-url-grep.out || true
else
  pass "tracked Phase 9B files do not contain school Canvas URL"
fi

python3 - .gitignore "${fetcher}" scripts/canvas-llm-phase-9b-status.sh >/tmp/canvas-phase-9b-secret-grep.out 2>&1 <<'PYSECRET'
import re
import sys
from pathlib import Path

patterns = [
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_=-]{20,}"),
    re.compile(r"CANVAS_API_TOKEN\s*=\s*['\"][^'\"]+['\"]"),
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
  cat /tmp/canvas-phase-9b-secret-grep.out || true
fi

if python3 - "${fetcher}" <<'PYSCAN'
import re
import sys
from pathlib import Path

allowed = {"24399", "99999"}
text = Path(sys.argv[1]).read_text(encoding="utf-8")
ids = sorted(set(re.findall(r"\b\d{5}\b", text)))
blocked = [course_id for course_id in ids if course_id not in allowed]
if blocked:
    print(", ".join(blocked))
    sys.exit(1)
print("Phase 9B fetcher contains no non-demo real course IDs")
PYSCAN
then
  pass "Phase 9B fetcher avoids non-demo real course IDs"
else
  fail "Phase 9B fetcher must not contain non-demo real course IDs"
fi

section "Phase 9A Continuity"
if bin/chief-of-staff --canvas-llm-phase-9a-status >/tmp/canvas-phase-9a-status.out 2>&1; then
  pass "Phase 9A status still passes"
else
  fail "Phase 9A status failed"
  tail -40 /tmp/canvas-phase-9a-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
