#!/usr/bin/env bash
set -euo pipefail

APPLY=false
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=true
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Usage: scripts/mode-teacher.sh [--apply]

Without --apply, this script prints the Teacher/Coding Mode changes it would make.
With --apply, it creates folders and applies reversible Dock/Desktop/Finder comfort settings.

It does not change macOS display scaling, accounts, secrets, browser profiles, Photos, Spotify, or Raycast settings.
HELP
  exit 0
fi

WORKSTATION_ROOT="$HOME/Pictures/Teacher-AI-Workstation"
TEACHER_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Teacher-Coding"
PRESENTATION_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Presentation"
SCREENSHOTS="$HOME/Screenshots"
FINDER_PREF="$HOME/Library/Preferences/com.apple.finder.plist"

cat <<INFO

Teacher/Coding Mode
===================

This mode keeps Display scaling on Default and applies a slight comfort/readability bump.

Planned settings:
- Dock size: 40
- Dock auto-hide: on
- Dock recent apps: off
- Desktop icon size: 68
- Desktop label text: 13
- Desktop grid spacing: 54
- Screenshot folder: $SCREENSHOTS

Folders:
- $TEACHER_WALLPAPERS
- $PRESENTATION_WALLPAPERS

Not changed:
- Display scaling
- Cursor font
- Terminal/Ghostty font
- pointer size
- Photos
- Spotify
- Raycast extensions
- accounts or secrets
INFO

if [[ "$APPLY" != true ]]; then
  cat <<'DRYRUN'
Dry run only. To apply these settings, run:

  scripts/mode-teacher.sh --apply

DRYRUN
  exit 0
fi

printf '\nApplying Teacher/Coding Mode...\n\n'

mkdir -p "$TEACHER_WALLPAPERS" "$PRESENTATION_WALLPAPERS" "$SCREENSHOTS"

printf 'Applying Dock comfort settings...\n'
defaults write com.apple.dock tilesize -int 40
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false
killall Dock >/dev/null 2>&1 || true

printf 'Applying screenshot location...\n'
defaults write com.apple.screencapture location -string "$SCREENSHOTS"
killall SystemUIServer >/dev/null 2>&1 || true

printf 'Applying desktop icon comfort settings...\n'
if [[ -f "$FINDER_PREF" ]]; then
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:iconSize 68" "$FINDER_PREF" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:textSize 13" "$FINDER_PREF" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:gridSpacing 54" "$FINDER_PREF" >/dev/null 2>&1 || true
  killall Finder >/dev/null 2>&1 || true
else
  printf 'WARN: Finder preference file does not exist yet; skipping Desktop icon settings.\n'
fi

cat <<'DONE'

Teacher/Coding Mode applied.

Manual app-level tuning still recommended:
- Cursor editor font: 15 or 16.
- Terminal/Ghostty font: 15 or 16.
- Pointer size: slightly larger than default if needed.

Display scaling was not changed. Keep System Settings -> Displays on Default unless you intentionally choose otherwise.

DONE
