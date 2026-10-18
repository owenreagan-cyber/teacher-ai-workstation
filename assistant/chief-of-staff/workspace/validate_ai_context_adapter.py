#!/usr/bin/env python3
"""Validate Phase L.5D contracts without invoking Ollama or another model."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass

from ai_context_adapter import (
    ALLOWED_CAPABILITIES,
    ALLOWED_TASKS,
    REQUIRED_RESTRICTIONS,
    SOURCE_LAYERS,
    ai_context_package_errors,
    ai_response_validation_errors,
    build_ai_context,
    local_model_audit_errors,
    local_model_boundary_policy_errors,
    local_model_request_errors,
    local_model_response_errors,
    synthetic_local_model_boundary_bundle,
    validate_ai_response,
)


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _check(condition: bool, code: str, success: str, failure: str) -> Check:
    return Check("PASS" if condition else "FAIL", code, success if condition else failure)


def _contains_key(value, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(
            key in forbidden or _contains_key(child, forbidden)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_key(child, forbidden) for child in value)
    return False


def run_validation() -> list[Check]:
    bundle = synthetic_local_model_boundary_bundle()
    policy = bundle["policy"]
    context = bundle["context"]
    request = bundle["request"]
    response = bundle["response"]
    validation = bundle["validation"]
    audit = bundle["audit"]
    checks = [
        _check(
            not local_model_boundary_policy_errors(policy),
            "local_ai.policy",
            "closed Phase L.5D policy is contract-only and non-executable",
            "local-model boundary policy is invalid",
        ),
        _check(
            set(policy["source_layers"]) == SOURCE_LAYERS,
            "local_ai.source_layers",
            "adapter consumes the existing query, explanation, and evidence layers",
            "adapter source-layer contract is incomplete",
        ),
        _check(
            set(policy["tasks"]) == ALLOWED_TASKS
            and set(policy["capabilities"]) == ALLOWED_CAPABILITIES
            and not policy["actions"],
            "local_ai.capabilities",
            "only explain is granted and the action set is empty",
            "task, capability, or action boundary is invalid",
        ),
        _check(
            set(policy["restrictions"]) == REQUIRED_RESTRICTIONS,
            "local_ai.restrictions",
            "filesystem, application, launch, mutation, permission, cloud, and tool access are denied",
            "one or more mandatory restrictions are absent",
        ),
        _check(
            policy["model_contract"]["runtime"] == "ollama"
            and policy["model_contract"]["model"] == "qwen3.5:35b"
            and policy["model_contract"]["quantization"] == "Q4_K_M"
            and not policy["model_contract"]["connector_enabled"]
            and not policy["model_contract"]["execution_enabled"],
            "local_ai.model_contract",
            "approved Qwen/Ollama identity is recorded without a connector or execution",
            "model identity or non-connection boundary is invalid",
        ),
        _check(
            not ai_context_package_errors(context, policy)
            and context["capabilities"] == ["explain"]
            and context["actions"] == []
            and not context["raw_observations_included"],
            "local_ai.context",
            "Writing explanation produces a closed sanitized AIContextPackage",
            "AI context package is invalid, actionable, or contains raw observations",
        ),
        _check(
            build_ai_context("application-concept:grade-4-writing-launcher")
            == build_ai_context("application-concept:grade-4-writing-launcher"),
            "local_ai.determinism",
            "identical entity input produces a byte-equivalent context package",
            "AI context construction is not deterministic",
        ),
        _check(
            context["authority_context"][0]["role"] == "unknown"
            and any("unknown" in item.lower() for item in context["uncertainties"])
            and context["review_state"][0]["state"] == "unreviewed",
            "local_ai.preservation",
            "unknown authority, uncertainty, confidence, and unreviewed state remain explicit",
            "the adapter hid or promoted a bounded evidence state",
        ),
        _check(
            "/Users/" not in json.dumps(context, sort_keys=True)
            and not _contains_key(
                context, {"raw_observation", "raw_observations", "student_name"}
            ),
            "local_ai.sanitization",
            "context contains no path, raw-observation, or student-data leakage",
            "context contains a forbidden raw or sensitive field",
        ),
        _check(
            not local_model_request_errors(request, context, policy)
            and request["connector_state"] == "not_connected"
            and request["execution_state"] == "not_executed",
            "local_ai.request",
            "LocalModelRequest names explain and the approved stack without connecting it",
            "local model request contract is invalid or executable",
        ),
        _check(
            not local_model_response_errors(response, request, context)
            and validation["validation_result"] == "pass"
            and not ai_response_validation_errors(validation),
            "local_ai.response",
            "grounded structured explanation preserves evidence and passes validation",
            "grounded explanation candidate failed validation",
        ),
    ]

    unsupported = copy.deepcopy(response)
    unsupported["claims"][0]["statement"] = "The launcher owns all Writing resources."
    action = copy.deepcopy(response)
    action["claims"][0]["statement"] = "Move the application."
    authority = copy.deepcopy(response)
    authority["authority_context"][0]["role"] = "canonical"
    inflated = copy.deepcopy(response)
    low_claim = next(
        claim for claim in inflated["claims"]
        if claim["claim_type"] == "evidence" and claim["confidence"] != "high"
    )
    low_claim["confidence"] = "high"
    checks.append(
        _check(
            bool(local_model_response_errors(unsupported, request, context))
            and bool(local_model_response_errors(action, request, context))
            and bool(local_model_response_errors(authority, request, context))
            and bool(local_model_response_errors(inflated, request, context)),
            "local_ai.rejection",
            "unsupported claims, actions, invented authority, and confidence inflation reject",
            "one or more unsafe explanation patterns passed validation",
        )
    )
    rejected = validate_ai_response(action, request, context, policy)
    checks.extend(
        [
            _check(
                rejected["validation_result"] == "rejected"
                and bool(rejected["violations"])
                and rejected["execution_state"] == "not_executed"
                and rejected["persisted"] is False,
                "local_ai.fail_closed",
                "failed output becomes an unexecuted, unpersisted rejection record",
                "failed output did not remain fail-closed",
            ),
            _check(
                not local_model_audit_errors(audit)
                and audit["validation_result"] == "pass"
                and audit["execution_state"] == "not_executed"
                and audit["persisted"] is False,
                "local_ai.audit",
                "audit contract records validation without writing a runtime log",
                "audit contract is invalid, executed, or persisted",
            ),
            _check(
                all(value is False for value in policy["persistence"].values())
                and all(
                    policy[key] is False
                    for key in (
                        "network_enabled",
                        "model_invocation_enabled",
                        "agent_enabled",
                        "tool_calling_enabled",
                        "action_execution_enabled",
                        "host_local_ai_data_enabled",
                    )
                ),
                "local_ai.no_runtime",
                "no model, network, agent, tool, action, persistence, or host-local AI runtime exists",
                "a prohibited Phase L.5D runtime is enabled",
            ),
        ]
    )
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: local_ai.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
