from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_ORIGINS = {"fixture", "sanitized-export", "local-ignored", "live-read-only"}

# Fields that must never appear in a Phase 27 snapshot: student records, grades,
# submissions, rosters, private discussion content, or credential material.
FORBIDDEN_SNAPSHOT_KEYS = {
    "studentid",
    "studentname",
    "studentemail",
    "grade",
    "grades",
    "score",
    "submission",
    "submissions",
    "roster",
    "rosterentry",
    "authorization",
    "cookie",
    "token",
    "password",
    "accesstoken",
    "sessiontoken",
    "discussionreply",
    "privatediscussion",
}

_UNSAFE_HOST_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0", ".internal", ".local")


class SnapshotValidationError(ValueError):
    pass


def _scan_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, val in value.items():
            if str(key).lower() in FORBIDDEN_SNAPSHOT_KEYS:
                raise SnapshotValidationError(f"forbidden field '{key}' found at {path}")
            _scan_forbidden(val, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_forbidden(item, f"{path}[{idx}]")


def validate_host(url: str, where: str = "url") -> None:
    if not url:
        return
    lowered = url.lower()
    if not (lowered.startswith("https://") or lowered.startswith("http://")):
        raise SnapshotValidationError(f"{where} has an unsafe URL scheme: {url!r}")
    for marker in _UNSAFE_HOST_MARKERS:
        if marker in lowered:
            raise SnapshotValidationError(f"{where} references an unsafe host: {url!r}")


def classify_origin(path: Path) -> str:
    parts = path.resolve().parts
    if ".local" in parts:
        return "local-ignored"
    if "fixtures" in parts:
        return "fixture"
    return "sanitized-export"


@dataclass
class CanvasSnapshot:
    snapshotId: str
    generatedAt: str
    source: str
    remoteObjects: list[dict[str, Any]] = field(default_factory=list)
    origin: str = "fixture"

    def __post_init__(self) -> None:
        if not self.snapshotId:
            raise SnapshotValidationError("snapshotId is required")
        if not self.generatedAt:
            raise SnapshotValidationError("generatedAt is required")
        if self.origin not in VALID_ORIGINS:
            raise SnapshotValidationError(f"invalid snapshot origin: {self.origin!r}")
        validate_host(self.source, "snapshot source")
        for obj in self.remoteObjects:
            _scan_forbidden(obj)
            link = obj.get("linkTarget")
            if link:
                validate_host(link, f"remote object {obj.get('canvasId', '?')} linkTarget")

    def objects_for_course(self, course_ref: str) -> list[dict[str, Any]]:
        return [obj for obj in self.remoteObjects if obj.get("courseRef") == course_ref]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshotId": self.snapshotId,
            "generatedAt": self.generatedAt,
            "source": self.source,
            "remoteObjects": self.remoteObjects,
            "origin": self.origin,
        }


def load_snapshot(path: str | Path, origin: str | None = None) -> CanvasSnapshot:
    resolved = Path(path)
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    _scan_forbidden(raw)
    return CanvasSnapshot(
        snapshotId=raw["snapshotId"],
        generatedAt=raw["generatedAt"],
        source=raw["source"],
        remoteObjects=raw.get("remoteObjects", []),
        origin=origin or classify_origin(resolved),
    )
