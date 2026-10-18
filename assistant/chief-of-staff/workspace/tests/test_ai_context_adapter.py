from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ai_context_adapter import (
    ALLOWED_CAPABILITIES,
    ALLOWED_TASKS,
    REQUIRED_RESTRICTIONS,
    SOURCE_LAYERS,
    AIContextBoundaryError,
    ai_context_package_errors,
    ai_response_validation_errors,
    build_ai_context,
    build_local_model_audit,
    build_local_model_request,
    build_synthetic_local_model_response,
    load_local_model_boundary_policy,
    local_model_audit_errors,
    local_model_boundary_policy_errors,
    local_model_request_errors,
    local_model_response_errors,
    synthetic_local_model_boundary_bundle,
    validate_ai_response,
)
from query_layer import DeterministicQueryLayer


ROOT = Path(__file__).resolve().parents[1]
WRITING_ENTITY = "application-concept:grade-4-writing-launcher"


class LayerProxy:
    def __init__(self, layer: DeterministicQueryLayer) -> None:
        self.layer = layer
        self.entities = copy.deepcopy(layer.entities)
        self.explain_calls = 0
        self.relationship_calls = 0
        self.evidence_calls = 0
        self.explanation_mutator = lambda value: value
        self.relationship_mutator = lambda value: value
        self.evidence_mutator = lambda value: value

    def explain(self, entity_id: str):
        self.explain_calls += 1
        original = self.layer.explain(entity_id)
        entity = self.entities.get(original["subject_ref"])
        if entity is not None:
            original["summary"] = entity["summary"]
            original["confidence"] = entity["confidence"]
            original["review_state"] = entity["review_state"]
            original["authority_context"] = copy.deepcopy(entity["authority_context"])
        return self.explanation_mutator(original)

    def related_to(self, entity_id: str):
        self.relationship_calls += 1
        return self.relationship_mutator(self.layer.related_to(entity_id))

    def why(self, entity_id: str):
        self.evidence_calls += 1
        return self.evidence_mutator(self.layer.why(entity_id))


class AIContextAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_local_model_boundary_policy()
        cls.bundle = synthetic_local_model_boundary_bundle()

    def test_policy_is_closed_contract_only_and_non_executable(self) -> None:
        self.assertEqual([], local_model_boundary_policy_errors(self.policy))
        self.assertEqual(SOURCE_LAYERS, set(self.policy["source_layers"]))
        self.assertEqual(ALLOWED_TASKS, set(self.policy["tasks"]))
        self.assertEqual(ALLOWED_CAPABILITIES, set(self.policy["capabilities"]))
        self.assertEqual([], self.policy["actions"])
        self.assertTrue(all(value is False for value in self.policy["persistence"].values()))
        for key in (
            "network_enabled", "model_invocation_enabled", "agent_enabled",
            "tool_calling_enabled", "action_execution_enabled",
            "host_local_ai_data_enabled",
        ):
            self.assertFalse(self.policy[key])

    def test_approved_stack_is_named_as_a_non_connected_contract(self) -> None:
        model = self.policy["model_contract"]
        self.assertEqual("ollama", model["runtime"])
        self.assertEqual("qwen3.5:35b", model["model"])
        self.assertEqual("Q4_K_M", model["quantization"])
        self.assertFalse(model["connector_enabled"])
        self.assertFalse(model["execution_enabled"])

    def test_context_package_uses_existing_three_layers(self) -> None:
        proxy = LayerProxy(DeterministicQueryLayer())
        package = build_ai_context(WRITING_ENTITY, query_layer=proxy)
        self.assertEqual([], ai_context_package_errors(package, self.policy))
        self.assertEqual(1, proxy.explain_calls)
        self.assertEqual(1, proxy.relationship_calls)
        self.assertEqual(1, proxy.evidence_calls)

    def test_same_input_produces_same_context_package(self) -> None:
        first = build_ai_context(WRITING_ENTITY)
        second = build_ai_context(WRITING_ENTITY)
        self.assertEqual(first, second)

    def test_context_preserves_identity_evidence_and_relationships(self) -> None:
        context = self.bundle["context"]
        self.assertEqual(WRITING_ENTITY, context["entities"][0]["entity_id"])
        self.assertEqual("Grade 4 Writing Launcher", context["entities"][0]["label"])
        self.assertEqual("application", context["entities"][0]["type"])
        self.assertTrue(context["evidence_summary"])
        self.assertTrue(context["relationships"])

    def test_context_preserves_confidence_uncertainty_authority_and_review(self) -> None:
        context = self.bundle["context"]
        explanation = DeterministicQueryLayer().explain(WRITING_ENTITY)
        entity_confidence = next(
            item for item in context["confidence"] if item["subject_ref"] == WRITING_ENTITY
        )
        entity_review = next(
            item for item in context["review_state"] if item["subject_ref"] == WRITING_ENTITY
        )
        self.assertEqual(explanation["confidence"], entity_confidence["value"])
        self.assertEqual(explanation["uncertainties"], context["uncertainties"])
        self.assertEqual(explanation["authority_context"]["role"], context["authority_context"][0]["role"])
        self.assertEqual(explanation["review_state"], entity_review["state"])

    def test_capability_is_explicit_and_actions_remain_empty(self) -> None:
        context = self.bundle["context"]
        self.assertEqual(["explain"], context["capabilities"])
        self.assertEqual([], context["actions"])
        self.assertEqual(REQUIRED_RESTRICTIONS, set(context["restrictions"]))
        self.assertEqual("none", context["action_authority"])

    def test_harmless_unlisted_internal_fields_are_not_projected(self) -> None:
        proxy = LayerProxy(DeterministicQueryLayer())
        proxy.entities[WRITING_ENTITY]["internal_display_hint"] = "not projected"
        context = build_ai_context(WRITING_ENTITY, query_layer=proxy)
        encoded = json.dumps(context, sort_keys=True)
        self.assertNotIn("internal_display_hint", encoded)
        self.assertNotIn("not projected", encoded)

    def test_raw_observations_are_rejected(self) -> None:
        proxy = LayerProxy(DeterministicQueryLayer())

        def add_raw_observation(values):
            changed = copy.deepcopy(values)
            changed[0]["raw_observation"] = {"content": "forbidden"}
            return changed

        proxy.evidence_mutator = add_raw_observation
        with self.assertRaises(AIContextBoundaryError):
            build_ai_context(WRITING_ENTITY, query_layer=proxy)

    def test_paths_private_filenames_and_student_fields_fail_closed(self) -> None:
        mutations = (
            ("summary", "/Users/example/private/report.txt"),
            ("summary", "private-notes.docx"),
            ("student_name", "Synthetic Student"),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                proxy = LayerProxy(DeterministicQueryLayer())
                proxy.entities[WRITING_ENTITY][key] = value
                with self.assertRaises(AIContextBoundaryError):
                    build_ai_context(WRITING_ENTITY, query_layer=proxy)

    def test_restricted_or_unknown_classification_fails_closed(self) -> None:
        for classification in ("restricted", "student_private", "unknown"):
            with self.subTest(classification=classification):
                proxy = LayerProxy(DeterministicQueryLayer())
                proxy.entities[WRITING_ENTITY]["classification"] = classification
                with self.assertRaises(AIContextBoundaryError):
                    build_ai_context(WRITING_ENTITY, query_layer=proxy)

    def test_unknown_entity_cannot_become_ai_context(self) -> None:
        with self.assertRaises(AIContextBoundaryError):
            build_ai_context("application-concept:not-present")

    def test_local_model_request_is_contract_only(self) -> None:
        context = self.bundle["context"]
        request = self.bundle["request"]
        self.assertEqual([], local_model_request_errors(request, context, self.policy))
        self.assertEqual("explain", request["task"])
        self.assertEqual(["explain"], request["capabilities"])
        self.assertEqual([], request["actions"])
        self.assertEqual("not_connected", request["connector_state"])
        self.assertEqual("not_executed", request["execution_state"])

    def test_non_explain_task_is_rejected(self) -> None:
        request = copy.deepcopy(self.bundle["request"])
        request["task"] = "plan"
        self.assertTrue(local_model_request_errors(request, self.bundle["context"], self.policy))

    def test_structured_synthetic_explanation_passes(self) -> None:
        response = self.bundle["response"]
        self.assertEqual(
            [],
            local_model_response_errors(response, self.bundle["request"], self.bundle["context"]),
        )
        self.assertEqual("pass", self.bundle["validation"]["validation_result"])
        self.assertEqual([], self.bundle["validation"]["violations"])

    def test_unsupported_claim_is_rejected_even_with_known_evidence_id(self) -> None:
        response = copy.deepcopy(self.bundle["response"])
        response["claims"][0]["statement"] = "The application owns every Writing resource."
        errors = local_model_response_errors(response, self.bundle["request"], self.bundle["context"])
        self.assertTrue(any("unsupported known claim" in error for error in errors))

    def test_invented_authority_is_rejected(self) -> None:
        response = copy.deepcopy(self.bundle["response"])
        response["authority_context"][0]["role"] = "canonical"
        errors = local_model_response_errors(response, self.bundle["request"], self.bundle["context"])
        self.assertTrue(any("invented or changed authority" in error for error in errors))

    def test_invented_permission_or_access_is_rejected(self) -> None:
        for field, value in (
            ("permissions_claimed", "filesystem.write"),
            ("access_claims", "I have access"),
        ):
            with self.subTest(field=field):
                response = copy.deepcopy(self.bundle["response"])
                response[field] = [value]
                self.assertTrue(
                    local_model_response_errors(
                        response, self.bundle["request"], self.bundle["context"]
                    )
                )

    def test_action_instructions_are_rejected(self) -> None:
        for statement in ("Move the application.", "Delete old versions."):
            with self.subTest(statement=statement):
                response = copy.deepcopy(self.bundle["response"])
                response["claims"][0]["statement"] = statement
                errors = local_model_response_errors(
                    response, self.bundle["request"], self.bundle["context"]
                )
                self.assertTrue(any("action instruction" in error for error in errors))

    def test_canonical_and_access_assertions_are_rejected(self) -> None:
        for statement, expected in (
            ("This is canonical.", "invented canonical authority"),
            ("I have access to the application.", "invented access"),
        ):
            with self.subTest(statement=statement):
                response = copy.deepcopy(self.bundle["response"])
                response["claims"][0]["statement"] = statement
                errors = local_model_response_errors(
                    response, self.bundle["request"], self.bundle["context"]
                )
                self.assertTrue(any(expected in error for error in errors))

    def test_confidence_inflation_is_rejected(self) -> None:
        response = copy.deepcopy(self.bundle["response"])
        target = next(
            claim for claim in response["claims"]
            if claim["claim_type"] == "evidence" and claim["confidence"] != "high"
        )
        target["confidence"] = "high"
        errors = local_model_response_errors(response, self.bundle["request"], self.bundle["context"])
        self.assertTrue(any("confidence" in error for error in errors))

    def test_missing_uncertainty_and_changed_review_state_are_rejected(self) -> None:
        missing = copy.deepcopy(self.bundle["response"])
        missing["uncertainties"] = missing["uncertainties"][1:]
        changed = copy.deepcopy(self.bundle["response"])
        changed["review_state"][0]["state"] = "approved"
        self.assertTrue(any(
            "uncertainty" in error
            for error in local_model_response_errors(missing, self.bundle["request"], self.bundle["context"])
        ))
        self.assertTrue(any(
            "review state" in error
            for error in local_model_response_errors(changed, self.bundle["request"], self.bundle["context"])
        ))

    def test_rejected_response_produces_non_executable_validation_record(self) -> None:
        response = copy.deepcopy(self.bundle["response"])
        response["claims"][0]["statement"] = "Delete old versions."
        validation = validate_ai_response(
            response, self.bundle["request"], self.bundle["context"], self.policy
        )
        self.assertEqual("rejected", validation["validation_result"])
        self.assertTrue(validation["violations"])
        self.assertEqual([], ai_response_validation_errors(validation))
        self.assertEqual("not_executed", validation["execution_state"])
        self.assertFalse(validation["persisted"])

    def test_audit_contract_is_in_memory_and_non_executable(self) -> None:
        audit = build_local_model_audit(self.bundle["validation"])
        self.assertEqual([], local_model_audit_errors(audit))
        self.assertEqual("qwen3.5:35b", audit["model"])
        self.assertEqual("explain", audit["task"])
        self.assertEqual("pass", audit["validation_result"])
        self.assertEqual("not_executed", audit["execution_state"])
        self.assertFalse(audit["persisted"])
        self.assertEqual("none", audit["action_authority"])

    def test_module_has_no_connector_network_tool_action_or_persistence_runtime(self) -> None:
        source = (ROOT / "ai_context_adapter.py").read_text(encoding="utf-8").lower()
        for forbidden in (
            "import ollama", "from ollama", "import requests", "from requests",
            "import urllib", "from urllib", "import socket", "from socket",
            "http.client", "subprocess", "openai", "anthropic", "langchain",
            "autogen", "crewai", "os.walk", ".rglob(", ".glob(", ".iterdir(",
            "os.remove", "os.rename", "os.replace", "shutil", "write_text",
            "open(\"w", "open('w", "tool_call(", "execute_action(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
