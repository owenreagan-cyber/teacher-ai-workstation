#!/usr/bin/env bash
set -euo pipefail

printf '\nTesting Phase 0E-D3 Reddit anime refresh dry-run...\n\n'

python3 scripts/refresh-anime-inspiration.py --dry-run --limit 3 --subreddit Animewallpaper

printf '\nPASS: anime refresh dry-run completed.\n\n'
