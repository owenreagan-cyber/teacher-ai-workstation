#!/usr/bin/env bash
# Lane-review hardening guardrail tests — banners and negative non-mutation assertions.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running lane-review hardening guardrail tests..."

assert_banner() {
  local script="$1"
  local needle="$2"
  local label="$3"
  local tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/lane-hardening.XXXXXX")"
  bash "${script}" >"${tmp}" 2>&1 || {
    echo "FAIL: ${script} exited nonzero"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  grep -q "${needle}" "${tmp}" || {
    echo "FAIL: ${label} — missing banner: ${needle}"
    cat "${tmp}"
    rm -f "${tmp}"
    exit 1
  }
  rm -f "${tmp}"
}

assert_banner scripts/teacher-workstation-health-status.sh 'Health vs Updater' 'health updater boundary'
assert_banner scripts/teacher-workstation-health-status.sh 'Canvas LLM: frozen' 'canvas frozen banner'
assert_banner scripts/teacher-workstation-system-updater-status.sh 'Check-only: yes' 'updater check-only banner'
assert_banner scripts/mac-workstation-experience-status.sh 'Planning-only: yes' 'mac planning-only banner'
assert_banner scripts/mac-workstation-experience-status.sh 'Widget/Shortcut lane (F1)' 'mac f1 cross-link'
assert_banner scripts/lovable-classroom-app-builder-status.sh 'External Lovable fetch: blocked' 'lovable no-fetch banner'
assert_banner scripts/ai-tool-routing-status.sh 'Routing matrix version: 2026-07-02-v1' 'routing matrix version stamp'
assert_banner scripts/ai-tool-routing-status.sh 'Local LLM D1' 'r0 d1 cross-link'
assert_banner scripts/local-llm-workstation-status.sh 'AI Tool Routing R0' 'd1 r0 cross-link'
assert_banner scripts/cursor-operating-modes-status.sh 'Discovery ≠ implementation approval' 'operating modes discovery banner'
assert_banner scripts/3d-builder-workshop-agent-status.sh 'Planning-only: yes' '3d planning-only banner'

for doc in \
  docs/cursor-autonomous-build-engine-sprint-queue-template.md \
  docs/3d-builder-workshop-agent-scope-one-pager.md \
  docs/lovable-classroom-app-builder-mission-approval-gate-checklist.md \
  docs/local-llm-readiness-checklist-tracker.md \
  docs/proposals/implemented/lane-review-hardening-sprint.md; do
  [[ -f "${doc}" ]] || {
    echo "FAIL: missing doc ${doc}"
    exit 1
  }
done

echo "PASS: lane-review hardening guardrail tests passed."
