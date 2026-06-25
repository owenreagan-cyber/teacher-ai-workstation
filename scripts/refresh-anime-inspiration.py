#!/usr/bin/env python3
"""Auth-gated scaffold for Reddit anime refresh.

Unauthenticated Reddit JSON was blocked during dry-run testing, so this script no
longer attempts public Reddit scraping as the approved path.

Next implementation step: add scripts/reddit-auth-setup.py and scripts/reddit-refresh.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TOKEN_PATH = Path.home() / ".teacher-ai-workstation" / "reddit-token.json"
CONFIG_PATH = Path.home() / ".teacher-ai-workstation" / "reddit-config.json"
REFERENCE_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Reference-Only" / "Anime-Inspiration"
PHOTOS_IMPORT_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Photos-Import" / "Casual-Anime-Shuffle"


def main() -> int:
    parser = argparse.ArgumentParser(description="Auth-gated Reddit anime refresh scaffold.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned behavior without downloading.")
    parser.add_argument("--download", action="store_true", help="Reserved for future authenticated refresh.")
    parser.add_argument("--limit", type=int, default=10, help="Reserved for future authenticated refresh.")
    parser.add_argument("--subreddit", action="append", help="Reserved for future authenticated refresh.")
    args = parser.parse_args()

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_IMPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Phase 0E-D3 Reddit Anime Refresh")
    print("Status: auth-gated scaffold")
    print("Reddit/anime content is Reference-Only by default.")
    print(f"Token path: {TOKEN_PATH}")
    print(f"Config path: {CONFIG_PATH}")
    print(f"Reference target: {REFERENCE_DIR}")
    print(f"Photos import target: {PHOTOS_IMPORT_DIR}")
    print()
    print("Unauthenticated Reddit JSON returned HTTP 403 during testing.")
    print("Authenticated Reddit access must be configured before downloads are enabled.")
    print("See: docs/reddit-developer-setup.md")
    print()

    if args.download:
        print("Refusing to download: Reddit auth setup has not been implemented/tested yet.")
        print("Next required step: scripts/reddit-auth-setup.py with --test-auth.")
        return 2

    print("Dry-run/scaffold check passed. No external Reddit request was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
