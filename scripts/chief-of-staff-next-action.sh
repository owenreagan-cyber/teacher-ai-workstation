#!/usr/bin/env bash
# Read-only deterministic next-action recommendation. No LLM, network, or automation.
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

build_queue_doc="docs/build-queue.md"
active_priorities_doc="assistant/memory/active-priorities.md"
roadmap_doc="docs/master-build-roadmap.md"
implementation_gate_doc="docs/implementation-approval-gate.md"
canvas_stop_doc="docs/canvas-llm-stop-marker-curriculum-builder-return.md"

section 'Chief of Staff Next Action (Deterministic)'
cat <<'EOF'
Status: read-only recommendation only
LLM inference: no
Autonomous mission start: no
Network calls: no
EOF

major_program=""
daily_focus=""
roadmap_mission=""
implementation_gate="not approved by default"
canvas_frozen="unknown"

if [[ -f "${build_queue_doc}" ]]; then
  pass "build queue doc exists"
  major_program="$(awk -F': ' '/Recommended next major program:/ { print $2; exit }' "${build_queue_doc}" | sed 's/\.$//')"
  if [[ -n "${major_program}" ]]; then
    pass "major program parsed from build queue"
  else
    warn "major program not found in build queue"
  fi
else
  fail "build queue doc missing"
fi

if [[ -f "${active_priorities_doc}" ]]; then
  pass "active priorities doc exists"
  daily_focus="$(awk -F': ' '/Recommended next focus:/ { print $2; exit }' "${active_priorities_doc}")"
  if [[ -n "${daily_focus}" ]]; then
    pass "daily focus parsed from active priorities"
  else
    warn "daily focus not found in active priorities"
  fi
else
  fail "active priorities doc missing"
fi

if [[ -f "${roadmap_doc}" ]]; then
  pass "master build roadmap doc exists"
  roadmap_mission="$(awk '
    /^## 10\. Immediate Next Recommended Mission$/ { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /^[*][*]/ { gsub(/^\*\*|\*\*$/, ""); print; exit }
  ' "${roadmap_doc}")"
  if [[ -n "${roadmap_mission}" ]]; then
    pass "roadmap immediate mission heading parsed"
  else
    warn "roadmap immediate mission heading not found"
  fi
else
  fail "master build roadmap doc missing"
fi

if [[ -f "${implementation_gate_doc}" ]]; then
  if grep -Fq "not approved by default" "${implementation_gate_doc}"; then
    pass "implementation gate default boundary documented"
  else
    warn "implementation gate missing not approved by default wording"
  fi
else
  fail "implementation approval gate doc missing"
fi

if [[ -f "${canvas_stop_doc}" ]]; then
  if grep -Fq "stop marker" "${canvas_stop_doc}" && grep -Fq "Do not start Canvas LLM PRs by default" "${canvas_stop_doc}"; then
    canvas_frozen="active"
    pass "canvas llm stop marker active"
  else
    canvas_frozen="unclear"
    warn "canvas llm stop marker wording incomplete"
  fi
else
  canvas_frozen="missing"
  fail "canvas llm stop marker doc missing"
fi

section 'Recommended Next Action'
if [[ -n "${major_program}" ]]; then
  printf 'Recommended major program: %s\n' "${major_program}"
  pass "recommended major program emitted"
else
  printf 'Recommended major program: (not parsed)\n'
  warn "recommended major program not emitted"
fi

if [[ -n "${daily_focus}" ]]; then
  printf 'Recommended daily focus: %s\n' "${daily_focus}"
  pass "recommended daily focus emitted"
fi

if [[ -n "${roadmap_mission}" ]]; then
  printf 'Roadmap immediate mission heading: %s\n' "${roadmap_mission}"
  pass "roadmap mission context emitted"
fi

printf 'Implementation gate: %s\n' "${implementation_gate}"
pass "implementation gate status emitted"

printf 'Canvas LLM runtime: frozen (stop marker %s)\n' "${canvas_frozen}"
pass "canvas llm frozen status emitted"

printf '\n>>> Next recommended action: proceed with %s using explicit mission authorization; do not start Canvas LLM runtime or approval-gated work by default. <<<\n\n' \
  "${major_program:-approved program mission from docs/master-build-roadmap.md}"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
