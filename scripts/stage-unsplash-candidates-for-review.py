#!/usr/bin/env python3
"""Stage local Unsplash candidate metadata into the approval manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from image_review_lib import (
    DEFAULT_MANIFEST_PATH,
    QUEUE_FOLDERS,
    append_entry,
    build_entry,
    expand_path,
    print_errors,
    print_warnings,
    today_iso,
    validate_entry,
)

ALLOWED_INTENDED_USES = {
    "personal_wallpaper",
    "photos_widget",
    "classroom_presentation",
    "reference_only",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage local Unsplash candidate JSON into the image approval manifest."
    )
    parser.add_argument("--candidates-json", required=True)
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--intended-use", choices=sorted(ALLOWED_INTENDED_USES), default="personal_wallpaper")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_candidates(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = None
        for key in ("candidates", "results", "entries", "photos"):
            value = data.get(key)
            if isinstance(value, list):
                raw = value
                break
        if raw is None:
            raise SystemExit(
                "FAIL: unknown candidate JSON format. Expected a list or an object with "
                "'candidates', 'results', 'entries', or 'photos'. Example: "
                '{"candidates":[{"id":"abc","filename":"example.jpg","source_url":"https://example.invalid","creator":"unknown"}]}'
            )
    else:
        raise SystemExit("FAIL: candidate JSON must be an array or object.")

    candidates: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            candidates.append(item)
    if not candidates:
        raise SystemExit("FAIL: no candidate objects found.")
    return candidates


def nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def candidate_to_entry(candidate: dict[str, Any], intended_use: str) -> dict[str, str]:
    candidate_id = str(candidate.get("id") or candidate.get("unsplash_photo_id") or "").strip()
    local_path = str(candidate.get("local_path") or candidate.get("path") or candidate.get("file_path") or "").strip()
    filename = str(candidate.get("filename") or (Path(local_path).name if local_path else "")).strip()
    if not filename:
        filename = f"unsplash-{candidate_id or 'candidate'}.jpg"
    if not local_path:
        local_path = str(QUEUE_FOLDERS["incoming"] / filename)

    source_url = (
        candidate.get("source_url")
        or candidate.get("url")
        or candidate.get("html_url")
        or nested_get(candidate, "links", "html")
        or "unknown"
    )
    creator = (
        candidate.get("creator")
        or candidate.get("creator_or_author")
        or candidate.get("author")
        or nested_get(candidate, "user", "name")
        or "unknown"
    )
    license_note = (
        candidate.get("license_or_usage_note")
        or candidate.get("license_status")
        or "Unsplash candidate metadata. Preserve source/creator info and review before use."
    )
    notes = candidate.get("notes") or "Staged from local Unsplash candidate JSON. No image downloaded or moved."

    return build_entry(
        filename=filename,
        local_path=local_path,
        source_platform="unsplash",
        source_url=str(source_url),
        creator=str(creator),
        license_or_usage_note=str(license_note),
        intended_use=intended_use,
        review_status="incoming",
        reviewer="Owen Reagan",
        review_date=today_iso(),
        notes=str(notes),
    )


def main() -> int:
    args = parse_args()
    candidates = load_candidates(expand_path(args.candidates_json))
    manifest_path = expand_path(args.manifest_path)

    entries = [candidate_to_entry(candidate, args.intended_use) for candidate in candidates]
    all_errors: list[str] = []
    for entry in entries:
        errors, warnings = validate_entry(entry)
        print_warnings(warnings)
        all_errors.extend(errors)
    if all_errors:
        print_errors(all_errors)
        return 2

    print(f"Unsplash candidates staged: {len(entries)}")
    print(json.dumps(entries, indent=2, sort_keys=True))

    if args.dry_run:
        print(f"DRY-RUN: would append {len(entries)} incoming entries to {manifest_path}")
        return 0

    for entry in entries:
        append_entry(manifest_path, entry, create_if_missing=True)
    print(f"PASS: appended {len(entries)} incoming Unsplash entries to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
