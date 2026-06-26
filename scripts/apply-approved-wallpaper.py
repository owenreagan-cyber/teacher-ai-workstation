#!/usr/bin/env python3
"""Copy an approved image into a wallpaper folder, dry-run by default."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from image_review_lib import (
    DEFAULT_MANIFEST_PATH,
    FINAL_FOLDERS,
    expand_path,
    find_entry,
    load_manifest,
)

ALLOWED_STATUS_BY_MODE = {
    "casual": {"approved_personal_wallpaper"},
    "teacher": {"approved_personal_wallpaper", "approved_presentation_safe"},
    "presentation": {"approved_presentation_safe"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy approved wallpaper into the selected mode folder.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--filename")
    selector.add_argument("--local-path")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--mode", choices=["casual", "teacher", "presentation"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--set-desktop", action="store_true", help="Scaffold only; desktop setting is not implemented in this phase.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.set_desktop:
        print("FAIL: --set-desktop is scaffold-only in Phase 0E-D6. No desktop wallpaper was changed.")
        return 2

    manifest, _ = load_manifest(expand_path(args.manifest_path), create_if_missing=False)
    entry = find_entry(manifest, filename=args.filename, local_path=args.local_path)
    if not entry:
        print("FAIL: no matching approval manifest entry found.")
        return 2

    status = str(entry.get("review_status", ""))
    allowed = ALLOWED_STATUS_BY_MODE[args.mode]
    if status not in allowed:
        print(f"FAIL: review_status {status!r} is not allowed for {args.mode} wallpaper.")
        print(f"Allowed statuses: {', '.join(sorted(allowed))}")
        return 2

    source = expand_path(str(entry.get("local_path", "")))
    target_dir = FINAL_FOLDERS[args.mode]
    target = target_dir / source.name

    print(f"Matched entry: {entry.get('id')}")
    print(f"Source: {source}")
    print(f"Target: {target}")
    if args.mode == "teacher":
        print("Teacher mode accepts approved_personal_wallpaper or approved_presentation_safe conservatively.")

    if not source.exists():
        print(f"WARN: source file does not exist yet: {source}")
        if args.apply:
            print("FAIL: cannot copy a missing source file.")
            return 2

    if not args.apply or args.dry_run:
        print("DRY-RUN: would copy approved wallpaper. Add --apply to copy.")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"PASS: copied approved wallpaper to {target}")
    print("No desktop wallpaper was set. Display scaling was not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
