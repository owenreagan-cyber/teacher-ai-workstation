"""One-attempt, loopback-only Phase L.5E Ollama runtime adapter.

The adapter accepts an already validated AIContextPackage and LocalModelRequest.
It does not query Chief of Staff, select entities, start Ollama, pull models,
expose tools, inspect the filesystem, retry, fall back, persist output, or act.
"""

from __future__ import annotations

import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from ai_context_adapter import (
    ai_context_package_errors,
    local_model_request_errors,
)
from grounding_contract import (
    CONTRACT_METADATA,
    RESPONSE_V2_SCHEMA_PATH,
    V2_OUTPUT_RULES,
    build_response_vocabulary,
    prompt_schema_consistency_errors,
    prompt_vocabulary,
    validate_grounding_response_v2,
)
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/local-model-runtime.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/local-model-runtime.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas/ollama-runtime-result.schema.json"
AUDIT_SCHEMA_PATH = ROOT / "schemas/ollama-runtime-audit.schema.json"

APPROVED_HOSTS = {"127.0.0.1", "localhost"}
APPROVED_MODELS = {"qwen3.5:35b"}
APPROVED_TASKS = {"explain"}
FAILURE_CODES = {
    "runtime_unavailable",
    "model_missing",
    "request_timeout",
    "connection_failure",
    "malformed_response",
    "schema_validation_failed",
    "grounding_validation_failed",
    "authority_violation",
    "capability_violation",
}

FIXED_SYSTEM_PROMPT = """You are a local reasoning assistant inside Teacher Chief of Staff.

You receive only approved sanitized context.

You do not have filesystem, application, network, shell, tool, recovery, modification, deletion, restore, or authority-changing capabilities.

Do not infer permissions.

Do not invent authority.

Do not invent facts absent from the supplied context.

Do not paraphrase supplied facts or create new factual sentences.

Select only identifiers supplied in the allowed response vocabulary.

Do not invent identifiers or omit required authority, confidence, review-state, or uncertainty values.

Return only the required JSON structure with no explanation outside JSON."""

FIXED_OUTPUT_RULES = V2_OUTPUT_RULES


class OllamaRuntimeError(ValueError):
    """Raised for invalid static runtime contracts."""


