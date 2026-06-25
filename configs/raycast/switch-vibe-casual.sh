#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Switch Vibe: Casual Anime
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation

# Optional parameters:
# @raycast.icon 🎧

set -euo pipefail

cd "$HOME/Projects/teacher-ai-workstation"
bash scripts/mode-casual.sh --apply
bash scripts/mode-status.sh
