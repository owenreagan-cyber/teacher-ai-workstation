#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/refresh-anime-inspiration.py" \
  --download \
  --limit 10 \
  --listing top \
  --copy-to-photos-import
