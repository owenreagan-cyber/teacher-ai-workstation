#!/usr/bin/env python3
"""Add one human-reviewed image entry to the local approval manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    parser = argparse.ArgumentParser(description="Add one image approval manifest entry.")
    parser.add_argument("--filename", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--source-platform", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--creator", required=True)
    parser.add_argument("--license-or-usage-note", required=True)
    parser.add_argument("--intended-use", required=True)
    parser.add_argument("--review-status", required=True)
    parser.add_argument("--reviewer", default="Owen Reagan")
    parser.add_argument("--review-date", default=today_iso())
    parser.add_argument("--notes", required=True)
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = expand_path(args.manifest_path)

    entry = build_entry(
        filename=args.filename,
        local_path=args.local_path,
        source_platform=args.source_platform,
        source_url=args.source_url,
        creator=args.creator,
        license_or_usage_note=args.license_or_usage_note,
        intended_use=args.intended_use,
        review_status=args.review_status,
        reviewer=args.reviewer,
        review_date=args.review_date,
        notes=args.notes,
    )

    errors, warnings = validate_entry(entry)
    print_warnings(warnings)
    if errors:
        print_errors(errors)
        return 2

    print("Validation: PASS")
    print("Entry:")
    print(json.dumps(entry, indent=2, sort_keys=True))

    if args.dry_run:
        print(f"DRY-RUN: would append entry to {manifest_path}")
        return 0

    created_message = "created" if not Path(manifest_path).exists() else "updated"
    append_entry(manifest_path, entry, create_if_missing=True)
    print(f"PASS: {created_message} manifest entry at {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
