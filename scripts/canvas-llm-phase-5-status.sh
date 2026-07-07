#!/usr/bin/env bash
# Read-only Canvas LLM Phase 5 fake/local knowledge DB status.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  if [[ -f "$1" ]]; then
    pass "file exists: $1"
  else
    fail "file missing: $1"
  fi
}

check_dir() {
  if [[ -d "$1" ]]; then
    pass "directory exists: $1"
  else
    fail "directory missing: $1"
  fi
}

check_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    fail "$file missing for $label"
    return
  fi
  if grep -F -- "$phrase" "$file" >/dev/null; then
    pass "doc mentions $label"
  else
    fail "$file must mention $label"
  fi
}

check_json() {
  local file="$1"
  if python3 -m json.tool "$file" >/dev/null 2>&1; then
    pass "JSON parses: $file"
  else
    fail "JSON parse failed: $file"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section "Canvas LLM Phase 5 Fake/Local Knowledge DB"
cat <<'STATUS'
Status: canvas_llm_phase_5_fake_local_knowledge_db_complete
Classification: docs/status/fake-local JSON prototype only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 5 Artifacts"
check_file "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md"
check_file "docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md"
check_dir "fixtures/canvas-llm/knowledge-db"
check_file "fixtures/canvas-llm/knowledge-db/README.md"

section "Knowledge DB JSON Fixtures"
for file in \
  fixtures/canvas-llm/knowledge-db/fake-sources.json \
  fixtures/canvas-llm/knowledge-db/fake-evidence.json \
  fixtures/canvas-llm/knowledge-db/fake-patterns.json \
  fixtures/canvas-llm/knowledge-db/fake-facts.json \
  fixtures/canvas-llm/knowledge-db/fake-qa.json \
  fixtures/canvas-llm/knowledge-db/fake-courses.json \
  fixtures/canvas-llm/knowledge-db/fake-modules.json \
  fixtures/canvas-llm/knowledge-db/fake-pages.json \
  fixtures/canvas-llm/knowledge-db/fake-assignments.json \
  fixtures/canvas-llm/knowledge-db/fake-announcements.json \
  fixtures/canvas-llm/knowledge-db/fake-files.json
do
  check_file "$file"
  check_json "$file"
done

section "Source-Backed Chain"
check_contains "fixtures/canvas-llm/knowledge-db/fake-qa.json" "fact_fake_banner_001" "QA links to fact"
check_contains "fixtures/canvas-llm/knowledge-db/fake-facts.json" "ev_fake_banner_pattern_001" "fact links to evidence"
check_contains "fixtures/canvas-llm/knowledge-db/fake-evidence.json" "src_fake_canvas_style_001" "evidence links to source"
check_contains "fixtures/canvas-llm/knowledge-db/fake-sources.json" "fake_local_fixture" "source class fake local"
check_contains "fixtures/canvas-llm/knowledge-db/fake-sources.json" "Level 0" "evidence level 0"
check_contains "fixtures/canvas-llm/knowledge-db/fake-qa.json" "fixture_approved" "approval status fixture approved"

section "Boundary Assertions"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Canvas API/OAuth/live reads: blocked" "Canvas live access blocked"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Student data: blocked" "student data blocked"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Real curriculum ingestion: blocked" "real curriculum ingestion blocked"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Runtime SQLite/database writes: blocked" "runtime database writes blocked"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Generation/RAG/embeddings: blocked" "generation RAG embeddings blocked"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "2024-2025" "inactive 2024-2025 source gate"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "2025-2026" "inactive 2025-2026 source gate"
check_contains "docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md" "Sandbox/demo Canvas courses" "sandbox demo course future target"

section "Future Query Boundary"
check_contains "docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md" "Question -> Answer -> Fact(s) -> Evidence -> Source Reference -> Source Class -> Evidence Level -> Approval Status" "source-backed lookup chain"
check_contains "docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md" "Phase 5 does not approve live Canvas lookup" "live lookup blocked"
check_contains "docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md" "AI-generated answers" "generated answers blocked"
check_contains "docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md" "SQLite writes" "SQLite writes blocked"

section "Continuity Checks"
if bin/chief-of-staff --canvas-llm-phase-4-status >/tmp/canvas-phase-4-status.out 2>&1; then
  pass "Phase 4 status still passes"
else
  fail "Phase 4 status failed"
  tail -40 /tmp/canvas-phase-4-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
