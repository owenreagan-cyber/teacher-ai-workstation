#!/usr/bin/env python3
"""Copy approved Photos widget images into the manual Photos import folder."""

from __future__ import annotations

import argparse
import shutil

from image_review_lib import (
    DEFAULT_MANIFEST_PATH,
    FINAL_FOLDERS,
    expand_path,
    find_entry,
    load_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare approved Photos widget image for manual import.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--filename")
    selector.add_argument("--local-path")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest, _ = load_manifest(expand_path(args.manifest_path), create_if_missing=False)
    entry = find_entry(manifest, filename=args.filename, local_path=args.local_path)
    if not entry:
        print("FAIL: no matching approval manifest entry found.")
        return 2

    status = str(entry.get("review_status", ""))
    if status != "approved_photos_widget":
        print(f"FAIL: review_status {status!r} is not approved_photos_widget.")
        return 2

    source = expand_path(str(entry.get("local_path", "")))
    target_dir = FINAL_FOLDERS["photos_widget"]
    target = target_dir / source.name

    print(f"Matched entry: {entry.get('id')}")
    print(f"Source: {source}")
    print(f"Target: {target}")

    if not source.exists():
        print(f"WARN: source file does not exist yet: {source}")
        if args.apply:
            print("FAIL: cannot copy a missing source file.")
            return 2

    if not args.apply or args.dry_run:
        print("DRY-RUN: would copy approved widget image. Add --apply to copy.")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"PASS: copied approved widget image to {target}")

    print()
    print("Manual next steps:")
    print("1. Open Photos.")
    print(f"2. Import from: {target_dir}")
    print("3. Add imported images to album: Casual Anime Shuffle")
    print("4. Configure the Photos widget manually if macOS offers that option.")
    print("This script did not open or modify Photos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
