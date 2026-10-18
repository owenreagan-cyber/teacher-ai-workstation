"""Metadata-only observation of the single approved Grade 4 Writing app."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pilot import (
    APPROVED_OUTPUT_ROOT,
    PilotBoundaryError,
    enforce_output_root,
    utc_now,
)
from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import audit_event_errors, inventory_run_errors


ROOT = Path(__file__).resolve().parent
APPROVED_APPLICATION = Path("/Users/owen/Applications/Grade 4 Writing.app")
CONFIG_PATH = ROOT / "registry/pilots/grade-4-writing-application-pilot.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/application-intelligence-pilot.schema.json"
OBSERVATION_SCHEMA_PATH = ROOT / "schemas/application-observation.schema.json"
MDLS_EXECUTABLE = "/usr/bin/mdls"
METADATA_FIELD_MAP = {
    "kMDItemDisplayName": "display_name",
    "kMDItemCFBundleIdentifier": "bundle_identifier",
    "kMDItemVersion": "version",
    "kMDItemContentType": "content_type",
}


@dataclass(frozen=True)
class ApplicationPilotResult:
    run_id: str
    observation_id: str
    status: str
    metadata_queries: int
    metadata_fields_available: int
    runtime_seconds: float
    snapshot_size_bytes: int
    total_output_size_bytes: int
    output_files: tuple[str, ...]
    audit_event_types: tuple[str, ...]


def new_application_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
    return f"run:grade-4-writing-application-pilot-{stamp}"


def application_config_errors(config: dict[str, Any]) -> list[str]:
    try:
        validate_schema(config, load_json(CONFIG_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(config["metadata_keys"]) != set(METADATA_FIELD_MAP):
        errors.append("metadata allowlist must contain exactly four approved keys")
    if any(config["prohibitions"].values()):
        errors.append("all Phase F prohibited capabilities must remain false")
    return errors


def load_application_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    errors = application_config_errors(config)
    if errors:
        raise PilotBoundaryError(errors[0])
    return config


def enforce_exact_application(requested: Path, approved: Path) -> Path:
    if ".." in requested.parts:
        raise PilotBoundaryError("application path traversal is forbidden")
    if not requested.is_absolute():
        raise PilotBoundaryError("application path must be absolute")
    if not requested.exists():
        raise PilotBoundaryError("approved application does not exist")
    if requested.is_symlink():
        raise PilotBoundaryError("approved application cannot be a symlink")
    try:
        resolved = requested.resolve(strict=True)
        approved_resolved = approved.resolve(strict=True)
    except OSError as exc:
        raise PilotBoundaryError("approved application is unavailable") from exc
    if resolved != approved_resolved:
        raise PilotBoundaryError("application is not the single approved bundle")
    if not resolved.is_dir() or resolved.suffix != ".app":
        raise PilotBoundaryError("approved application must be an application bundle")
    return resolved


def normalize_mdls_value(raw: str) -> str | None:
    value = raw.strip()
    if not value or value in {"(null)", "null"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value
    return value


class ReadOnlyApplicationMetadata:
    """Query only four Spotlight metadata attributes for one exact bundle."""

    def __init__(self, path: Path, *, query_limit: int, timeout_seconds: int) -> None:
        self.path = path
        self.query_limit = query_limit
        self.timeout_seconds = timeout_seconds
        self.query_count = 0

    def query(self, key: str) -> str | None:
        if key not in METADATA_FIELD_MAP:
            raise PilotBoundaryError(f"application metadata key is not approved: {key}")
        if self.query_count >= self.query_limit:
            raise PilotBoundaryError("application metadata query limit exceeded")
        self.query_count += 1
        completed = subprocess.run(
            [MDLS_EXECUTABLE, "-raw", "-name", key, str(self.path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        if completed.returncode != 0:
            return None
        return normalize_mdls_value(completed.stdout)


def collect_application_metadata(
    path: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    path.lstat()
    reader = ReadOnlyApplicationMetadata(
        path,
        query_limit=config["limits"]["max_metadata_queries"],
        timeout_seconds=config["limits"]["query_timeout_seconds"],
    )
    values = {
        METADATA_FIELD_MAP[key]: reader.query(key) for key in config["metadata_keys"]
    }
    return (
        {
            "exists": True,
            "is_directory": True,
            "is_symlink": False,
            "display_name": values["display_name"],
            "bundle_identifier": values["bundle_identifier"],
            "version": values["version"],
            "application_type": "macos_application_bundle",
            "content_type": values["content_type"],
            "availability": "available",
            "metadata_source": "spotlight_metadata_allowlist",
            "bundle_contents_read": False,
            "signing_inspected": False,
        },
        reader.query_count,
    )


def build_application_observation(
    run_id: str, config: dict[str, Any], metadata: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "observation_id": f"observation:{run_id}:grade-4-writing-application",
        "run_id": run_id,
        "application_instance_id": config["application_instance_id"],
        "application_concept_id": config["application_concept_id"],
        "source_id": config["source_id"],
        "path_ref": {
            "source_id": config["source_id"],
            "relative_path": config["approved_relative_path"],
            "representation_id": config["representation_id"],
        },
        "metadata": metadata,
        "relationships": [
            {
                "type": "used_by_project",
                "source_ref": config["application_concept_id"],
                "target_ref": "project:grade-4-writing",
                "basis": "declared_application_mapping",
                "confidence": "high",
                "review_state": "unreviewed",
                "authority_claim": "none",
                "automatic_linking": False,
            },
            {
                "type": "related_to_resource_registry",
                "source_ref": config["application_concept_id"],
                "target_ref": "registry-system:writing",
                "basis": "declared_application_mapping",
                "confidence": "high",
                "review_state": "unreviewed",
                "authority_claim": "none",
                "automatic_linking": False,
            },
        ],
        "trust": {
            "evidence_role": "observation",
            "confidence": "high",
            "authority_claim": "none",
            "basis": "approved_application_metadata_observation",
        },
        "freshness": {"observed_at": utc_now(), "stale_status": "unknown"},
        "review_state": "unreviewed",
        "authority_claim": "none",
    }


def application_observation_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(OBSERVATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    identities = {
        value["application_concept_id"],
        value["application_instance_id"],
        value["observation_id"],
    }
    if len(identities) != 3:
        errors.append("application concept, instance, and observation identities must differ")
    expected_relationships = {
        ("used_by_project", "project:grade-4-writing"),
        ("related_to_resource_registry", "registry-system:writing"),
    }
    actual_relationships = {
        (item["type"], item["target_ref"]) for item in value["relationships"]
    }
    if actual_relationships != expected_relationships:
        errors.append("application relationship candidate set is invalid")
    if value["authority_claim"] != "none" or any(
        item["authority_claim"] != "none" for item in value["relationships"]
    ):
        errors.append("application evidence cannot claim authority")
    return errors


def _audit_event(
    run_id: str,
    concept_id: str,
    instance_id: str,
    event_type: str,
    timestamp: str,
    result: str,
    suffix: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event_id": f"audit:{run_id.removeprefix('run:')}-{suffix}",
        "event_type": event_type,
        "timestamp": timestamp,
        "actor": "system:grade-4-writing-application-pilot",
        "target_ref": run_id,
        "evidence": {
            "refs": [run_id, concept_id, instance_id],
            "summary": f"Phase F {event_type.replace('_', ' ')}.",
        },
        "result": result,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def execute_application_pilot() -> ApplicationPilotResult:
    config = load_application_config()
    application_path = enforce_exact_application(
        APPROVED_APPLICATION, APPROVED_APPLICATION
    )
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)

    run_id = new_application_run_id()
    started_at = utc_now()
    started_clock = time.perf_counter()
    metadata, query_count = collect_application_metadata(application_path, config)
    observation = build_application_observation(run_id, config, metadata)
    validation_errors = application_observation_errors(observation)
    completed_at = utc_now()

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
        "approved_subtree": config["approved_relative_path"],
        "permissions": ["basic_stat_metadata", "read_application_metadata"],
        "limits": {
            "max_depth": 0,
            "max_items": 1,
            "max_duration_seconds": (
                config["limits"]["max_metadata_queries"]
                * config["limits"]["query_timeout_seconds"]
            ),
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
        "status": "failed" if validation_errors else "completed",
        "errors": [
            {"code": "application_observation_validation_error", "message": error}
            for error in validation_errors
        ],
    }
    run_errors = inventory_run_errors(run)
    if run_errors:
        raise PilotBoundaryError(run_errors[0])

    audit_events = [
        _audit_event(
            run_id,
            config["application_concept_id"],
            config["application_instance_id"],
            "observation_started",
            started_at,
            "recorded",
            "started",
        ),
        _audit_event(
            run_id,
            config["application_concept_id"],
            config["application_instance_id"],
            "observation_completed",
            completed_at,
            "recorded",
            "completed",
        ),
        _audit_event(
            run_id,
            config["application_concept_id"],
            config["application_instance_id"],
            "validation_failed" if validation_errors else "validation_passed",
            completed_at,
            "failed" if validation_errors else "passed",
            "validation",
        ),
    ]
    audit_errors = [
        error for event in audit_events for error in audit_event_errors(event)
    ]
    if audit_errors:
        raise PilotBoundaryError(audit_errors[0])

    run_file = output_root / "inventory-runs" / f"{run_id}.json"
    observation_file = output_root / "observations" / f"{run_id}-application.json"
    audit_file = output_root / "audit" / f"{run_id}-application.json"
    _write_json(run_file, run)
    _write_json(observation_file, observation)
    _write_json(
        audit_file,
        {"schema_version": 1, "run_id": run_id, "events": audit_events},
    )

    output_files = (run_file, observation_file, audit_file)
    available = sum(
        metadata[field] is not None
        for field in ("display_name", "bundle_identifier", "version", "content_type")
    )
    runtime_seconds = time.perf_counter() - started_clock
    return ApplicationPilotResult(
        run_id=run_id,
        observation_id=observation["observation_id"],
        status=run["status"],
        metadata_queries=query_count,
        metadata_fields_available=available,
        runtime_seconds=runtime_seconds,
        snapshot_size_bytes=observation_file.stat().st_size,
        total_output_size_bytes=sum(path.stat().st_size for path in output_files),
        output_files=tuple(
            str(path.relative_to(ROOT.parents[2])) for path in output_files
        ),
        audit_event_types=tuple(event["event_type"] for event in audit_events),
    )
