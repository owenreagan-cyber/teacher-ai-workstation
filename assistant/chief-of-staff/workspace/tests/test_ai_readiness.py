from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_compatibility import AIProjectionError, synthetic_internal_model  # noqa: E402
from ai_readiness import (  # noqa: E402
    CLAIM_TYPES,
    REASONING_CAPABILITIES,
    RESTRICTED_CAPABILITIES,
    REJECTION_RULES,
    TRUST_LEVELS,
    agent_grant_errors,
    ai_output_candidate_errors,
    ai_readiness_policy_errors,
    audit_record_errors,
    build_context_projection,
    build_prompt_envelope,
    build_synthetic_agent_grant,
    build_synthetic_ai_output,
    context_projection_errors,
    load_ai_readiness_policy,
    prompt_envelope_errors,
    route_request,
    synthetic_readiness_bundle,
)


class AIReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_ai_readiness_policy()
        cls.bundle = synthetic_readiness_bundle()

    def test_policy_declares_capabilities_without_enabling_runtime(self) -> None:
        self.assertEqual([], ai_readiness_policy_errors(self.policy))
        self.assertEqual(REASONING_CAPABILITIES, set(self.policy["capabilities"]["reasoning"]))
        self.assertEqual(RESTRICTED_CAPABILITIES, set(self.policy["capabilities"]["restricted"]))
        self.assertTrue(all(value is False for value in self.policy["runtime"].values()))

    def test_trust_levels_zero_through_four_have_fixed_states(self) -> None:
        levels = {item["level"]: item for item in self.policy["trust_levels"]}
        self.assertEqual(set(TRUST_LEVELS), set(levels))
        self.assertEqual("current", levels[0]["state"])
        self.assertEqual("planned", levels[1]["state"])
        self.assertEqual("planned", levels[2]["state"])
        self.assertEqual("future_only", levels[3]["state"])
        self.assertEqual("prohibited", levels[4]["state"])
        self.assertEqual([], levels[3]["allowed_capabilities"])
        self.assertEqual([], levels[4]["allowed_capabilities"])

    def test_deterministic_answer_is_always_preferred(self) -> None:
        routed = route_request(
            deterministic_answer_available=True,
            context_projection_available=True,
            trust_level=2,
            policy=self.policy,
        )
        self.assertEqual("deterministic_explanation", routed["route"])
        self.assertFalse(routed["ai_requested"])
        self.assertEqual("none", routed["model"])

    def test_ai_escalation_requires_projection_then_stays_disabled(self) -> None:
        missing = route_request(
            deterministic_answer_available=False,
            context_projection_available=False,
            trust_level=1,
            policy=self.policy,
        )
        ready = route_request(
            deterministic_answer_available=False,
            context_projection_available=True,
            trust_level=1,
            policy=self.policy,
        )
        self.assertEqual("context_projection_required", missing["route"])
        self.assertEqual("ai_runtime_disabled", ready["route"])
        self.assertFalse(missing["ai_requested"])
        self.assertFalse(ready["ai_requested"])

    def test_context_projection_is_schema_valid_and_sanitized(self) -> None:
        projection = self.bundle["projection"]
        self.assertEqual([], context_projection_errors(projection, self.policy))
        encoded = json.dumps(projection, sort_keys=True)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("raw observation", encoded.lower())
        self.assertFalse(projection["raw_observations_included"])
        self.assertEqual([], projection["action_capabilities"])

    def test_context_contains_identity_evidence_confidence_uncertainty_authority_and_review(self) -> None:
        projection = self.bundle["projection"]
        self.assertTrue(projection["identity"])
        self.assertTrue(projection["sources"])
        self.assertTrue(projection["evidence"])
        self.assertIn(projection["confidence"], {"high", "medium", "low", "unknown"})
        self.assertTrue(projection["uncertainties"])
        self.assertTrue(projection["authority_states"])
        self.assertTrue(projection["review_states"])

    def test_raw_paths_and_restricted_data_fail_closed(self) -> None:
        raw = synthetic_internal_model()
        raw["entities"][0]["metadata"]["path"] = "/Users/example/private.txt"
        restricted = synthetic_internal_model()
        restricted["entities"][0]["classification"] = "restricted"
        student = synthetic_internal_model()
        student["entities"][0]["student_name"] = "Example Student"
        private = synthetic_internal_model()
        private["entities"][0]["private_document"] = "Private notes"
        with self.assertRaises(AIProjectionError):
            build_context_projection(raw, destination="cloud", policy=self.policy)
        with self.assertRaises(AIProjectionError):
            build_context_projection(restricted, destination="cloud", policy=self.policy)
        with self.assertRaises(AIProjectionError):
            build_context_projection(student, destination="cloud", policy=self.policy)
        with self.assertRaises(AIProjectionError):
            build_context_projection(private, destination="cloud", policy=self.policy)

    def test_local_and_cloud_are_policy_only_with_distinct_requirements(self) -> None:
        local = self.policy["model_policy"]["local"]
        cloud = self.policy["model_policy"]["cloud"]
        self.assertEqual("architecture_only", local["state"])
        self.assertEqual("architecture_only", cloud["state"])
        self.assertIn("local_permission", local["requirements"])
        self.assertIn("human_cloud_export_approval", cloud["requirements"])
        self.assertIn("no_student_data", cloud["requirements"])
        local_projection = build_context_projection(
            synthetic_internal_model(), destination="local", policy=self.policy
        )
        cloud_projection = build_context_projection(
            synthetic_internal_model(), destination="cloud", policy=self.policy
        )
        for projection in (local_projection, cloud_projection):
            encoded = json.dumps(projection, sort_keys=True)
            self.assertNotIn("/Users/", encoded)
            self.assertFalse(projection["raw_observations_included"])
            self.assertEqual([], projection["action_capabilities"])

    def test_prompt_boundary_has_four_required_sections_and_no_connection(self) -> None:
        prompt = self.bundle["prompt"]
        self.assertEqual([], prompt_envelope_errors(prompt, self.bundle["projection"], self.policy))
        self.assertEqual("not_connected", prompt["runtime_state"])
        self.assertEqual("none", prompt["action_authority"])
        self.assertTrue(prompt["required_output"]["cite_evidence"])
        self.assertTrue(prompt["required_output"]["expose_uncertainty"])

    def test_prompt_cannot_grant_restricted_capability(self) -> None:
        prompt = copy.deepcopy(self.bundle["prompt"])
        prompt["capabilities_granted"].append("delete")
        self.assertTrue(prompt_envelope_errors(prompt, self.bundle["projection"], self.policy))

    def test_prompt_rejects_raw_path_in_user_request(self) -> None:
        prompt = copy.deepcopy(self.bundle["prompt"])
        prompt["user_request"] = "Explain /Users/example/private.txt"
        self.assertTrue(prompt_envelope_errors(prompt, self.bundle["projection"], self.policy))

    def test_valid_synthetic_output_is_grounded_and_non_executable(self) -> None:
        output = self.bundle["output"]
        self.assertEqual([], ai_output_candidate_errors(output, self.bundle["projection"]))
        self.assertEqual(CLAIM_TYPES, set(self.policy["output_validation"]["claim_types"]))
        self.assertEqual(REJECTION_RULES, set(self.policy["output_validation"]["rejection_rules"]))
        self.assertEqual([], output["requested_actions"])
        self.assertEqual("none", output["authority_effect"])
        self.assertTrue(any(claim["claim_type"] == "unknown" for claim in output["claims"]))
        self.assertTrue(output["uncertainties"])

    def test_unsupported_claim_is_rejected(self) -> None:
        output = copy.deepcopy(self.bundle["output"])
        output["claims"][0]["evidence_refs"] = ["evidence-package:not-present"]
        self.assertTrue(any(
            "unsupported evidence" in error
            for error in ai_output_candidate_errors(output, self.bundle["projection"])
        ))

    def test_uncited_known_claim_is_rejected(self) -> None:
        output = copy.deepcopy(self.bundle["output"])
        output["claims"][0]["evidence_refs"] = []
        self.assertTrue(any(
            "requires evidence citation" in error
            for error in ai_output_candidate_errors(output, self.bundle["projection"])
        ))

    def test_confidence_inflation_is_rejected(self) -> None:
        projection = copy.deepcopy(self.bundle["projection"])
        projection["evidence"][0]["confidence"] = "low"
        output = build_synthetic_ai_output(projection)
        output["claims"][0]["confidence"] = "high"
        self.assertTrue(any(
            "confidence inflation" in error
            for error in ai_output_candidate_errors(output, projection)
        ))

    def test_authority_change_hidden_action_and_missing_uncertainty_are_rejected(self) -> None:
        authority = copy.deepcopy(self.bundle["output"])
        authority["authority_effect"] = "canonical"
        action = copy.deepcopy(self.bundle["output"])
        action["claims"][0]["statement"] = "Delete the unsupported representation."
        missing = copy.deepcopy(self.bundle["output"])
        missing["uncertainties"] = []
        self.assertTrue(ai_output_candidate_errors(authority, self.bundle["projection"]))
        self.assertTrue(any(
            "hidden action" in error
            for error in ai_output_candidate_errors(action, self.bundle["projection"])
        ))
        self.assertTrue(ai_output_candidate_errors(missing, self.bundle["projection"]))

    def test_hallucination_policy_keeps_inference_distinct(self) -> None:
        policy = self.policy["hallucination_handling"]
        self.assertEqual(CLAIM_TYPES, set(policy["required_distinctions"]))
        self.assertFalse(policy["inference_may_become_fact"])
        self.assertEqual("reject", policy["unsupported_claim_disposition"])
        self.assertEqual("mark_unknown", policy["missing_evidence_disposition"])

    def test_audit_contract_records_required_fields_without_writing_log(self) -> None:
        audit = self.bundle["audit"]
        self.assertEqual([], audit_record_errors(audit))
        self.assertEqual("unselected", audit["model"])
        self.assertEqual("pass", audit["output_validation"])
        self.assertEqual("required", audit["human_review"])
        self.assertFalse(audit["persisted"])
        self.assertEqual("not_executed", audit["execution_state"])

    def test_human_approval_boundary_is_explicit(self) -> None:
        approval = self.policy["human_approval"]
        for decision in (
            "authority_changes", "canonical_replacement", "restore", "delete",
            "move_canonical_resources", "permission_changes", "cloud_export_approval",
        ):
            self.assertIn(decision, approval["always_human"])
        self.assertFalse(approval["approval_runtime_enabled"])

    def test_future_agent_grant_requires_scope_duration_approval_rollback_and_audit(self) -> None:
        grant = build_synthetic_agent_grant()
        self.assertEqual([], agent_grant_errors(grant))
        self.assertTrue(grant["target_scope"])
        self.assertTrue(grant["duration"]["expires_at"])
        self.assertTrue(grant["approval"]["required"])
        self.assertTrue(grant["rollback_plan"])
        self.assertTrue(grant["audit_required"])
        self.assertFalse(grant["execution_enabled"])
        self.assertFalse(grant["autonomous"])
        self.assertEqual("none", grant["action_authority"])

    def test_ai_readiness_module_has_no_model_network_agent_or_execution_runtime(self) -> None:
        source = (ROOT / "ai_readiness.py").read_text(encoding="utf-8").lower()
        for forbidden in (
            "requests", "urllib", "socket", "http.client", "subprocess", "openai",
            "anthropic", "ollama", "transformers", "langchain", "autogen", "crewai",
            "os.walk", ".rglob(", ".glob(", ".iterdir(", "os.remove", "os.rename",
            "os.replace", "shutil", "write_text", "open(\"w", "open('w",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
