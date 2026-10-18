#!/usr/bin/env python3
"""Validate Phase L.5E with synthetic transport only; never call Ollama."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass

from ai_context_adapter import synthetic_local_model_boundary_bundle
from grounding_contract import build_ideal_response_v2
from ollama_runtime import (
    FIXED_SYSTEM_PROMPT,
    RuntimeTransportError,
    build_ollama_payload,
    build_runtime_audit,
    endpoint_policy_errors,
    execute_local_explanation,
    load_runtime_policy,
    preflight_ollama,
    runtime_audit_errors,
    runtime_policy_errors,
    runtime_result_errors,
)


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


class SyntheticTransport:
    def __init__(self, *, tags=None, response=None, get_error=None, post_error=None):
        self.tags = tags if tags is not None else {
            "models": [{"name": "qwen3.5:35b"}]
        }
        self.response = response or {}
        self.get_error = get_error
        self.post_error = post_error
        self.get_calls = 0
        self.post_calls = 0

    def get_json(self, endpoint, route, **kwargs):
        self.get_calls += 1
        if self.get_error:
            raise self.get_error
        return copy.deepcopy(self.tags)

    def post_json(self, endpoint, route, payload, **kwargs):
        self.post_calls += 1
        if self.post_error:
            raise self.post_error
        return copy.deepcopy(self.response)


def _check(condition: bool, code: str, success: str, failure: str) -> Check:
    return Check("PASS" if condition else "FAIL", code, success if condition else failure)


def _outer(candidate: dict) -> dict:
    return {
        "model": "qwen3.5:35b",
        "message": {"role": "assistant", "content": json.dumps(candidate)},
        "done": True,
        "total_duration": 100,
        "load_duration": 20,
        "prompt_eval_count": 50,
        "eval_count": 25,
    }


def _available() -> dict:
    return {
        "status": "available",
        "failure_code": "none",
        "message": "available",
        "endpoint": "http://127.0.0.1:11434",
        "runtime_available": True,
        "model_present": True,
        "model": "qwen3.5:35b",
    }


def _execute(context, request, candidate):
    transport = SyntheticTransport(response=_outer(candidate))
    result = execute_local_explanation(
        context,
        request,
        preflight=_available(),
        transport=transport,
        wall_clock=lambda: "2026-09-21T12:00:00Z",
        monotonic=iter((1.0, 1.1)).__next__,
    )
    return result, transport


def run_validation() -> list[Check]:
    policy = load_runtime_policy()
    bundle = synthetic_local_model_boundary_bundle()
    context = bundle["context"]
    request = bundle["request"]
    candidate = build_ideal_response_v2(context, request)
    prompt = build_ollama_payload(context, request, policy)
    preflight_transport = SyntheticTransport()
    preflight = preflight_ollama(transport=preflight_transport, policy=policy)
    accepted, accepted_transport = _execute(context, request, candidate)
    audit = build_runtime_audit(accepted)
    checks = [
        _check(
            not runtime_policy_errors(policy),
            "ollama.policy",
            "runtime policy is loopback-only, one-model, one-task, and one-attempt",
            "Ollama runtime policy is invalid",
        ),
        _check(
            not endpoint_policy_errors("http://127.0.0.1:11434", policy)
            and not endpoint_policy_errors("http://localhost:11434", policy)
            and bool(endpoint_policy_errors("http://192.168.1.5:11434", policy)),
            "ollama.endpoint",
            "localhost forms pass while LAN and remote endpoint forms fail closed",
            "endpoint loopback enforcement is invalid",
        ),
        _check(
            policy["approved_models"] == ["qwen3.5:35b"]
            and policy["approved_tasks"] == ["explain"],
            "ollama.model_task",
            "qwen3.5:35b and explain are the only approved model and task",
            "model or task allowlist is broader than approved",
        ),
        _check(
            not policy["automatic_startup_enabled"]
            and not policy["automatic_pull_enabled"]
            and not policy["automatic_retry_enabled"]
            and not policy["cloud_fallback_enabled"]
            and not policy["model_fallback_enabled"],
            "ollama.lifecycle",
            "startup, pull, retry, and all fallbacks remain human-controlled or disabled",
            "runtime lifecycle contains a prohibited automatic behavior",
        ),
        _check(
            prompt["messages"][0]["content"] == FIXED_SYSTEM_PROMPT
            and prompt["model"] == "qwen3.5:35b"
            and prompt["stream"] is False
            and prompt["think"] is False
            and "tools" not in prompt
            and "images" not in prompt,
            "ollama.prompt",
            "fixed structured prompt has no tools, vision, streaming, or thinking output",
            "prompt boundary is dynamic or exposes a prohibited model feature",
        ),
        _check(
            "/Users/" not in json.dumps(prompt, sort_keys=True)
            and '"raw_observation":' not in json.dumps(prompt, sort_keys=True),
            "ollama.context",
            "prompt contains only the validated sanitized AIContextPackage",
            "prompt contains a raw path or raw observation",
        ),
        _check(
            preflight["status"] == "available"
            and preflight["model_present"] is True
            and preflight_transport.get_calls == 1
            and preflight_transport.post_calls == 0,
            "ollama.preflight",
            "synthetic preflight confirms exact model without a generation request",
            "preflight failed or attempted generation",
        ),
        _check(
            not runtime_result_errors(accepted)
            and accepted["status"] == "accepted"
            and accepted["validation_result"] == "pass"
            and accepted_transport.post_calls == 1,
            "ollama.accepted",
            "one structured response passes existing deterministic validation",
            "valid structured response was not accepted exactly once",
        ),
    ]

    missing = preflight_ollama(
        transport=SyntheticTransport(tags={"models": [{"name": "llama3.2"}]}),
        policy=policy,
    )
    unavailable = preflight_ollama(
        transport=SyntheticTransport(get_error=RuntimeTransportError(
            "connection_failure", "not running"
        )),
        policy=policy,
    )
    checks.extend([
        _check(
            missing["failure_code"] == "model_missing"
            and unavailable["failure_code"] == "runtime_unavailable",
            "ollama.availability_failures",
            "missing model and stopped runtime return distinct controlled failures",
            "runtime availability failures are not controlled",
        )
    ])

    authority = copy.deepcopy(candidate)
    authority["authority"] = "canonical"
    action = copy.deepcopy(candidate)
    action["actions"] = ["Delete older versions."]
    confidence = copy.deepcopy(candidate)
    confidence["confidence"] = "medium"
    authority_result, _ = _execute(context, request, authority)
    action_result, _ = _execute(context, request, action)
    confidence_result, _ = _execute(context, request, confidence)
    checks.extend([
        _check(
            authority_result["failure_code"] == "authority_violation"
            and action_result["failure_code"] == "capability_violation"
            and confidence_result["failure_code"] == "grounding_validation_failed",
            "ollama.rejection",
            "invented authority, action language, and confidence inflation fail closed",
            "one or more unsafe response patterns passed",
        ),
    ])

    malformed_transport = SyntheticTransport(response={
        "model": "qwen3.5:35b",
        "message": {"content": "not-json"},
    })
    malformed = execute_local_explanation(
        context,
        request,
        preflight=_available(),
        transport=malformed_transport,
    )
    timeout_transport = SyntheticTransport(post_error=RuntimeTransportError(
        "request_timeout", "timed out"
    ))
    timeout = execute_local_explanation(
        context,
        request,
        preflight=_available(),
        transport=timeout_transport,
    )
    checks.extend([
        _check(
            malformed["failure_code"] == "malformed_response"
            and malformed["validated_response"] == {},
            "ollama.malformed",
            "malformed output is rejected and never exposed as trusted fact",
            "malformed output was accepted or exposed",
        ),
        _check(
            timeout["failure_code"] == "request_timeout"
            and timeout["attempt_count"] == 1
            and timeout_transport.post_calls == 1
            and not timeout["retry_used"]
            and not timeout["fallback_used"],
            "ollama.timeout",
            "timeout stops after one attempt with no retry or fallback",
            "timeout retried or used a fallback",
        ),
        _check(
            not runtime_audit_errors(audit)
            and audit["persisted"] is False
            and audit["hidden_reasoning_persisted"] is False
            and audit["raw_response_persisted"] is False,
            "ollama.audit",
            "runtime audit remains in memory without response or reasoning persistence",
            "runtime audit contract is invalid or persistent",
        ),
        _check(
            accepted["action_authority"] == "none"
            and accepted["hidden_reasoning_exposed"] is False
            and not policy["tools_enabled"]
            and not policy["vision_enabled"]
            and not policy["action_execution_enabled"],
            "ollama.no_actions",
            "accepted explanations expose no tools, hidden reasoning, or action authority",
            "accepted runtime result exposes a prohibited capability",
        ),
        _check(
            policy["timeout_seconds"] == 120
            and policy["maximum_attempts"] == 1
            and policy["maximum_response_bytes"] == 1000000,
            "ollama.resources",
            "execution is bounded by one attempt, 120 seconds, and a response-size ceiling",
            "runtime resource limits are incomplete",
        ),
    ])
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: ollama.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
