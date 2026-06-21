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
log "A full log will be saved to ${LOG_FILE}."

run_step "setup/00-check-system.sh"
run_step "setup/01-install-homebrew.sh"
run_step "setup/02-install-apps.sh"
run_step "setup/03-macos-defaults.sh"
run_step "setup/04-folder-structure.sh"
run_step "setup/05-dock-layout.sh"
run_step "setup/06-wallpapers.sh"
run_step "setup/07-git-github.sh"
run_step "setup/08-local-ai.sh"
run_step "setup/09-generate-report.sh"
run_step "setup/99-verify-setup.sh"

log ""
log "🎉 Phase 0 setup finished. Review any WARN messages above, then continue when ready."
