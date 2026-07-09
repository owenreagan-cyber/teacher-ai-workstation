#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SANDBOX_COURSE_ID = "24399"
REFERENCE_COURSE_IDS = {"21944", "21957", "21919"}
ALLOWED_WRITE_COURSE_IDS = {SANDBOX_COURSE_ID}
BLOCKED_ENDPOINT_MARKERS = {
    "grades",
    "gradebook",
    "submissions",
    "analytics",
    "users",
    "people",
    "enrollments",
    "settings",
    "rubrics",
    "outcomes",
    "quizzes",
    "item_banks",
    "collaborations",
    "conferences",
}
ALLOWED_READ_ENDPOINTS = {
    "course",
    "tabs",
    "pages",
    "page",
    "assignments",
    "announcements",
    "files",
    "folders",
    "modules",
    "module_items",
}
ALLOWED_WRITE_ARTIFACTS = {"page", "assignment", "announcement", "module", "file"}


@dataclass(frozen=True)
class SafetyResult:
    level: str
    message: str


def is_blocked_path(path: str) -> bool:
    lowered = path.lower()
    return any(marker in lowered for marker in BLOCKED_ENDPOINT_MARKERS)


def require_safe_endpoint(kind: str, path: str) -> None:
    if kind not in ALLOWED_READ_ENDPOINTS:
        raise PermissionError(f"BLOCKED: endpoint kind is not allowlisted: {kind}")
    if is_blocked_path(path):
        raise PermissionError(f"BLOCKED: endpoint touches a blocked Canvas area: {path}")


def require_write_allowed(course_id: str, artifact_type: str, allow_writes: bool) -> None:
    if not allow_writes:
        raise PermissionError("BLOCKED: experiment mode requires --allow-writes for Canvas mutations")
    if str(course_id) not in ALLOWED_WRITE_COURSE_IDS:
        raise PermissionError("BLOCKED: Canvas writes are locked to sandbox course 24399")
    if artifact_type not in ALLOWED_WRITE_ARTIFACTS:
        raise PermissionError(f"BLOCKED: unsupported write artifact type: {artifact_type}")


def require_reference_read_only(course_id: str, method: str) -> None:
    if str(course_id) in REFERENCE_COURSE_IDS and method.upper() != "GET":
        raise PermissionError("BLOCKED: reference courses 21944, 21957, and 21919 are read-only")


def require_local_output_path(path: Path, root: Path) -> None:
    resolved = path.resolve()
    allowed = root.resolve()
    if allowed not in resolved.parents and resolved != allowed:
        raise PermissionError("BLOCKED: raw Canvas output must stay under .local/canvas-llm")


def deletion_is_temporary(ledger_item: dict) -> bool:
    title = str(ledger_item.get("title") or "")
    artifact_id = ledger_item.get("id")
    return bool(artifact_id) and title.startswith("TAW Phase 21 Temporary ")
