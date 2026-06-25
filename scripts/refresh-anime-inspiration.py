#!/usr/bin/env python3
"""Refresh Casual Anime Mode reference images from Reddit.

This tool is intentionally conservative:
- Dry-run mode is the default unless --download is passed.
- Reddit/anime images are saved as Reference-Only by default.
- No secrets or Reddit API credentials are required.
- The source manifest is updated for downloaded files.

The script uses Reddit's public JSON listing endpoints with a clear user-agent.
If Reddit rate-limits or blocks a request, the script reports the issue and stops.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "Pictures" / "Teacher-AI-Workstation"
REFERENCE_DIR = ROOT / "Reference-Only" / "Anime-Inspiration"
PHOTOS_IMPORT_DIR = ROOT / "Photos-Import" / "Casual-Anime-Shuffle"
MANIFEST_PATH = ROOT / "source-manifest.json"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "wallpaper-sources.json"
USER_AGENT = "teacher-ai-workstation/0.1 by owenreagan-cyber"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now_iso()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_manifest() -> dict[str, Any]:
    return load_json(
        MANIFEST_PATH,
        {
            "version": 1,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "policy": "docs/image-source-policy.md",
            "entries": [],
        },
    )


def existing_source_urls(manifest: dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    for entry in manifest.get("entries", []):
        url = entry.get("source_url")
        if isinstance(url, str) and url:
            urls.add(url)
    return urls


def request_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} for {url}")
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} for {url}")
        return response.read()


def image_url_from_post(data: dict[str, Any]) -> str | None:
    # Direct image posts are preferred.
    direct = data.get("url_overridden_by_dest") or data.get("url")
    if isinstance(direct, str) and looks_like_image_url(direct):
        return html.unescape(direct)

    # Fallback to Reddit preview image.
    preview = data.get("preview", {})
    images = preview.get("images", []) if isinstance(preview, dict) else []
    if images:
        source = images[0].get("source", {})
        url = source.get("url")
        if isinstance(url, str):
            return html.unescape(url)

    return None


def looks_like_image_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url.lower())
    path = parsed.path
    return path.endswith(IMAGE_EXTENSIONS) or "preview.redd.it" in parsed.netloc or "i.redd.it" in parsed.netloc


def safe_filename(subreddit: str, post_id: str, image_url: str) -> str:
    parsed = urllib.parse.urlparse(image_url)
    ext = Path(parsed.path).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        ext = ".jpg"
    digest = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:10]
    clean_sub = re.sub(r"[^A-Za-z0-9_-]+", "-", subreddit).strip("-")
    clean_post = re.sub(r"[^A-Za-z0-9_-]+", "-", post_id).strip("-")
    return f"reddit-{clean_sub}-{clean_post}-{digest}{ext}"


def subreddit_presets(config: dict[str, Any]) -> list[str]:
    reddit = config.get("reddit", {})
    names = []
    for item in reddit.get("subreddits", []):
        name = item.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names or ["ImaginarySliceOfLife", "Animewallpaper", "Moescape"]


def fetch_candidates(subreddit: str, limit: int, listing: str) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(subreddit)
    url = f"https://www.reddit.com/r/{encoded}/{listing}.json?limit={limit}&t=week"
    payload = request_json(url)
    children = payload.get("data", {}).get("children", [])
    candidates: list[dict[str, Any]] = []
    for child in children:
        data = child.get("data", {})
        if not isinstance(data, dict):
            continue
        image_url = image_url_from_post(data)
        if not image_url:
            continue
        candidates.append(
            {
                "subreddit": subreddit,
                "post_id": data.get("id", "unknown"),
                "title": data.get("title", "untitled"),
                "author": data.get("author"),
                "permalink": "https://www.reddit.com" + data.get("permalink", ""),
                "image_url": image_url,
            }
        )
    return candidates


def add_manifest_entry(manifest: dict[str, Any], candidate: dict[str, Any], local_path: Path) -> None:
    manifest.setdefault("entries", []).append(
        {
            "local_path": str(local_path),
            "source_platform": "reddit",
            "source_url": candidate["permalink"],
            "source_title": candidate["title"],
            "creator_or_author": candidate.get("author"),
            "downloaded_at": now_iso(),
            "intended_use": "personal-reference-only",
            "license_status": "reference-only by default; not commercial-safe",
            "review_status": "reference-only",
            "notes": f"Downloaded from r/{candidate['subreddit']} for Casual Anime Mode personal wallpaper/widget candidates.",
            "image_url": candidate["image_url"],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh Reddit anime/reference-only image candidates.")
    parser.add_argument("--download", action="store_true", help="Actually download images. Without this, dry-run is used.")
    parser.add_argument("--dry-run", action="store_true", help="Preview candidates without downloading. This is the default.")
    parser.add_argument("--limit", type=int, default=10, help="Max posts to inspect per subreddit. Default: 10.")
    parser.add_argument("--listing", choices=["top", "hot", "new"], default="top", help="Reddit listing to inspect.")
    parser.add_argument("--subreddit", action="append", help="Subreddit to use. May be passed multiple times.")
    parser.add_argument("--copy-to-photos-import", action="store_true", help="Copy downloaded images to the Photos import staging folder.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to pause between subreddit requests.")
    args = parser.parse_args()

    dry_run = args.dry_run or not args.download
    limit = max(1, min(args.limit, 50))

    config = load_json(CONFIG_PATH, {})
    subreddits = args.subreddit or subreddit_presets(config)

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    seen_urls = existing_source_urls(manifest)

    print("Phase 0E-D3 Reddit Anime Refresh")
    print("Reddit/anime content is Reference-Only by default.")
    print(f"Mode: {'DRY-RUN' if dry_run else 'DOWNLOAD'}")
    print(f"Target: {REFERENCE_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")

    total_candidates = 0
    downloaded = 0
    skipped = 0

    for subreddit in subreddits:
        print(f"\nChecking r/{subreddit}...")
        try:
            candidates = fetch_candidates(subreddit, limit, args.listing)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print(f"WARN: could not fetch r/{subreddit}: {exc}")
            continue

        total_candidates += len(candidates)
        for candidate in candidates:
            permalink = candidate["permalink"]
            if permalink in seen_urls:
                skipped += 1
                print(f"SKIP existing: {candidate['title'][:80]}")
                continue

            filename = safe_filename(subreddit, str(candidate["post_id"]), candidate["image_url"])
            local_path = REFERENCE_DIR / filename
            print(f"CANDIDATE: r/{subreddit} - {candidate['title'][:100]}")
            print(f"  post: {permalink}")
            print(f"  file: {local_path}")

            if dry_run:
                continue

            try:
                data = request_bytes(candidate["image_url"])
                local_path.write_bytes(data)
                add_manifest_entry(manifest, candidate, local_path)
                seen_urls.add(permalink)
                downloaded += 1
                if args.copy_to_photos_import:
                    shutil.copy2(local_path, PHOTOS_IMPORT_DIR / local_path.name)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, OSError) as exc:
                print(f"WARN: could not download {candidate['image_url']}: {exc}")

        time.sleep(max(0.0, args.sleep))

    if not dry_run:
        save_json(MANIFEST_PATH, manifest)

    print("\nSummary:")
    print(f"- candidates seen: {total_candidates}")
    print(f"- skipped existing: {skipped}")
    print(f"- downloaded: {downloaded}")
    print("- review status: reference-only")

    if dry_run:
        print("\nDry-run only. Re-run with --download to save images.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
