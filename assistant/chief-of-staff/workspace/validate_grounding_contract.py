#!/usr/bin/env python3
"""Validate Phase L.5F without contacting Ollama or any network service."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass

from ai_context_adapter import synthetic_local_model_boundary_bundle
from grounding_contract import (
    CONTRACT_METADATA,
    GROUNDING_VIOLATION_CODES,
    RESPONSE_V2_SCHEMA_PATH,
    build_ideal_response_v2,
    build_response_vocabulary,
    prompt_schema_consistency_errors,
    prompt_vocabulary,
    render_validated_explanation_v2,
    validate_grounding_response_v2,
)
from ollama_runtime import build_ollama_payload, load_runtime_policy
from validate import load_json, validate_schema


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def check(condition: bool, code: str, message: str) -> Check:
    return Check("PASS" if condition else "FAIL", code, message)


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["violations"]}


def main() -> int:
    bundle = synthetic_local_model_boundary_bundle()
    context = bundle["context"]
    request = bundle["request"]
    ideal = build_ideal_response_v2(context, request)
    vocabulary = build_response_vocabulary(context, request)
    accepted = validate_grounding_response_v2(ideal, request, context)
    rendered = render_validated_explanation_v2(ideal, request, context)
    schema = load_json(RESPONSE_V2_SCHEMA_PATH)
    validate_schema(ideal, schema)
    payload = build_ollama_payload(context, request, load_runtime_policy())

    missing_evidence = copy.deepcopy(ideal)
    missing_evidence["evidence_refs"].pop()
    evidence_result = validate_grounding_response_v2(
        missing_evidence, request, context
    )
    missing_uncertainty = copy.deepcopy(ideal)
    missing_uncertainty["uncertainty_refs"].pop()
    uncertainty_result = validate_grounding_response_v2(
        missing_uncertainty, request, context
    )
    authority = copy.deepcopy(ideal)
    authority["authority"] = "canonical"
    authority_result = validate_grounding_response_v2(authority, request, context)
    recommendation = copy.deepcopy(ideal)
    recommendation["recommendations"] = ["unsafe rejected content"]
    recommendation_result = validate_grounding_response_v2(
        recommendation, request, context
    )
    duplicate = copy.deepcopy(ideal)
    duplicate["known_refs"].append(duplicate["known_refs"][0])
    duplicate_result = validate_grounding_response_v2(duplicate, request, context)
    diagnostic_text = json.dumps(recommendation_result, sort_keys=True)

    checks = [
        check(bundle["response"]["schema_version"] == 1 and ideal["schema_version"] == 2,
              "grounding.versioning", "v1 prose and v2 reference contracts remain distinct"),
        check(vocabulary["contract_id"] == "local-model-response.v2",
              "grounding.vocabulary", "stable response vocabulary is explicit"),
        check(CONTRACT_METADATA["known_refs"] == "exactly_all_supplied" and
              CONTRACT_METADATA["evidence_refs"] == "exactly_all_supplied" and
              CONTRACT_METADATA["uncertainty_refs"] == "exactly_all_supplied",
              "grounding.cardinality", "known, evidence, and uncertainty refs require exact coverage"),
        check(CONTRACT_METADATA["relationship_refs"] == "exactly_zero",
              "grounding.relationships", "relationship generation is excluded"),
        check(accepted["accepted"] and not accepted["violations"],
              "grounding.ideal", "ideal deterministic v2 response passes"),
        check("EVIDENCE_CLAIM_MISSING" in codes(evidence_result) and
              "EVIDENCE_COUNT_MISMATCH" in codes(evidence_result),
              "grounding.evidence", "missing evidence has stable safe diagnostics"),
        check("UNCERTAINTY_MISSING" in codes(uncertainty_result) and
              "UNCERTAINTY_COUNT_MISMATCH" in codes(uncertainty_result),
              "grounding.uncertainty", "missing uncertainty has stable safe diagnostics"),
        check(authority_result["failure_category"] == "authority_violation" and
              "AUTHORITY_CHANGED" in codes(authority_result),
              "grounding.authority", "authority remains exact and non-generative"),
        check(recommendation_result["failure_category"] == "capability_violation" and
              "RECOMMENDATION_CONTENT_PRESENT" in codes(recommendation_result),
              "grounding.capability", "recommendations remain forbidden"),
        check("DUPLICATE_REFERENCE" in codes(duplicate_result),
              "grounding.duplicates", "duplicate reference IDs fail closed"),
        check("unsafe rejected content" not in diagnostic_text and
              not recommendation_result["raw_response_retained"] and
              not recommendation_result["persisted"],
              "grounding.diagnostic_safety", "diagnostics retain structure, never rejected prose"),
        check(codes(recommendation_result) <= GROUNDING_VIOLATION_CODES,
              "grounding.code_set", "diagnostic codes come from the finite approved set"),
        check(not prompt_schema_consistency_errors(),
              "grounding.prompt_schema", "prompt, schema, cardinality, and validator agree"),
        check(payload["format"]["properties"]["schema_version"] == {"const": 2} and
              "allowed_response_vocabulary" in json.loads(payload["messages"][1]["content"])["response_contract"],
              "grounding.future_payload", "future payload is pinned to v2 and its allowed vocabulary"),
        check(not any(key.startswith("_") for key in prompt_vocabulary(vocabulary)),
              "grounding.prompt_projection", "private renderer maps do not enter the prompt"),
        check(rendered.startswith("Subject: Grade 4 Writing Launcher") and
              context["entities"][0]["summary"] in rendered,
              "grounding.renderer", "deterministic renderer uses validated context facts"),
        check(ideal["actions"] == ideal["recommendations"] == ideal["permissions"] ==
              ideal["access_claims"] == [] and ideal["action_authority"] == "none",
              "grounding.no_actions", "v2 grants no actions, permissions, recommendations, or access"),
        check(payload["stream"] is False and payload["think"] is False and
              "tools" not in payload and "images" not in payload,
              "grounding.runtime_boundary", "future payload retains no-tool and no-thinking-output boundary"),
    ]
    for item in checks:
        print(f"{item.level}: {item.code}: {item.message}")
    totals = {level: sum(item.level == level for item in checks) for level in ("PASS", "WARN", "FAIL")}
    print(f"Summary: PASS={totals['PASS']} WARN={totals['WARN']} FAIL={totals['FAIL']}")
    return 1 if totals["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
