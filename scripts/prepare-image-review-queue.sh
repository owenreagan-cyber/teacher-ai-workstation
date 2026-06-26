#!/usr/bin/env bash
set -euo pipefail

WORKSTATION_PICTURES="$HOME/Pictures/Teacher-AI-Workstation"
REVIEW_ROOT="$WORKSTATION_PICTURES/Image-Review"
INCOMING="$REVIEW_ROOT/Incoming-Candidates"
APPROVED_PERSONAL_WALLPAPER="$REVIEW_ROOT/Approved-Personal-Wallpaper"
APPROVED_PHOTOS_WIDGET="$REVIEW_ROOT/Approved-Photos-Widget"
APPROVED_PRESENTATION_SAFE="$REVIEW_ROOT/Approved-Presentation-Safe"
REJECTED_OR_HOLD="$REVIEW_ROOT/Rejected-or-Hold"
REFERENCE_ONLY="$REVIEW_ROOT/Reference-Only"
README_FILE="$REVIEW_ROOT/README.txt"

mkdir -p \
  "$INCOMING" \
  "$APPROVED_PERSONAL_WALLPAPER" \
  "$APPROVED_PHOTOS_WIDGET" \
  "$APPROVED_PRESENTATION_SAFE" \
  "$REJECTED_OR_HOLD" \
  "$REFERENCE_ONLY"

cat >"$README_FILE" <<'README'
Image Source Review Queue
=========================

This folder is a local manual queue for image candidates before they are used as wallpapers, Photos widgets, classroom backgrounds, or creative reference.

Folders:

- Incoming-Candidates:
  Images that have not been reviewed.

- Approved-Personal-Wallpaper:
  Images approved for private/personal wallpaper only.

- Approved-Photos-Widget:
  Images approved for private/personal Photos widget use only.

- Approved-Presentation-Safe:
  Images that are appropriate for classroom/public presentation backgrounds.

- Rejected-or-Hold:
  Unclear, questionable, duplicate, low-quality, or not-yet-approved images.

- Reference-Only:
  Inspiration images that should not be used directly.

Default rules:

- Anime, character, Reddit, fan-art, and inspiration images are Reference-Only by default.
- They may be approved for personal/private wallpaper or widget use after human review.
- They are not approved for public classroom materials, business products, commercial 3D printing, public portfolio work, or sale without review/licensing.
- Unsplash or other open-license candidates still require source metadata and human review before use.
- When unsure, keep the image in Reference-Only or Rejected-or-Hold.

This queue does not download images, approve licenses automatically, modify Photos, or move images into final wallpaper/widget folders.
README

cat <<STEPS

Image source review queue is ready.

Folders:
- $INCOMING
- $APPROVED_PERSONAL_WALLPAPER
- $APPROVED_PHOTOS_WIDGET
- $APPROVED_PRESENTATION_SAFE
- $REJECTED_OR_HOLD
- $REFERENCE_ONLY

Local guide:
- $README_FILE

Manual next steps:
1. Place candidate images in:
   $INCOMING
2. Review the image, source, license, creator/attribution, and intended use.
3. Move it manually into one review folder:
   - Reference-Only
   - Approved-Personal-Wallpaper
   - Approved-Photos-Widget
   - Approved-Presentation-Safe
   - Rejected-or-Hold
4. Only after approval, copy or move images into final wallpaper/widget/import folders.

Safety boundaries:
- This script does not download images.
- This script does not call Reddit, Unsplash, Spotify, Photos, or any network API.
- This script does not modify Photos.
- This script does not move existing user images automatically.
- This script does not use accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- This script does not change Display scaling.
- This script does not touch Raycast, Shortcuts, Spotify, iCloud, browser profiles, or Git settings.

STEPS
