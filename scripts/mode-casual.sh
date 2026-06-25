#!/usr/bin/env bash
set -euo pipefail

APPLY=false
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=true
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Usage: scripts/mode-casual.sh [--apply]

Without --apply, this script prints the Casual Anime Mode changes it would make.
With --apply, it creates folders and applies reversible Dock/Desktop/Finder comfort settings.

It does not change macOS display scaling, accounts, secrets, browser profiles, Photos, Spotify, or Raycast settings.
HELP
  exit 0
fi

WORKSTATION_ROOT="$HOME/Pictures/Teacher-AI-Workstation"
CASUAL_WALLPAPERS="$WORKSTATION_ROOT/Wallpapers/Casual-Anime"
ANIME_REFERENCE="$WORKSTATION_ROOT/Reference-Only/Anime-Inspiration"
PHOTOS_IMPORT="$WORKSTATION_ROOT/Photos-Import/Casual-Anime-Shuffle"
SCREENSHOTS="$HOME/Screenshots"
FINDER_PREF="$HOME/Library/Preferences/com.apple.finder.plist"

cat <<INFO

Casual Anime Mode
=================

This mode keeps Display scaling on Default and makes the workspace more fun, visual, and relaxed without going huge.

Planned settings:
- Dock size: 48
- Dock auto-hide: on
- Dock recent apps: off
- Desktop icon size: 80
- Desktop label text: 14
- Desktop grid spacing: 64
- Screenshot folder: $SCREENSHOTS

Folders:
- $CASUAL_WALLPAPERS
- $ANIME_REFERENCE
- $PHOTOS_IMPORT

Source boundary:
- Anime, Reddit, character, and fan-art images are Reference-Only by default.
- They are fine for personal wallpaper/widgets/inspiration.
- They are not approved for business products, commercial 3D printing, or public classroom materials without review.

Not changed:
- Display scaling
- Cursor font
- Terminal/Ghostty font
- pointer size
- Photos albums/widgets
- Spotify playlists
- Raycast extensions
- accounts or secrets
INFO

if [[ "$APPLY" != true ]]; then
  cat <<'DRYRUN'
Dry run only. To apply these settings, run:

  scripts/mode-casual.sh --apply

DRYRUN
  exit 0
fi

printf '\nApplying Casual Anime Mode...\n\n'

mkdir -p "$CASUAL_WALLPAPERS" "$ANIME_REFERENCE" "$PHOTOS_IMPORT" "$SCREENSHOTS"

printf 'Applying Dock comfort settings...\n'
defaults write com.apple.dock tilesize -int 48
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false
killall Dock >/dev/null 2>&1 || true

printf 'Applying screenshot location...\n'
defaults write com.apple.screencapture location -string "$SCREENSHOTS"
killall SystemUIServer >/dev/null 2>&1 || true

printf 'Applying desktop icon comfort settings...\n'
if [[ -f "$FINDER_PREF" ]]; then
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:iconSize 80" "$FINDER_PREF" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:textSize 14" "$FINDER_PREF" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:gridSpacing 64" "$FINDER_PREF" >/dev/null 2>&1 || true
  killall Finder >/dev/null 2>&1 || true
else
  printf 'WARN: Finder preference file does not exist yet; skipping Desktop icon settings.\n'
fi

cat <<'DONE'

Casual Anime Mode applied.

Manual next steps:
- Add approved wallpapers to the Casual-Anime folder.
- Add personal anime/reference images to Reference-Only only.
- Create Photos album: Casual Anime Shuffle.
- Add Photos, Music/Spotify, Weather, Clock, and Battery widgets if desired.

Display scaling was not changed. Keep System Settings -> Displays on Default unless you intentionally choose otherwise.

DONE
