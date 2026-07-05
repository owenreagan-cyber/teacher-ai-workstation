#!/usr/bin/env bash
# Optional local timing map for dashboard/validate-all subchecks.
# Writes to .tmp/validation-subcheck-timing.log (gitignored). Does not run aggregates.
#
# Usage:
#   bash scripts/validation-subcheck-timing.sh dashboard-core
#   bash scripts/validation-subcheck-timing.sh validate-all-tracks
#   bash scripts/validation-subcheck-timing.sh vault-chain
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
cd "${repo_root}"
mkdir -p .tmp
log_file=".tmp/validation-subcheck-timing.log"

time_one() {
  local label="$1"
  local script="$2"
  shift 2
  if [[ ! -f "${script}" ]]; then
    printf 'MISSING %s (%s)\n' "${label}" "${script}" | tee -a "${log_file}"
    return
  fi
  local start end elapsed rc=0
  start=$(date +%s)
  bash "${script}" "$@" >/dev/null 2>&1 || rc=$?
  end=$(date +%s)
  elapsed=$((end - start))
  printf '%ss exit=%s %s (%s)\n' "${elapsed}" "${rc}" "${label}" "${script}" | tee -a "${log_file}"
}

profile="${1:-dashboard-core}"
{
  printf '\n=== validation-subcheck-timing profile=%s at %s ===\n' "${profile}" "$(date '+%Y-%m-%d %H:%M:%S')"
} >>"${log_file}"

case "${profile}" in
  dashboard-core)
    time_one phase-1 scripts/phase-1-status.sh
    time_one phase-0e scripts/verify-phase-0e.sh
    time_one curriculum-builder-foundation scripts/curriculum-builder-foundation-status.sh
    time_one whole-system-coherence scripts/whole-system-coherence-status.sh
    time_one whole-system-master-roadmap scripts/whole-system-master-roadmap-status.sh
    ;;
  vault-chain)
    time_one vault-m0 scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh
    time_one vault-m7e scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh
    time_one vault-m7e-skip-preservation scripts/teacher-knowledge-vault-m7e-local-test-catalog-status.sh
    ;;
  validate-all-tracks)
    time_one cursor-workflow scripts/cursor-workflow-status.sh
    time_one curriculum-contract-suite tests/curriculum-contract-suite-v0-test.sh
    time_one vibe-wallpaper-widgets scripts/vibe-wallpaper-widgets-planning-status.sh
    ;;
  *)
    echo "Unknown profile: ${profile}" >&2
    echo "Profiles: dashboard-core, vault-chain, validate-all-tracks" >&2
    exit 1
    ;;
esac

printf 'Timing log: %s\n' "${log_file}"