class RuntimeTransportError(ConnectionError):
    """Safe transport error carrying one controlled failure code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def endpoint_policy_errors(endpoint: str, policy: dict[str, Any]) -> list[str]:
    try:
        parsed = urlparse(endpoint)
        port = parsed.port
    except ValueError:
        return ["endpoint is malformed"]
    errors: list[str] = []
    if parsed.scheme != "http":
        errors.append("Ollama transport must use HTTP")
    if parsed.hostname not in set(policy["approved_hosts"]):
        errors.append("Ollama host is not an approved loopback host")
    if parsed.hostname not in APPROVED_HOSTS:
        errors.append("Ollama host is outside the fixed loopback allowlist")
    if port != policy["port"] or port != 11434:
        errors.append("Ollama port is not approved")
    if parsed.username or parsed.password:
        errors.append("Ollama endpoint cannot contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        errors.append("Ollama endpoint cannot contain a path, query, or fragment")
    return errors


def canonical_loopback_endpoint(endpoint: str, policy: dict[str, Any]) -> str:
    errors = endpoint_policy_errors(endpoint, policy)
    if errors:
        raise OllamaRuntimeError(errors[0])
    parsed = urlparse(endpoint)
    host = "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname
    return f"http://{host}:{parsed.port}"


def runtime_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors = endpoint_policy_errors(policy["endpoint"], policy)
    if set(policy["approved_hosts"]) != APPROVED_HOSTS:
        errors.append("approved hosts must be exactly localhost and 127.0.0.1")
    if set(policy["approved_models"]) != APPROVED_MODELS:
        errors.append("qwen3.5:35b must be the only approved model")
    if set(policy["approved_tasks"]) != APPROVED_TASKS:
        errors.append("explain must be the only approved task")
    if policy["timeout_seconds"] != 120 or policy["maximum_attempts"] != 1:
        errors.append("runtime must use one attempt with a 120-second ceiling")
    for key in (
        "streaming_enabled",
        "thinking_output_enabled",
        "tools_enabled",
        "vision_enabled",
        "cloud_fallback_enabled",
        "model_fallback_enabled",
        "automatic_retry_enabled",
        "automatic_pull_enabled",
        "automatic_startup_enabled",
        "runtime_audit_persistence_enabled",
        "raw_response_persistence_enabled",
        "hidden_reasoning_persistence_enabled",
        "action_execution_enabled",
    ):
        if policy[key]:
            errors.append(f"{key} must remain disabled")
    return errors


def load_runtime_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = runtime_policy_errors(policy)
    if errors:
        raise OllamaRuntimeError(errors[0])
    return policy


class LoopbackHTTPTransport:
    """Small JSON transport with proxies disabled and bounded response reads."""

    def _json_request(
        self,
        method: str,
        endpoint: str,
        route: str,
        *,
        timeout_seconds: int,
        maximum_response_bytes: int,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(f"{endpoint}{route}", data=body, headers=headers, method=method)
        opener = build_opener(ProxyHandler({}))
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                encoded = response.read(maximum_response_bytes + 1)
        except HTTPError as exc:
            raise RuntimeTransportError(
                "connection_failure", f"Ollama returned HTTP status {exc.code}."
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise RuntimeTransportError(
                "request_timeout", "The loopback Ollama request timed out."
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise RuntimeTransportError(
                    "request_timeout", "The loopback Ollama request timed out."
                ) from exc
            raise RuntimeTransportError(
                "connection_failure", "The loopback Ollama endpoint could not be reached."
            ) from exc
        except OSError as exc:
            raise RuntimeTransportError(
                "connection_failure", "The loopback Ollama endpoint could not be reached."
            ) from exc
        if len(encoded) > maximum_response_bytes:
            raise RuntimeTransportError(
                "malformed_response", "Ollama response exceeded the approved size limit."
            )
        try:
            decoded = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeTransportError(
                "malformed_response", "Ollama returned malformed JSON."
            ) from exc
        if not isinstance(decoded, dict):
            raise RuntimeTransportError(
                "malformed_response", "Ollama returned a non-object response."
            )
        return decoded

    def get_json(
        self,
        endpoint: str,
        route: str,
        *,
        timeout_seconds: int,
        maximum_response_bytes: int,
    ) -> dict[str, Any]:
        return self._json_request(
            "GET",
            endpoint,
            route,
            timeout_seconds=timeout_seconds,
            maximum_response_bytes=maximum_response_bytes,
        )

    def post_json(
        self,
        endpoint: str,
        route: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: int,
        maximum_response_bytes: int,
    ) -> dict[str, Any]:
        return self._json_request(
            "POST",
            endpoint,
            route,
            timeout_seconds=timeout_seconds,
            maximum_response_bytes=maximum_response_bytes,
            payload=payload,
        )


def preflight_ollama(
    *,
    endpoint: str | None = None,
    transport: Any | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_runtime_policy()
    policy_failures = runtime_policy_errors(active)
    if policy_failures:
        raise OllamaRuntimeError(policy_failures[0])
    selected_endpoint = endpoint or active["endpoint"]
    endpoint_failures = endpoint_policy_errors(selected_endpoint, active)
    if endpoint_failures:
        return {
            "status": "failed",
            "failure_code": "capability_violation",
            "message": endpoint_failures[0],
            "endpoint": selected_endpoint,
            "runtime_available": False,
            "model_present": False,
            "model": active["approved_models"][0],
        }
    canonical = canonical_loopback_endpoint(selected_endpoint, active)
    client = transport or LoopbackHTTPTransport()
    try:
        response = client.get_json(
            canonical,
            "/api/tags",
            timeout_seconds=active["timeout_seconds"],
            maximum_response_bytes=active["maximum_response_bytes"],
        )
    except RuntimeTransportError as exc:
        code = "runtime_unavailable" if exc.code == "connection_failure" else exc.code
        message = (
            "Ollama is not available on the approved loopback endpoint; start it manually."
            if code == "runtime_unavailable"
            else str(exc)
        )
        return {
            "status": "failed",
            "failure_code": code,
            "message": message,
            "endpoint": canonical,
            "runtime_available": False,
            "model_present": False,
            "model": active["approved_models"][0],
        }
    models = response.get("models")
    if not isinstance(models, list):
        return {
            "status": "failed",
            "failure_code": "malformed_response",
            "message": "Ollama model inventory response is malformed.",
            "endpoint": canonical,
            "runtime_available": True,
            "model_present": False,
            "model": active["approved_models"][0],
        }
    installed = {
        name
        for item in models
        if isinstance(item, dict)
        for name in (item.get("name"), item.get("model"))
        if isinstance(name, str)
    }
    approved_model = active["approved_models"][0]
    if approved_model not in installed:
        return {
            "status": "failed",
            "failure_code": "model_missing",
            "message": "The exact approved model is not installed; automatic pull is prohibited.",
            "endpoint": canonical,
            "runtime_available": True,
            "model_present": False,
            "model": approved_model,
        }
    return {
        "status": "available",
        "failure_code": "none",
        "message": "Ollama and the exact approved model are available.",
        "endpoint": canonical,
        "runtime_available": True,
        "model_present": True,
        "model": approved_model,
    }


def build_ollama_payload(
    context: dict[str, Any],
    request: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = policy or load_runtime_policy()
    context_errors = ai_context_package_errors(context)
    if context_errors:
        raise OllamaRuntimeError(context_errors[0])
    request_errors = local_model_request_errors(request, context)
    if request_errors:
        raise OllamaRuntimeError(request_errors[0])
    if request["model"] not in active["approved_models"]:
        raise OllamaRuntimeError("request model is not approved for runtime")
    if request["task"] not in active["approved_tasks"]:
        raise OllamaRuntimeError("request task is not approved for runtime")
    if request["capabilities"] != ["explain"] or request["actions"]:
        raise OllamaRuntimeError("runtime request capability boundary is invalid")
    consistency_errors = prompt_schema_consistency_errors()
    if consistency_errors:
        raise OllamaRuntimeError(consistency_errors[0])
    vocabulary = build_response_vocabulary(context, request)
    response_contract = {
        "contract_id": CONTRACT_METADATA["contract_id"],
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "task": "explain",
        "cardinality": CONTRACT_METADATA,
        "output_rules": FIXED_OUTPUT_RULES,
        "allowed_response_vocabulary": prompt_vocabulary(vocabulary),
    }
    user_content = json.dumps(
        {
            "local_model_request": request,
            "sanitized_context_package": context,
            "response_contract": response_contract,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return {
        "model": request["model"],
        "messages": [
            {"role": "system", "content": FIXED_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "think": False,
        "format": load_json(RESPONSE_V2_SCHEMA_PATH),
        "options": {"temperature": 0},
    }


def _empty_metrics() -> dict[str, Any]:
    return {
        "total_duration_ns": 0,
        "load_duration_ns": 0,
        "prompt_eval_count": 0,
        "eval_count": 0,
        "model_load_state": "not_reported",
    }


def _runtime_metrics(response: dict[str, Any]) -> dict[str, Any]:
    def safe_integer(key: str) -> int:
        value = response.get(key, 0)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    return {
        "total_duration_ns": safe_integer("total_duration"),
        "load_duration_ns": safe_integer("load_duration"),
        "prompt_eval_count": safe_integer("prompt_eval_count"),
        "eval_count": safe_integer("eval_count"),
        "model_load_state": "reported" if "load_duration" in response else "not_reported",
    }


def runtime_result_errors(result: dict[str, Any]) -> list[str]:
    try:
        validate_schema(result, load_json(RESULT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if result["duration_ms"] < 0 or result["response_size_bytes"] < 0:
        errors.append("runtime sizes and durations cannot be negative")
    if result["attempt_count"] > 1 or result["retry_used"] or result["fallback_used"]:
        errors.append("Phase L.5E permits exactly one attempt and no retry or fallback")
    if result["status"] == "accepted":
        if result["failure_code"] != "none" or result["validation_result"] != "pass":
            errors.append("accepted result must have no failure and must pass validation")
        if not result["validated_response"] or result["attempt_count"] != 1:
            errors.append("accepted result requires one attempt and a validated response")
        if not result["grounding_diagnostics"].get("accepted"):
            errors.append("accepted result requires accepted grounding diagnostics")
    else:
        if result["failure_code"] not in FAILURE_CODES:
            errors.append("failed result requires a controlled failure code")
        if result["validated_response"]:
            errors.append("failed result cannot expose rejected model output")
        if result["validation_result"] == "rejected":
            diagnostics = result["grounding_diagnostics"]
            if diagnostics.get("accepted") is not False or not diagnostics.get("violations"):
                errors.append("rejected model output requires safe grounding diagnostics")
            if diagnostics.get("raw_response_retained") or diagnostics.get("persisted"):
                errors.append("grounding diagnostics cannot retain or persist rejected output")
    if result["action_authority"] != "none":
        errors.append("runtime result cannot grant action authority")
    return errors


def _failure_result(
    request: dict[str, Any],
    context: dict[str, Any],
    endpoint: str,
    code: str,
    message: str,
    *,
    started_at: str,
    ended_at: str,
    duration_ms: int,
    attempt_count: int,
    validation_result: str = "not_run",
    response_size_bytes: int = 0,
    metrics: dict[str, Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "schema_version": 1,
        "status": "failed",
        "failure_code": code,
        "message": message,
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "runtime": "ollama",
        "model": "qwen3.5:35b",
        "task": "explain",
        "endpoint": endpoint,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "attempt_count": attempt_count,
        "retry_used": False,
        "fallback_used": False,
        "validation_result": validation_result,
        "grounding_diagnostics": diagnostics or {},
        "validated_response": {},
        "response_size_bytes": response_size_bytes,
        "runtime_metrics": metrics or _empty_metrics(),
        "hidden_reasoning_exposed": False,
        "hidden_reasoning_persisted": False,
        "raw_response_persisted": False,
        "action_authority": "none",
    }
    errors = runtime_result_errors(result)
    if errors:
        raise OllamaRuntimeError(errors[0])
    return result


def _failure_code_for_violations(violations: list[str]) -> str:
    combined = " ".join(violations).lower()
    if "authority" in combined or "canonical" in combined:
        return "authority_violation"
    if any(
        marker in combined
        for marker in (
            "action", "access", "permission", "recommendation",
            "requested_actions", "access_claims", "permissions_claimed",
        )
    ):
        return "capability_violation"
    if any(
        marker in combined
        for marker in (
            "expected type", "missing required", "unexpected properties",
            "expected constant", "too many items", "too few items",
            "value does not match pattern", "is not allowed",
        )
    ):
        return "schema_validation_failed"
    return "grounding_validation_failed"


def execute_local_explanation(
    context: dict[str, Any],
    request: dict[str, Any],
    *,
    preflight: dict[str, Any] | None = None,
    endpoint: str | None = None,
    transport: Any | None = None,
    policy: dict[str, Any] | None = None,
    wall_clock: Callable[[], str] = _utc_now,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Make at most one approved model request and return a controlled result."""

    active = policy or load_runtime_policy()
    selected_endpoint = endpoint or active["endpoint"]
    try:
        canonical = canonical_loopback_endpoint(selected_endpoint, active)
        payload = build_ollama_payload(context, request, active)
    except (OllamaRuntimeError, KeyError, TypeError) as exc:
        now = wall_clock()
        return _failure_result(
            request, context, active["endpoint"], "capability_violation", str(exc),
            started_at=now, ended_at=now, duration_ms=0, attempt_count=0,
        )

    checked = preflight or preflight_ollama(
        endpoint=canonical, transport=transport, policy=active
    )
    if checked["status"] != "available":
        now = wall_clock()
        return _failure_result(
            request, context, canonical, checked["failure_code"], checked["message"],
            started_at=now, ended_at=now, duration_ms=0, attempt_count=0,
        )
    if (
        checked.get("endpoint") != canonical
        or checked.get("model") != request["model"]
        or not checked.get("runtime_available")
        or not checked.get("model_present")
    ):
        now = wall_clock()
        return _failure_result(
            request, context, canonical, "capability_violation",
            "Runtime preflight does not match the approved request.",
            started_at=now, ended_at=now, duration_ms=0, attempt_count=0,
        )

    client = transport or LoopbackHTTPTransport()
    started_at = wall_clock()
    started = monotonic()
    try:
        outer = client.post_json(
            canonical,
            "/api/chat",
            payload,
            timeout_seconds=active["timeout_seconds"],
            maximum_response_bytes=active["maximum_response_bytes"],
        )
    except RuntimeTransportError as exc:
        ended_at = wall_clock()
        duration_ms = max(0, round((monotonic() - started) * 1000))
        return _failure_result(
            request, context, canonical, exc.code, str(exc),
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1,
        )
    ended_at = wall_clock()
    duration_ms = max(0, round((monotonic() - started) * 1000))
    metrics = _runtime_metrics(outer)
    if outer.get("model") not in {None, request["model"]}:
        return _failure_result(
            request, context, canonical, "capability_violation",
            "Ollama responded from a model other than the approved model.",
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1, metrics=metrics,
        )
    message = outer.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        return _failure_result(
            request, context, canonical, "malformed_response",
            "Ollama response did not contain structured final content.",
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1, metrics=metrics,
        )
    response_size = len(content.encode("utf-8"))
    try:
        candidate = json.loads(content)
    except json.JSONDecodeError:
        return _failure_result(
            request, context, canonical, "malformed_response",
            "The model final response was not valid JSON.",
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1,
            response_size_bytes=response_size, metrics=metrics,
        )
    if not isinstance(candidate, dict):
        return _failure_result(
            request, context, canonical, "malformed_response",
            "The model final response was not a JSON object.",
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1,
            response_size_bytes=response_size, metrics=metrics,
        )
    validation = validate_grounding_response_v2(candidate, request, context)
    if not validation["accepted"]:
        code = validation["failure_category"]
        return _failure_result(
            request, context, canonical, code,
            "Model output failed deterministic response validation.",
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration_ms, attempt_count=1,
            validation_result="rejected", response_size_bytes=response_size,
            metrics=metrics, diagnostics=validation,
        )
    result = {
        "schema_version": 1,
        "status": "accepted",
        "failure_code": "none",
        "message": "The structured local-model explanation passed deterministic validation.",
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "runtime": "ollama",
        "model": "qwen3.5:35b",
        "task": "explain",
        "endpoint": canonical,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "attempt_count": 1,
        "retry_used": False,
        "fallback_used": False,
        "validation_result": "pass",
        "grounding_diagnostics": validation,
        "validated_response": candidate,
        "response_size_bytes": response_size,
        "runtime_metrics": metrics,
        "hidden_reasoning_exposed": False,
        "hidden_reasoning_persisted": False,
        "raw_response_persisted": False,
        "action_authority": "none",
    }
    errors = runtime_result_errors(result)
    if errors:
        raise OllamaRuntimeError(errors[0])
    return result


