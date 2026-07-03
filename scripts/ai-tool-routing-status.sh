#!/usr/bin/env bash
# Read-only AI Tool Routing operational status. Reports lanes only — no live routing.
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

check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  if [[ ! -f "${path}" ]]; then
    fail "${path} must mention ${label}"
    return
  fi
  if grep -Fq -- "${needle}" "${path}"; then
    pass "doc mentions ${label}"
  else
    fail "${path} must mention ${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'AI Tool Routing Matrix (Read-Only Operational Surface)'
cat <<'EOF'
Status: read-only routing visibility only
Routing matrix version: 2026-07-02-v1
Local LLM D1: separate lane — see --local-llm-workstation-status
Automated routing: no
Network calls: no
Ollama ping: no
Model inference: no
Package managers: no
EOF

check_file docs/ai-tool-routing-operational-surface.md
check_file docs/ai-tool-routing-foundation.md
check_file docs/ai-tool-routing-matrix.md
check_file assistant/model-routing.md
check_doc_contains docs/ai-tool-routing-operational-surface.md "read-only routing visibility" "operational read-only boundary"
check_doc_contains docs/ai-tool-routing-operational-surface.md "Health Monitor" "health monitor separation"
check_doc_contains docs/ai-tool-routing-operational-surface.md "Network calls: no" "no network boundary"
check_doc_contains docs/ai-tool-routing-foundation.md "complete_v1_r" "routing closure status"
check_doc_contains docs/ai-tool-routing-matrix.md "no automated routing active" "matrix no automated routing boundary"
check_doc_contains docs/ai-tool-routing-matrix.md "Matrix version: 2026-07-02-v1" "routing matrix version stamp"
check_doc_contains assistant/model-routing.md "inactive by default" "model routing inactive default"
check_doc_contains docs/lovable-classroom-app-builder-foundation.md "complete_v1_g1" "lovable g1 routing cross-link"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "AI Tool Routing Matrix" "roadmap ai tool routing"
check_doc_contains docs/teacher-workstation-capability-map.md "Tool routing surface" "capability map tool routing"
check_doc_contains docs/build-queue.md "AI Tool Routing" "build queue ai tool routing"

section 'Tool Lane Summary (Planning)'
printf 'Cursor: active local repo work only\n'
printf 'Cloud tools (ChatGPT/Claude/Gemini): manual browser only — routing inactive\n'
printf 'Lovable: planning only — blocked\n'
printf 'Ollama/local LLM: planning only — blocked\n'
printf '3D Builder: planning only — blocked\n'
pass 'tool lane summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--model-routing-status' bin/chief-of-staff && pass 'CLI exposes --model-routing-status' || fail 'CLI missing --model-routing-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'

section 'Negative Non-Activation Assertions'
routing_invocations="$(grep -Ev 'must not shell-invoke|does not shell-invoke|must not reference|does not reference' scripts/ai-tool-routing-status.sh || true)"
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' <<< "${routing_invocations}"; then
  fail 'routing status script must not shell-invoke curl'
else
  pass 'routing status script does not shell-invoke curl'
fi
if grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' <<< "${routing_invocations}"; then
  fail 'routing status script must not shell-invoke ollama'
else
  pass 'routing status script does not shell-invoke ollama'
fi
if grep -Eq '(api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|lovable\.dev)' <<< "${routing_invocations}"; then
  fail 'routing status script must not reference cloud API endpoint invocation'
else
  pass 'routing status script does not reference cloud API endpoint invocation'
fi
pass 'no automated routing attempted'
pass 'no API call attempted'
pass 'no network call attempted'
pass 'no package manager invoked'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
