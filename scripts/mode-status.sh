#!/usr/bin/env bash
set -euo pipefail

printf '\nVisual Mode Status\n'
printf '==================\n\n'

printf 'Dock settings:\n'
printf '%s\n' "- tile size: $(defaults read com.apple.dock tilesize 2>/dev/null || printf 'unknown')"
printf '%s\n' "- auto-hide: $(defaults read com.apple.dock autohide 2>/dev/null || printf 'unknown')"
printf '%s\n' "- show recents: $(defaults read com.apple.dock show-recents 2>/dev/null || printf 'unknown')"

printf '\nScreenshot location:\n'
printf '%s\n' "- $(defaults read com.apple.screencapture location 2>/dev/null || printf 'unknown')"

PREF="$HOME/Library/Preferences/com.apple.finder.plist"
printf '\nDesktop icon settings:\n'
if [[ -f "$PREF" ]]; then
  printf '%s\n' "- icon size: $(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:iconSize' "$PREF" 2>/dev/null || printf 'unknown')"
  printf '%s\n' "- text size: $(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:textSize' "$PREF" 2>/dev/null || printf 'unknown')"
  printf '%s\n' "- grid spacing: $(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:gridSpacing' "$PREF" 2>/dev/null || printf 'unknown')"
else
  printf '%s\n' '- Finder preference file not found yet.'
fi

printf '\nMode folders:\n'
for dir in \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding" \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime" \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation" \
  "$HOME/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration" \
  "$HOME/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle" \
  "$HOME/Screenshots"; do
  if [[ -d "$dir" ]]; then
    printf 'PASS: %s\n' "$dir"
  else
    printf 'WARN: missing %s\n' "$dir"
  fi
done

printf '\nReminder: this status script does not check global display scaling. Leave Displays on Default unless you intentionally change it.\n\n'
