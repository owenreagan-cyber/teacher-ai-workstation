#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Dry Run Approved Wallpaper
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation
# @raycast.description Dry-run copying an approved wallpaper from the manifest

# Arguments:
# @raycast.argument1 {"type":"text","placeholder":"filename"}
# @raycast.argument2 {"type":"text","placeholder":"mode: casual|teacher|presentation"}

set -euo pipefail

REPO_DIR="${HOME}/Projects/teacher-ai-workstation"
FILENAME="${1:-}"
MODE="${2:-}"

if [[ ! -d "$REPO_DIR" ]]; then
  printf 'FAIL: repo directory not found: %s\n' "$REPO_DIR"
  printf 'Update REPO_DIR in this Raycast script template.\n'
  exit 1
fi

if [[ -z "$FILENAME" || -z "$MODE" ]]; then
  printf 'Usage: provide filename and mode.\n'
  printf 'Example mode values: casual, teacher, presentation\n'
  exit 0
fi

cd "$REPO_DIR"
python3 scripts/apply-approved-wallpaper.py --filename "$FILENAME" --mode "$MODE" --dry-run
