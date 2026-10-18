from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from controlled_execution import (
    build_pre_live_gate,
    build_safe_execution_audit,
    finalize_execution,
)
from ollama_runtime import execute_local_explanation, runtime_result_errors


ROOT = Path(__file__).resolve().parents[1]


class SyntheticTransport:
    def __init__(self, candidate):
        self.candidate = candidate
        self.post_calls = 0

    def post_json(self, endpoint, route, payload, **kwargs):
        self.post_calls += 1
        return {
            "model": "qwen3.5:35b",
            "message": {"role": "assistant", "content": json.dumps(self.candidate)},
            "done": True,
            "total_duration": 100,
            "load_duration": 20,
            "prompt_eval_count": 50,
            "eval_count": 25,
        }


def available_preflight():
    return {
        "status": "available",
        "failure_code": "none",
        "message": "available",
        "endpoint": "http://127.0.0.1:11434",
        "runtime_available": True,
        "model_present": True,
        "model": "qwen3.5:35b",
    }


class ControlledExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = build_pre_live_gate()

    def execute(self, candidate):
        transport = SyntheticTransport(candidate)
        result = execute_local_explanation(
            self.gate["context"],
            self.gate["request"],
            preflight=available_preflight(),
            transport=transport,
            wall_clock=iter(("2026-09-21T18:00:00Z", "2026-09-21T18:00:01Z")).__next__,
            monotonic=iter((1.0, 2.0)).__next__,
        )
        return result, transport

    def test_pre_live_gate_passes_without_runtime(self) -> None:
        self.assertEqual("PASS", self.gate["status"])
        self.assertEqual([], self.gate["errors"])
        self.assertTrue(self.gate["ideal_validation"]["accepted"])
        self.assertTrue(self.gate["ideal_rendered_explanation"])

    def test_context_semantic_boundary_is_exact(self) -> None:
        summary = self.gate["context_summary"]
        self.assertEqual("Grade 4 Writing Launcher", summary["label"])
        self.assertEqual("application", summary["entity_type"])
        self.assertEqual("high", summary["confidence"])
        self.assertEqual("unknown", summary["authority"])
        self.assertEqual("unreviewed", summary["review_state"])
        self.assertEqual(["explain"], summary["capabilities"])
        self.assertEqual([], summary["actions"])
        self.assertEqual("none", summary["action_authority"])

    def test_vocabulary_cardinality_is_current_and_closed(self) -> None:
        summary = self.gate["vocabulary_summary"]
        self.assertEqual(1, summary["known_ref_count"])
        self.assertEqual(5, summary["evidence_ref_count"])
        self.assertEqual(4, summary["uncertainty_ref_count"])
        self.assertEqual(0, summary["relationship_ref_count"])
        self.assertTrue(all("exactly" in value for key, value in summary.items() if key.endswith("cardinality")))

    def test_accepted_candidate_is_rendered_after_one_attempt(self) -> None:
        result, transport = self.execute(self.gate["ideal_response"])
        final = finalize_execution(result, self.gate["context"], self.gate["request"])
        self.assertEqual([], runtime_result_errors(result))
        self.assertEqual(1, transport.post_calls)
        self.assertEqual("PASS", final["outcome"])
        self.assertIn("Subject: Grade 4 Writing Launcher", final["explanation"])
        self.assertEqual(1, final["audit"]["attempt_count"])

    def test_rejected_candidate_returns_only_safe_diagnostics(self) -> None:
        candidate = copy.deepcopy(self.gate["ideal_response"])
        candidate["uncertainty_refs"].pop()
        result, transport = self.execute(candidate)
        final = finalize_execution(result, self.gate["context"], self.gate["request"])
        encoded = json.dumps(final, sort_keys=True)
        self.assertEqual(1, transport.post_calls)
        self.assertEqual("SAFE REJECTION", final["outcome"])
        self.assertIn("UNCERTAINTY_MISSING", final["audit"]["violation_codes"])
        self.assertNotIn("validated_response", encoded)
        self.assertFalse(final["audit"]["persisted"])

    def test_safe_audit_contains_no_response_or_reasoning(self) -> None:
        result, _ = self.execute(self.gate["ideal_response"])
        audit = build_safe_execution_audit(result)
        encoded = json.dumps(audit, sort_keys=True)
        self.assertNotIn("validated_response", encoded)
        self.assertNotIn("thinking", encoded)
        self.assertFalse(audit["raw_response_persisted"])
        self.assertFalse(audit["hidden_reasoning_persisted"])
        self.assertFalse(audit["persisted"])

    def test_runner_has_one_execution_site_and_no_retry_loop(self) -> None:
        source = (ROOT / "run_second_controlled_ollama_explain.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(1, source.count("execute_local_explanation("))
        self.assertNotIn("while ", source)
        self.assertNotIn("for attempt", source)
        self.assertNotIn("sleep(", source)

    def test_gate_module_has_no_transport_or_persistence_primitive(self) -> None:
        source = (ROOT / "controlled_execution.py").read_text(encoding="utf-8").lower()
        for forbidden in (
            "urllib", "socket", "subprocess", "/api/chat", "write_text",
            "open(\"w", "open('w", "ollama serve",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
