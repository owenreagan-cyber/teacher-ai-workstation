"""Deterministic Phase L.5D boundary for a future local explanation model.

This module builds and validates contracts only. It has no model connector,
network client, tool surface, action path, filesystem locator, or persistence.
"""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from ai_compatibility import (
    AIProjectionError,
    load_ai_policy,
    reject_forbidden_ai_input,
)
from query_layer import (
    DeterministicQueryLayer,
    QuerySecurityError,
    QueryValidationError,
    explanation_errors,
)
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/local-model-boundary.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/local-model-boundary.schema.json"
CONTEXT_SCHEMA_PATH = ROOT / "schemas/ai-context-package.schema.json"
REQUEST_SCHEMA_PATH = ROOT / "schemas/local-model-request.schema.json"
RESPONSE_SCHEMA_PATH = ROOT / "schemas/local-model-response.schema.json"
VALIDATION_SCHEMA_PATH = ROOT / "schemas/ai-response-validation.schema.json"
AUDIT_SCHEMA_PATH = ROOT / "schemas/local-model-audit.schema.json"

SOURCE_LAYERS = {"query_layer", "explanation_layer", "evidence_layer"}
ALLOWED_TASKS = {"explain"}
ALLOWED_CAPABILITIES = {"explain"}
SAFE_CLASSIFICATIONS = {"public", "teacher_internal", "student_safe"}
REQUIRED_RESTRICTIONS = {
    "no_application_access",
    "no_authority_inference",
    "no_cloud_connection",
    "no_filesystem_access",
    "no_launch_access",
    "no_modification_rights",
    "no_permission_inference",
    "no_restore_or_deletion_rights",
    "no_tools",
}
CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2, "unknown": 3}
ACTION_LANGUAGE = re.compile(
    r"\b(delete|remove|move|restore|replace|modify|launch|execute|write|rename)\b",
    re.IGNORECASE,
)
ACCESS_LANGUAGE = re.compile(r"\bi\s+(have|can gain|was granted)\s+access\b", re.IGNORECASE)
CANONICAL_ASSERTION = re.compile(r"\b(this|it)\s+is\s+canonical\b", re.IGNORECASE)


class AIContextBoundaryError(ValueError):
    """Raised when data cannot safely cross the local-model context boundary."""


def local_model_boundary_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(policy["source_layers"]) != SOURCE_LAYERS:
        errors.append("the adapter must use the query, explanation, and evidence layers")
    if set(policy["tasks"]) != ALLOWED_TASKS:
        errors.append("Phase L.5D supports only explain")
    if set(policy["capabilities"]) != ALLOWED_CAPABILITIES or policy["actions"]:
        errors.append("the local-model contract may grant explain and no actions")
    if set(policy["restrictions"]) != REQUIRED_RESTRICTIONS:
        errors.append("the local-model restriction set is incomplete")
    if policy["sanitization"]["inherits"] != "registry/ai-trust-policy.json":
        errors.append("the adapter must inherit the Phase I AI compatibility policy")
    if any(policy["persistence"].values()):
        errors.append("Phase L.5D cannot persist context, request, response, or audit data")
    for key in (
        "network_enabled",
        "model_invocation_enabled",
        "agent_enabled",
        "tool_calling_enabled",
        "action_execution_enabled",
        "host_local_ai_data_enabled",
    ):
        if policy[key]:
            errors.append(f"{key} must remain disabled")
    if policy["model_contract"]["connector_enabled"]:
        errors.append("the Ollama connector must remain disabled")
    if policy["model_contract"]["execution_enabled"]:
        errors.append("local model execution must remain disabled")
    return errors


def load_local_model_boundary_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = local_model_boundary_policy_errors(policy)
    if errors:
        raise AIContextBoundaryError(errors[0])
    return policy


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9._:-]+", "-", value.lower()).strip("-:")
    if not normalized:
        raise AIContextBoundaryError("a stable non-empty identity is required")
    return normalized


