"""Pure Phase L AI-readiness contracts; no model, network, agent, or action runtime."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_compatibility import (
    AIProjectionError,
    ai_view_errors,
    load_ai_policy,
    project_ai_compatibility_view,
    reject_forbidden_ai_input,
    synthetic_internal_model,
)
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/ai-readiness.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/ai-readiness.schema.json"
CONTEXT_SCHEMA_PATH = ROOT / "schemas/ai-context-projection.schema.json"
PROMPT_SCHEMA_PATH = ROOT / "schemas/ai-prompt-envelope.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas/ai-output-candidate.schema.json"
AUDIT_SCHEMA_PATH = ROOT / "schemas/ai-interaction-audit.schema.json"
AGENT_GRANT_SCHEMA_PATH = ROOT / "schemas/agent-capability-grant.schema.json"

REASONING_CAPABILITIES = {
    "summarize", "explain", "compare", "prioritize", "draft", "plan", "identify_patterns"
}
RESTRICTED_CAPABILITIES = {
    "modify", "delete", "restore", "move", "replace", "approve_authority", "change_permissions"
}
CLAIM_TYPES = {"known", "evidence", "inference", "unknown", "recommendation"}
REJECTION_RULES = {
    "unsupported_claim", "authority_change", "hidden_action", "confidence_inflation",
    "missing_uncertainty", "uncited_known_claim",
}
TRUST_LEVELS = {
    0: ("No AI", "current"),
    1: ("Explanation Assistance", "planned"),
    2: ("Planning Assistance", "planned"),
    3: ("Scoped Agent Assistance", "future_only"),
    4: ("Autonomous Operations", "prohibited"),
}
CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2, "unknown": 3}
CLASSIFICATION_RANK = {"public": 0, "student_safe": 1, "teacher_internal": 2}
ACTION_LANGUAGE = re.compile(
    r"\b(delete|restore|move|modify|replace|approve authority|change permissions)\b",
    re.IGNORECASE,
)


class AIReadinessError(ValueError):
    """Raised when an architecture-only AI boundary contract fails closed."""


def ai_readiness_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(policy["capabilities"]["reasoning"]) != REASONING_CAPABILITIES:
        errors.append("Phase L reasoning capability set is incomplete")
    if set(policy["capabilities"]["restricted"]) != RESTRICTED_CAPABILITIES:
        errors.append("Phase L restricted capability set is incomplete")
    levels = {item["level"]: item for item in policy["trust_levels"]}
    if set(levels) != set(TRUST_LEVELS):
        errors.append("AI trust levels must be exactly 0 through 4")
    else:
        for level, (name, state) in TRUST_LEVELS.items():
            if levels[level]["name"] != name or levels[level]["state"] != state:
                errors.append(f"AI trust level {level} identity or state is invalid")
        if levels[0]["allowed_capabilities"]:
            errors.append("AI trust level 0 cannot allow AI capabilities")
        if set(levels[1]["allowed_capabilities"]) != {"summarize", "explain", "compare"}:
            errors.append("AI trust level 1 capability boundary is invalid")
        if set(levels[2]["allowed_capabilities"]) != REASONING_CAPABILITIES:
            errors.append("AI trust level 2 capability boundary is invalid")
        if levels[3]["allowed_capabilities"] or levels[4]["allowed_capabilities"]:
            errors.append("future agent and autonomous levels cannot grant capabilities in Phase L")
    if any(policy["runtime"].values()):
        errors.append("all Phase L AI, network, agent, export, audit-log, and action runtimes must remain disabled")
    if not policy["routing"]["deterministic_first"]:
        errors.append("model routing must prefer deterministic Chief of Staff answers")
    if policy["routing"]["approved_models"] or policy["routing"]["provider_selection"] != "unselected":
        errors.append("Phase L cannot select or approve a model")
    if set(policy["output_validation"]["claim_types"]) != CLAIM_TYPES:
        errors.append("output claim distinctions are incomplete")
    if set(policy["output_validation"]["rejection_rules"]) != REJECTION_RULES:
        errors.append("output rejection rules are incomplete")
    if policy["hallucination_handling"]["inference_may_become_fact"]:
        errors.append("inference cannot be converted into fact")
    if policy["human_approval"]["approval_runtime_enabled"]:
        errors.append("human approval architecture cannot enable an approval runtime")
    if policy["future_agent"]["runtime_enabled"] or policy["future_agent"]["autonomous_operations_allowed"]:
        errors.append("agent and autonomous operation runtimes must remain disabled")
    return errors


def load_ai_readiness_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = ai_readiness_policy_errors(policy)
    if errors:
        raise AIReadinessError(errors[0])
    return policy


def route_request(
    *,
    deterministic_answer_available: bool,
    context_projection_available: bool,
    trust_level: int,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_ai_readiness_policy()
    if trust_level not in TRUST_LEVELS:
        raise AIReadinessError("unknown AI trust level")
    if deterministic_answer_available:
        return {
            "route": "deterministic_explanation",
            "reason": "Chief of Staff can answer from approved deterministic evidence.",
            "ai_requested": False,
            "model": "none",
            "action_authority": "none",
        }
    if trust_level == 0:
        return {
            "route": "ai_unavailable",
            "reason": "Trust level 0 permits deterministic Chief of Staff only.",
            "ai_requested": False,
            "model": "none",
            "action_authority": "none",
        }
    if not context_projection_available:
        return {
            "route": "context_projection_required",
            "reason": "AI escalation cannot occur without an approved context projection.",
            "ai_requested": False,
            "model": "none",
            "action_authority": "none",
        }
    if (
        not active["runtime"]["ai_enabled"]
        or not active["runtime"]["model_connection_enabled"]
        or not active["routing"]["approved_models"]
    ):
        return {
            "route": "ai_runtime_disabled",
            "reason": "Architecture is defined, but no AI runtime or approved model exists.",
            "ai_requested": False,
            "model": "none",
            "action_authority": "none",
        }
    raise AIReadinessError("Phase L cannot route to a model")


def context_projection_errors(
    projection: dict[str, Any], policy: dict[str, Any] | None = None
) -> list[str]:
    try:
        validate_schema(projection, load_json(CONTEXT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    active = policy or load_ai_readiness_policy()
    try:
        reject_forbidden_ai_input(projection, load_ai_policy())
    except AIProjectionError as exc:
        return [str(exc)]
    if not active["context_projection"]["sanitization_required"]:
        return ["context sanitization must be required"]
    if projection["raw_observations_included"] or projection["action_capabilities"]:
        return ["context projections cannot contain raw observations or actions"]
    evidence_ids = {
        item.get("evidence_package_id") for item in projection["evidence"]
    }
    if None in evidence_ids or len(evidence_ids) != len(projection["evidence"]):
        return ["every projected evidence item requires a unique package identity"]
    if any(item.get("authority_effect") != "none" for item in projection["evidence"]):
        return ["projected evidence cannot create authority"]
    return []


def build_context_projection(
    internal: dict[str, Any],
    *,
    destination: str,
    projection_id: str = "ai-context:synthetic-readiness",
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_ai_readiness_policy()
    if destination not in {"local", "cloud"}:
        raise AIReadinessError("AI context destination must be local or cloud")
    view = project_ai_compatibility_view(internal)
    view_failures = ai_view_errors(view)
    if view_failures:
        raise AIReadinessError(view_failures[0])
    confidences = [item["confidence"] for item in view["entities"]]
    confidences.extend(item["confidence"] for item in view["evidence_summaries"])
    classifications = [item["classification"] for item in view["entities"]]
    projection = {
        "schema_version": 1,
        "projection_id": projection_id,
        "destination": destination,
        "source_view_id": view["view_id"],
        "identity": [
            {
                "entity_id": item["entity_id"],
                "label": item["label"],
                "type": item["type"],
                "classification": item["classification"],
                "confidence": item["confidence"],
                "review_state": item["review_state"],
                "authority": item["authority"],
            }
            for item in view["entities"]
        ],
        "sources": sorted(view["generated_from_refs"]),
        "evidence": sorted(
            view["evidence_summaries"], key=lambda item: item["evidence_package_id"]
        ),
        "relationships": sorted(
            view["relationships"],
            key=lambda item: (item["relationship_type"], item["source_ref"], item["target_ref"]),
        ),
        "confidence": max(confidences, key=lambda item: CONFIDENCE_RANK[item]),
        "uncertainties": sorted({
            unknown
            for item in view["evidence_summaries"]
            for unknown in item["uncertainty"]
        }),
        "authority_states": sorted({item["authority"] for item in view["entities"]}),
        "review_states": sorted({item["review_state"] for item in view["entities"]}),
        "input_classification": max(
            classifications, key=lambda item: CLASSIFICATION_RANK[item]
        ),
        "raw_observations_included": False,
        "action_capabilities": [],
    }
    errors = context_projection_errors(projection, active)
    if errors:
        raise AIReadinessError(errors[0])
    return projection


def prompt_envelope_errors(
    envelope: dict[str, Any],
    projection: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> list[str]:
    try:
        validate_schema(envelope, load_json(PROMPT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    active = policy or load_ai_readiness_policy()
    try:
        reject_forbidden_ai_input(envelope, load_ai_policy())
    except AIProjectionError as exc:
        return [str(exc)]
    if envelope["evidence_context"]["projection_id"] != projection["projection_id"]:
        return ["prompt evidence context does not reference its approved projection"]
    levels = {item["level"]: item for item in active["trust_levels"]}
    allowed = set(levels[envelope["trust_level"]]["allowed_capabilities"])
    if not set(envelope["capabilities_granted"]) <= allowed:
        return ["prompt grants a capability outside its trust level"]
    if set(envelope["capabilities_granted"]) & RESTRICTED_CAPABILITIES:
        return ["prompt cannot grant restricted action capabilities"]
    if envelope["runtime_state"] != "not_connected" or envelope["action_authority"] != "none":
        return ["prompt boundary cannot connect a runtime or create action authority"]
    return []


def build_prompt_envelope(
    projection: dict[str, Any],
    user_request: str,
    *,
    trust_level: int = 1,
    prompt_id: str = "ai-prompt:synthetic-readiness",
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_ai_readiness_policy()
    if trust_level not in {1, 2}:
        raise AIReadinessError("prompt architecture supports planned trust levels 1 and 2 only")
    levels = {item["level"]: item for item in active["trust_levels"]}
    envelope = {
        "schema_version": 1,
        "prompt_id": prompt_id,
        "trust_level": trust_level,
        "system_context": {
            "role": "non_authoritative_reasoning_assistant",
            "restrictions": [
                "Use only the projected evidence context.",
                "Do not execute or request filesystem actions.",
                "Do not infer or change authority.",
            ],
            "authority_boundaries": [
                "Chief of Staff evidence and authority state remain controlling.",
                "Human approval is required for authority, recovery, deletion, movement, permission, and cloud export decisions.",
            ],
        },
        "evidence_context": {
            "projection_id": projection["projection_id"],
            "facts": sorted(item["claim"] for item in projection["evidence"]),
            "provenance": sorted(
                item["evidence_package_id"] for item in projection["evidence"]
            ),
            "confidence": projection["confidence"],
            "uncertainty": projection["uncertainties"],
        },
        "user_request": user_request,
        "required_output": {
            "distinguish_claim_types": True,
            "cite_evidence": True,
            "expose_uncertainty": True,
            "avoid_unsupported_assumptions": True,
        },
        "capabilities_granted": sorted(levels[trust_level]["allowed_capabilities"]),
        "runtime_state": "not_connected",
        "action_authority": "none",
    }
    errors = prompt_envelope_errors(envelope, projection, active)
    if errors:
        raise AIReadinessError(errors[0])
    return envelope


def ai_output_candidate_errors(
    output: dict[str, Any], projection: dict[str, Any]
) -> list[str]:
    try:
        validate_schema(output, load_json(OUTPUT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    try:
        reject_forbidden_ai_input(output, load_ai_policy())
    except AIProjectionError as exc:
        return [str(exc)]
    errors: list[str] = []
    evidence = {
        item["evidence_package_id"]: item for item in projection["evidence"]
    }
    for claim in output["claims"]:
        refs = claim["evidence_refs"]
        unknown_refs = sorted(set(refs) - set(evidence))
        if unknown_refs:
            errors.append(f"{claim['claim_id']}: unsupported evidence reference")
            continue
        if claim["claim_type"] != "unknown" and not refs:
            errors.append(f"{claim['claim_id']}: supported claim requires evidence citation")
        if refs:
            weakest = max(
                (evidence[ref]["confidence"] for ref in refs),
                key=lambda value: CONFIDENCE_RANK[value],
            )
            if CONFIDENCE_RANK[claim["confidence"]] < CONFIDENCE_RANK[weakest]:
                errors.append(f"{claim['claim_id']}: confidence inflation")
        if ACTION_LANGUAGE.search(claim["statement"]):
            errors.append(f"{claim['claim_id']}: hidden action language")
    if output["authority_effect"] != "none":
        errors.append("AI output cannot change authority")
    if output["requested_actions"]:
        errors.append("AI output cannot request actions")
    if not output["uncertainties"]:
        errors.append("AI output must preserve uncertainty")
    return errors


def build_synthetic_ai_output(projection: dict[str, Any]) -> dict[str, Any]:
    evidence = projection["evidence"][0]
    return {
        "schema_version": 1,
        "response_id": "ai-response:synthetic-readiness",
        "claims": [
            {
                "claim_id": "claim:synthetic-known",
                "statement": evidence["claim"],
                "claim_type": "known",
                "evidence_refs": [evidence["evidence_package_id"]],
                "confidence": evidence["confidence"],
            },
            {
                "claim_id": "claim:synthetic-unknown",
                "statement": "Authority remains unknown.",
                "claim_type": "unknown",
                "evidence_refs": [],
                "confidence": "unknown",
            },
        ],
        "uncertainties": projection["uncertainties"],
        "requested_actions": [],
        "authority_effect": "none",
        "validation_state": "candidate_not_executed",
    }


def audit_record_errors(record: dict[str, Any]) -> list[str]:
    try:
        validate_schema(record, load_json(AUDIT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if record["persisted"] or record["execution_state"] != "not_executed":
        return ["Phase L audit examples cannot be persisted or executed"]
    return []


def build_synthetic_audit_record(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": "ai-request:synthetic-readiness",
        "model": "unselected",
        "context_projection_id": projection["projection_id"],
        "trust_level": 1,
        "capabilities_granted": ["explain", "summarize"],
        "input_classification": projection["input_classification"],
        "output_validation": "pass",
        "human_review": "required",
        "execution_state": "not_executed",
        "persisted": False,
        "action_authority": "none",
    }


def agent_grant_errors(grant: dict[str, Any]) -> list[str]:
    try:
        validate_schema(grant, load_json(AGENT_GRANT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if not grant["target_scope"] or not grant["rollback_plan"]:
        return ["future agent grants require a target scope and rollback plan"]
    if not grant["duration"]["starts_at"] or not grant["duration"]["expires_at"]:
        return ["future agent grants require a bounded duration"]
    if grant["execution_enabled"] or grant["autonomous"]:
        return ["Phase L cannot enable agent execution or autonomy"]
    if grant["action_authority"] != "none":
        return ["an architecture-only grant cannot create action authority"]
    return []


def build_synthetic_agent_grant() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "grant_id": "agent-grant:synthetic-readiness",
        "agent_id": "future-agent:unconnected",
        "allowed_action": "restore",
        "target_scope": "resource:synthetic-only",
        "duration": {
            "starts_at": "not_scheduled",
            "expires_at": "not_scheduled",
        },
        "approval": {
            "required": True,
            "state": "not_requested",
            "approved_by": None,
        },
        "rollback_plan": "A separately approved future architecture must define rollback before execution.",
        "audit_required": True,
        "grant_state": "architecture_only",
        "execution_enabled": False,
        "autonomous": False,
        "action_authority": "none",
    }


def synthetic_readiness_bundle() -> dict[str, Any]:
    policy = load_ai_readiness_policy()
    internal = synthetic_internal_model()
    projection = build_context_projection(internal, destination="cloud", policy=policy)
    prompt = build_prompt_envelope(
        projection,
        "Explain the evidence-backed application and project relationship.",
        policy=policy,
    )
    output = build_synthetic_ai_output(projection)
    audit = build_synthetic_audit_record(projection)
    grant = build_synthetic_agent_grant()
    return {
        "policy": policy,
        "projection": projection,
        "prompt": prompt,
        "output": output,
        "audit": audit,
        "agent_grant": grant,
    }
