from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ResourceIdentity, compact


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> list[ResourceIdentity]:
    payload = load_json(path)
    entries: list[ResourceIdentity] = []
    for raw in payload.get("resources", []):
        entries.append(
            ResourceIdentity(
                resource_id=raw["resourceId"],
                canonical_name=raw["canonicalName"],
                subject=raw.get("subject", ""),
                program=raw.get("program"),
                grade=raw.get("grade"),
                resource_type=raw.get("resourceType", ""),
                lesson_ref=raw.get("lessonRef"),
                lesson_number=raw.get("lessonNumber"),
                assessment_number=raw.get("assessmentNumber"),
                unit=raw.get("unit"),
                chapter=raw.get("chapter"),
                applicability=dict(raw.get("applicability") or {}),
                source_provider=raw.get("sourceProvider"),
                source_reference=raw.get("sourceReference"),
                content_hash=raw.get("contentHash"),
                filename=raw.get("filename"),
                file_size=raw.get("fileSize"),
                modified_at=raw.get("modifiedAt"),
                verification_status=raw.get("verificationStatus", "verified"),
                availability_status=raw.get("availabilityStatus", "available"),
                visibility=raw.get("visibility", "student-facing"),
                deployment_policy=raw.get("deploymentPolicy", "approved-for-canvas-link"),
                canvas_status=raw.get("canvasStatus", "unknown"),
                notes=raw.get("notes", ""),
                provenance=list(raw.get("provenance", [])),
                revision=int(raw.get("revision", 1)),
                aliases=list(raw.get("aliases", [])),
            )
        )
    return entries


def load_corrections(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    return list(payload.get("records", []))


def registry_index(registry: list[ResourceIdentity]) -> dict[str, list[ResourceIdentity]]:
    index: dict[str, list[ResourceIdentity]] = {}
    for item in registry:
        index.setdefault(f"resource_id:{compact(item.resource_id).lower()}", []).append(item)
        if item.lesson_ref:
            index.setdefault(f"lesson_ref:{compact(item.lesson_ref).lower()}", []).append(item)
        for alias in item.aliases:
            index.setdefault(f"alias:{compact(alias).lower()}", []).append(item)
    return index


def resource_lookup(registry: list[ResourceIdentity]) -> dict[str, ResourceIdentity]:
    return {compact(item.resource_id).lower(): item for item in registry}


def is_verified(item: ResourceIdentity) -> bool:
    return item.verification_status in {"verified", "owner-approved"}
