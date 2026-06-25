#!/usr/bin/env bash
set -euo pipefail

LABEL="com.owen.teacher-ai-workstation.refresh-anime-inspiration"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ -f "$TARGET" ]]; then
  launchctl unload "$TARGET" >/dev/null 2>&1 || true
  rm -f "$TARGET"
  echo "PASS: removed $LABEL LaunchAgent."
else
  echo "WARN: LaunchAgent was not installed: $TARGET"
fi
