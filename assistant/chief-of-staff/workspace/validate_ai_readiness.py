#!/usr/bin/env python3
"""Validate Phase L AI-readiness architecture without connecting an AI runtime."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass

from ai_readiness import (
    CLAIM_TYPES,
    REASONING_CAPABILITIES,
    RESTRICTED_CAPABILITIES,
    agent_grant_errors,
    ai_output_candidate_errors,
    ai_readiness_policy_errors,
    audit_record_errors,
    context_projection_errors,
    prompt_envelope_errors,
    route_request,
    synthetic_readiness_bundle,
)


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _check(condition: bool, code: str, success: str, failure: str) -> Check:
    return Check("PASS" if condition else "FAIL", code, success if condition else failure)


def run_validation() -> list[Check]:
    bundle = synthetic_readiness_bundle()
    policy = bundle["policy"]
    projection = bundle["projection"]
    prompt = bundle["prompt"]
    output = bundle["output"]
    audit = bundle["audit"]
    grant = bundle["agent_grant"]
    checks = [
        _check(
            not ai_readiness_policy_errors(policy),
            "readiness.policy",
            "closed Phase L architecture policy is valid and all runtimes are disabled",
            "AI readiness policy is invalid",
        ),
        _check(
            set(policy["capabilities"]["reasoning"]) == REASONING_CAPABILITIES
            and set(policy["capabilities"]["restricted"]) == RESTRICTED_CAPABILITIES,
            "readiness.capabilities",
            "reasoning capabilities are separated from restricted action capabilities",
            "AI capability separation is incomplete",
        ),
        _check(
            [(item["level"], item["state"]) for item in policy["trust_levels"]]
            == [(0, "current"), (1, "planned"), (2, "planned"), (3, "future_only"), (4, "prohibited")],
            "readiness.trust_levels",
            "trust levels 0–4 are ordered, with only deterministic level 0 current",
            "AI trust-level identity or state is invalid",
        ),
    ]

    deterministic = route_request(
        deterministic_answer_available=True,
        context_projection_available=True,
        trust_level=2,
        policy=policy,
    )
    requires_projection = route_request(
        deterministic_answer_available=False,
        context_projection_available=False,
        trust_level=1,
        policy=policy,
    )
    remains_disabled = route_request(
        deterministic_answer_available=False,
        context_projection_available=True,
        trust_level=1,
        policy=policy,
    )
    checks.extend([
        _check(
            deterministic["route"] == "deterministic_explanation"
            and deterministic["ai_requested"] is False,
            "readiness.deterministic_first",
            "deterministic Chief of Staff answers are always preferred",
            "routing bypassed a deterministic answer",
        ),
        _check(
            requires_projection["route"] == "context_projection_required"
            and remains_disabled["route"] == "ai_runtime_disabled"
            and remains_disabled["model"] == "none",
            "readiness.routing_boundary",
            "AI escalation requires a projection and still stops because no runtime or model exists",
            "AI routing could bypass projection or reach a model",
        ),
        _check(
            policy["model_policy"]["local"]["state"] == "architecture_only"
            and policy["model_policy"]["cloud"]["state"] == "architecture_only"
            and "human_cloud_export_approval" in policy["model_policy"]["cloud"]["requirements"],
            "readiness.model_policy",
            "local and cloud routes are unselected architecture with distinct safety requirements",
            "local/cloud model policy is incomplete",
        ),
        _check(
            not context_projection_errors(projection, policy)
            and projection["raw_observations_included"] is False
            and projection["action_capabilities"] == []
            and "/Users/" not in json.dumps(projection, sort_keys=True),
            "readiness.context_projection",
            "synthetic context contains sanitized identity, evidence, confidence, uncertainty, authority, and review state",
            "context projection is invalid or leaks raw data/actions",
        ),
        _check(
            not prompt_envelope_errors(prompt, projection, policy)
            and prompt["runtime_state"] == "not_connected"
            and prompt["action_authority"] == "none",
            "readiness.prompt_boundary",
            "prompt envelope separates system, evidence, user request, and required output without connection",
            "prompt boundary is invalid or connected",
        ),
        _check(
            not ai_output_candidate_errors(output, projection)
            and set(policy["output_validation"]["claim_types"]) == CLAIM_TYPES,
            "readiness.output_validation",
            "grounded synthetic output preserves claim types, citations, uncertainty, and no-action state",
            "valid grounded output did not pass",
        ),
    ])

    unsupported = copy.deepcopy(output)
    unsupported["claims"][0]["evidence_refs"] = ["evidence-package:not-present"]
    inflated_projection = copy.deepcopy(projection)
    inflated_projection["evidence"][0]["confidence"] = "low"
    inflated = copy.deepcopy(output)
    inflated["claims"][0]["evidence_refs"] = [
        inflated_projection["evidence"][0]["evidence_package_id"]
    ]
    inflated["claims"][0]["confidence"] = "high"
    hidden_action = copy.deepcopy(output)
    hidden_action["claims"][0]["statement"] = "Restore the candidate representation."
    checks.append(_check(
        bool(ai_output_candidate_errors(unsupported, projection))
        and any("confidence inflation" in error for error in ai_output_candidate_errors(inflated, inflated_projection))
        and any("hidden action" in error for error in ai_output_candidate_errors(hidden_action, projection)),
        "readiness.output_rejection",
        "unsupported claims, confidence inflation, and hidden action language fail closed",
        "one or more unsafe AI output patterns passed validation",
    ))

    checks.extend([
        _check(
            policy["hallucination_handling"]["inference_may_become_fact"] is False
            and policy["hallucination_handling"]["unsupported_claim_disposition"] == "reject"
            and policy["hallucination_handling"]["missing_evidence_disposition"] == "mark_unknown",
            "readiness.hallucination",
            "inference stays distinct from fact; unsupported claims reject and missing evidence remains unknown",
            "hallucination handling could promote inference or hide missing evidence",
        ),
        _check(
            not audit_record_errors(audit)
            and audit["persisted"] is False
            and audit["execution_state"] == "not_executed",
            "readiness.audit_contract",
            "future audit contract records model, projection, capabilities, classification, validation, and review without logging",
            "AI audit contract is invalid or writes/executed state is enabled",
        ),
        _check(
            {
                "authority_changes", "canonical_replacement", "restore", "delete",
                "move_canonical_resources", "permission_changes", "cloud_export_approval",
            } <= set(policy["human_approval"]["always_human"])
            and policy["human_approval"]["approval_runtime_enabled"] is False,
            "readiness.human_approval",
            "authority, recovery, destructive, permission, and cloud-export decisions remain human-only",
            "human approval boundary is incomplete or executable",
        ),
        _check(
            not agent_grant_errors(grant)
            and grant["execution_enabled"] is False
            and grant["autonomous"] is False
            and grant["action_authority"] == "none",
            "readiness.future_agent",
            "future grant contract requires action, scope, duration, approval, rollback, and audit but enables nothing",
            "future agent contract is incomplete or executable",
        ),
        _check(
            all(value is False for value in policy["runtime"].values())
            and policy["routing"]["approved_models"] == []
            and policy["routing"]["provider_selection"] == "unselected",
            "readiness.no_runtime",
            "no AI, model, provider, network, agent, tool, action, export, or audit-log runtime exists",
            "a prohibited runtime or model route is enabled",
        ),
    ])
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: readiness.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
