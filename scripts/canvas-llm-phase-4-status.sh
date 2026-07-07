#!/usr/bin/env bash
# Read-only Canvas LLM Phase 4 status. No live Canvas access; no runtime storage.
set -euo pipefail
PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass(){ PASS_COUNT=$((PASS_COUNT+1)); printf 'PASS: %s\n' "$1"; }
warn(){ WARN_COUNT=$((WARN_COUNT+1)); printf 'WARN: %s\n' "$1"; }
fail(){ FAIL_COUNT=$((FAIL_COUNT+1)); printf 'FAIL: %s\n' "$1"; }
section(){ printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file(){ [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_dir(){ [[ -d "$1" ]] && pass "directory exists: $1" || fail "directory missing: $1"; }
check_contains(){ local f="$1" p="$2" l="$3"; [[ -f "$f" ]] || { fail "$f must mention $l"; return; }; grep -F -- "$p" "$f" >/dev/null && pass "doc mentions $l" || fail "$f must mention $l"; }
check_help(){ bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$repo_root" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "$repo_root"

section 'Canvas LLM Phase 4 Knowledge Architecture'
cat <<'BANNER'
Status: canvas_llm_phase_4_knowledge_architecture_complete
Classification: docs/status/schema/fake-local fixtures only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Generation/RAG/embeddings: blocked
Local JSON/SQLite runtime writes: blocked
BANNER

section 'Artifacts'
check_file docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md
check_file docs/programs/canvas-llm/canvas-knowledge-object-model.md
check_file docs/programs/canvas-llm/canvas-pattern-catalog-schema.md
check_file docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md
check_file docs/programs/canvas-llm/canvas-local-storage-schema-plan.md
check_dir fixtures/canvas-llm/knowledge-architecture
check_file fixtures/canvas-llm/knowledge-architecture/README.md
check_file scripts/canvas-llm-phase-4-status.sh

section 'JSON Fixture Proof'
json_count="$(find fixtures/canvas-llm/knowledge-architecture -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')"
if [[ "${json_count}" -gt 0 ]]; then
  pass 'at least one fake/local knowledge architecture JSON fixture exists'
else
  fail 'at least one fake/local knowledge architecture JSON fixture must exist'
fi
if python3 - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("fixtures/canvas-llm/knowledge-architecture").glob("*.json")):
    with path.open("r", encoding="utf-8") as fh:
        json.load(fh)
PY
then
  pass 'knowledge architecture JSON fixtures parse'
else
  fail 'knowledge architecture JSON fixtures must parse'
fi

section 'Shell Syntax'
bash -n scripts/canvas-llm-phase-4-status.sh && pass 'phase 4 status shell syntax valid' || fail 'phase 4 status shell syntax invalid'

section 'Boundary Assertions'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Inactive historical Canvas courses include the 2024-2025 and 2025-2026 school years' 'inactive historical courses and school years'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Sandbox/demo Canvas courses are preferred for future API testing because Owen can create them with no student data' 'sandbox/demo Canvas courses no student data'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Canvas API/OAuth/live reads: blocked' 'Canvas API/OAuth/live reads blocked'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Canvas writes/publishing: blocked' 'Canvas writes/publishing blocked'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Real curriculum ingestion: blocked' 'real curriculum ingestion blocked'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Student data: blocked' 'student data blocked'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Generation/RAG/embeddings: blocked' 'RAG/embeddings/generation blocked'
check_contains docs/programs/canvas-llm/canvas-local-storage-schema-plan.md 'Runtime SQLite/database writes: blocked' 'local JSON/SQLite schema planned/static only'
check_contains docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md 'Future Q&A and fact lookup must be source-backed' 'evidence-backed Q&A future-only'
check_contains docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md 'No evidence level authorizes Canvas API/OAuth/live reads' 'no evidence level authorizes live reads'
check_contains docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md 'inactive historical course evidence, approval-gated' 'inactive historical courses approval-gated'
check_contains docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md 'sandbox/demo Canvas course evidence' 'sandbox/demo source class'

section 'Documentation And Wiring'
check_help '--canvas-llm-phase-4-status'
check_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--canvas-llm-phase-4-status"' 'manifest Canvas Phase 4 command'
check_contains docs/chief-of-staff-command-index-v1.md '--canvas-llm-phase-4-status' 'command index Canvas Phase 4 command'
check_contains docs/programs/canvas-llm/README.md 'Phase 4 knowledge architecture and pattern catalog' 'Canvas README Phase 4 update'
check_contains docs/programs/canvas-llm/canvas-llm-phase-plan.md 'Phase 4 - Canvas Knowledge Architecture And Pattern Catalog' 'phase plan Phase 4 update'
check_contains docs/master-plan/build-state-checklist.md 'Canvas LLM Phase 4 knowledge architecture and pattern catalog' 'build-state Phase 4 status'
check_contains docs/master-plan/current-focus.md 'Maintain Canvas LLM Phase 4 as knowledge architecture and pattern catalog schema only' 'current focus Phase 4 boundary'
check_contains docs/build-queue.md 'canvas_llm_phase_4_knowledge_architecture_complete' 'build queue Phase 4 closure'
check_contains assistant/memory/active-priorities.md 'Canvas LLM Phase 4 knowledge architecture and pattern catalog: complete' 'active priorities Phase 4 closure'

section 'Continuity'
check_help '--canvas-llm-phase-0-status'
check_help '--canvas-llm-phase-1-status'
check_help '--canvas-llm-phase-2-status'
check_help '--canvas-llm-phase-3-status'
check_help '--antigravity-evaluation-status'

section 'Summary'
printf 'PASS: %s\n' "$PASS_COUNT"; printf 'WARN: %s\n' "$WARN_COUNT"; printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -gt 0 ]] && exit 1
exit 0
