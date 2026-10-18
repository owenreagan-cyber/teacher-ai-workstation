"""Read-only project metadata intelligence for the single Phase E pilot."""

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
    APPROVED_SOURCE_ROOT,
    PilotBoundaryError,
    enforce_approved_subtree,
    enforce_exact_source_root,
    enforce_output_root,
    utc_now,
)
from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import audit_event_errors, inventory_run_errors


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "registry/pilots/history-project-intelligence-pilot.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/project-intelligence-pilot.schema.json"
OBSERVATION_SCHEMA_PATH = ROOT / "schemas/project-observation.schema.json"
GIT_EXECUTABLE = "/usr/bin/git"
GIT_OPERATION_ARGS = {
    "detect_repository": ("rev-parse", "--is-inside-work-tree"),
    "verify_repository_root": ("rev-parse", "--show-toplevel"),
    "read_current_branch": ("branch", "--show-current"),
    "read_head": ("rev-parse", "--verify", "HEAD"),
    "summarize_dirty_state": (
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
        "--ignore-submodules=all",
    ),
}
CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


@dataclass(frozen=True)
class ProjectPilotResult:
    run_id: str
    observation_id: str
    status: str
    git_commands: int
    metadata_records: int
    runtime_seconds: float
    snapshot_size_bytes: int
    total_output_size_bytes: int
    output_files: tuple[str, ...]
    audit_event_types: tuple[str, ...]


def new_project_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
    return f"run:history-project-intelligence-pilot-{stamp}"


