#!/usr/bin/env python3
"""Stage one manually gathered reference image as reference-only."""

from __future__ import annotations

import argparse
import json

from image_review_lib import (
    DEFAULT_MANIFEST_PATH,
    append_entry,
    build_entry,
    expand_path,
    print_errors,
    print_warnings,
    today_iso,
    validate_entry,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage one Reddit/anime/fan-art/reference candidate as reference-only."
    )
    parser.add_argument("--filename", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--source-platform", required=True)
    parser.add_argument("--source-url", default="unknown")
    parser.add_argument("--creator", default="unknown")
    parser.add_argument("--notes", default="Reference-only personal inspiration. Not approved for classroom, business, commercial, or 3D sale use.")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notes = args.notes
    if "reference-only" not in notes.lower() and "reference_only" not in notes.lower():
        notes = f"Reference-only. {notes}"

    entry = build_entry(
        filename=args.filename,
        local_path=args.local_path,
        source_platform=args.source_platform,
        source_url=args.source_url,
        creator=args.creator,
        license_or_usage_note="Reference-only by default; not approved for classroom, business, commercial, or 3D sale use.",
        intended_use="reference_only",
        review_status="reference_only",
        reviewer="Owen Reagan",
        review_date=today_iso(),
        notes=notes,
    )

    errors, warnings = validate_entry(entry)
    print_warnings(warnings)
    if errors:
        print_errors(errors)
        return 2

    print("Reference-only staging entry:")
    print(json.dumps(entry, indent=2, sort_keys=True))

    manifest_path = expand_path(args.manifest_path)
    if args.dry_run:
        print(f"DRY-RUN: would append reference-only entry to {manifest_path}")
        return 0

    append_entry(manifest_path, entry, create_if_missing=True)
    print(f"PASS: appended reference-only entry to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
