"""Deterministic Phase G relationships from three explicitly named local artifacts."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from application_pilot import application_observation_errors
from pilot import APPROVED_OUTPUT_ROOT, PilotBoundaryError, enforce_output_root, utc_now
from project_pilot import project_observation_errors
from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import audit_event_errors, observation_errors


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "registry/pilots/relationship-intelligence-pilot.json"
POLICY_PATH = ROOT / "registry/relationship-policy.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/relationship-pilot.schema.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/relationship-policy.schema.json"
NODE_SCHEMA_PATH = ROOT / "schemas/relationship-node.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "schemas/relationship-candidate.schema.json"
EVIDENCE_SCHEMA_PATH = ROOT / "schemas/evidence-package.schema.json"
CONFLICT_SCHEMA_PATH = ROOT / "schemas/relationship-conflict.schema.json"
DRIFT_SCHEMA_PATH = ROOT / "schemas/relationship-drift.schema.json"
GRAPH_SCHEMA_PATH = ROOT / "schemas/relationship-graph.schema.json"
PHASE_D_RELATIONSHIP_SCHEMA_PATH = ROOT / "schemas/relationship-evidence.schema.json"

NODE_TYPES = {
    "Workspace",
    "StorageSource",
    "WorkspaceItem",
    "LogicalResource",
    "Representation",
    "Project",
    "ApplicationConcept",
    "ApplicationInstance",
    "Workflow",
    "RegistryEntry",
    "Observation",
    "Recommendation",
}
RELATIONSHIP_TYPES = {
    "belongs_to_project",
    "representation_of",
    "used_by_application",
    "deployed_to",
    "mirrored_to",
    "backed_up_by",
    "version_of",
    "supersedes",
    "referenced_by_registry",
    "expected_artifact_of",
}
ASSERTION_TYPES = {"observed", "inferred", "owner_asserted", "registry_asserted"}
EXPECTED_EVIDENCE_INPUTS = {
    (
        "D",
        "run:history-project-metadata-pilot-20260913t004754454694z",
        "observations/run:history-project-metadata-pilot-20260913t004754454694z.json",
    ),
    (
        "E",
        "run:history-project-intelligence-pilot-20260913t010602083477z",
        "observations/run:history-project-intelligence-pilot-20260913t010602083477z-project.json",
    ),
    (
        "F",
        "run:grade-4-writing-application-pilot-20260913t012118468832z",
        "observations/run:grade-4-writing-application-pilot-20260913t012118468832z-application.json",
    ),
}

# The matrix is intentionally explicit. It rejects vague or action-like graph edges.
RELATIONSHIP_TYPE_MATRIX: dict[str, set[tuple[str, str]]] = {
    "belongs_to_project": {
        ("WorkspaceItem", "Project"),
        ("LogicalResource", "Project"),
        ("Representation", "Project"),
        ("Workflow", "Project"),
    },
    "representation_of": {
        ("Representation", "LogicalResource"),
        ("Representation", "Project"),
        ("Representation", "ApplicationInstance"),
        ("Representation", "ApplicationConcept"),
        ("ApplicationInstance", "ApplicationConcept"),
    },
    "used_by_application": {
        ("Project", "ApplicationConcept"),
        ("Project", "ApplicationInstance"),
        ("LogicalResource", "ApplicationConcept"),
        ("LogicalResource", "ApplicationInstance"),
        ("Workflow", "ApplicationConcept"),
    },
    "deployed_to": {
        ("Project", "ApplicationInstance"),
        ("Project", "Representation"),
        ("ApplicationConcept", "ApplicationInstance"),
    },
    "mirrored_to": {
        ("Representation", "Representation"),
        ("Representation", "StorageSource"),
    },
    "backed_up_by": {
        ("Representation", "Representation"),
        ("Representation", "StorageSource"),
        ("Project", "Representation"),
        ("Project", "StorageSource"),
        ("LogicalResource", "Representation"),
    },
    "version_of": {
        ("WorkspaceItem", "WorkspaceItem"),
        ("LogicalResource", "LogicalResource"),
        ("Representation", "Representation"),
        ("Project", "Project"),
        ("ApplicationConcept", "ApplicationConcept"),
        ("ApplicationInstance", "ApplicationInstance"),
    },
    "supersedes": {
        ("WorkspaceItem", "WorkspaceItem"),
        ("LogicalResource", "LogicalResource"),
        ("Representation", "Representation"),
        ("Project", "Project"),
        ("ApplicationConcept", "ApplicationConcept"),
        ("ApplicationInstance", "ApplicationInstance"),
    },
    "referenced_by_registry": {
        ("Project", "RegistryEntry"),
        ("ApplicationConcept", "RegistryEntry"),
        ("LogicalResource", "RegistryEntry"),
    },
    "expected_artifact_of": {
        ("WorkspaceItem", "Project"),
        ("WorkspaceItem", "Workflow"),
        ("Representation", "Project"),
        ("Representation", "Workflow"),
        ("LogicalResource", "Project"),
        ("LogicalResource", "Workflow"),
    },
}


@dataclass(frozen=True)
class RelationshipPilotResult:
    run_id: str
    graph_id: str
    status: str
    input_artifacts: int
    node_count: int
    relationship_count: int
    evidence_package_count: int
    conflict_count: int
    drift_count: int
    runtime_seconds: float
    graph_size_bytes: int
    total_output_size_bytes: int
    output_files: tuple[str, ...]
    audit_event_types: tuple[str, ...]


def new_relationship_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
    return f"run:relationship-intelligence-pilot-{stamp}"


def relationship_config_errors(
    config: dict[str, Any], policy: dict[str, Any]
) -> list[str]:
    try:
        validate_schema(config, load_json(CONFIG_SCHEMA_PATH))
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if any(config["prohibitions"].values()):
        errors.append("all Phase G prohibited capabilities must remain false")
    if set(policy["supported_node_types"]) != NODE_TYPES:
        errors.append("Phase G node type set is incomplete")
    if set(policy["supported_relationship_types"]) != RELATIONSHIP_TYPES:
        errors.append("Phase G relationship type set is incomplete")
    if set(policy["supported_assertion_types"]) != ASSERTION_TYPES:
        errors.append("Phase G assertion type set is incomplete")
    if any(value != "none" for value in policy["effects"].values()):
        errors.append("relationship policy effects must all be none")
    actual_inputs = {
        (item["phase"], item["run_id"], item["artifact_ref"])
        for item in config["evidence_inputs"]
    }
    if actual_inputs != EXPECTED_EVIDENCE_INPUTS:
        errors.append("Phase G must name exactly the approved Phase D, E, and F artifacts")
    return errors


def load_relationship_configuration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_json(CONFIG_PATH)
    policy = load_json(POLICY_PATH)
    errors = relationship_config_errors(config, policy)
    if errors:
        raise PilotBoundaryError(errors[0])
    return config, policy


def resolve_evidence_artifact(artifact_ref: str) -> Path:
    relative = PurePosixPath(artifact_ref)
    if relative.is_absolute() or ".." in relative.parts:
        raise PilotBoundaryError("relationship evidence path traversal is forbidden")
    if len(relative.parts) != 2 or relative.parts[0] != "observations":
        raise PilotBoundaryError("relationship evidence must be an explicit observation artifact")
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)
    candidate = output_root.joinpath(*relative.parts)
    if candidate.is_symlink():
        raise PilotBoundaryError("relationship evidence cannot be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(output_root)
    except (OSError, ValueError) as exc:
        raise PilotBoundaryError("approved relationship evidence artifact is unavailable") from exc
    if not resolved.is_file():
        raise PilotBoundaryError("relationship evidence must be a regular non-symlink file")
    return resolved


def load_evidence_inputs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inputs: dict[str, dict[str, Any]] = {}
    for item in config["evidence_inputs"]:
        artifact = load_json(resolve_evidence_artifact(item["artifact_ref"]))
        if artifact.get("run_id") != item["run_id"]:
            raise PilotBoundaryError(f"Phase {item['phase']} evidence run provenance mismatch")
        inputs[item["phase"]] = artifact
    if set(inputs) != {"D", "E", "F"}:
        raise PilotBoundaryError("relationship evidence input set is incomplete")
    return inputs


def source_evidence_errors(inputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    phase_d = inputs["D"]
    if set(phase_d) != {
        "schema_version",
        "run_id",
        "source_id",
        "observations",
        "relationship_preparation",
    }:
        errors.append("Phase D evidence wrapper is invalid")
    elif not phase_d["observations"] or len(phase_d["relationship_preparation"]) != 1:
        errors.append("Phase D evidence is incomplete")
    else:
        errors.extend(observation_errors(phase_d["observations"][0]))
        try:
            validate_schema(
                phase_d["relationship_preparation"][0],
                load_json(PHASE_D_RELATIONSHIP_SCHEMA_PATH),
            )
        except (SchemaValidationError, TypeError) as exc:
            errors.append(str(exc))
    errors.extend(project_observation_errors(inputs["E"]))
    errors.extend(application_observation_errors(inputs["F"]))
    return errors


def _node(
    node_id: str, node_type: str, label: str, evidence_refs: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "node_id": node_id,
        "node_type": node_type,
        "label": label,
        "evidence_refs": evidence_refs,
        "review_state": "unreviewed",
        "authority_claim": "none",
    }


def build_nodes(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    phase_d_root = inputs["D"]["observations"][0]["observation_id"]
    phase_e_ref = inputs["E"]["observation_id"]
    phase_f_ref = inputs["F"]["observation_id"]
    phase_d_relation = inputs["D"]["relationship_preparation"][0]["evidence_id"]
    return [
        _node("representation:history:local-git", "Representation", "History local Git representation", [phase_d_root, phase_e_ref]),
        _node("project:history", "Project", "History project", [phase_e_ref]),
        _node("registry-system:history", "RegistryEntry", "History Resource Registry entry", [phase_d_relation, phase_e_ref]),
        _node("representation:grade-4-writing:installed-bundle", "Representation", "Installed Grade 4 Writing bundle", [phase_f_ref]),
        _node("application-instance:grade-4-writing-local", "ApplicationInstance", "Local Grade 4 Writing application instance", [phase_f_ref]),
        _node("application-concept:grade-4-writing-launcher", "ApplicationConcept", "Grade 4 Writing Launcher", [phase_f_ref]),
        _node("project:grade-4-writing", "Project", "Grade 4 Writing project", [phase_f_ref]),
        _node("registry-system:writing", "RegistryEntry", "Writing Resource Registry entry", [phase_f_ref]),
    ]


def _relationship_slug(run_id: str, suffix: str) -> str:
    return f"relationship:{run_id.removeprefix('run:')}:{suffix}"


def make_evidence_package(
    relationship_id: str,
    finding: str,
    evidence: list[str],
    provenance_refs: list[str],
    *,
    confidence: str = "high",
    alternatives: list[str] | None = None,
) -> dict[str, Any]:
    suffix = relationship_id.removeprefix("relationship:")
    return {
        "schema_version": 1,
        "package_id": f"evidence-package:{suffix}",
        "subject_ref": relationship_id,
        "finding": finding,
        "evidence": evidence,
        "confidence": confidence,
        "alternatives": alternatives or [],
        "review_state": "unreviewed",
        "provenance_refs": provenance_refs,
        "authority_claim": "none",
    }


def make_relationship_candidate(
    relationship_id: str,
    relationship_type: str,
    source_ref: str,
    target_ref: str,
    package: dict[str, Any],
    *,
    source_phase: str,
    source_observation_ref: str,
    rule_id: str,
    observed_at: str,
    assertion_type: str = "inferred",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "relationship_id": relationship_id,
        "relationship_type": relationship_type,
        "source_ref": source_ref,
        "target_ref": target_ref,
        "assertion_type": assertion_type,
        "confidence": package["confidence"],
        "evidence": {
            "package_id": package["package_id"],
            "evidence_refs": package["provenance_refs"],
        },
        "provenance": {
            "source_phase": source_phase,
            "source_observation_ref": source_observation_ref,
            "rule_id": rule_id,
        },
        "observed_at": observed_at,
        "review_state": "unreviewed",
        "authority_claim": "none",
        "ownership_effect": "none",
        "permission_effect": "none",
        "action_effect": "none",
    }


def build_relationships(
    run_id: str, inputs: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    d_root = inputs["D"]["observations"][0]
    d_relation = inputs["D"]["relationship_preparation"][0]
    e_observation = inputs["E"]
    f_observation = inputs["F"]
    specifications = [
        (
            "history-representation-project",
            "representation_of",
            "representation:history:local-git",
            "project:history",
            "History local Git representation is associated with the History project concept.",
            ["observed_representation", "approved_history_project_identity"],
            [d_root["observation_id"], e_observation["observation_id"]],
            "E",
            e_observation["observation_id"],
            "observed_representation",
            e_observation["freshness"]["observed_at"],
            [],
        ),
        (
            "history-project-registry",
            "referenced_by_registry",
            "project:history",
            "registry-system:history",
            "History project relates to the History Resource Registry entry.",
            ["approved_source_mapping", "approved_project_mapping"],
            [d_relation["evidence_id"], e_observation["observation_id"]],
            "D",
            d_root["observation_id"],
            "approved_source_mapping",
            d_root["freshness"]["observed_at"],
            [],
        ),
        (
            "writing-bundle-instance",
            "representation_of",
            "representation:grade-4-writing:installed-bundle",
            "application-instance:grade-4-writing-local",
            "The observed installed bundle represents the observed local application instance.",
            ["observed_representation", "approved_application_instance_identity"],
            [f_observation["observation_id"]],
            "F",
            f_observation["observation_id"],
            "observed_representation",
            f_observation["freshness"]["observed_at"],
            [],
        ),
        (
            "writing-instance-concept",
            "representation_of",
            "application-instance:grade-4-writing-local",
            "application-concept:grade-4-writing-launcher",
            "The observed local application instance represents the declared launcher concept.",
            ["declared_application_mapping", "distinct_concept_and_instance_identity"],
            [f_observation["observation_id"]],
            "F",
            f_observation["observation_id"],
            "declared_application_mapping",
            f_observation["freshness"]["observed_at"],
            [],
        ),
        (
            "writing-project-application",
            "used_by_application",
            "project:grade-4-writing",
            "application-concept:grade-4-writing-launcher",
            "The Grade 4 Writing project is related to and used by the declared launcher application.",
            ["declared_application_mapping", "normalized_supported_inverse"],
            [f_observation["observation_id"]],
            "F",
            f_observation["observation_id"],
            "declared_application_mapping",
            f_observation["freshness"]["observed_at"],
            ["Phase F expressed application used_by_project project; Phase G records the supported inverse Project used_by_application ApplicationConcept."],
        ),
        (
            "writing-application-registry",
            "referenced_by_registry",
            "application-concept:grade-4-writing-launcher",
            "registry-system:writing",
            "The Grade 4 Writing launcher concept relates to the Writing Resource Registry entry.",
            ["declared_application_mapping", "related_to_resource_registry"],
            [f_observation["observation_id"]],
            "F",
            f_observation["observation_id"],
            "declared_application_mapping",
            f_observation["freshness"]["observed_at"],
            [],
        ),
    ]
    relationships: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    for (
        suffix,
        relationship_type,
        source_ref,
        target_ref,
        finding,
        evidence,
        provenance_refs,
        source_phase,
        source_observation_ref,
        rule_id,
        observed_at,
        alternatives,
    ) in specifications:
        relationship_id = _relationship_slug(run_id, suffix)
        package = make_evidence_package(
            relationship_id,
            finding,
            evidence,
            provenance_refs,
            alternatives=alternatives,
        )
        packages.append(package)
        relationships.append(
            make_relationship_candidate(
                relationship_id,
                relationship_type,
                source_ref,
                target_ref,
                package,
                source_phase=source_phase,
                source_observation_ref=source_observation_ref,
                rule_id=rule_id,
                observed_at=observed_at,
            )
        )
    return relationships, packages


def evidence_package_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(EVIDENCE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if value["authority_claim"] != "none":
        return ["evidence package cannot claim authority"]
    return []


def relationship_conflict_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(CONFLICT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def relationship_drift_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(DRIFT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def relationship_candidate_errors(
    value: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
    packages: dict[str, dict[str, Any]],
) -> list[str]:
    try:
        validate_schema(value, load_json(CANDIDATE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    source = nodes.get(value["source_ref"])
    target = nodes.get(value["target_ref"])
    if source is None:
        errors.append("relationship source does not resolve to a graph node")
    if target is None:
        errors.append("relationship target does not resolve to a graph node")
    if source and target:
        pair = (source["node_type"], target["node_type"])
        if pair not in RELATIONSHIP_TYPE_MATRIX[value["relationship_type"]]:
            errors.append("relationship source and target types are not allowed")
    package = packages.get(value["evidence"]["package_id"])
    if package is None:
        errors.append("relationship evidence package does not resolve")
    else:
        errors.extend(evidence_package_errors(package))
        if package.get("subject_ref") != value["relationship_id"]:
            errors.append("evidence package subject does not match relationship")
        if package.get("confidence") != value["confidence"]:
            errors.append("relationship confidence does not match its evidence package")
        assertion = value["assertion_type"]
        evidence = package.get("evidence", [])
        if assertion == "owner_asserted" and not any(
            item.startswith("owner-evidence:") for item in evidence
        ):
            errors.append("owner_asserted relationship requires explicit owner evidence")
        if assertion == "registry_asserted" and not any(
            item.startswith("registry-evidence:") for item in evidence
        ):
            errors.append("registry_asserted relationship requires source registry evidence")
    if any(
        value[key] != "none"
        for key in ("authority_claim", "ownership_effect", "permission_effect", "action_effect")
    ):
        errors.append("relationship cannot create authority, ownership, permissions, or actions")
    return errors


def graph_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(GRAPH_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    nodes: dict[str, dict[str, Any]] = {}
    for node in value["nodes"]:
        try:
            validate_schema(node, load_json(NODE_SCHEMA_PATH))
        except (SchemaValidationError, TypeError) as exc:
            errors.append(str(exc))
            continue
        if node["node_id"] in nodes:
            errors.append(f"duplicate graph node: {node['node_id']}")
        nodes[node["node_id"]] = node
    packages: dict[str, dict[str, Any]] = {}
    for package in value["evidence_packages"]:
        package_errors = evidence_package_errors(package)
        errors.extend(package_errors)
        package_id = package.get("package_id")
        if package_id in packages:
            errors.append(f"duplicate evidence package: {package_id}")
        if package_id:
            packages[package_id] = package
    relationship_ids: set[str] = set()
    for relationship in value["relationships"]:
        errors.extend(relationship_candidate_errors(relationship, nodes, packages))
        identity = relationship.get("relationship_id")
        if identity in relationship_ids:
            errors.append(f"duplicate relationship: {identity}")
        relationship_ids.add(identity)
    for conflict in value["conflicts"]:
        errors.extend(relationship_conflict_errors(conflict))
    for drift in value["drift_events"]:
        errors.extend(relationship_drift_errors(drift))
    return errors


def detect_relationship_conflicts(
    relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for relationship in relationships:
        grouped[(relationship["source_ref"], relationship["relationship_type"])].append(relationship)
    conflicts: list[dict[str, Any]] = []
    for index, ((source_ref, relationship_type), candidates) in enumerate(sorted(grouped.items()), start=1):
        if len({candidate["target_ref"] for candidate in candidates}) < 2:
            continue
        conflicts.append(
            {
                "schema_version": 1,
                "conflict_id": f"relationship-conflict:detected-{index:04d}",
                "relationship_type": relationship_type,
                "source_ref": source_ref,
                "competing_relationship_ids": sorted(candidate["relationship_id"] for candidate in candidates),
                "evidence_package_ids": sorted(candidate["evidence"]["package_id"] for candidate in candidates),
                "resolution_state": "unresolved",
                "review_state": "unreviewed",
                "automatic_resolution": False,
                "authority_claim": "none",
            }
        )
    return conflicts


def detect_relationship_drift(
    previous: list[dict[str, Any]], current: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    previous_by_key = {
        (item["source_ref"], item["relationship_type"]): item for item in previous
    }
    drift: list[dict[str, Any]] = []
    for index, item in enumerate(current, start=1):
        prior = previous_by_key.get((item["source_ref"], item["relationship_type"]))
        if prior is None or prior["target_ref"] == item["target_ref"]:
            continue
        drift.append(
            {
                "schema_version": 1,
                "drift_id": f"relationship-drift:detected-{index:04d}",
                "relationship_type": item["relationship_type"],
                "source_ref": item["source_ref"],
                "previous_relationship_id": prior["relationship_id"],
                "current_relationship_id": item["relationship_id"],
                "previous_target_ref": prior["target_ref"],
                "current_target_ref": item["target_ref"],
                "result": "relationship_changed",
                "review_state": "unreviewed",
                "automatic_deletion": False,
                "authority_claim": "none",
            }
        )
    return drift


def relationship_audit_event(
    run_id: str,
    target_ref: str,
    event_type: str,
    timestamp: str,
    index: int,
    *,
    actor: str = "system:relationship-intelligence-pilot",
) -> dict[str, Any]:
    suffix_by_type = {
        "relationship_created": "created",
        "relationship_validated": "validated",
        "relationship_conflict_detected": "conflict",
        "relationship_reviewed": "reviewed",
    }
    if event_type not in suffix_by_type:
        raise PilotBoundaryError("unsupported relationship audit event type")
    suffix = suffix_by_type[event_type]
    result = "passed" if event_type == "relationship_validated" else "recorded"
    return {
        "schema_version": 1,
        "event_id": f"audit:{run_id.removeprefix('run:')}-{index:04d}-{suffix}",
        "event_type": event_type,
        "timestamp": timestamp,
        "actor": actor,
        "target_ref": target_ref,
        "evidence": {
            "refs": [run_id, target_ref],
            "summary": f"Phase G {event_type.replace('_', ' ')} without authority or action.",
        },
        "result": result,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def execute_relationship_pilot() -> RelationshipPilotResult:
    config, _policy = load_relationship_configuration()
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)
    start_clock = time.perf_counter()
    run_id = new_relationship_run_id()
    started_at = utc_now()
    inputs = load_evidence_inputs(config)
    input_errors = source_evidence_errors(inputs)
    if input_errors:
        raise PilotBoundaryError(input_errors[0])

    nodes = build_nodes(inputs)
    relationships, packages = build_relationships(run_id, inputs)
    conflicts = detect_relationship_conflicts(relationships)
    drift_events: list[dict[str, Any]] = []
    completed_at = utc_now()
    graph = {
        "schema_version": 1,
        "graph_id": f"relationship-graph:{run_id.removeprefix('run:')}",
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "input_artifacts": [item["artifact_ref"] for item in config["evidence_inputs"]],
        "nodes": nodes,
        "relationships": relationships,
        "evidence_packages": packages,
        "conflicts": conflicts,
        "drift_events": drift_events,
        "review_state": "unreviewed",
        "authority_effect": "none",
        "ownership_effect": "none",
        "permission_effect": "none",
        "action_effect": "none",
    }
    validation_errors = graph_errors(graph)
    if validation_errors:
        raise PilotBoundaryError(validation_errors[0])
    if len(nodes) > config["limits"]["max_nodes"] or len(relationships) > config["limits"]["max_relationships"]:
        raise PilotBoundaryError("relationship graph exceeds pilot limits")

    audit_events = []
    for index, relationship in enumerate(relationships, start=1):
        audit_events.append(relationship_audit_event(run_id, relationship["relationship_id"], "relationship_created", completed_at, index))
        audit_events.append(relationship_audit_event(run_id, relationship["relationship_id"], "relationship_validated", completed_at, index))
    audit_errors = [error for event in audit_events for error in audit_event_errors(event)]
    if audit_errors:
        raise PilotBoundaryError(audit_errors[0])
    runtime_seconds = time.perf_counter() - start_clock
    if runtime_seconds > config["limits"]["max_runtime_seconds"]:
        raise PilotBoundaryError("relationship pilot runtime limit exceeded")

    graph_file = output_root / "relationships" / f"{run_id}.json"
    audit_file = output_root / "audit" / f"{run_id}-relationships.json"
    _write_json(graph_file, graph)
    _write_json(audit_file, {"schema_version": 1, "run_id": run_id, "events": audit_events})
    output_files = (graph_file, audit_file)
    return RelationshipPilotResult(
        run_id=run_id,
        graph_id=graph["graph_id"],
        status="completed",
        input_artifacts=len(inputs),
        node_count=len(nodes),
        relationship_count=len(relationships),
        evidence_package_count=len(packages),
        conflict_count=len(conflicts),
        drift_count=len(drift_events),
        runtime_seconds=runtime_seconds,
        graph_size_bytes=graph_file.stat().st_size,
        total_output_size_bytes=sum(path.stat().st_size for path in output_files),
        output_files=tuple(str(path.relative_to(ROOT.parents[2])) for path in output_files),
        audit_event_types=tuple(event["event_type"] for event in audit_events),
    )
