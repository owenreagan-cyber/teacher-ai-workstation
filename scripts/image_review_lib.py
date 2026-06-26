#!/usr/bin/env python3
"""Shared helpers for local image review and Vibe Engine scripts."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

ROOT = Path.home() / "Pictures" / "Teacher-AI-Workstation"
REVIEW_ROOT = ROOT / "Image-Review"
DEFAULT_MANIFEST_PATH = REVIEW_ROOT / "approval-manifest.json"

QUEUE_FOLDERS = {
    "incoming": REVIEW_ROOT / "Incoming-Candidates",
    "approved_personal_wallpaper": REVIEW_ROOT / "Approved-Personal-Wallpaper",
    "approved_photos_widget": REVIEW_ROOT / "Approved-Photos-Widget",
    "approved_presentation_safe": REVIEW_ROOT / "Approved-Presentation-Safe",
    "rejected_or_hold": REVIEW_ROOT / "Rejected-or-Hold",
    "reference_only": REVIEW_ROOT / "Reference-Only",
}

FINAL_FOLDERS = {
    "casual": ROOT / "Wallpapers" / "Casual-Anime",
    "teacher": ROOT / "Wallpapers" / "Teacher-Coding",
    "presentation": ROOT / "Wallpapers" / "Presentation",
    "photos_widget": ROOT / "Photos-Import" / "Casual-Anime-Shuffle",
}

VALID_INTENDED_USES = {
    "reference_only",
    "personal_wallpaper",
    "photos_widget",
    "classroom_presentation",
    "business_or_commercial",
    "commercial_3d_printing",
}

VALID_REVIEW_STATUSES = {
    "incoming",
    "reference_only",
    "approved_personal_wallpaper",
    "approved_photos_widget",
    "approved_presentation_safe",
    "rejected_or_hold",
}

REQUIRED_ENTRY_FIELDS = [
    "id",
    "filename",
    "local_path",
    "source_platform",
    "source_url",
    "creator",
    "license_or_usage_note",
    "intended_use",
    "review_status",
    "reviewer",
    "review_date",
    "notes",
]

RISKY_SOURCE_TERMS = (
    "reddit",
    "anime",
    "fan-art",
    "fanart",
    "character",
    "pixiv",
    "artstation",
    "pinterest",
    "unknown",
)

HUMAN_APPROVAL_TERMS = (
    "explicit human approval",
    "human approval",
    "human-approved",
    "approved by owen",
    "reviewed by owen",
    "approved_presentation_safe",
    "presentation-safe approval",
)

LICENSING_REVIEW_TERMS = (
    "explicit licensing",
    "license reviewed",
    "licensing reviewed",
    "rights confirmed",
    "permission confirmed",
    "commercial approval",
    "ip review",
    "human licensing review",
)


class ManifestError(RuntimeError):
    """Raised when the approval manifest cannot be read safely."""


def expand_path(value: Union[str, Path]) -> Path:
    return Path(os.path.expanduser(str(value)))


def today_iso() -> str:
    return dt.date.today().isoformat()


def default_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_by": "teacher-ai-workstation image review tools",
        "purpose": (
            "Human review log for image candidates before wallpaper, Photos widget, "
            "classroom presentation, reference, business, or 3D printing use."
        ),
        "entries": [],
    }


def load_manifest(path: Path, create_if_missing: bool = False) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        manifest = default_manifest()
        if create_if_missing:
            save_manifest(path, manifest)
        return manifest, True

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(f"Manifest must be a JSON object: {path}")

    entries = data.setdefault("entries", [])
    if not isinstance(entries, list):
        raise ManifestError(f"Manifest entries must be an array: {path}")

    return data, False


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    entries = manifest.setdefault("entries", [])
    if isinstance(entries, list):
        entries.sort(key=lambda item: str(item.get("id", "")) if isinstance(item, dict) else "")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug[:64] or "image"


def generate_entry_id(filename: str, review_date: str) -> str:
    timestamp = dt.datetime.now().strftime("%H%M%S")
    return f"{review_date}-{slugify(filename)}-{timestamp}"


def build_entry(
    *,
    filename: str,
    local_path: str,
    source_platform: str,
    source_url: str,
    creator: str,
    license_or_usage_note: str,
    intended_use: str,
    review_status: str,
    reviewer: str,
    review_date: str,
    notes: str,
    entry_id: Optional[str] = None,
) -> dict[str, str]:
    entry_id = entry_id or generate_entry_id(filename, review_date)
    return {
        "id": entry_id,
        "filename": filename,
        "local_path": local_path,
        "source_platform": source_platform or "unknown",
        "source_url": source_url or "unknown",
        "creator": creator or "unknown",
        "license_or_usage_note": license_or_usage_note or "unknown",
        "intended_use": intended_use,
        "review_status": review_status,
        "reviewer": reviewer or "Owen Reagan",
        "review_date": review_date,
        "notes": notes or "",
    }


def source_is_risky(source_platform: str) -> bool:
    lowered = source_platform.lower()
    return any(term in lowered for term in RISKY_SOURCE_TERMS)


def source_is_unknown(entry: dict[str, Any]) -> bool:
    source_platform = str(entry.get("source_platform", "")).strip().lower()
    source_url = str(entry.get("source_url", "")).strip().lower()
    return source_platform in {"", "unknown", "n/a", "none"} or source_url in {"", "unknown", "n/a", "none"}


def contains_any(value: str, terms: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in terms)


def validate_entry(entry: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    intended_use = str(entry.get("intended_use", ""))
    review_status = str(entry.get("review_status", ""))
    notes = str(entry.get("notes", ""))
    source_platform = str(entry.get("source_platform", ""))

    if intended_use not in VALID_INTENDED_USES:
        errors.append(f"invalid intended_use: {intended_use}")
    if review_status not in VALID_REVIEW_STATUSES:
        errors.append(f"invalid review_status: {review_status}")

    local_path = str(entry.get("local_path", "")).strip()
    if local_path and local_path != "unknown" and not expand_path(local_path).exists():
        warnings.append(f"local_path does not exist yet: {local_path}")

    if intended_use == "classroom_presentation":
        if source_is_risky(source_platform) and not (
            review_status == "approved_presentation_safe"
            and contains_any(notes, HUMAN_APPROVAL_TERMS)
        ):
            errors.append(
                "risky source platforms cannot be used for classroom_presentation "
                "without approved_presentation_safe and explicit human approval notes"
            )
        if source_is_unknown(entry) and not (
            review_status == "approved_presentation_safe"
            and contains_any(notes, HUMAN_APPROVAL_TERMS)
        ):
            errors.append(
                "unknown source cannot be used for classroom_presentation without "
                "approved_presentation_safe and explicit human approval notes"
            )
        if review_status == "approved_presentation_safe" and not contains_any(notes, HUMAN_APPROVAL_TERMS):
            warnings.append("approved_presentation_safe entries should include explicit human approval notes")

    if intended_use in {"business_or_commercial", "commercial_3d_printing"}:
        if not contains_any(notes, LICENSING_REVIEW_TERMS):
            errors.append(
                f"{intended_use} requires explicit licensing/review language in notes"
            )
        else:
            warnings.append(
                f"{intended_use} is tracked only; this scaffold does not grant commercial approval"
            )

    if source_is_unknown(entry) and intended_use in {
        "classroom_presentation",
        "business_or_commercial",
        "commercial_3d_printing",
    }:
        warnings.append("unknown source should normally remain reference_only or rejected_or_hold")

    return errors, warnings


def append_entry(
    manifest_path: Path,
    entry: dict[str, Any],
    *,
    create_if_missing: bool = True,
) -> tuple[dict[str, Any], bool]:
    manifest, created = load_manifest(manifest_path, create_if_missing=create_if_missing)
    entries = manifest.setdefault("entries", [])
    entries.append(entry)
    save_manifest(manifest_path, manifest)
    return manifest, created


def find_entry(
    manifest: dict[str, Any],
    *,
    filename: Optional[str] = None,
    local_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    entries = manifest.get("entries", [])
    wanted_name = filename or (Path(local_path).name if local_path else None)
    wanted_path = str(expand_path(local_path)) if local_path else None
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        entry_path = str(expand_path(str(entry.get("local_path", "")))) if entry.get("local_path") else ""
        if wanted_path and entry_path == wanted_path:
            return entry
        if wanted_name and str(entry.get("filename", "")) == wanted_name:
            return entry
        if wanted_name and entry_path and Path(entry_path).name == wanted_name:
            return entry
    return None


def print_warnings(warnings: list[str]) -> None:
    for warning in warnings:
        print(f"WARN: {warning}")


def print_errors(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL: {error}")