def project_config_errors(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        validate_schema(config, load_json(CONFIG_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if set(config["git_operations"]) != set(GIT_OPERATION_ARGS):
        errors.append("Git operation allowlist must contain exactly five read-only operations")
    if any(config["prohibitions"].values()):
        errors.append("all Phase E prohibited capabilities must remain false")
    return errors


def load_project_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    errors = project_config_errors(config)
    if errors:
        raise PilotBoundaryError(errors[0])
    return config


def git_operation_args(operation: str) -> tuple[str, ...]:
    try:
        return GIT_OPERATION_ARGS[operation]
    except KeyError as exc:
        raise PilotBoundaryError(f"Git operation is not approved: {operation}") from exc


class ReadOnlyGitMetadata:
    """Execute only the five named Git metadata commands without optional locks."""

    def __init__(self, root: Path, *, command_limit: int, timeout_seconds: int) -> None:
        self.root = root
        self.command_limit = command_limit
        self.timeout_seconds = timeout_seconds
        self.command_count = 0

    def run(self, operation: str) -> str:
        arguments = git_operation_args(operation)
        if self.command_count >= self.command_limit:
            raise PilotBoundaryError("Git metadata command limit exceeded")
        self.command_count += 1
        completed = subprocess.run(
            [
                GIT_EXECUTABLE,
                "--no-optional-locks",
                "-c",
                "core.fsmonitor=false",
                *arguments,
            ],
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
            env={
                "PATH": "/usr/bin:/bin",
                "LC_ALL": "C",
                "GIT_OPTIONAL_LOCKS": "0",
            },
        )
        if completed.returncode != 0:
            raise PilotBoundaryError(f"approved Git metadata operation failed: {operation}")
        return completed.stdout.rstrip("\n")


def summarize_porcelain(status_output: str, max_records: int) -> dict[str, Any]:
    records = status_output.splitlines() if status_output else []
    truncated = len(records) > max_records
    records = records[:max_records]
    staged = 0
    worktree = 0
    untracked = 0
    conflicted = 0
    for record in records:
        code = record[:2] if len(record) >= 2 else ""
        if code == "??":
            untracked += 1
            continue
        if code in CONFLICT_CODES:
            conflicted += 1
        if len(code) == 2 and code[0] not in {" ", "?"}:
            staged += 1
        if len(code) == 2 and code[1] not in {" ", "?"}:
            worktree += 1
    return {
        "is_dirty": bool(records) or truncated,
        "staged_changes": staged,
        "tracked_worktree_changes": worktree,
        "untracked_items": untracked,
        "conflicted_items": conflicted,
        "status_records_observed": len(records),
        "truncated": truncated,
    }


def collect_git_metadata(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    reader = ReadOnlyGitMetadata(
        root,
        command_limit=config["limits"]["max_git_commands"],
        timeout_seconds=config["limits"]["git_command_timeout_seconds"],
    )
    detected = reader.run("detect_repository") == "true"
    if not detected:
        raise PilotBoundaryError("approved project is not a Git repository")
    reported_root = Path(reader.run("verify_repository_root")).resolve(strict=True)
    root_matches = reported_root == root
    if not root_matches:
        raise PilotBoundaryError("Git repository root does not match approved project")
    branch = reader.run("read_current_branch") or None
    head = reader.run("read_head") or None
    dirty = summarize_porcelain(
        reader.run("summarize_dirty_state"), config["limits"]["max_status_records"]
    )
    return (
        {
            "repository_detected": True,
            "repository_root_matches_approved": True,
            "current_branch": branch,
            "head_ref": head,
            "dirty_summary": dirty,
            "metadata_method": "read_only_git_allowlist",
            "history_inspected": False,
            "other_branches_inspected": False,
        },
        reader.command_count,
    )


def project_observation_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(OBSERVATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if value["project_id"] == value["observation_id"]:
        errors.append("project concept and physical observation identities must differ")
    if any(item["state_candidate"] == "abandoned" for item in value["state_evidence"]):
        errors.append("abandoned requires owner confirmation and is outside this contract")
    if any(item["authority_claim"] != "none" for item in value["relationships"]):
        errors.append("relationship candidates cannot claim authority")
    if value["authority_claim"] != "none":
        errors.append("project observation cannot claim authority")
    return errors


def build_project_observation(
    run_id: str, config: dict[str, Any], git_metadata: dict[str, Any]
) -> dict[str, Any]:
    evidence = ["repository_detected", "head_present", "dirty_state_observed"]
    if git_metadata["current_branch"] is not None:
        evidence.append("branch_present")
    return {
        "schema_version": 1,
        "observation_id": f"observation:{run_id}:history-project",
        "run_id": run_id,
        "project_id": config["project_id"],
        "source_id": config["source_id"],
        "path_ref": {
            "source_id": config["source_id"],
            "relative_path": config["approved_subtree"],
            "representation_id": config["representation_id"],
        },
        "project_type": "software_project",
        "exists": True,
        "is_directory": True,
        "git": git_metadata,
        "state_evidence": [
            {
                "rule_id": "project.git_metadata",
                "evidence": evidence,
                "state_candidate": "unknown",
                "confidence": "medium",
                "review_state": "unreviewed",
                "owner_confirmation": False,
            }
        ],
        "relationships": [
            {
                "type": "related_to_resource_registry",
                "basis": {
                    "rule": "approved_project_mapping",
                    "source_ref": "project:history",
                    "target_ref": "registry-system:history",
                },
                "confidence": "high",
                "review_state": "unreviewed",
                "authority_claim": "none",
                "automatic_linking": False,
            }
        ],
        "trust": {
            "evidence_role": "observation",
            "confidence": "high",
            "authority_claim": "none",
            "basis": "approved_project_metadata_observation",
        },
        "freshness": {
            "observed_at": utc_now(),
            "stale_status": "unknown",
        },
        "review_state": "unreviewed",
        "authority_claim": "none",
    }


def _audit_event(
    run_id: str,
    project_id: str,
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
        "actor": "system:history-project-intelligence-pilot",
        "target_ref": run_id,
        "evidence": {
            "refs": [run_id, project_id],
            "summary": f"Phase E {event_type.replace('_', ' ')}.",
        },
        "result": result,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def execute_project_pilot() -> ProjectPilotResult:
    config = load_project_config()
    source_root = enforce_exact_source_root(
        APPROVED_SOURCE_ROOT, APPROVED_SOURCE_ROOT
    )
    source_root = enforce_approved_subtree(source_root, config["approved_subtree"])
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)

    run_id = new_project_run_id()
    started_at = utc_now()
    started_clock = time.perf_counter()
    git_metadata, command_count = collect_git_metadata(source_root, config)
    observation = build_project_observation(run_id, config, git_metadata)
    validation_errors = project_observation_errors(observation)
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
        "approved_subtree": config["approved_subtree"],
        "permissions": ["basic_stat_metadata", "read_git_metadata"],
        "limits": {
            "max_depth": 0,
            "max_items": 1,
            "max_duration_seconds": (
                config["limits"]["git_command_timeout_seconds"]
                * config["limits"]["max_git_commands"]
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
            {"code": "project_observation_validation_error", "message": error}
            for error in validation_errors
        ],
    }
    run_errors = inventory_run_errors(run)
    if run_errors:
        raise PilotBoundaryError(run_errors[0])

    audit_events = [
        _audit_event(
            run_id,
            config["project_id"],
            "observation_started",
            started_at,
            "recorded",
            "started",
        ),
        _audit_event(
            run_id,
            config["project_id"],
            "observation_completed",
            completed_at,
            "recorded",
            "completed",
        ),
        _audit_event(
            run_id,
            config["project_id"],
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
    observation_file = output_root / "observations" / f"{run_id}-project.json"
    audit_file = output_root / "audit" / f"{run_id}-project.json"
    _write_json(run_file, run)
    _write_json(observation_file, observation)
    _write_json(
        audit_file,
        {"schema_version": 1, "run_id": run_id, "events": audit_events},
    )

    output_files = (run_file, observation_file, audit_file)
    runtime_seconds = time.perf_counter() - started_clock
    return ProjectPilotResult(
        run_id=run_id,
        observation_id=observation["observation_id"],
        status=run["status"],
        git_commands=command_count,
        metadata_records=1,
        runtime_seconds=runtime_seconds,
        snapshot_size_bytes=observation_file.stat().st_size,
        total_output_size_bytes=sum(path.stat().st_size for path in output_files),
        output_files=tuple(
            str(path.relative_to(ROOT.parents[2])) for path in output_files
        ),
        audit_event_types=tuple(event["event_type"] for event in audit_events),
    )
