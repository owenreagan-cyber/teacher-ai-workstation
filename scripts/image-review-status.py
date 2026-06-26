#!/usr/bin/env python3
"""Print local image review queue and approval manifest status."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from image_review_lib import (
    DEFAULT_MANIFEST_PATH,
    QUEUE_FOLDERS,
    REQUIRED_ENTRY_FIELDS,
    expand_path,
    load_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show image review queue status.")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    return parser.parse_args()


def count_files(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for path in folder.rglob("*") if path.is_file())


def collect_file_names(folder: Path) -> set[str]:
    if not folder.exists():
        return set()
    return {path.name for path in folder.rglob("*") if path.is_file()}


def main() -> int:
    args = parse_args()
    manifest_path = expand_path(args.manifest_path)
    warnings: list[str] = []

    print("Image Review Status")
    print("===================")
    print()
    print("Folders:")
    for status, folder in QUEUE_FOLDERS.items():
        print(f"- {status}: {count_files(folder)} files ({folder})")

    if not manifest_path.exists():
        print()
        print(f"WARN: manifest missing: {manifest_path}")
        return 0

    try:
        manifest, _ = load_manifest(manifest_path, create_if_missing=False)
    except Exception as exc:
        print()
        print(f"FAIL: could not read manifest: {exc}")
        return 2

    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        print()
        print("FAIL: manifest entries is not an array")
        return 2

    print()
    print(f"Manifest: {manifest_path}")
    print(f"Manifest entries: {len(entries)}")

    status_counts: Counter[str] = Counter()
    intended_counts: Counter[str] = Counter()
    manifest_filenames: set[str] = set()

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            warnings.append(f"entry {index} is not an object")
            continue
        missing = [field for field in REQUIRED_ENTRY_FIELDS if not entry.get(field)]
        if missing:
            warnings.append(f"entry {index} missing fields: {', '.join(missing)}")
        status_counts[str(entry.get("review_status", "missing"))] += 1
        intended_counts[str(entry.get("intended_use", "missing"))] += 1
        filename = str(entry.get("filename", "")).strip()
        local_path = str(entry.get("local_path", "")).strip()
        if filename:
            manifest_filenames.add(filename)
        if local_path:
            manifest_filenames.add(Path(local_path).name)
            expanded = expand_path(local_path)
            if local_path != "unknown" and not expanded.exists():
                warnings.append(f"manifest entry points to missing file: {local_path}")

    print()
    print("By review_status:")
    for key, count in sorted(status_counts.items()):
        print(f"- {key}: {count}")

    print()
    print("By intended_use:")
    for key, count in sorted(intended_counts.items()):
        print(f"- {key}: {count}")

    for status in (
        "approved_personal_wallpaper",
        "approved_photos_widget",
        "approved_presentation_safe",
    ):
        folder = QUEUE_FOLDERS[status]
        for filename in sorted(collect_file_names(folder)):
            if filename not in manifest_filenames:
                warnings.append(f"approved folder file has no manifest entry by filename: {folder / filename}")

    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print()
        print("Warnings: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
