#!/usr/bin/env bash
set -euo pipefail

printf '\nTesting Phase 0E-D4-C Unsplash wallpaper scaffold...\n\n'

python3 scripts/unsplash-wallpaper-search.py --dry-run --check-config --show-presets

printf '\nTesting Phase 0E-D4-C Unsplash API search dry-run...\n\n'

python3 scripts/unsplash-wallpaper-search.py \
  --api-search \
  --preset teacher_coding_calm \
  --limit 3 \
  --orientation landscape

printf '\nTesting Phase 0E-D4-C selected download safety gate...\n\n'

python3 scripts/unsplash-wallpaper-search.py \
  --download-photo-id CCu-16eRBOs \
  --target teacher

printf '\nPASS: Unsplash wallpaper download safety gate completed.\n\n'
