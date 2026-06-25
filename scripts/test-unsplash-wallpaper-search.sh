#!/usr/bin/env bash
set -euo pipefail

printf '\nTesting Phase 0E-D4 Unsplash wallpaper scaffold...\n\n'

python3 scripts/unsplash-wallpaper-search.py --dry-run --check-config --show-presets

printf '\nPASS: Unsplash wallpaper scaffold dry-run completed.\n\n'
