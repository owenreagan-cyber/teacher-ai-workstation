#!/usr/bin/env python3
"""Unsplash wallpaper search scaffold for Phase 0E-D4.

This script is intentionally conservative:
- Dry-run is default.
- No access key is stored in the repo.
- Network search requires ~/.teacher-ai-workstation/unsplash-config.json.
- Download behavior is not implemented yet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".teacher-ai-workstation" / "unsplash-config.json"
TEACHER_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Wallpapers" / "Teacher-Coding"
PRESENTATION_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Wallpapers" / "Presentation"
PRESETS = [
    ("teacher_coding_calm", "dark desk setup calm workspace", TEACHER_DIR),
    ("teacher_library_soft", "quiet library soft light", PRESENTATION_DIR),
    ("teacher_presentation_nature", "calm nature background classroom presentation", PRESENTATION_DIR),
    ("minimal_abstract", "minimal abstract background", PRESENTATION_DIR),
    ("clean_classroom_desk", "clean classroom desk", TEACHER_DIR),
]


def config_exists() -> bool:
    return CONFIG_PATH.exists()


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Unsplash wallpaper searches.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned searches without network access.")
    parser.add_argument("--check-config", action="store_true", help="Check whether local Unsplash config exists.")
    parser.add_argument("--show-presets", action="store_true", help="Print search presets.")
    parser.add_argument("--query", help="Custom search query for a future network search.")
    parser.add_argument("--limit", type=int, default=5, help="Future result limit. Default: 5.")
    args = parser.parse_args()

    TEACHER_DIR.mkdir(parents=True, exist_ok=True)
    PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Phase 0E-D4 Unsplash Wallpaper Search")
    print("Status: setup/scaffold")
    print(f"Config path: {CONFIG_PATH}")
    print(f"Teacher/Coding target: {TEACHER_DIR}")
    print(f"Presentation target: {PRESENTATION_DIR}")
    print()

    if args.check_config:
        if config_exists():
            config = load_config()
            if config.get("access_key"):
                print("PASS: Unsplash config exists and has an access_key field.")
            else:
                print("WARN: Unsplash config exists but does not contain access_key.")
        else:
            print("WARN: Unsplash config is missing.")
            print("Create ~/.teacher-ai-workstation/unsplash-config.json after saving the access key in 1Password.")

    if args.show_presets or args.dry_run:
        print("Configured search presets:")
        for name, query, target in PRESETS:
            print(f"- {name}: query={query!r} target={target}")

    if args.query:
        print()
        print(f"Custom query requested: {args.query!r}")
        print(f"Limit: {max(1, min(args.limit, 30))}")
        print("Network search/download is not implemented in this scaffold yet.")

    print()
    print("No network request was made. No images were downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
