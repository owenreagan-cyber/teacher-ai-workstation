#!/usr/bin/env bash
set -euo pipefail

printf '\nTesting Phase 0E-D4-B Unsplash wallpaper scaffold...\n\n'

python3 scripts/unsplash-wallpaper-search.py --dry-run --check-config --show-presets

printf '\nTesting Phase 0E-D4-B Unsplash API search dry-run...\n\n'

python3 scripts/unsplash-wallpaper-search.py \
  --api-search \
  --preset teacher_coding_calm \
  --limit 3 \
  --orientation landscape

printf '\nPASS: Unsplash wallpaper API search dry-run completed.\n\n'
