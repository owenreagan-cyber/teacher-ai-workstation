#!/usr/bin/env bash
set -euo pipefail

run_section() {
  local title="$1"
  shift

  printf '\n%s\n' "$title"
  printf '%s\n' "$(printf '%*s' "${#title}" '' | tr ' ' '=')"

  if "$@"; then
    printf '\nPASS: %s completed.\n' "$title"
  else
    printf '\nWARN: %s returned a nonzero status. Continue reading the dashboard output above.\n' "$title"
  fi
}

printf '\nPhase 0E Dashboard\n'
printf '==================\n'
printf 'Read-only status dashboard. No --apply commands are used.\n'

if [[ -f scripts/mode-status.sh ]]; then
  run_section "Visual Mode Status" bash scripts/mode-status.sh
else
  printf '\nWARN: scripts/mode-status.sh missing.\n'
fi

if command -v python3 >/dev/null 2>&1 && [[ -f scripts/image-review-status.py ]]; then
  run_section "Image Review Status" python3 scripts/image-review-status.py
else
  printf '\nWARN: python3 or scripts/image-review-status.py missing; skipping image review status.\n'
fi

if [[ -f scripts/verify-phase-0e.sh ]]; then
  run_section "Phase 0E Verification" bash scripts/verify-phase-0e.sh
else
  printf '\nWARN: scripts/verify-phase-0e.sh missing.\n'
fi

printf '\nDashboard complete.\n'
printf 'Reminder: warnings about missing optional local folders are usually fixed by setup scripts.\n'
