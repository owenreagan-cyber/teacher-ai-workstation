#!/usr/bin/env python3
"""Unsplash wallpaper search and approved candidate download.

This script is intentionally conservative:
- Dry-run is still the default.
- The access key is read from ~/.teacher-ai-workstation/unsplash-config.json.
- Search requests print candidate metadata.
- Downloads require an explicit photo ID, target, and confirmation flag.
- Saved images are tracked in ~/Pictures/Teacher-AI-Workstation/source-manifest.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".teacher-ai-workstation" / "unsplash-config.json"
ROOT_DIR = Path.home() / "Pictures" / "Teacher-AI-Workstation"
TEACHER_DIR = ROOT_DIR / "Wallpapers" / "Teacher-Coding"
PRESENTATION_DIR = ROOT_DIR / "Wallpapers" / "Presentation"
MANIFEST_PATH = ROOT_DIR / "source-manifest.json"
API_ROOT = "https://api.unsplash.com"
USER_AGENT = "TeacherAIWorkstation/1.0 by owenreagan-cyber"
PRESETS = [
    ("teacher_coding_calm", "dark desk setup calm workspace", TEACHER_DIR),
    ("teacher_library_soft", "quiet library soft light", PRESENTATION_DIR),
    ("teacher_presentation_nature", "calm nature background classroom presentation", PRESENTATION_DIR),
    ("minimal_abstract", "minimal abstract background", PRESENTATION_DIR),
    ("clean_classroom_desk", "clean classroom desk", TEACHER_DIR),
]
TARGETS = {
    "teacher": TEACHER_DIR,
    "presentation": PRESENTATION_DIR,
}


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


def api_request(access_key: str, url: str) -> tuple[Any, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
        headers = {
            "x-ratelimit-limit": response.headers.get("X-Ratelimit-Limit", "unknown"),
            "x-ratelimit-remaining": response.headers.get("X-Ratelimit-Remaining", "unknown"),
        }
    return body, headers


def search_unsplash(access_key: str, query: str, limit: int, orientation: str | None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    params = {
        "query": query,
        "per_page": str(max(1, min(limit, 30))),
        "content_filter": "high",
    }
    if orientation:
        params["orientation"] = orientation

    url = f"{API_ROOT}/search/photos?{urllib.parse.urlencode(params)}"
    body, headers = api_request(access_key, url)
    results = body.get("results", []) if isinstance(body, dict) else []
    return results if isinstance(results, list) else [], headers


def get_photo(access_key: str, photo_id: str) -> tuple[dict[str, Any], dict[str, str]]:
    quoted_id = urllib.parse.quote(photo_id, safe="")
    body, headers = api_request(access_key, f"{API_ROOT}/photos/{quoted_id}")
    if not isinstance(body, dict):
        raise SystemExit("FAIL: Unexpected Unsplash photo response.")
    return body, headers


def register_unsplash_download(access_key: str, photo: dict[str, Any]) -> None:
    links = photo.get("links") if isinstance(photo.get("links"), dict) else {}
    download_location = links.get("download_location")
    if not download_location:
        print("WARN: Unsplash download_location missing; continuing with image download only.")
        return
    try:
        api_request(access_key, str(download_location))
        print("PASS: Unsplash download event registered.")
    except urllib.error.HTTPError as exc:
        print(f"WARN: Could not register Unsplash download event: HTTP {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        print(f"WARN: Could not register Unsplash download event: {exc}")


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


def extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".jpg"
    clean_type = content_type.split(";", 1)[0].strip().lower()
    return mimetypes.guess_extension(clean_type) or ".jpg"


def download_bytes(url: str) -> tuple[bytes, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type")
        return response.read(), content_type


def load_manifest() -> tuple[Any, list[dict[str, Any]]]:
    if not MANIFEST_PATH.exists():
        return {"entries": []}, []
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup_path = MANIFEST_PATH.with_suffix(".json.invalid")
        MANIFEST_PATH.rename(backup_path)
        print(f"WARN: Existing manifest was invalid JSON and was moved to {backup_path}")
        return {"entries": []}, []

    if isinstance(data, dict):
        entries = data.setdefault("entries", [])
        if not isinstance(entries, list):
            data["entries"] = []
            entries = data["entries"]
        return data, entries
    if isinstance(data, list):
        return data, data
    return {"entries": []}, []


def write_manifest(data: Any) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest_entry(photo: dict[str, Any], local_path: Path, target_name: str) -> dict[str, Any]:
    user = photo.get("user") if isinstance(photo.get("user"), dict) else {}
    links = photo.get("links") if isinstance(photo.get("links"), dict) else {}
    return {
        "local_path": str(local_path),
        "source_platform": "unsplash",
        "source_url": links.get("html", ""),
        "source_title": photo.get("description") or photo.get("alt_description") or "untitled",
        "creator_or_author": user.get("name", "unknown"),
        "creator_username": user.get("username", "unknown"),
        "downloaded_at": dt.datetime.now(dt.UTC).isoformat(),
        "intended_use": f"{target_name}-wallpaper-candidate",
        "license_status": "unsplash-api-source",
        "review_status": "teacher-candidate",
        "notes": "Downloaded by explicit Unsplash photo ID. Review before school-facing use.",
        "unsplash_photo_id": photo.get("id", "unknown"),
        "width": photo.get("width"),
        "height": photo.get("height"),
    }


def download_photo(access_key: str, photo_id: str, target_name: str, confirm_download: bool) -> int:
    target_dir = TARGETS[target_name]
    target_dir.mkdir(parents=True, exist_ok=True)

    photo, headers = get_photo(access_key, photo_id)
    print(f"Rate limit: {headers['x-ratelimit-remaining']} remaining of {headers['x-ratelimit-limit']}")
    print("Selected photo:")
    print_candidate(1, photo)

    urls = photo.get("urls") if isinstance(photo.get("urls"), dict) else {}
    image_url = urls.get("regular")
    if not image_url:
        print("FAIL: selected photo has no regular image URL.")
        return 2

    if not confirm_download:
        print()
        print("No image was downloaded.")
        print("Add --confirm-download to download this selected photo and update the manifest.")
        return 0

    register_unsplash_download(access_key, photo)
    image_bytes, content_type = download_bytes(str(image_url))
    ext = extension_from_content_type(content_type)
    safe_photo_id = "".join(ch for ch in photo_id if ch.isalnum() or ch in "-_")
    local_path = target_dir / f"unsplash-{safe_photo_id}-{target_name}{ext}"
    local_path.write_bytes(image_bytes)

    manifest_data, entries = load_manifest()
    entries.append(build_manifest_entry(photo, local_path, target_name))
    write_manifest(manifest_data)

    print()
    print(f"PASS: downloaded image to {local_path}")
    print(f"PASS: updated manifest at {MANIFEST_PATH}")
    print("Review status: teacher-candidate")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Search and download Unsplash wallpaper candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Print local plan or candidate metadata without downloads.")
    parser.add_argument("--check-config", action="store_true", help="Check whether local Unsplash config exists.")
    parser.add_argument("--show-presets", action="store_true", help="Print search presets.")
    parser.add_argument("--query", help="Custom search query.")
    parser.add_argument("--preset", choices=[name for name, _, _ in PRESETS], help="Run one configured preset search.")
    parser.add_argument("--limit", type=int, default=5, help="Result limit. Default: 5. Max: 30.")
    parser.add_argument("--orientation", choices=["landscape", "portrait", "squarish"], default="landscape")
    parser.add_argument("--api-search", action="store_true", help="Make a real Unsplash API search request. Downloads are still disabled.")
    parser.add_argument("--download-photo-id", help="Unsplash photo ID to download after review.")
    parser.add_argument("--target", choices=sorted(TARGETS), help="Download target folder: teacher or presentation.")
    parser.add_argument("--confirm-download", action="store_true", help="Required to actually download the selected image.")
    args = parser.parse_args()

    TEACHER_DIR.mkdir(parents=True, exist_ok=True)
    PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Phase 0E-D4-C Unsplash Wallpaper Search")
    print("Status: candidate download and manifest")
    print(f"Config path: {CONFIG_PATH}")
    print(f"Teacher/Coding target: {TEACHER_DIR}")
    print(f"Presentation target: {PRESENTATION_DIR}")
    print(f"Manifest path: {MANIFEST_PATH}")
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

    if args.download_photo_id:
        if not args.target:
            raise SystemExit("FAIL: --download-photo-id requires --target teacher or --target presentation.")
        access_key = require_access_key()
        print()
        print(f"Preparing selected Unsplash download: {args.download_photo_id}")
        print(f"Target: {args.target}")
        return download_photo(access_key, args.download_photo_id, args.target, args.confirm_download)

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