def runtime_audit_errors(audit: dict[str, Any]) -> list[str]:
    try:
        validate_schema(audit, load_json(AUDIT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if audit["duration_ms"] < 0:
        return ["audit duration cannot be negative"]
    if audit["persisted"] or audit["hidden_reasoning_persisted"] or audit["raw_response_persisted"]:
        return ["Phase L.5E audit data cannot be persisted"]
    if audit["action_authority"] != "none":
        return ["runtime audit cannot grant action authority"]
    return []


def build_runtime_audit(result: dict[str, Any]) -> dict[str, Any]:
    errors = runtime_result_errors(result)
    if errors:
        raise OllamaRuntimeError(errors[0])
    audit = {
        "schema_version": 1,
        "request_id": result["request_id"],
        "context_id": result["context_id"],
        "model": result["model"],
        "runtime": result["runtime"],
        "task": result["task"],
        "started_at": result["started_at"],
        "ended_at": result["ended_at"],
        "duration_ms": result["duration_ms"],
        "validation_result": result["validation_result"],
        "failure_code": result["failure_code"],
        "action_authority": "none",
        "persisted": False,
        "hidden_reasoning_persisted": False,
        "raw_response_persisted": False,
    }
    audit_failures = runtime_audit_errors(audit)
    if audit_failures:
        raise OllamaRuntimeError(audit_failures[0])
    return audit
