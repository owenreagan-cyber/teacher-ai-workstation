#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Dry Run Approved Photos Import
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation
# @raycast.description Dry-run preparing an approved Photos widget image for manual import

# Arguments:
# @raycast.argument1 {"type":"text","placeholder":"filename"}

set -euo pipefail

REPO_DIR="${HOME}/Projects/teacher-ai-workstation"
FILENAME="${1:-}"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this Raycast script template.\n'
  exit 1
fi

if [[ -z "$FILENAME" ]]; then
  printf 'Usage: provide filename from approval-manifest.json.\n'
  exit 0
fi

cd "$REPO_DIR"
python3 scripts/prepare-approved-photos-import.py --filename "$FILENAME" --dry-run
