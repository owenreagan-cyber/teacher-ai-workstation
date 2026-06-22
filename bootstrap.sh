#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/setup.log"

mkdir -p "${LOG_DIR}"
: > "${LOG_FILE}"

log() {
  echo "$1" | tee -a "${LOG_FILE}"
}

run_step() {
  local script="$1"
  log ""
  log "▶ Running ${script}"
  log "This may take a few minutes. If something needs your attention, the script will explain what to do."
  if bash "${script}" 2>&1 | tee -a "${LOG_FILE}"; then
    log "✅ Finished ${script}"
  else
    log "❌ Critical setup step failed: ${script}"
    log "Setup stopped so you can fix the issue above. After fixing it, rerun: ./bootstrap.sh"
    exit 1
  fi
}

log "Welcome to the Teacher AI Workstation Phase 0 setup."
log "We will check your Mac, install tools, apply helpful settings, create folders, and verify the result."
log "The final verification step checks automated setup only. Manual Day 1 items stay in docs/day-1-manual-steps.md."
log "A full log will be saved to ${LOG_FILE}."

setup_scripts=(
  "setup/00-check-system.sh"
  "setup/01-install-homebrew.sh"
  "setup/02-install-apps.sh"
  "setup/03-macos-defaults.sh"
  "setup/04-folder-structure.sh"
  "setup/05-dock-layout.sh"
  "setup/06-wallpapers.sh"
  "setup/07-git-github.sh"
  "setup/08-local-ai.sh"
  "setup/09-generate-report.sh"
  "setup/10-shell-profile.sh"
)

setup_scripts+=("setup/99-verify-setup.sh")

for script in "${setup_scripts[@]}"; do
  run_step "${script}"
done

log ""
log "🎉 Phase 0 setup finished. Review any WARN messages above."
log "Shell enhancements may require opening a new Terminal window, or running: source ~/.zshrc"
log "Complete the manual checklist, restart once, then rerun final verification: bash setup/99-verify-setup.sh"
log "Remember: automated verification is not final manual certification."
