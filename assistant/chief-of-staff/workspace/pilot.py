"""Bounded metadata-only observation primitives for the Phase D history pilot."""

from __future__ import annotations

import json
import os
import stat as stat_module
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import (
    audit_event_errors,
    inventory_run_errors,
    observation_errors,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "registry/pilots/history-project-metadata-pilot.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/pilot.schema.json"
RELATIONSHIP_SCHEMA_PATH = ROOT / "schemas/relationship-evidence.schema.json"
APPROVED_SOURCE_ROOT = Path("/Users/owen/Projects/history")
APPROVED_OUTPUT_ROOT = REPO_ROOT / ".local/chief-of-staff/workspace"
REQUIRED_PROHIBITIONS = {
    "content_read",
    "hashing",
    "writes",
    "follow_symlinks",
    "cross_filesystem",
    "hidden_entries",
    "git_metadata",
    "recommendations",
}


class PilotBoundaryError(ValueError):
    """Raised when a requested observation exceeds the approved pilot boundary."""


@dataclass(frozen=True)
class PilotResult:
    run_id: str
    status: str
    item_count: int
    runtime_seconds: float
    observation_size_bytes: int
    total_output_size_bytes: int
    hidden_entries_skipped: int
    symlinks_skipped: int
    output_files: tuple[str, ...]
    audit_event_types: tuple[str, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
    return f"run:history-project-metadata-pilot-{stamp}"


def pilot_config_errors(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        validate_schema(config, load_json(CONFIG_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if set(config["prohibitions"]) != REQUIRED_PROHIBITIONS:
        errors.append("pilot must explicitly declare every prohibition")
    if any(config["prohibitions"].values()):
        errors.append("all Phase D prohibited capabilities must remain false")
    return errors


def load_pilot_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    errors = pilot_config_errors(config)
    if errors:
        raise PilotBoundaryError(errors[0])
    return config


def _reject_parent_traversal(path: Path | PurePosixPath) -> None:
    if ".." in path.parts:
        raise PilotBoundaryError("parent traversal is forbidden")


def enforce_exact_source_root(requested: Path, approved: Path) -> Path:
    _reject_parent_traversal(requested)
    if not requested.is_absolute():
        raise PilotBoundaryError("source root must be absolute")
    if requested.is_symlink():
        raise PilotBoundaryError("approved source root cannot be a symlink")
    try:
        resolved = requested.resolve(strict=True)
        approved_resolved = approved.resolve(strict=True)
    except OSError as exc:
        raise PilotBoundaryError(f"approved source is unavailable: {exc}") from exc
    if resolved != approved_resolved:
        raise PilotBoundaryError("source is outside the single approved root")
    if not resolved.is_dir():
        raise PilotBoundaryError("approved source root must be a directory")
    return resolved


def enforce_approved_subtree(root: Path, subtree: str) -> Path:
    relative = PurePosixPath(subtree)
    if relative.is_absolute():
        raise PilotBoundaryError("approved subtree must be relative")
    _reject_parent_traversal(relative)
    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        if part == ".":
            continue
        current = current / part
        if current.is_symlink():
            raise PilotBoundaryError("symlink subtree is forbidden")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise PilotBoundaryError("subtree escapes or is unavailable") from exc
    return resolved


def enforce_output_root(requested: Path, approved: Path) -> Path:
    _reject_parent_traversal(requested)
    if not requested.is_absolute():
        raise PilotBoundaryError("output root must be absolute")
    try:
        approved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise PilotBoundaryError("approved output is outside the repository") from exc
    current = REPO_ROOT
    for part in approved.relative_to(REPO_ROOT).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise PilotBoundaryError("output boundary cannot contain symlinks")
    requested_resolved = requested.resolve(strict=False)
    approved_resolved = approved.resolve(strict=False)
    if requested_resolved != approved_resolved:
        raise PilotBoundaryError("output is outside the approved host-local boundary")
    try:
        requested_resolved.relative_to(REPO_ROOT.resolve(strict=True))
    except ValueError as exc:
        raise PilotBoundaryError("resolved output escapes the repository") from exc
    return requested_resolved


def _timestamp_from_stat(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


class MetadataCollector:
    """Collect only lstat/scandir metadata under one already-approved root."""

    def __init__(
        self,
        root: Path,
        run_id: str,
        source_id: str,
        *,
        max_depth: int,
        max_items: int,
        max_duration_seconds: int,
    ) -> None:
        self.root = root
        self.run_id = run_id
        self.source_id = source_id
        self.max_depth = max_depth
        self.max_items = max_items
        self.deadline = time.monotonic() + max_duration_seconds
        self.root_device = root.lstat().st_dev
        self.observations: list[dict[str, Any]] = []
        self.hidden_entries_skipped = 0
        self.symlinks_skipped = 0
        self.cross_filesystem_skipped = 0
        self.stop_reason: str | None = None

    def _capacity_available(self) -> bool:
        if time.monotonic() > self.deadline:
            self.stop_reason = "duration_limit_reached"
            return False
        if len(self.observations) >= self.max_items:
            self.stop_reason = "item_limit_reached"
            return False
        return True

    def _observation(
        self,
        relative_path: str,
        item_type: str,
        availability: str,
        stat_value: os.stat_result | None,
        *,
        is_symlink: bool,
    ) -> dict[str, Any]:
        token = f"item-{len(self.observations) + 1:06d}"
        extension = None
        if item_type == "file":
            suffix = PurePosixPath(relative_path).suffix
            extension = suffix[1:].lower() if suffix else None
        return {
            "schema_version": 1,
            "observation_id": (
                f"observation:{self.run_id}:{self.source_id}:{token}"
            ),
            "run_id": self.run_id,
            "source_id": self.source_id,
            "relative_path": relative_path,
            "item_type": item_type,
            "metadata": {
                "size_bytes": stat_value.st_size if stat_value else None,
                "modified_at": (
                    _timestamp_from_stat(stat_value.st_mtime) if stat_value else None
                ),
                "extension": extension,
                "bundle_identifier": None,
                "placeholder_state": "not_applicable" if stat_value else "unknown",
                "is_symlink": is_symlink,
            },
            "availability": availability,
            "trust": {
                "evidence_role": "observation",
                "confidence": "high" if stat_value and not is_symlink else "low",
                "authority_claim": "none",
                "basis": "approved_metadata_observation",
            },
            "freshness": {
                "observed_at": utc_now(),
                "source_modified_at": (
                    _timestamp_from_stat(stat_value.st_mtime) if stat_value else None
                ),
                "stale_status": "unknown",
            },
            "classification": {
                "data_sensitivity": "unknown",
                "classification_basis": "unknown",
                "review_state": "unreviewed",
            },
            "review_state": "unreviewed",
        }

    def _observe_entry(self, entry: os.DirEntry[str], relative: str) -> tuple[dict[str, Any], bool]:
        try:
            is_symlink = entry.is_symlink()
            stat_value = entry.stat(follow_symlinks=False)
            if is_symlink:
                self.symlinks_skipped += 1
                return (
                    self._observation(
                        relative,
                        "unavailable_item",
                        "unavailable",
                        stat_value,
                        is_symlink=True,
                    ),
                    False,
                )
            if stat_value.st_dev != self.root_device:
                self.cross_filesystem_skipped += 1
                return (
                    self._observation(
                        relative,
                        "unavailable_item",
                        "unavailable",
                        stat_value,
                        is_symlink=False,
                    ),
                    False,
                )
            if stat_module.S_ISDIR(stat_value.st_mode):
                return (
                    self._observation(
                        relative,
                        "directory",
                        "available",
                        stat_value,
                        is_symlink=False,
                    ),
                    True,
                )
            if stat_module.S_ISREG(stat_value.st_mode):
                return (
                    self._observation(
                        relative,
                        "file",
                        "available",
                        stat_value,
                        is_symlink=False,
                    ),
                    False,
                )
            return (
                self._observation(
                    relative,
                    "unavailable_item",
                    "unavailable",
                    stat_value,
                    is_symlink=False,
                ),
                False,
            )
        except OSError:
            return (
                self._observation(
                    relative,
                    "unavailable_item",
                    "unavailable",
                    None,
                    is_symlink=False,
                ),
                False,
            )

    def _walk(self, directory: Path, depth: int) -> None:
        if self.stop_reason or depth >= self.max_depth:
            return
        try:
            entries = os.scandir(directory)
        except OSError:
            return
        with entries:
            for entry in entries:
                if self.stop_reason or not self._capacity_available():
                    return
                if entry.name.startswith("."):
                    self.hidden_entries_skipped += 1
                    continue
                entry_path = directory / entry.name
                relative = entry_path.relative_to(self.root).as_posix()
                observation, is_directory = self._observe_entry(entry, relative)
                self.observations.append(observation)
                if is_directory and depth + 1 < self.max_depth:
                    self._walk(entry_path, depth + 1)

    def collect(self) -> list[dict[str, Any]]:
        if not self._capacity_available():
            return []
        root_stat = self.root.lstat()
        self.observations.append(
            self._observation(
                ".", "directory", "available", root_stat, is_symlink=False
            )
        )
        self._walk(self.root, 0)
        return self.observations


def validate_observation_batch(
    observations: list[dict[str, Any]],
    *,
    run_id: str,
    source_id: str,
    max_items: int,
) -> list[str]:
    errors: list[str] = []
    if not observations:
        errors.append("observation batch must not be empty")
    if len(observations) > max_items:
        errors.append("observation batch exceeds item limit")
    identifiers: set[str] = set()
    for observation in observations:
        errors.extend(observation_errors(observation))
        if observation.get("run_id") != run_id:
            errors.append("observation run_id does not match batch")
        if observation.get("source_id") != source_id:
            errors.append("observation source_id does not match batch")
        identity = observation.get("observation_id")
        if identity in identifiers:
            errors.append(f"duplicate observation identity: {identity}")
        identifiers.add(identity)
    return errors


def relationship_evidence(run_id: str, source_id: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "evidence_id": f"relationship-evidence:{run_id.removeprefix('run:')}",
        "run_id": run_id,
        "source_id": source_id,
        "possible_relationship": "project-to-registry",
        "basis": {
            "rule": "approved_source_mapping",
            "source_ref": "project:history",
            "target_ref": "registry-system:history",
        },
        "confidence": "high",
        "review_state": "unreviewed",
        "authority_claim": "none",
        "automatic_linking": False,
    }


def _audit_event(
    run_id: str, event_type: str, timestamp: str, result: str, suffix: str
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event_id": f"audit:{run_id.removeprefix('run:')}-{suffix}",
        "event_type": event_type,
        "timestamp": timestamp,
        "actor": "system:history-metadata-pilot",
        "target_ref": run_id,
        "evidence": {
            "refs": [run_id],
            "summary": f"Phase D {event_type.replace('_', ' ')}.",
        },
        "result": result,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def execute_history_pilot() -> PilotResult:
    config = load_pilot_config()
    source_root = enforce_exact_source_root(
        APPROVED_SOURCE_ROOT, APPROVED_SOURCE_ROOT
    )
    source_root = enforce_approved_subtree(source_root, config["approved_subtree"])
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)

    run_id = new_run_id()
    started_at = utc_now()
    start_clock = time.perf_counter()
    collector = MetadataCollector(
        source_root,
        run_id,
        config["source_id"],
        max_depth=config["limits"]["max_depth"],
        max_items=config["limits"]["max_items"],
        max_duration_seconds=config["limits"]["max_duration_seconds"],
    )
    observations = collector.collect()
    completed_at = utc_now()

    batch_errors = validate_observation_batch(
        observations,
        run_id=run_id,
        source_id=config["source_id"],
        max_items=config["limits"]["max_items"],
    )
    if collector.stop_reason:
        batch_errors.append(collector.stop_reason)

    run = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "purpose": config["purpose"],
        "approval": {
            "approval_id": config["approval"]["approval_id"],
            "approved_by": config["approval"]["approved_by"],
            "approved_at": started_at,
            "basis": "explicit_mission",
        },
        "approved_source_id": config["source_id"],
        "approved_subtree": config["approved_subtree"],
        "permissions": config["permissions"],
        "limits": {
            **config["limits"],
            "follow_symlinks": False,
            "cross_filesystem": False,
        },
        "hash_policy": "forbidden",
        "content_read_policy": "metadata_only_no_content",
        "prohibited_operations": [
            "content_read",
            "hashing",
            "writes",
            "symlink_following",
            "cloud_download",
            "unapproved_recursion",
            "source_escape",
        ],
        "status": "failed" if batch_errors else "completed",
        "errors": [
            {"code": "pilot_validation_error", "message": error}
            for error in batch_errors
        ],
    }
    run_errors = inventory_run_errors(run)
    if run_errors:
        raise PilotBoundaryError(run_errors[0])

    relation = relationship_evidence(run_id, config["source_id"])
    validate_schema(relation, load_json(RELATIONSHIP_SCHEMA_PATH))

    audit_events = [
        _audit_event(run_id, "observation_started", started_at, "recorded", "started"),
        _audit_event(
            run_id, "observation_completed", completed_at, "recorded", "completed"
        ),
        _audit_event(
            run_id,
            "validation_failed" if batch_errors else "validation_passed",
            completed_at,
            "failed" if batch_errors else "passed",
            "validation",
        ),
    ]
    audit_errors = [
        error for event in audit_events for error in audit_event_errors(event)
    ]
    if audit_errors:
        raise PilotBoundaryError(audit_errors[0])

    run_file = output_root / "inventory-runs" / f"{run_id}.json"
    observation_file = output_root / "observations" / f"{run_id}.json"
    audit_file = output_root / "audit" / f"{run_id}.json"
    _write_json(run_file, run)
    _write_json(
        observation_file,
        {
            "schema_version": 1,
            "run_id": run_id,
            "source_id": config["source_id"],
            "observations": observations,
            "relationship_preparation": [relation],
        },
    )
    _write_json(
        audit_file,
        {"schema_version": 1, "run_id": run_id, "events": audit_events},
    )

    output_files = (run_file, observation_file, audit_file)
    runtime_seconds = time.perf_counter() - start_clock
    return PilotResult(
        run_id=run_id,
        status=run["status"],
        item_count=len(observations),
        runtime_seconds=runtime_seconds,
        observation_size_bytes=observation_file.stat().st_size,
        total_output_size_bytes=sum(path.stat().st_size for path in output_files),
        hidden_entries_skipped=collector.hidden_entries_skipped,
        symlinks_skipped=collector.symlinks_skipped,
        output_files=tuple(path.relative_to(REPO_ROOT).as_posix() for path in output_files),
        audit_event_types=tuple(event["event_type"] for event in audit_events),
    )
