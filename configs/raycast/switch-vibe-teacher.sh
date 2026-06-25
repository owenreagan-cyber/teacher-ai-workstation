#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Switch Vibe: Teacher Coding
# @raycast.mode fullOutput
# @raycast.packageName Teacher AI Workstation

# Optional parameters:
# @raycast.icon 💻

set -euo pipefail

cd "$HOME/Projects/teacher-ai-workstation"
bash scripts/mode-teacher.sh --apply
bash scripts/mode-status.sh
