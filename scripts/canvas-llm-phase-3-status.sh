#!/usr/bin/env bash
# Read-only Canvas LLM Phase 3 status. No live Canvas access; no packet writes.
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

section 'Canvas LLM Phase 3 Manual Evidence Normalizer'
cat <<'BANNER'
Status: canvas_llm_phase_3_manual_evidence_normalizer_complete
Classification: fake/local/manual/redacted fixture normalization only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Production writes: blocked
Network access: no
BANNER

section 'Artifacts'
check_file docs/programs/canvas-llm/canvas-phase-3-manual-evidence-normalizer.md
check_file docs/programs/canvas-llm/canvas-manual-evidence-packet-format.md
check_file docs/programs/canvas-llm/canvas-future-knowledge-domains.md
check_dir fixtures/canvas-llm/manual-evidence-packets/sample-redacted-packet
check_file fixtures/canvas-llm/manual-evidence-packets/sample-redacted-packet/packet.json
check_file scripts/canvas-llm-manual-evidence-normalizer.sh
check_file scripts/canvas-llm-phase-3-status.sh

section 'Shell Syntax'
bash -n scripts/canvas-llm-manual-evidence-normalizer.sh && pass 'normalizer shell syntax valid' || fail 'normalizer shell syntax invalid'
bash -n scripts/canvas-llm-phase-3-status.sh && pass 'phase 3 status shell syntax valid' || fail 'phase 3 status shell syntax invalid'

section 'Normalizer Proof'
if scripts/canvas-llm-manual-evidence-normalizer.sh fixtures/canvas-llm/manual-evidence-packets/sample-redacted-packet >/tmp/canvas-phase-3-normalizer.out 2>&1; then
  pass 'sample redacted packet normalizes in dry-run mode'
else
  fail 'sample redacted packet failed normalizer'
  cat /tmp/canvas-phase-3-normalizer.out || true
fi
if scripts/canvas-llm-manual-evidence-normalizer.sh >/tmp/canvas-phase-3-missing.out 2>&1; then fail 'normalizer must reject missing argument'; else pass 'normalizer rejects missing argument'; fi
if scripts/canvas-llm-manual-evidence-normalizer.sh / >/tmp/canvas-phase-3-root.out 2>&1; then fail 'normalizer must reject broad root path'; else pass 'normalizer rejects broad root path'; fi
if scripts/canvas-llm-manual-evidence-normalizer.sh .. >/tmp/canvas-phase-3-parent.out 2>&1; then fail 'normalizer must reject parent traversal'; else pass 'normalizer rejects parent traversal'; fi

tmp_packet="$(mktemp -d "${TMPDIR:-/tmp}/canvas-phase-3-missing.XXXXXX")"
if scripts/canvas-llm-manual-evidence-normalizer.sh "$tmp_packet" >/tmp/canvas-phase-3-outside.out 2>&1; then fail 'normalizer must reject outside temp packet'; else pass 'normalizer rejects outside packet path'; fi
rm -rf "$tmp_packet"

section 'Documentation And Wiring'
check_help '--canvas-llm-phase-3-status'
check_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--canvas-llm-phase-3-status"' 'manifest Canvas Phase 3 command'
check_contains docs/chief-of-staff-command-index-v1.md '--canvas-llm-phase-3-status' 'command index Canvas Phase 3 command'
check_contains docs/master-plan/build-state-checklist.md 'Canvas LLM Phase 3 manual evidence normalizer' 'build-state Phase 3 status'
check_contains docs/build-queue.md 'canvas_llm_phase_3_manual_evidence_normalizer_complete' 'build queue Phase 3 closure'
check_contains docs/master-plan/current-focus.md 'Maintain Canvas LLM Phase 3 as manual/redacted packet normalization only' 'current focus Phase 3 boundary'
check_contains assistant/memory/active-priorities.md 'Canvas LLM Phase 3 manual evidence normalizer: complete' 'active priorities Phase 3 closure'
check_contains docs/programs/canvas-llm/canvas-llm-phase-plan.md 'Phase 3 - Manual Evidence Normalizer' 'phase plan Phase 3 update'
check_contains docs/programs/canvas-llm/README.md 'Phase 3 manual evidence normalizer' 'Canvas README Phase 3 update'

section 'Boundary Assertions'
check_contains docs/programs/canvas-llm/canvas-phase-3-manual-evidence-normalizer.md 'Canvas API/OAuth/live reads: blocked' 'Canvas live access blocked'
check_contains docs/programs/canvas-llm/canvas-phase-3-manual-evidence-normalizer.md 'Student data: blocked' 'student data blocked'
check_contains docs/programs/canvas-llm/canvas-phase-3-manual-evidence-normalizer.md 'Real curriculum ingestion: blocked' 'real curriculum ingestion blocked'
check_contains docs/programs/canvas-llm/canvas-phase-3-manual-evidence-normalizer.md 'Future real Canvas source use requires a later approval-gated phase' 'future Canvas fetch deferred'
check_contains docs/programs/canvas-llm/canvas-manual-evidence-packet-format.md 'Phase 3 does not approve that promotion' 'no promotion approval'

section 'Phase 0-2 Continuity'
check_help '--canvas-llm-phase-0-status'
check_help '--canvas-llm-phase-1-status'
check_help '--canvas-llm-phase-2-status'

section 'Summary'
printf 'PASS: %s\n' "$PASS_COUNT"; printf 'WARN: %s\n' "$WARN_COUNT"; printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -gt 0 ]] && exit 1
exit 0
