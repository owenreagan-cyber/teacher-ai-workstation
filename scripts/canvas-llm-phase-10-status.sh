#!/usr/bin/env bash
# Canvas LLM Phase 10 sandbox metadata review/import gate status.
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

reviewer="scripts/canvas-llm-sandbox-metadata-review.py"
phase9b_status="scripts/canvas-llm-phase-9b-status.sh"
staging_manifest=".local/canvas-llm/sandbox-metadata/course-24399/manifest.json"

section "Canvas LLM Phase 10 Sandbox Metadata Review And Import Gate"
cat <<'STATUS'
Status: canvas_llm_phase_10_sandbox_metadata_review_gate_complete
Classification: local ignored sandbox metadata review/import gate
Approved course ID: 24399 only
Source: ignored local Phase 9B staged metadata only
Canvas API calls: blocked
Metadata import: blocked
Production writes: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 10 Artifacts"
check_executable "${reviewer}"
check_executable "${phase9b_status}"
python3 -m py_compile "${reviewer}" >/dev/null 2>&1 && pass "Phase 10 reviewer Python compiles" || fail "Phase 10 reviewer Python compile failed"

section "Static Safety Guards"
check_contains "${reviewer}" 'APPROVED_COURSE_ID = "24399"' "approved course ID 24399"
check_contains "${reviewer}" "APPROVED_STAGING_ROOT" "approved local staging root"
check_contains "${reviewer}" "EXPECTED_ENDPOINTS" "expected endpoint set"
check_contains "${reviewer}" "FORBIDDEN_KEYS" "forbidden key list"
check_contains "${reviewer}" "FORBIDDEN_TEXT_PATTERNS" "forbidden text patterns"
check_contains "${reviewer}" '"import_performed": False' "import not performed"
check_contains "${reviewer}" '"canvas_api_call": False' "Canvas API call not performed"
check_contains "${reviewer}" '"production_write": False' "production write not performed"

section "Local Staging Presence And Ignore Guards"
if [[ -f "${staging_manifest}" ]]; then
  pass "local Phase 9B staging manifest exists"
else
  fail "local Phase 9B staging manifest missing"
fi

if git check-ignore -q "${staging_manifest}"; then
  pass "local Phase 9B staging manifest is ignored"
else
  fail "local Phase 9B staging manifest must be ignored"
fi

if [[ -n "$(git status --short -- .local/canvas-llm || true)" ]]; then
  fail "ignored local Canvas metadata appeared in git status"
  git status --short -- .local/canvas-llm || true
else
  pass "ignored local Canvas metadata does not appear in git status"
fi

section "Plan Command"
if "${reviewer}" plan >/tmp/canvas-phase-10-plan.out 2>&1; then
  pass "review plan command succeeds"
else
  fail "review plan command failed"
  cat /tmp/canvas-phase-10-plan.out || true
fi

for phrase in \
  '"course_id": "24399"' \
  '"review_only": true' \
  '"import_performed": false' \
  '"canvas_api_call": false' \
  '"production_write": false'
do
  grep -F -- "$phrase" /tmp/canvas-phase-10-plan.out >/dev/null && pass "plan output proves $phrase" || fail "plan output missing $phrase"
done

section "Review Command"
if "${reviewer}" review >/tmp/canvas-phase-10-review.out 2>&1; then
  pass "review command succeeds"
else
  fail "review command failed"
  cat /tmp/canvas-phase-10-review.out || true
fi

for phrase in \
  "manifest confirms course 24399 only" \
  "manifest confirms read-only metadata-only output" \
  "manifest endpoint classes match approved Phase 10 review set" \
  "manifest record counts match staged files" \
  "forbidden body/content/student/grade/enrollment-style keys not found" \
  "token/bearer/access-token text patterns not found" \
  "review only; no Canvas API call, import, or production write performed" \
  '"import_performed": false' \
  '"canvas_api_call": false' \
  '"production_write": false'
do
  grep -F -- "$phrase" /tmp/canvas-phase-10-review.out >/dev/null && pass "review output proves $phrase" || fail "review output missing $phrase"
done

if grep -F "WARN: announcements_metadata has 0 records in sandbox staging" /tmp/canvas-phase-10-review.out >/dev/null; then
  warn "expected sandbox warning preserved: announcements_metadata has 0 records"
else
  pass "no announcement-count warning emitted"
fi

section "Tracked Secret And School URL Guards"
if grep -R "thalesacademy\.instructure\.com" "${reviewer}" scripts/canvas-llm-phase-10-status.sh >/tmp/canvas-phase-10-url-grep.out 2>&1; then
  fail "tracked school Canvas URL found in Phase 10 files"
  cat /tmp/canvas-phase-10-url-grep.out || true
else
  pass "tracked Phase 10 files do not contain school Canvas URL"
fi

python3 - "${reviewer}" scripts/canvas-llm-phase-10-status.sh >/tmp/canvas-phase-10-secret-grep.out 2>&1 <<'PYSECRET'
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
  cat /tmp/canvas-phase-10-secret-grep.out || true
fi

section "Course ID Guard"
if python3 - "${reviewer}" scripts/canvas-llm-phase-10-status.sh <<'PYSCAN'
import re
import sys
from pathlib import Path

allowed = {"24399"}
bad = {}
for file_name in sys.argv[1:]:
    text = Path(file_name).read_text(encoding="utf-8")
    ids = sorted(set(re.findall(r"\b\d{5}\b", text)))
    blocked = [course_id for course_id in ids if course_id not in allowed]
    if blocked:
        bad[file_name] = blocked
if bad:
    for file_name, ids in bad.items():
        print(f"{file_name}: {', '.join(ids)}")
    sys.exit(1)
print("Phase 10 tracked files contain only allowed demo course ID 24399")
PYSCAN
then
  pass "tracked Phase 10 files avoid non-demo real course IDs"
else
  fail "tracked Phase 10 files must not contain non-demo real course IDs"
fi

section "Phase 9B Continuity"
if bin/chief-of-staff --canvas-llm-phase-9b-status >/tmp/canvas-phase-9b-status.out 2>&1; then
  pass "Phase 9B status still passes"
else
  fail "Phase 9B status failed"
  tail -40 /tmp/canvas-phase-9b-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