def _validate_schema(value: dict[str, Any], path: Path) -> list[str]:
    try:
        validate_schema(value, load_json(path))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def _reject_unsafe(value: Any) -> list[str]:
    try:
        reject_forbidden_ai_input(value, load_ai_policy())
    except (AIProjectionError, TypeError) as exc:
        return [str(exc)]
    return []


def ai_context_package_errors(
    package: dict[str, Any], policy: dict[str, Any] | None = None
) -> list[str]:
    errors = _validate_schema(package, CONTEXT_SCHEMA_PATH)
    if errors:
        return errors
    active = policy or load_local_model_boundary_policy()
    errors.extend(_reject_unsafe(package))
    if errors:
        return errors
    if package["created_at"] != active["contract_created_at"]:
        errors.append("context creation time must use the deterministic contract timestamp")
    if set(package["capabilities"]) != ALLOWED_CAPABILITIES:
        errors.append("context must explicitly grant only explain")
    if package["actions"] or package["action_authority"] != "none":
        errors.append("context cannot expose actions or action authority")
    if set(package["restrictions"]) != REQUIRED_RESTRICTIONS:
        errors.append("context restrictions do not match the fixed policy")
    if package["raw_observations_included"]:
        errors.append("raw observations cannot enter a local-model context")

    entity_ids = [item["entity_id"] for item in package["entities"]]
    evidence_ids = [item["evidence_id"] for item in package["evidence_summary"]]
    relationship_ids = [item["relationship_id"] for item in package["relationships"]]
    if len(entity_ids) != len(set(entity_ids)):
        errors.append("context entity identities must be unique")
    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("context evidence identities must be unique")
    if len(relationship_ids) != len(set(relationship_ids)):
        errors.append("context relationship identities must be unique")
    if any(item["classification"] not in SAFE_CLASSIFICATIONS for item in package["entities"]):
        errors.append("context contains a blocked classification")
    if any(item["authority_effect"] != "none" for item in package["evidence_summary"]):
        errors.append("evidence summaries cannot create authority")
    if any(item["action_authority"] != "none" for item in package["evidence_summary"]):
        errors.append("evidence summaries cannot expose actions")
    if any(item["authority_effect"] != "none" for item in package["relationships"]):
        errors.append("relationships cannot create authority")
    if not set(item["evidence_id"] for item in package["relationships"]) <= set(evidence_ids):
        errors.append("every relationship evidence reference must resolve inside the package")

    expected_confidence_refs = set(entity_ids) | set(evidence_ids)
    confidence_refs = [item["subject_ref"] for item in package["confidence"]]
    if set(confidence_refs) != expected_confidence_refs or len(confidence_refs) != len(set(confidence_refs)):
        errors.append("confidence must be preserved exactly once for every entity and evidence summary")
    expected_review_refs = set(entity_ids) | set(evidence_ids)
    review_refs = [item["subject_ref"] for item in package["review_state"]]
    if set(review_refs) != expected_review_refs or len(review_refs) != len(set(review_refs)):
        errors.append("review state must be preserved exactly once for every entity and evidence summary")
    authority_refs = [item["subject_ref"] for item in package["authority_context"]]
    if authority_refs != entity_ids:
        errors.append("authority context must be preserved for each projected entity")
    return errors


