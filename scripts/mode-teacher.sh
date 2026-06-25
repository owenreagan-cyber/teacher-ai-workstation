#!/usr/bin/env bash
set -euo pipefail

printf "\nEngaging Teacher/Coding Mode...\n\n"

WORKSTATION_ROOT="$HOME/Pictures/Teacher-AI-Workstation"
TEACHER_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Teacher-Coding"
PRESENTATION_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Presentation"
SCREENSHOTS="$HOME/Screenshots"

mkdir -p "$TEACHER_WALLPAPERS" "$PRESENTATION_WALLPAPERS" "$SCREENSHOTS"

printf "Created/verified visual mode folders:\n"
printf "- %s\n" "$TEACHER_WALLPAPERS"
printf "- %s\n" "$PRESENTATION_WALLPAPERS"
printf "- %s\n" "$SCREENSHOTS"

printf "\nApplying Dock comfort settings...\n"
defaults write com.apple.dock tilesize -int 40
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false
killall Dock >/dev/null 2>&1 || true

printf "Applying screenshot location...\n"
defaults write com.apple.screencapture location -string "$SCREENSHOTS"
killall SystemUIServer >/dev/null 2>&1 || true

printf "Applying desktop icon comfort settings...\n"
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:iconSize 68" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:textSize 13" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:gridSpacing 54" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
killall Finder >/dev/null 2>&1 || true

printf "\nTeacher/Coding Mode applied.\n"
printf "Display scaling was not changed. Keep System Settings -> Displays on Default unless you choose otherwise.\n"
printf "Manual app-level tuning still recommended: Cursor font 15-16, Terminal/Ghostty font 15-16, pointer slightly larger if needed.\n\n"
