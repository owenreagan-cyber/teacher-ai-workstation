#!/usr/bin/env python3
"""Wallpaper and image provisioning scaffold for Phase 0E-D2.

This first version is intentionally conservative:
- It creates the local folder structure.
- It creates or updates a local source manifest.
- It supports dry-run output.
- It does not call Unsplash, Reddit, Photos, Spotify, or Raycast yet.

Future versions may add API-backed downloads after source policy and credential
handling are reviewed.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "Pictures" / "Teacher-AI-Workstation"
DEFAULT_MANIFEST = ROOT / "source-manifest.json"
FOLDERS = [
    ROOT / "Wallpapers" / "Teacher-Coding",
    ROOT / "Wallpapers" / "Casual-Anime",
    ROOT / "Wallpapers" / "Presentation",
    ROOT / "Reference-Only" / "Anime-Inspiration",
    ROOT / "Photos-Import" / "Casual-Anime-Shuffle",
]

CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "wallpaper-sources.json"


def expand(path: str) -> Path:
    return Path(os.path.expanduser(path))


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "policy": "docs/image-source-policy.md",
            "entries": [],
        }
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = now_iso()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_folders(dry_run: bool) -> None:
    print("Mode image folders:")
    for folder in FOLDERS:
        if dry_run:
            print(f"DRY-RUN: would create {folder}")
        else:
            folder.mkdir(parents=True, exist_ok=True)
            print(f"PASS: {folder}")


def print_presets(config: dict[str, Any]) -> None:
    print("\nConfigured source presets:")

    unsplash = config.get("unsplash", {})
    for item in unsplash.get("queries", []):
        print(
            "- unsplash/{name}: query={query!r} target={target}".format(
                name=item.get("name", "unnamed"),
                query=item.get("query", ""),
                target=item.get("target_folder", ""),
            )
        )

    reddit = config.get("reddit", {})
    for item in reddit.get("subreddits", []):
        print(
            "- reddit/{name}: target={target} status=reference-only".format(
                name=item.get("name", "unnamed"),
                target=item.get("target_folder", ""),
            )
        )


def add_placeholder_manifest_entries(
    manifest: dict[str, Any], config: dict[str, Any], source: str | None
) -> int:
    """Add non-download planning entries so Owen can inspect the pipeline."""
    entries = manifest.setdefault("entries", [])
    added = 0

    if source in (None, "unsplash"):
        for item in config.get("unsplash", {}).get("queries", []):
            entries.append(
                {
                    "local_path": None,
                    "source_platform": "unsplash",
                    "source_url": None,
                    "source_title": item.get("query"),
                    "creator_or_author": None,
                    "downloaded_at": None,
                    "intended_use": "teacher-candidate",
                    "license_status": "requires review before publishing/distribution",
                    "review_status": "teacher-candidate",
                    "notes": item.get("notes", "future download candidate"),
                }
            )
            added += 1

    if source in (None, "reddit"):
        for item in config.get("reddit", {}).get("subreddits", []):
            entries.append(
                {
                    "local_path": None,
                    "source_platform": "reddit",
                    "source_url": None,
                    "source_title": item.get("name"),
                    "creator_or_author": None,
                    "downloaded_at": None,
                    "intended_use": "personal-reference-only",
                    "license_status": "reference-only by default; not commercial-safe",
                    "review_status": "reference-only",
                    "notes": item.get("notes", "future reference-only candidate"),
                }
            )
            added += 1

    return added


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare wallpaper/image provisioning folders and source manifest."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files.")
    parser.add_argument("--init-folders", action="store_true", help="Create local visual mode folders.")
    parser.add_argument(
        "--source",
        choices=["unsplash", "reddit", "all"],
        default="all",
        help="Source lane to inspect or scaffold.",
    )
    parser.add_argument(
        "--add-placeholders",
        action="store_true",
        help="Add source planning entries to the local manifest without downloads.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Path to the local source manifest.",
    )
    parser.add_argument(
        "--show-presets",
        action="store_true",
        help="Print configured source presets.",
    )

    args = parser.parse_args()
    config = load_config()
    manifest_path = expand(args.manifest)

    print("Phase 0E-D2 Wallpaper Provisioning")
    print("No API downloads are performed by this scaffold.")
    print(f"Manifest: {manifest_path}")

    if args.init_folders:
        print()
        init_folders(args.dry_run)

    if args.show_presets:
        print_presets(config)

    if args.add_placeholders:
        selected_source = None if args.source == "all" else args.source
        if args.dry_run:
            print("\nDRY-RUN: would add placeholder source entries to manifest.")
        else:
            manifest = load_manifest(manifest_path)
            added = add_placeholder_manifest_entries(manifest, config, selected_source)
            save_manifest(manifest_path, manifest)
            print(f"\nPASS: added {added} placeholder entries to {manifest_path}")

    if not any([args.init_folders, args.show_presets, args.add_placeholders]):
        print("\nNothing to do. Try --dry-run --init-folders --show-presets")

    print("\nReminder: Reddit/anime sources are reference-only by default.")
    print("Reminder: do not store API keys or OAuth secrets in this repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
