from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ai_context_adapter import synthetic_local_model_boundary_bundle
from grounding_contract import build_ideal_response_v2
from ollama_runtime import (
    APPROVED_HOSTS,
    APPROVED_MODELS,
    APPROVED_TASKS,
    FIXED_SYSTEM_PROMPT,
    RuntimeTransportError,
    build_ollama_payload,
    build_runtime_audit,
    canonical_loopback_endpoint,
    endpoint_policy_errors,
    execute_local_explanation,
    load_runtime_policy,
    preflight_ollama,
    runtime_audit_errors,
    runtime_policy_errors,
    runtime_result_errors,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeTransport:
    def __init__(self, *, tags=None, response=None, get_error=None, post_error=None):
        self.tags = tags if tags is not None else {
            "models": [{"name": "qwen3.5:35b", "model": "qwen3.5:35b"}]
        }
        self.response = response or {}
        self.get_error = get_error
        self.post_error = post_error
        self.get_calls = 0
        self.post_calls = 0
        self.last_endpoint = ""
        self.last_route = ""
        self.last_payload = None

    def get_json(self, endpoint, route, **kwargs):
        self.get_calls += 1
        self.last_endpoint = endpoint
        self.last_route = route
        if self.get_error:
            raise self.get_error
        return copy.deepcopy(self.tags)

    def post_json(self, endpoint, route, payload, **kwargs):
        self.post_calls += 1
        self.last_endpoint = endpoint
        self.last_route = route
        self.last_payload = copy.deepcopy(payload)
        if self.post_error:
            raise self.post_error
        return copy.deepcopy(self.response)


class OllamaRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_runtime_policy()
        cls.bundle = synthetic_local_model_boundary_bundle()
        cls.context = cls.bundle["context"]
        cls.request = cls.bundle["request"]
        cls.valid_candidate = build_ideal_response_v2(cls.context, cls.request)

    def outer(self, candidate=None, **overrides):
        value = {
            "model": "qwen3.5:35b",
            "message": {"role": "assistant", "content": json.dumps(
                candidate if candidate is not None else self.valid_candidate,
                separators=(",", ":"),
            )},
            "done": True,
            "total_duration": 100,
            "load_duration": 20,
            "prompt_eval_count": 50,
            "eval_count": 25,
        }
        value.update(overrides)
        return value

    def available_preflight(self):
        return {
            "status": "available",
            "failure_code": "none",
            "message": "available",
            "endpoint": "http://127.0.0.1:11434",
            "runtime_available": True,
            "model_present": True,
            "model": "qwen3.5:35b",
        }

    def execute_with(self, outer):
        transport = FakeTransport(response=outer)
        result = execute_local_explanation(
            self.context,
            self.request,
            preflight=self.available_preflight(),
            transport=transport,
            policy=self.policy,
            wall_clock=lambda: "2026-09-21T12:00:00Z",
            monotonic=iter((1.0, 1.25)).__next__,
        )
        return result, transport

    def test_runtime_policy_is_exact_and_fail_closed(self) -> None:
        self.assertEqual([], runtime_policy_errors(self.policy))
        self.assertEqual(APPROVED_HOSTS, set(self.policy["approved_hosts"]))
        self.assertEqual(APPROVED_MODELS, set(self.policy["approved_models"]))
        self.assertEqual(APPROVED_TASKS, set(self.policy["approved_tasks"]))
        self.assertEqual(120, self.policy["timeout_seconds"])
        self.assertEqual(1, self.policy["maximum_attempts"])

    def test_localhost_and_ipv4_loopback_are_accepted(self) -> None:
        for endpoint in ("http://localhost:11434", "http://127.0.0.1:11434"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual([], endpoint_policy_errors(endpoint, self.policy))
                self.assertEqual(
                    "http://127.0.0.1:11434",
                    canonical_loopback_endpoint(endpoint, self.policy),
                )

    def test_lan_remote_and_alternate_port_endpoints_are_rejected(self) -> None:
        for endpoint in (
            "http://192.168.1.50:11434",
            "http://ollama.example.com:11434",
            "http://127.0.0.1:11435",
            "https://127.0.0.1:11434",
        ):
            with self.subTest(endpoint=endpoint):
                self.assertTrue(endpoint_policy_errors(endpoint, self.policy))

    def test_exact_qwen_model_is_present(self) -> None:
        transport = FakeTransport()
        result = preflight_ollama(transport=transport, policy=self.policy)
        self.assertEqual("available", result["status"])
        self.assertTrue(result["runtime_available"])
        self.assertTrue(result["model_present"])
        self.assertEqual(1, transport.get_calls)
        self.assertEqual(0, transport.post_calls)

    def test_alternate_or_unknown_model_does_not_substitute(self) -> None:
        for installed in ("llama3.2", "unknown:model"):
            with self.subTest(installed=installed):
                transport = FakeTransport(tags={"models": [{"name": installed}]})
                result = preflight_ollama(transport=transport, policy=self.policy)
                self.assertEqual("model_missing", result["failure_code"])
                self.assertFalse(result["model_present"])
                self.assertEqual(0, transport.post_calls)

    def test_missing_runtime_is_controlled_and_never_started(self) -> None:
        transport = FakeTransport(get_error=RuntimeTransportError(
            "connection_failure", "not running"
        ))
        result = preflight_ollama(transport=transport, policy=self.policy)
        self.assertEqual("runtime_unavailable", result["failure_code"])
        self.assertIn("start it manually", result["message"])
        self.assertEqual(1, transport.get_calls)
        self.assertEqual(0, transport.post_calls)

    def test_prompt_is_fixed_structured_and_tool_free(self) -> None:
        payload = build_ollama_payload(self.context, self.request, self.policy)
        self.assertEqual(FIXED_SYSTEM_PROMPT, payload["messages"][0]["content"])
        self.assertEqual("qwen3.5:35b", payload["model"])
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("images", payload)
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn('"raw_observation":', encoded)

    def test_valid_context_and_structured_response_are_accepted(self) -> None:
        result, transport = self.execute_with(self.outer())
        self.assertEqual([], runtime_result_errors(result))
        self.assertEqual("accepted", result["status"])
        self.assertEqual("pass", result["validation_result"])
        self.assertEqual(self.valid_candidate, result["validated_response"])
        self.assertEqual(1, transport.post_calls)
        self.assertEqual("/api/chat", transport.last_route)

    def test_unsanitized_context_is_rejected_before_transport(self) -> None:
        context = copy.deepcopy(self.context)
        context["absolute_path"] = "/Users/example/private"
        transport = FakeTransport(response=self.outer())
        result = execute_local_explanation(
            context,
            self.request,
            preflight=self.available_preflight(),
            transport=transport,
            policy=self.policy,
        )
        self.assertEqual("capability_violation", result["failure_code"])
        self.assertEqual(0, transport.post_calls)

    def test_nonempty_actions_are_rejected_before_transport(self) -> None:
        context = copy.deepcopy(self.context)
        context["actions"] = ["launch"]
        transport = FakeTransport(response=self.outer())
        result = execute_local_explanation(
            context,
            self.request,
            preflight=self.available_preflight(),
            transport=transport,
            policy=self.policy,
        )
        self.assertEqual("capability_violation", result["failure_code"])
        self.assertEqual(0, transport.post_calls)

    def test_malformed_model_json_is_rejected(self) -> None:
        result, transport = self.execute_with(self.outer(message={
            "role": "assistant", "content": "not-json"
        }))
        self.assertEqual("malformed_response", result["failure_code"])
        self.assertEqual({}, result["validated_response"])
        self.assertEqual(1, transport.post_calls)

    def test_response_with_extra_field_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["unsupported"] = "must fail closed"
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("schema_validation_failed", result["failure_code"])

    def test_response_omitting_uncertainty_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["uncertainty_refs"].pop()
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("grounding_validation_failed", result["failure_code"])

    def test_alternate_response_model_is_rejected(self) -> None:
        result, _ = self.execute_with(self.outer(model="qwen3.5:9b"))
        self.assertEqual("capability_violation", result["failure_code"])

    def test_invented_authority_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["authority"] = "canonical"
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("authority_violation", result["failure_code"])
        self.assertEqual("rejected", result["validation_result"])
        self.assertEqual(
            "AUTHORITY_CHANGED",
            result["grounding_diagnostics"]["violations"][0]["code"],
        )

    def test_confidence_inflation_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["confidence"] = "medium"
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("grounding_validation_failed", result["failure_code"])

    def test_tool_or_access_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["access_claims"] = ["I inspected the filesystem."]
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("capability_violation", result["failure_code"])

    def test_action_language_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.valid_candidate)
        candidate["actions"] = ["Delete older versions."]
        result, _ = self.execute_with(self.outer(candidate))
        self.assertEqual("capability_violation", result["failure_code"])

    def test_timeout_has_one_attempt_no_retry_and_no_fallback(self) -> None:
        transport = FakeTransport(post_error=RuntimeTransportError(
            "request_timeout", "timed out"
        ))
        result = execute_local_explanation(
            self.context,
            self.request,
            preflight=self.available_preflight(),
            transport=transport,
            policy=self.policy,
        )
        self.assertEqual("request_timeout", result["failure_code"])
        self.assertEqual(1, result["attempt_count"])
        self.assertFalse(result["retry_used"])
        self.assertFalse(result["fallback_used"])
        self.assertEqual(1, transport.post_calls)

    def test_hidden_reasoning_is_discarded_and_never_persisted(self) -> None:
        outer = self.outer()
        outer["message"]["thinking"] = "private chain of thought"
        result, _ = self.execute_with(outer)
        self.assertEqual("accepted", result["status"])
        self.assertNotIn("thinking", json.dumps(result, sort_keys=True))
        self.assertFalse(result["hidden_reasoning_exposed"])
        self.assertFalse(result["hidden_reasoning_persisted"])

    def test_audit_is_in_memory_only(self) -> None:
        result, _ = self.execute_with(self.outer())
        audit = build_runtime_audit(result)
        self.assertEqual([], runtime_audit_errors(audit))
        self.assertFalse(audit["persisted"])
        self.assertFalse(audit["hidden_reasoning_persisted"])
        self.assertFalse(audit["raw_response_persisted"])
        self.assertEqual("none", audit["action_authority"])

    def test_adapter_contains_no_start_pull_shell_write_or_fallback_primitive(self) -> None:
        source = (ROOT / "ollama_runtime.py").read_text(encoding="utf-8").lower()
        for forbidden in (
            "subprocess", "os.system", "popen", "ollama serve", "/api/pull",
            "brew services", "launchctl", "open -a", "write_text", "open(\"w",
            "open('w", "cloud model", "fallback_model", "while true",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
