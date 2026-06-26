#!/usr/bin/env bash
set -euo pipefail

WORKSTATION_PICTURES="$HOME/Pictures/Teacher-AI-Workstation"
PHOTOS_IMPORT="$WORKSTATION_PICTURES/Photos-Import/Casual-Anime-Shuffle"
ANIME_REFERENCE="$WORKSTATION_PICTURES/Reference-Only/Anime-Inspiration"
CASUAL_WALLPAPERS="$WORKSTATION_PICTURES/Wallpapers/Casual-Anime"
README_FILE="$PHOTOS_IMPORT/README.txt"

mkdir -p "$PHOTOS_IMPORT" "$ANIME_REFERENCE" "$CASUAL_WALLPAPERS"

cat >"$README_FILE" <<'README'
Casual Anime Shuffle Photos Import
==================================

This folder is for images Owen intentionally wants to import into Photos.

Anime, character, Reddit, fan-art, and inspiration images are personal/reference-only by default.

Do not use these images for public classroom materials, business products, commercial 3D printing, or public portfolio work without review/licensing.

After adding images here, manually import them into Photos and create an album named:

Casual Anime Shuffle

Do not import huge random folders blindly. Keep anything questionable in Reference-Only first.
README

cat <<STEPS

Photos and widget setup folders are ready.

Folders:
- $PHOTOS_IMPORT
- $ANIME_REFERENCE
- $CASUAL_WALLPAPERS

Local guide:
- $README_FILE

Manual next steps:
1. Add only selected personal/reference images to:
   $PHOTOS_IMPORT
2. Open Photos manually.
3. Import those selected images.
4. Create a Photos album named:
   Casual Anime Shuffle
5. Add the imported images to that album.
6. Add a Photos widget manually and select the Casual Anime Shuffle album if macOS offers that option.
7. Keep anything questionable in:
   $ANIME_REFERENCE

Safety boundaries:
- This script does not automate Photos.
- This script does not modify the Photos library.
- This script does not download images or use network calls.
- This script does not use accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- This script does not change Display scaling.
- This script does not touch Spotify, Raycast, Apple Shortcuts, browser profiles, iCloud, or Git settings.

STEPS