def build_ai_context(
    entity_id: str,
    *,
    query_layer: DeterministicQueryLayer | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic, sanitized package from existing read-only layers."""

    active = policy or load_local_model_boundary_policy()
    policy_errors = local_model_boundary_policy_errors(active)
    if policy_errors:
        raise AIContextBoundaryError(policy_errors[0])
    unsafe_id = _reject_unsafe({"entity_id": entity_id})
    if unsafe_id:
        raise AIContextBoundaryError(unsafe_id[0])
    layer = query_layer or DeterministicQueryLayer()
    try:
        explanation = layer.explain(entity_id)
        explanation_failures = explanation_errors(explanation)
        if explanation_failures:
            raise AIContextBoundaryError(explanation_failures[0])
        if explanation["subject_type"] == "unknown":
            raise AIContextBoundaryError("AI context requires a known deterministic entity")
        canonical_id = explanation["subject_ref"]
        entity = layer.entities.get(canonical_id)
        if entity is None:
            raise AIContextBoundaryError("deterministic explanation entity is unavailable")
        relationships = layer.related_to(canonical_id)
        evidence_packages = layer.why(canonical_id)
    except (QuerySecurityError, QueryValidationError) as exc:
        raise AIContextBoundaryError(str(exc)) from exc

    for source_name, source_value in (
        ("entity", entity),
        ("explanation", explanation),
        ("relationships", relationships),
        ("evidence", evidence_packages),
    ):
        unsafe = _reject_unsafe(source_value)
        if unsafe:
            raise AIContextBoundaryError(f"{source_name}: {unsafe[0]}")
    if entity["classification"] not in SAFE_CLASSIFICATIONS:
        raise AIContextBoundaryError(
            f"blocked AI context classification: {entity['classification']}"
        )

    evidence_summary = sorted(
        (
            {
                "evidence_id": item["package_id"],
                "evidence_type": item["evidence_type"],
                "claim": item["claim"],
                "sources": sorted(set(item["sources"])),
                "confidence": item["confidence"],
                "review_state": item["review_state"],
                "authority_effect": "none",
                "action_authority": "none",
            }
            for item in evidence_packages
        ),
        key=lambda item: item["evidence_id"],
    )
    expected_evidence = set(explanation["evidence_packages"])
    if {item["evidence_id"] for item in evidence_summary} != expected_evidence:
        raise AIContextBoundaryError(
            "AI context evidence must exactly match the deterministic explanation"
        )

    projected_relationships = sorted(
        (
            {
                "relationship_id": item["relationship_id"],
                "relationship_type": item["relationship_type"],
                "direction": item["direction"],
                "related_entity_id": item["related_ref"],
                "evidence_id": item["evidence_package_id"],
                "confidence": item["confidence"],
                "review_state": item["review_state"],
                "authority_effect": "none",
            }
            for item in relationships
        ),
        key=lambda item: item["relationship_id"],
    )
    projected_entity = {
        "entity_id": canonical_id,
        "label": entity["label"],
        "type": explanation["subject_type"],
        "summary": explanation["summary"],
        "classification": entity["classification"],
    }
    confidence = [
        {
            "subject_ref": canonical_id,
            "value": explanation["confidence"],
            "basis": "deterministic_explanation",
        }
    ]
    confidence.extend(
        {
            "subject_ref": item["evidence_id"],
            "value": item["confidence"],
            "basis": "evidence_package",
        }
        for item in evidence_summary
    )
    review_state = [
        {"subject_ref": canonical_id, "state": explanation["review_state"]}
    ]
    review_state.extend(
        {"subject_ref": item["evidence_id"], "state": item["review_state"]}
        for item in evidence_summary
    )
    package = {
        "schema_version": 1,
        "context_id": f"ai-context-package:{_safe_id(canonical_id)}",
        "created_at": active["contract_created_at"],
        "purpose": "explain_entity",
        "entities": [projected_entity],
        "relationships": projected_relationships,
        "evidence_summary": evidence_summary,
        "confidence": confidence,
        "uncertainties": sorted(set(explanation["uncertainties"])),
        "authority_context": [
            {
                "subject_ref": canonical_id,
                "role": explanation["authority_context"]["role"],
                "scope": explanation["authority_context"]["scope"],
                "basis": explanation["authority_context"]["basis"],
            }
        ],
        "review_state": review_state,
        "capabilities": sorted(active["capabilities"]),
        "actions": [],
        "restrictions": sorted(active["restrictions"]),
        "raw_observations_included": False,
        "action_authority": "none",
    }
    errors = ai_context_package_errors(package, active)
    if errors:
        raise AIContextBoundaryError(errors[0])
    return package


def local_model_request_errors(
    request: dict[str, Any],
    context: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> list[str]:
    errors = _validate_schema(request, REQUEST_SCHEMA_PATH)
    if errors:
        return errors
    active = policy or load_local_model_boundary_policy()
    errors.extend(_reject_unsafe(request))
    if errors:
        return errors
    if request["context_package_id"] != context["context_id"]:
        errors.append("local-model request must reference its validated context package")
    if request["task"] not in active["tasks"]:
        errors.append("only explain is supported")
    if set(request["capabilities"]) != set(context["capabilities"]):
        errors.append("request capabilities must match the context package")
    if request["actions"] or request["action_authority"] != "none":
        errors.append("local-model requests cannot expose actions")
    if request["connector_state"] != "not_connected" or request["execution_state"] != "not_executed":
        errors.append("the local-model request is a contract and cannot execute")
    model = active["model_contract"]
    if request["runtime"] != model["runtime"] or request["model"] != model["model"]:
        errors.append("request model identity does not match the approved contract")
    return errors


def build_local_model_request(
    context: dict[str, Any], policy: dict[str, Any] | None = None
) -> dict[str, Any]:
    active = policy or load_local_model_boundary_policy()
    context_failures = ai_context_package_errors(context, active)
    if context_failures:
        raise AIContextBoundaryError(context_failures[0])
    suffix = context["context_id"].removeprefix("ai-context-package:")
    request = {
        "schema_version": 1,
        "request_id": f"local-model-request:{suffix}",
        "context_package_id": context["context_id"],
        "runtime": active["model_contract"]["runtime"],
        "model": active["model_contract"]["model"],
        "task": "explain",
        "capabilities": deepcopy(context["capabilities"]),
        "actions": [],
        "connector_state": "not_connected",
        "execution_state": "not_executed",
        "action_authority": "none",
    }
    errors = local_model_request_errors(request, context, active)
    if errors:
        raise AIContextBoundaryError(errors[0])
    return request


def _weakest_confidence(refs: list[str], evidence: dict[str, dict[str, Any]]) -> str:
    return max(
        (evidence[ref]["confidence"] for ref in refs),
        key=lambda value: CONFIDENCE_RANK[value],
    )


def local_model_response_errors(
    response: dict[str, Any],
    request: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    errors = _validate_schema(response, RESPONSE_SCHEMA_PATH)
    if errors:
        return errors
    errors.extend(_reject_unsafe(response))
    if errors:
        return errors
    if response["request_id"] != request["request_id"]:
        errors.append("response request identity does not match")
    if response["context_id"] != context["context_id"]:
        errors.append("response context identity does not match")
    if response["task"] != request["task"] or response["task"] != "explain":
        errors.append("response task must remain explain")
    if response["confidence"] != context["confidence"]:
        errors.append("response did not preserve context confidence")
    if response["uncertainties"] != context["uncertainties"]:
        errors.append("response did not preserve all context uncertainty")
    if response["authority_context"] != context["authority_context"]:
        errors.append("response invented or changed authority")
    if response["review_state"] != context["review_state"]:
        errors.append("response did not preserve review state")
    if any(
        response[key]
        for key in (
            "requested_actions",
            "recommendations",
            "permissions_claimed",
            "access_claims",
        )
    ):
        errors.append("explanation responses cannot request actions, recommend changes, or claim access")
    if response["authority_effect"] != "none":
        errors.append("response cannot create authority")

    evidence = {item["evidence_id"]: item for item in context["evidence_summary"]}
    known_statements = {item["summary"] for item in context["entities"]}
    unknown_statements = set(context["uncertainties"])
    seen_types: set[str] = set()
    seen_known_statements: set[str] = set()
    seen_evidence_ids: set[str] = set()
    seen_unknown_statements: set[str] = set()
    for claim in response["claims"]:
        seen_types.add(claim["claim_type"])
        statement = claim["statement"]
        refs = claim["evidence_refs"]
        unknown_refs = set(refs) - set(evidence)
        if unknown_refs:
            errors.append(f"{claim['claim_id']}: unsupported evidence reference")
            continue
        if ACTION_LANGUAGE.search(statement):
            errors.append(f"{claim['claim_id']}: action instruction is forbidden")
        if ACCESS_LANGUAGE.search(statement):
            errors.append(f"{claim['claim_id']}: invented access is forbidden")
        if CANONICAL_ASSERTION.search(statement) and not any(
            item["role"] == "canonical" for item in context["authority_context"]
        ):
            errors.append(f"{claim['claim_id']}: invented canonical authority")

        if claim["claim_type"] == "known":
            if statement not in known_statements:
                errors.append(f"{claim['claim_id']}: unsupported known claim")
            else:
                seen_known_statements.add(statement)
            if not refs:
                errors.append(f"{claim['claim_id']}: known claim requires evidence")
        elif claim["claim_type"] == "evidence":
            matching = [item for item in evidence.values() if item["claim"] == statement]
            if len(matching) != 1:
                errors.append(f"{claim['claim_id']}: unsupported evidence claim")
            elif refs != [matching[0]["evidence_id"]]:
                errors.append(f"{claim['claim_id']}: evidence claim citation mismatch")
            elif claim["confidence"] != matching[0]["confidence"]:
                errors.append(f"{claim['claim_id']}: evidence confidence changed")
            else:
                seen_evidence_ids.add(matching[0]["evidence_id"])
        elif claim["claim_type"] == "unknown":
            if statement not in unknown_statements:
                errors.append(f"{claim['claim_id']}: unsupported uncertainty")
            else:
                seen_unknown_statements.add(statement)
            if refs or claim["confidence"] != "unknown":
                errors.append(f"{claim['claim_id']}: unknown claims cannot assert evidence or confidence")

        if refs:
            weakest = _weakest_confidence(refs, evidence)
            if CONFIDENCE_RANK[claim["confidence"]] < CONFIDENCE_RANK[weakest]:
                errors.append(f"{claim['claim_id']}: confidence inflation")
    if seen_types != {"known", "evidence", "unknown"}:
        errors.append("an explanation must include known, evidence, and unknown claim sections")
    if seen_known_statements != known_statements:
        errors.append("response omitted required known context")
    if seen_evidence_ids != set(evidence):
        errors.append("response omitted required evidence")
    if seen_unknown_statements != unknown_statements:
        errors.append("response omitted required uncertainty")
    return sorted(set(errors))


def build_synthetic_local_model_response(
    context: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Build a deterministic test candidate; this does not invoke a model."""

    context_failures = ai_context_package_errors(context)
    if context_failures:
        raise AIContextBoundaryError(context_failures[0])
    request_failures = local_model_request_errors(request, context)
    if request_failures:
        raise AIContextBoundaryError(request_failures[0])
    evidence = {item["evidence_id"]: item for item in context["evidence_summary"]}
    evidence_ids = sorted(evidence)
    if not evidence_ids:
        raise AIContextBoundaryError("a synthetic explanation requires evidence")
    weakest = _weakest_confidence(evidence_ids, evidence)
    claims = [
        {
            "claim_id": "local-claim:known-entity",
            "claim_type": "known",
            "statement": context["entities"][0]["summary"],
            "evidence_refs": evidence_ids,
            "confidence": weakest,
        }
    ]
    claims.extend(
        {
            "claim_id": f"local-claim:evidence-{index}",
            "claim_type": "evidence",
            "statement": item["claim"],
            "evidence_refs": [item["evidence_id"]],
            "confidence": item["confidence"],
        }
        for index, item in enumerate(context["evidence_summary"], start=1)
    )
    claims.extend(
        {
            "claim_id": f"local-claim:unknown-{index}",
            "claim_type": "unknown",
            "statement": uncertainty,
            "evidence_refs": [],
            "confidence": "unknown",
        }
        for index, uncertainty in enumerate(context["uncertainties"], start=1)
    )
    suffix = request["request_id"].removeprefix("local-model-request:")
    return {
        "schema_version": 1,
        "response_id": f"local-model-response:{suffix}",
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "task": "explain",
        "claims": claims,
        "confidence": deepcopy(context["confidence"]),
        "uncertainties": deepcopy(context["uncertainties"]),
        "authority_context": deepcopy(context["authority_context"]),
        "review_state": deepcopy(context["review_state"]),
        "requested_actions": [],
        "recommendations": [],
        "permissions_claimed": [],
        "access_claims": [],
        "authority_effect": "none",
        "validation_state": "candidate_not_executed",
    }


def ai_response_validation_errors(record: dict[str, Any]) -> list[str]:
    errors = _validate_schema(record, VALIDATION_SCHEMA_PATH)
    if errors:
        return errors
    if (record["validation_result"] == "pass") != (record["violations"] == []):
        return ["validation result and violation list disagree"]
    if record["execution_state"] != "not_executed" or record["persisted"]:
        return ["response validation cannot execute or persist"]
    return []


def validate_ai_response(
    response: dict[str, Any],
    request: dict[str, Any],
    context: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_local_model_boundary_policy()
    context_failures = ai_context_package_errors(context, active)
    if context_failures:
        raise AIContextBoundaryError(context_failures[0])
    request_failures = local_model_request_errors(request, context, active)
    if request_failures:
        raise AIContextBoundaryError(request_failures[0])
    violations = local_model_response_errors(response, request, context)
    suffix = request["request_id"].removeprefix("local-model-request:")
    record = {
        "schema_version": 1,
        "validation_id": f"ai-response-validation:{suffix}",
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "model": active["model_contract"]["model"],
        "task": request["task"],
        "validation_result": "rejected" if violations else "pass",
        "violations": violations,
        "created_at": active["contract_created_at"],
        "execution_state": "not_executed",
        "persisted": False,
        "action_authority": "none",
    }
    record_errors = ai_response_validation_errors(record)
    if record_errors:
        raise AIContextBoundaryError(record_errors[0])
    return record


def local_model_audit_errors(record: dict[str, Any]) -> list[str]:
    errors = _validate_schema(record, AUDIT_SCHEMA_PATH)
    if errors:
        return errors
    if record["execution_state"] != "not_executed" or record["persisted"]:
        return ["local-model audit contract cannot execute or persist"]
    if record["action_authority"] != "none":
        return ["local-model audit contract cannot grant action authority"]
    return []


def build_local_model_audit(validation: dict[str, Any]) -> dict[str, Any]:
    validation_errors = ai_response_validation_errors(validation)
    if validation_errors:
        raise AIContextBoundaryError(validation_errors[0])
    record = {
        "schema_version": 1,
        "request_id": validation["request_id"],
        "context_id": validation["context_id"],
        "model": validation["model"],
        "task": validation["task"],
        "validation_result": validation["validation_result"],
        "created_at": validation["created_at"],
        "execution_state": "not_executed",
        "persisted": False,
        "action_authority": "none",
    }
    errors = local_model_audit_errors(record)
    if errors:
        raise AIContextBoundaryError(errors[0])
    return record


def synthetic_local_model_boundary_bundle() -> dict[str, Any]:
    policy = load_local_model_boundary_policy()
    context = build_ai_context(
        "application-concept:grade-4-writing-launcher", policy=policy
    )
    request = build_local_model_request(context, policy)
    response = build_synthetic_local_model_response(context, request)
    validation = validate_ai_response(response, request, context, policy)
    audit = build_local_model_audit(validation)
    return {
        "policy": policy,
        "context": context,
        "request": request,
        "response": response,
        "validation": validation,
        "audit": audit,
    }
