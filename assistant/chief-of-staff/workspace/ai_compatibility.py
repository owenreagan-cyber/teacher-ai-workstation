"""Pure, fail-closed metadata projection for future AI compatibility."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from evidence_model import make_shared_evidence_package, shared_evidence_errors
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/ai-trust-policy.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/ai-trust-policy.schema.json"
VIEW_SCHEMA_PATH = ROOT / "schemas/ai-compatibility-view.schema.json"
EXPLANATION_SCHEMA_PATH = ROOT / "schemas/ai-explanation.schema.json"
ALLOWED_OPERATIONS = {
    "summarize",
    "explain_relationships",
    "answer_metadata_questions",
    "suggest_reviews",
}
FORBIDDEN_OPERATIONS = {
    "modify_records",
    "execute_actions",
    "change_authority",
    "approve_recovery",
    "delete",
    "restore",
    "move_files",
}
SAFE_METADATA_FIELDS = {"purpose", "status", "availability", "resource_type", "artifact_type"}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{8,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
)
RAW_FILENAME_PATTERN = re.compile(r"(^|[/\\])[^/\\\s]+\.[A-Za-z0-9]{1,8}$")


class AIProjectionError(ValueError):
    """Raised when internal data cannot safely enter an AI projection."""


def ai_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(policy["allowed_operations"]) != ALLOWED_OPERATIONS:
        errors.append("AI allowed operation set is invalid")
    if set(policy["forbidden_operations"]) != FORBIDDEN_OPERATIONS:
        errors.append("AI forbidden operation set is invalid")
    if policy["ai_connection_enabled"] or policy["raw_observation_export_enabled"]:
        errors.append("AI connections and raw observation export must remain disabled")
    if not all(policy[key] for key in ("read_only", "metadata_only", "non_authoritative", "non_executable")):
        errors.append("AI projection trust invariants must remain enabled")
    if policy["action_capabilities"]:
        errors.append("AI projection cannot expose action capabilities")
    return errors


def load_ai_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = ai_policy_errors(policy)
    if errors:
        raise AIProjectionError(errors[0])
    return policy


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _unsafe_string_reason(value: str) -> str | None:
    normalized = value.replace("\\", "/")
    if normalized.startswith(("/", "~/")) or "/Users/" in normalized:
        return "absolute or home-directory path"
    if re.match(r"^[A-Za-z]:/", normalized):
        return "absolute path"
    if RAW_FILENAME_PATTERN.search(value):
        return "raw filename"
    if any(pattern.search(value) for pattern in SECRET_PATTERNS):
        return "credential or token"
    return None


def reject_forbidden_ai_input(value: Any, policy: dict[str, Any], location: str = "$") -> None:
    forbidden_fields = {_normalized_key(item) for item in policy["forbidden_fields"]}
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = _normalized_key(str(key))
            if normalized_key in forbidden_fields:
                raise AIProjectionError(f"{location}.{key}: forbidden AI-view field")
            if normalized_key in {"authority_effect", "permission_effect", "action_effect"} and child != "none":
                raise AIProjectionError(f"{location}.{key}: AI view cannot create authority, permission, or action effects")
            if normalized_key == "action_capabilities" and child:
                raise AIProjectionError(f"{location}.{key}: AI view cannot expose action capabilities")
            reject_forbidden_ai_input(child, policy, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_forbidden_ai_input(child, policy, f"{location}[{index}]")
    elif isinstance(value, str):
        reason = _unsafe_string_reason(value)
        if reason:
            raise AIProjectionError(f"{location}: {reason} is forbidden")


def _project_entity(entity: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    classification = entity["classification"]
    if classification in set(policy["blocked_sensitivities"]):
        raise AIProjectionError(f"blocked sensitivity: {classification}")
    metadata = {
        key: value
        for key, value in entity.get("metadata", {}).items()
        if key in SAFE_METADATA_FIELDS
    }
    return {
        "entity_id": entity["entity_id"],
        "label": entity["label"],
        "type": entity["type"],
        "authority": entity["authority"],
        "confidence": entity["confidence"],
        "review_state": entity["review_state"],
        "classification": classification,
        "metadata": metadata,
    }


def _project_evidence_summary(
    package: dict[str, Any],
    source_systems: list[str],
    uncertainty: list[str],
) -> dict[str, Any]:
    errors = shared_evidence_errors(package)
    if errors:
        raise AIProjectionError(errors[0])
    evidence: list[str] = []
    if package["observations"]:
        evidence.append(f"{len(package['observations'])} observation reference(s)")
    if package["relationships"]:
        evidence.append(f"{len(package['relationships'])} relationship reference(s)")
    basis = package["authority_context"]["basis"]
    if basis not in {"unknown", "none"}:
        evidence.append("explicit authority-context basis")
    if not evidence:
        raise AIProjectionError("evidence summary has no safe evidence description")
    return {
        "evidence_package_id": package["evidence_package_id"],
        "evidence_type": package["evidence_type"],
        "subject_ref": package["subject_ref"],
        "claim": package["claim"],
        "source_systems": source_systems,
        "evidence": evidence,
        "confidence": package["confidence"],
        "review_state": package["review_state"],
        "uncertainty": uncertainty,
        "authority_effect": "none",
    }


def ai_view_errors(value: dict[str, Any], policy: dict[str, Any] | None = None) -> list[str]:
    try:
        validate_schema(value, load_json(VIEW_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    active_policy = policy or load_ai_policy()
    try:
        reject_forbidden_ai_input(value, active_policy)
    except AIProjectionError as exc:
        return [str(exc)]
    if value["action_capabilities"]:
        return ["AI view cannot contain action capabilities"]
    if value["trust"] != {
        "read_only": True,
        "metadata_only": True,
        "authoritative": False,
        "executable": False,
        "raw_observations_included": False,
    }:
        return ["AI view trust boundary is invalid"]
    return []


def project_ai_compatibility_view(
    internal: dict[str, Any], policy: dict[str, Any] | None = None
) -> dict[str, Any]:
    active_policy = policy or load_ai_policy()
    errors = ai_policy_errors(active_policy)
    if errors:
        raise AIProjectionError(errors[0])
    reject_forbidden_ai_input(internal, active_policy)
    entities = [_project_entity(item, active_policy) for item in internal["entities"]]
    relationships = [
        {
            "relationship_type": item["relationship_type"],
            "source_ref": item["source_ref"],
            "target_ref": item["target_ref"],
            "confidence": item["confidence"],
            "review_state": item["review_state"],
            "authority_effect": "none",
        }
        for item in internal["relationships"]
    ]
    evidence_summaries = []
    for package in internal["evidence_packages"]:
        package_id = package["evidence_package_id"]
        sources = internal["evidence_source_systems"].get(package_id, [])
        uncertainty = internal["evidence_uncertainty"].get(package_id, [])
        if not sources or not uncertainty:
            raise AIProjectionError("every evidence summary requires sources and uncertainty")
        evidence_summaries.append(_project_evidence_summary(package, sources, uncertainty))
    recommendations = [
        {
            "finding": item["finding"],
            "confidence": item["confidence"],
            "next_step": item["next_step"],
            "review_state": item["review_state"],
            "action_state": "not_an_action",
            "authority_effect": "none",
        }
        for item in internal.get("recommendations", [])
    ]
    view = {
        "schema_version": 1,
        "view_id": internal["view_id"],
        "projection_kind": "sanitized_metadata_projection",
        "generated_from_refs": internal["source_refs"],
        "entities": entities,
        "relationships": relationships,
        "evidence_summaries": evidence_summaries,
        "recommendations": recommendations,
        "trust": {
            "read_only": True,
            "metadata_only": True,
            "authoritative": False,
            "executable": False,
            "raw_observations_included": False,
        },
        "action_capabilities": [],
    }
    view_errors = ai_view_errors(view, active_policy)
    if view_errors:
        raise AIProjectionError(view_errors[0])
    return view


def explain(view: dict[str, Any], entity_id: str) -> dict[str, Any]:
    entities = {item["entity_id"]: item for item in view["entities"]}
    if entity_id not in entities:
        raise AIProjectionError("AI explanation entity is not present in the projection")
    entity = entities[entity_id]
    relevant = [
        item for item in view["evidence_summaries"] if item["subject_ref"] == entity_id
    ]
    if not relevant:
        raise AIProjectionError("AI explanation requires evidence for the entity")
    explanation = {
        "entity_id": entity_id,
        "source_systems": sorted({source for item in relevant for source in item["source_systems"]}),
        "evidence": [item["claim"] for item in relevant],
        "confidence": entity["confidence"],
        "review_state": entity["review_state"],
        "uncertainty": sorted({unknown for item in relevant for unknown in item["uncertainty"]}),
        "authority": entity["authority"],
        "action_authority": "none",
    }
    try:
        validate_schema(explanation, load_json(EXPLANATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        raise AIProjectionError(str(exc)) from exc
    return explanation


def synthetic_internal_model() -> dict[str, Any]:
    application_id = "application-concept:grade-4-writing-launcher"
    project_id = "project:grade-4-writing"
    package = make_shared_evidence_package(
        "evidence-package:ai-view:writing-application-project",
        "relationship",
        application_id,
        "Grade 4 Writing Launcher relates to the Grade 4 Writing project and Writing Registry.",
        observations=["observation:approved-writing-application-metadata"],
        relationships=["relationship:approved-writing-project-application"],
        confidence="high",
        alternatives=["Relationship remains subject to review."],
    )
    return {
        "view_id": "ai-view:synthetic-writing-metadata",
        "source_refs": ["registry-system:writing", "relationship-graph:approved-phase-g"],
        "entities": [
            {
                "entity_id": application_id,
                "label": "Grade 4 Writing Launcher",
                "type": "application",
                "authority": "unknown",
                "confidence": "high",
                "review_state": "unreviewed",
                "classification": "teacher_internal",
                "metadata": {"purpose": "writing_classroom_launcher", "status": "static_declared"},
            },
            {
                "entity_id": project_id,
                "label": "Grade 4 Writing",
                "type": "project",
                "authority": "unknown",
                "confidence": "high",
                "review_state": "unreviewed",
                "classification": "teacher_internal",
                "metadata": {"purpose": "writing_curriculum_project", "status": "observed"},
            },
        ],
        "relationships": [
            {
                "relationship_type": "used_by_application",
                "source_ref": project_id,
                "target_ref": application_id,
                "confidence": "high",
                "review_state": "unreviewed",
            }
        ],
        "evidence_packages": [package],
        "evidence_source_systems": {
            package["evidence_package_id"]: ["writing-application-observation", "teacher-resource-registry"]
        },
        "evidence_uncertainty": {
            package["evidence_package_id"]: ["authority remains unknown", "relationship remains unreviewed"]
        },
        "recommendations": [
            {
                "finding": "Review the Writing application-to-project relationship.",
                "confidence": "high",
                "next_step": "review_candidate",
                "review_state": "unreviewed",
            }
        ],
    }
