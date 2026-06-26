#!/usr/bin/env bash
set -euo pipefail

REVIEW_ROOT="$HOME/Pictures/Teacher-AI-Workstation/Image-Review"
MANIFEST="$REVIEW_ROOT/approval-manifest.json"

mkdir -p "$REVIEW_ROOT"

if [[ ! -f "$MANIFEST" ]]; then
  cat >"$MANIFEST" <<'JSON'
{
  "schema_version": "1.0",
  "created_by": "teacher-ai-workstation scripts/init-image-approval-manifest.sh",
  "purpose": "Human review log for image candidates before wallpaper, Photos widget, classroom presentation, reference, business, or 3D printing use.",
  "entries": []
}
JSON
  printf 'Created approval manifest:\n%s\n' "$MANIFEST"
else
  printf 'Approval manifest already exists; leaving it unchanged:\n%s\n' "$MANIFEST"
fi

cat <<STEPS

Manual next steps:
1. Put candidate images in:
   $REVIEW_ROOT/Incoming-Candidates
2. Review each image source, intended use, license/usage note, creator/author, and any attribution needs.
3. Move the image manually into the correct review queue folder.
4. Add or update an entry in:
   $MANIFEST
5. Validate the manifest with:
   python3 -m json.tool "$MANIFEST"
6. Only after approval, copy or move images into final wallpaper/widget/presentation folders.

Safety boundaries:
- This script does not scan image folders.
- This script does not download images.
- This script does not call Reddit, Unsplash, Spotify, Photos, or any network API.
- This script does not modify Photos.
- This script does not move existing user images.
- This script does not use accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- This script does not change Display scaling.
- This script does not touch Raycast, Shortcuts, Spotify, iCloud, browser profiles, or Git settings.

STEPS
