#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.owen.teacher-ai-workstation.refresh-anime-inspiration"
TEMPLATE="$REPO_ROOT/configs/launchd/$LABEL.plist"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/teacher-ai-workstation"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "FAIL: missing template $TEMPLATE" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

sed \
  -e "s#__REPO_PATH__#$REPO_ROOT#g" \
  -e "s#__HOME__#$HOME#g" \
  "$TEMPLATE" > "$TARGET"

chmod +x "$REPO_ROOT/scripts/refresh-anime-inspiration.sh" "$REPO_ROOT/scripts/refresh-anime-inspiration.py"

launchctl unload "$TARGET" >/dev/null 2>&1 || true
launchctl load "$TARGET"

echo "PASS: installed weekly anime refresh LaunchAgent."
echo "Label: $LABEL"
echo "Plist: $TARGET"
echo "Schedule: Saturday at 10:00 AM"
echo "Logs: $LOG_DIR"
echo "Manual trigger: scripts/refresh-anime-inspiration.sh"
