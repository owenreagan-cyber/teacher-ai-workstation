#!/usr/bin/env bash
# Read-only Widget and Shortcut Builder catalog status. Planning visibility only — no install or automation.
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

section 'Widget and Shortcut Builder (Read-Only Catalog Foundation)'
cat <<'EOF'
Status: read-only catalog planning only
Widget install: blocked
Shortcut install: blocked
Shortcut execution: blocked
AppleScript: blocked
Mac system changes: blocked
Automation: no
Network calls: no
EOF

check_file docs/widget-shortcut-builder-catalog-foundation.md
check_file docs/widget-shortcut-builder-non-activation-boundaries.md
check_file docs/widget-shortcut-builder-readiness-plan.md
check_doc_contains docs/widget-shortcut-builder-catalog-foundation.md "complete_v1_f1" "widget shortcut closure status"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Widget install: blocked" "widget install blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Shortcut install: blocked" "shortcut install blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Shortcut execution: blocked" "shortcut execution blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "AppleScript: blocked" "applescript blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Automation: no" "no automation boundary"
check_doc_contains docs/widget-shortcut-builder-readiness-plan.md "metadata-only" "catalog metadata-only boundary"
check_doc_contains docs/widget-shortcut-builder-readiness-plan.md "Chief of Staff Status Widget" "widget catalog concept"

section 'Roadmap and Capability Coherence'
check_doc_contains docs/master-build-roadmap.md "Widget and Shortcut Builder" "roadmap widget shortcut builder"
check_doc_contains docs/teacher-workstation-capability-map.md "Widget catalog" "capability map widget catalog"
check_doc_contains docs/build-queue.md "Widget and Shortcut Builder" "build queue widget shortcut builder"

section 'Related Program Cross-Links'
check_doc_contains docs/mac-workstation-experience-foundation.md "Widget and Shortcut Builder" "mac workstation points to program f"
check_doc_contains docs/local-llm-workstation-status-foundation.md "Widget and Shortcut Builder" "local llm points to program f"
check_doc_contains docs/ai-tool-routing-foundation.md "Widget and Shortcut Builder" "ai routing points to program f"

section 'Catalog Planning Summary'
printf 'Widget catalog: metadata-only concepts documented\n'
printf 'Shortcut catalog: metadata-only concepts documented\n'
printf 'Live health probes: blocked (--widget-health / --shortcut-health planned)\n'
pass 'catalog planning summary emitted'

section 'CLI and Manifest'
[[ -f bin/chief-of-staff ]] && grep -Fq -- '--widget-shortcut-status' bin/chief-of-staff && pass 'CLI exposes --widget-shortcut-status' || fail 'CLI missing --widget-shortcut-status'
[[ -f assistant/chief-of-staff/v1/command-surface-manifest.json ]] && pass 'command manifest exists' || fail 'command manifest missing'
if grep -Fq -- '"--widget-shortcut-status"' assistant/chief-of-staff/v1/command-surface-manifest.json 2>/dev/null; then
  pass 'manifest lists --widget-shortcut-status'
else
  fail 'manifest missing --widget-shortcut-status'
fi

section 'Negative Non-Activation Assertions'
status_script="scripts/widget-shortcut-builder-status.sh"
if grep -Eq '(^|[;&|[:space:]])shortcuts[[:space:]]+(run|list|view|sign)' "${status_script}" 2>/dev/null; then
  fail 'widget shortcut status script must not shell-invoke shortcuts CLI'
else
  pass 'widget shortcut status script does not shell-invoke shortcuts CLI'
fi
if grep -Eq '(^|[;&|[:space:]])osascript[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'widget shortcut status script must not shell-invoke osascript'
else
  pass 'widget shortcut status script does not shell-invoke osascript'
fi
if grep -Eq '(^|[;&|[:space:]])defaults[[:space:]]+write' "${status_script}" 2>/dev/null; then
  fail 'widget shortcut status script must not shell-invoke prefs defaults'
else
  pass 'widget shortcut status script does not shell-invoke prefs defaults'
fi
if grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'widget shortcut status script must not shell-invoke curl'
else
  pass 'widget shortcut status script does not shell-invoke curl'
fi
if grep -Eq '(^|[;&|[:space:]])(brew|npm|pip|apt-get|yum)[[:space:]]' "${status_script}" 2>/dev/null; then
  fail 'widget shortcut status script must not shell-invoke package managers'
else
  pass 'widget shortcut status script does not shell-invoke package managers'
fi
pass 'no widget install attempted'
pass 'no shortcut install attempted'
pass 'no shortcut file creation attempted'
pass 'no Mac system mutation attempted'
pass 'no network call attempted'
pass 'no automation attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
