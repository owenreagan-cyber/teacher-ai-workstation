#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Image Review Status
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation
# @raycast.description Show local image review queue and approval manifest status

set -euo pipefail

REPO_DIR="${HOME}/Projects/teacher-ai-workstation"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this Raycast script template.\n'
  exit 1
fi

cd "$REPO_DIR"
python3 scripts/image-review-status.py
