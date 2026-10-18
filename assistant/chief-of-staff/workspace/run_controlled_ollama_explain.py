#!/usr/bin/env python3
"""Run the one approved Phase L.5E Writing explanation without persistence."""

from __future__ import annotations

import json
import sys

from ai_context_adapter import build_ai_context, build_local_model_request
from ollama_runtime import (
    build_runtime_audit,
    execute_local_explanation,
    load_runtime_policy,
    preflight_ollama,
)


APPROVED_ENTITY = "application:grade-4-writing-launcher"


def semantic_summary(context: dict) -> dict:
    entity = context["entities"][0]
    entity_id = entity["entity_id"]
    confidence = next(
        item["value"] for item in context["confidence"]
        if item["subject_ref"] == entity_id
    )
    review_state = next(
        item["state"] for item in context["review_state"]
        if item["subject_ref"] == entity_id
    )
    return {
        "entity_id": entity_id,
        "label": entity["label"],
        "type": entity["type"],
        "evidence_summary_count": len(context["evidence_summary"]),
        "relationship_count": len(context["relationships"]),
        "confidence": confidence,
        "uncertainty_count": len(context["uncertainties"]),
        "authority": context["authority_context"][0]["role"],
        "review_state": review_state,
        "capabilities": context["capabilities"],
        "actions": context["actions"],
        "action_authority": context["action_authority"],
        "raw_observations_included": context["raw_observations_included"],
    }


def main() -> int:
    policy = load_runtime_policy()
    context = build_ai_context(APPROVED_ENTITY)
    request = build_local_model_request(context)
    preflight = preflight_ollama(policy=policy)
    if preflight["status"] != "available":
        print(json.dumps({
            "context_summary": semantic_summary(context),
            "preflight": preflight,
            "execution": "not_attempted",
            "audit": "not_created",
        }, indent=2, sort_keys=True))
        return 1
    result = execute_local_explanation(
        context,
        request,
        preflight=preflight,
        policy=policy,
    )
    audit = build_runtime_audit(result)
    print(json.dumps({
        "context_summary": semantic_summary(context),
        "preflight": preflight,
        "result": result,
        "audit": audit,
    }, indent=2, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    sys.exit(main())
