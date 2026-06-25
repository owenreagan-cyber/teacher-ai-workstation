#!/usr/bin/env python3
"""Unsplash wallpaper search for Phase 0E-D4-B.

This script is intentionally conservative:
- Dry-run is still the default.
- The access key is read from ~/.teacher-ai-workstation/unsplash-config.json.
- Search requests print candidate metadata only.
- No images are downloaded in this phase.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".teacher-ai-workstation" / "unsplash-config.json"
TEACHER_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Wallpapers" / "Teacher-Coding"
PRESENTATION_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation" / "Wallpapers" / "Presentation"
API_ROOT = "https://api.unsplash.com"
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


def require_access_key() -> str:
    config = load_config()
    access_key = config.get("access_key", "").strip()
    if not access_key:
        raise SystemExit(
            "FAIL: Unsplash access_key missing. Create ~/.teacher-ai-workstation/unsplash-config.json first."
        )
    return access_key


def search_unsplash(access_key: str, query: str, limit: int, orientation: str | None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    params = {
        "query": query,
        "per_page": str(max(1, min(limit, 30))),
        "content_filter": "high",
    }
    if orientation:
        params["orientation"] = orientation

    url = f"{API_ROOT}/search/photos?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
            "User-Agent": "TeacherAIWorkstation/1.0 by owenreagan-cyber",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
        headers = {
            "x-ratelimit-limit": response.headers.get("X-Ratelimit-Limit", "unknown"),
            "x-ratelimit-remaining": response.headers.get("X-Ratelimit-Remaining", "unknown"),
        }
    results = body.get("results", [])
    return results if isinstance(results, list) else [], headers


def print_candidate(index: int, photo: dict[str, Any]) -> None:
    user = photo.get("user") if isinstance(photo.get("user"), dict) else {}
    urls = photo.get("urls") if isinstance(photo.get("urls"), dict) else {}
    links = photo.get("links") if isinstance(photo.get("links"), dict) else {}
    width = photo.get("width", "unknown")
    height = photo.get("height", "unknown")
    description = photo.get("description") or photo.get("alt_description") or "untitled"

    print(f"{index}. {description}")
    print(f"   id: {photo.get('id', 'unknown')}")
    print(f"   by: {user.get('name', 'unknown')} (@{user.get('username', 'unknown')})")
    print(f"   size: {width} x {height}")
    print(f"   page: {links.get('html', 'unknown')}")
    print(f"   regular_url_present: {'yes' if urls.get('regular') else 'no'}")


def print_presets() -> None:
    print("Configured search presets:")
    for name, query, target in PRESETS:
        print(f"- {name}: query={query!r} target={target}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Unsplash wallpaper candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Print local plan or candidate metadata without downloads.")
    parser.add_argument("--check-config", action="store_true", help="Check whether local Unsplash config exists.")
    parser.add_argument("--show-presets", action="store_true", help="Print search presets.")
    parser.add_argument("--query", help="Custom search query.")
    parser.add_argument("--preset", choices=[name for name, _, _ in PRESETS], help="Run one configured preset search.")
    parser.add_argument("--limit", type=int, default=5, help="Result limit. Default: 5. Max: 30.")
    parser.add_argument("--orientation", choices=["landscape", "portrait", "squarish"], default="landscape")
    parser.add_argument("--api-search", action="store_true", help="Make a real Unsplash API search request. Downloads are still disabled.")
    args = parser.parse_args()

    TEACHER_DIR.mkdir(parents=True, exist_ok=True)
    PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Phase 0E-D4-B Unsplash Wallpaper Search")
    print("Status: API search dry-run")
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
        print_presets()

    selected_query = args.query
    if args.preset:
        selected_query = next(query for name, query, _ in PRESETS if name == args.preset)

    if args.api_search:
        if not selected_query:
            raise SystemExit("FAIL: --api-search requires --query or --preset.")
        access_key = require_access_key()
        print()
        print(f"Searching Unsplash for: {selected_query!r}")
        print(f"Limit: {max(1, min(args.limit, 30))}")
        print(f"Orientation: {args.orientation}")
        try:
            results, headers = search_unsplash(access_key, selected_query, args.limit, args.orientation)
        except urllib.error.HTTPError as exc:
            print(f"FAIL: Unsplash API returned HTTP {exc.code}: {exc.reason}")
            return 2
        except urllib.error.URLError as exc:
            print(f"FAIL: Unsplash API request failed: {exc}")
            return 2

        print(f"Rate limit: {headers['x-ratelimit-remaining']} remaining of {headers['x-ratelimit-limit']}")
        print(f"Candidates returned: {len(results)}")
        print()
        for index, photo in enumerate(results, start=1):
            print_candidate(index, photo)
        print()
        print("No images were downloaded. Candidate metadata only.")
    else:
        print()
        print("No network request was made. No images were downloaded.")
        if selected_query:
            print("Add --api-search to run a real Unsplash search dry-run.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
