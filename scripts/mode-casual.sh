#!/usr/bin/env bash
set -euo pipefail

printf '\nEngaging Casual Anime Mode...\n\n'

WORKSTATION_ROOT="$HOME/Pictures/Teacher-AI-Workstation"
CASUAL_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Casual-Anime"
ANIME_REFERENCE="$WORKSTATION_ROOT/Reference-Only/Anime-Inspiration"
PHOTOS_IMPORT="$WORKSTATION_ROOT/Photos-Import/Casual-Anime-Shuffle"
SCREENSHOTS="$HOME/Screenshots"

mkdir -p "$CASUAL_WALLPAPERS" "$ANIME_REFERENCE" "$PHOTOS_IMPORT" "$SCREENSHOTS"

printf 'Created/verified casual mode folders:\n'
printf '%s\n' "- $CASUAL_WALLPAPERS"
printf '%s\n' "- $ANIME_REFERENCE"
printf '%s\n' "- $PHOTOS_IMPORT"
printf '%s\n' "- $SCREENSHOTS"

printf '\nApplying Dock comfort settings...\n'
defaults write com.apple.dock tilesize -int 48
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false
killall Dock >/dev/null 2>&1 || true

printf 'Applying screenshot location...\n'
defaults write com.apple.screencapture location -string "$SCREENSHOTS"
killall SystemUIServer >/dev/null 2>&1 || true

printf 'Applying desktop icon comfort settings...\n'
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:iconSize 80" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:textSize 14" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:gridSpacing 64" "$HOME/Library/Preferences/com.apple.finder.plist" >/dev/null 2>&1 || true
killall Finder >/dev/null 2>&1 || true

printf '\nCasual Anime Mode applied.\n'
printf 'Display scaling was not changed. Keep System Settings -> Displays on Default unless you choose otherwise.\n'
printf 'Anime/reference images belong in Reference-Only unless separately reviewed for broader use.\n'
printf "Manual next steps: add wallpapers, create Photos album 'Casual Anime Shuffle', and select widgets.\n\n"
