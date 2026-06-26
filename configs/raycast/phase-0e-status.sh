#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Phase 0E Status
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation
# @raycast.description Check Phase 0E visual mode and image review status

set -euo pipefail

REPO_DIR="${HOME}/Projects/teacher-ai-workstation"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this Raycast script template.\n'
  exit 1
fi

cd "$REPO_DIR"
bash scripts/phase-0e-summary.sh
