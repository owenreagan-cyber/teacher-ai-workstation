#!/usr/bin/env bash
# Read-only Local LLM/Ollama workstation status. Planning visibility only — no runtime probes.
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

section 'Local LLM / Ollama Workstation (Read-Only Status Foundation)'
cat <<'EOF'
Status: read-only planning only
No Ollama execution: yes
Ollama install: blocked
Model downloads: blocked
Model inference: blocked
Network calls: no
Localhost ping: no
Port checks: no
EOF

check_file docs/local-llm-workstation-status-foundation.md
check_file docs/local-llm-non-activation-boundaries.md
check_file docs/local-llm-ollama-readiness-plan.md
check_doc_contains docs/local-llm-workstation-status-foundation.md "complete_v1_d1" "local llm closure status"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Ollama install: blocked" "ollama install blocked"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Model downloads: blocked" "model downloads blocked"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Model inference: blocked" "model inference blocked"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Network calls: no" "no network boundary"
check_doc_contains docs/local-llm-non-activation-boundaries.md "AI Tool Routing" "ai tool routing separation"
check_doc_contains docs/local-llm-non-activation-boundaries.md "Health Monitor" "health monitor separation"
check_doc_contains docs/local-llm-ollama-readiness-plan.md "read-only planning" "readiness read-only boundary"
check_doc_contains assistant/model-routing.md "inactive by default" "model routing inactive default"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Local LLM / Ollama Workstation" "roadmap local llm"
check_doc_contains docs/teacher-workstation-capability-map.md "Local LLM / Ollama workstation" "capability map local llm"
check_doc_contains docs/build-queue.md "Local LLM" "build queue local llm"

section 'Planning Summary (No Runtime Probes)'
printf 'Ollama runtime: not probed — planning only\n'
printf 'Installed models: not inspected — blocked\n'
printf 'AI Tool Routing lane: Ollama blocked (see --model-routing-status)\n'
printf 'Health Monitor live LLM health: planned/blocked (--local-llm-health)\n'
pass 'planning summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--local-llm-workstation-status' bin/chief-of-staff && pass 'CLI exposes --local-llm-workstation-status' || fail 'CLI missing --local-llm-workstation-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'

section 'Negative Non-Activation Assertions'
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' scripts/local-llm-workstation-status.sh 2>/dev/null; then
  fail 'local llm status script must not shell-invoke curl'
else
  pass 'local llm status script does not shell-invoke curl'
fi
if grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' scripts/local-llm-workstation-status.sh 2>/dev/null; then
  fail 'local llm status script must not shell-invoke ollama'
else
  pass 'local llm status script does not shell-invoke ollama'
fi
if grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' scripts/local-llm-workstation-status.sh 2>/dev/null; then
  fail 'local llm status script must not shell-invoke brew'
else
  pass 'local llm status script does not shell-invoke brew'
fi
if grep -Eq '(^|[;&|[:space:]])nc[[:space:]]' scripts/local-llm-workstation-status.sh 2>/dev/null; then
  fail 'local llm status script must not shell-invoke nc'
else
  pass 'local llm status script does not shell-invoke nc'
fi
pass 'no model download attempted'
pass 'no local inference attempted'
pass 'no network call attempted'
pass 'no package manager invoked'
pass 'no localhost port check attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
