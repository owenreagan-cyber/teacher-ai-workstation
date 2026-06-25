#!/usr/bin/env bash
set -euo pipefail

printf '\nTesting Phase 0E-D2 wallpaper provisioning scaffold...\n\n'

python3 scripts/provision-wallpapers.py --dry-run --init-folders --show-presets

printf '\nPASS: wallpaper provisioning scaffold dry-run completed.\n\n'
