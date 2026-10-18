"""Deterministic Phase L.5G gates and safe result finalization.

This module contains no transport. The existing Ollama adapter remains the sole
owner of runtime I/O and its one-attempt policy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_context_adapter import build_ai_context, build_local_model_request
from grounding_contract import (
    build_ideal_response_v2,
    build_response_vocabulary,
    prompt_schema_consistency_errors,
    render_validated_explanation_v2,
    validate_grounding_response_v2,
)
from ollama_runtime import build_ollama_payload, load_runtime_policy, runtime_policy_errors
from validate import load_json, validate_schema


ROOT = Path(__file__).resolve().parent
AUDIT_SCHEMA_PATH = ROOT / "schemas/controlled-execution-audit.schema.json"
APPROVED_ENTITY = "application:grade-4-writing-launcher"


def _semantic_summary(context: dict[str, Any]) -> dict[str, Any]:
    entity = context["entities"][0]
    subject = entity["entity_id"]
    confidence = next(
        item["value"] for item in context["confidence"]
        if item["subject_ref"] == subject
    )
    authority = next(
        item["role"] for item in context["authority_context"]
        if item["subject_ref"] == subject
    )
    review_state = next(
        item["state"] for item in context["review_state"]
        if item["subject_ref"] == subject
    )
    return {
        "identity": subject,
        "label": entity["label"],
        "entity_type": entity["type"],
        "confidence": confidence,
        "authority": authority,
        "review_state": review_state,
        "capabilities": context["capabilities"],
        "actions": context["actions"],
        "action_authority": context["action_authority"],
        "raw_observations_included": context["raw_observations_included"],
    }


def build_pre_live_gate() -> dict[str, Any]:
    """Build and prove the complete deterministic path without runtime I/O."""

    policy = load_runtime_policy()
    policy_errors = runtime_policy_errors(policy)
    context = build_ai_context(APPROVED_ENTITY)
    request = build_local_model_request(context)
    vocabulary = build_response_vocabulary(context, request)
    ideal = build_ideal_response_v2(context, request)
    validation = validate_grounding_response_v2(ideal, request, context)
    rendered = (
        render_validated_explanation_v2(ideal, request, context)
        if validation["accepted"] else ""
    )
    payload = build_ollama_payload(context, request, policy)
    consistency_errors = prompt_schema_consistency_errors()
    errors = list(policy_errors) + list(consistency_errors)
    if not validation["accepted"]:
        errors.append("deterministic ideal v2 response failed grounding validation")
    if not rendered:
        errors.append("deterministic renderer produced no explanation")
    if payload["format"].get("properties", {}).get("schema_version") != {"const": 2}:
        errors.append("future runtime payload is not pinned to response schema v2")
    summary = _semantic_summary(context)
    if summary != {
        "identity": "application-concept:grade-4-writing-launcher",
        "label": "Grade 4 Writing Launcher",
        "entity_type": "application",
        "confidence": "high",
        "authority": "unknown",
        "review_state": "unreviewed",
        "capabilities": ["explain"],
        "actions": [],
        "action_authority": "none",
        "raw_observations_included": False,
    }:
        errors.append("current context semantic boundary differs from approved L.5G target")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "context": context,
        "request": request,
        "vocabulary": vocabulary,
        "ideal_response": ideal,
        "ideal_validation": validation,
        "ideal_rendered_explanation": rendered,
        "context_summary": summary,
        "vocabulary_summary": {
            "known_ref_count": len(vocabulary["known_refs"]),
            "evidence_ref_count": len(vocabulary["evidence_refs"]),
            "uncertainty_ref_count": len(vocabulary["uncertainty_refs"]),
            "relationship_ref_count": len(vocabulary["relationship_refs"]),
            "known_cardinality": "exactly_all_once",
            "evidence_cardinality": "exactly_all_once",
            "uncertainty_cardinality": "exactly_all_once",
            "relationship_cardinality": "exactly_zero",
        },
    }


def build_safe_execution_audit(result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = result.get("grounding_diagnostics", {})
    audit = {
        "audit_schema_version": 1,
        "request_id": result["request_id"],
        "context_id": result["context_id"],
        "runtime": result["runtime"],
        "model": result["model"],
        "task": result["task"],
        "response_schema_version": 2,
        "attempt_count": result["attempt_count"],
        "validation_result": result["validation_result"],
        "failure_category": None if result["failure_code"] == "none" else result["failure_code"],
        "violation_codes": sorted({
            item["code"] for item in diagnostics.get("violations", [])
        }),
        "duration_seconds": round(result["duration_ms"] / 1000, 3),
        "action_authority": "none",
        "raw_response_persisted": False,
        "hidden_reasoning_persisted": False,
        "persisted": False,
    }
    validate_schema(audit, load_json(AUDIT_SCHEMA_PATH))
    return audit


def finalize_execution(
    result: dict[str, Any], context: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Classify one result and render only an accepted v2 reference selection."""

    if result["status"] == "accepted":
        explanation = render_validated_explanation_v2(
            result["validated_response"], request, context
        )
        outcome = "PASS"
    elif result["attempt_count"] == 1:
        explanation = "No trusted explanation produced."
        outcome = "SAFE REJECTION"
    else:
        explanation = "No trusted explanation produced."
        outcome = "PREFLIGHT STOP"
    return {
        "outcome": outcome,
        "explanation": explanation,
        "audit": build_safe_execution_audit(result),
        "execution": {
            "request_id": result["request_id"],
            "context_id": result["context_id"],
            "runtime": result["runtime"],
            "endpoint": result["endpoint"],
            "model": result["model"],
            "task": result["task"],
            "response_schema_version": 2,
            "started_at": result["started_at"],
            "ended_at": result["ended_at"],
            "duration_ms": result["duration_ms"],
            "attempt_count": result["attempt_count"],
            "result": result["status"],
            "failure_category": result["failure_code"],
            "violation_codes": build_safe_execution_audit(result)["violation_codes"],
            "runtime_metrics": result["runtime_metrics"],
            "response_size_bytes": result["response_size_bytes"],
            "retry_used": result["retry_used"],
            "fallback_used": result["fallback_used"],
        },
    }
