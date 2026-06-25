#!/usr/bin/env bash
set -euo pipefail

printf "\nVisual Mode Status\n"
printf "==================\n\n"

printf "Dock settings:\n"
printf "- tile size: %s\n" "$(defaults read com.apple.dock tilesize 2>/dev/null || printf 'unknown')"
printf "- auto-hide: %s\n" "$(defaults read com.apple.dock autohide 2>/dev/null || printf 'unknown')"
printf "- show recents: %s\n" "$(defaults read com.apple.dock show-recents 2>/dev/null || printf 'unknown')"

printf "\nScreenshot location:\n"
printf "- %s\n" "$(defaults read com.apple.screencapture location 2>/dev/null || printf 'unknown')"

PREF="$HOME/Library/Preferences/com.apple.finder.plist"
printf "\nDesktop icon settings:\n"
if [[ -f "$PREF" ]]; then
  printf "- icon size: %s\n" "$(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:iconSize' "$PREF" 2>/dev/null || printf 'unknown')"
  printf "- text size: %s\n" "$(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:textSize' "$PREF" 2>/dev/null || printf 'unknown')"
  printf "- grid spacing: %s\n" "$(/usr/libexec/PlistBuddy -c 'Print :DesktopViewSettings:IconViewSettings:gridSpacing' "$PREF" 2>/dev/null || printf 'unknown')"
else
  printf "- Finder preference file not found yet.\n"
fi

printf "\nMode folders:\n"
for dir in \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding" \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime" \
  "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation" \
  "$HOME/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration" \
  "$HOME/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle" \
  "$HOME/Screenshots"; do
  if [[ -d "$dir" ]]; then
    printf "PASS: %s\n" "$dir"
  else
    printf "WARN: missing %s\n" "$dir"
  fi
done

printf "\nReminder: this status script does not check global display scaling. Leave Displays on Default unless you intentionally change it.\n\n"
