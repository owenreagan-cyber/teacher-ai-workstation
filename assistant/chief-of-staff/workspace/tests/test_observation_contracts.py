from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sanitization import SanitizationError, sanitize_for_cloud  # noqa: E402
from validate import load_json, validate_schema  # noqa: E402
from validate_observation import (  # noqa: E402
    CONTRACT_SCHEMAS,
    POLICY_SCHEMAS,
    audit_event_errors,
    inventory_run_errors,
    observation_errors,
    recommendation_errors,
    run_validation,
)


class ObservationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(
            (ROOT / "tests/fixtures/observation-cases.json").read_text(
                encoding="utf-8"
            )
        )

    def valid_run(self) -> dict:
        return copy.deepcopy(self.fixtures["inventory_run"]["valid"])

    def valid_observation(self) -> dict:
        return copy.deepcopy(self.fixtures["observation"]["valid_file"])

    def valid_audit_event(self) -> dict:
        return copy.deepcopy(self.fixtures["audit_event"]["valid"])

    def valid_recommendation(self) -> dict:
        return copy.deepcopy(self.fixtures["recommendation"]["valid"])

    def test_all_phase_c_policy_registries_match_closed_schemas(self) -> None:
        for registry_name, schema_name in POLICY_SCHEMAS.items():
            with self.subTest(registry=registry_name):
                validate_schema(
                    load_json(ROOT / "registry" / registry_name),
                    load_json(ROOT / "schemas" / schema_name),
                )

    def test_phase_c_validation_passes(self) -> None:
        self.assertEqual(
            [], [check for check in run_validation() if check.level != "PASS"]
        )

    def test_inventory_run_valid(self) -> None:
        self.assertEqual([], inventory_run_errors(self.valid_run()))

    def test_inventory_run_missing_approval_is_rejected(self) -> None:
        value = self.valid_run()
        value.pop("approval")
        self.assertTrue(inventory_run_errors(value))

    def test_inventory_run_invalid_limits_are_rejected(self) -> None:
        value = self.valid_run()
        value["limits"].update({"max_depth": -1, "max_items": 0})
        errors = inventory_run_errors(value)
        self.assertTrue(any("max_depth" in error for error in errors))
        self.assertTrue(any("max_items" in error for error in errors))

    def test_inventory_run_content_read_is_rejected(self) -> None:
        value = self.valid_run()
        value["content_read_policy"] = "full_content"
        self.assertTrue(inventory_run_errors(value))

    def test_inventory_run_missing_prohibition_is_rejected(self) -> None:
        value = self.valid_run()
        value["prohibited_operations"].remove("hashing")
        self.assertTrue(inventory_run_errors(value))

    def test_valid_file_observation(self) -> None:
        self.assertEqual([], observation_errors(self.valid_observation()))

    def test_valid_unavailable_observation(self) -> None:
        value = self.fixtures["observation"]["unavailable_item"]
        self.assertEqual([], observation_errors(value))

    def test_valid_cloud_placeholder_observation(self) -> None:
        value = self.fixtures["observation"]["cloud_placeholder"]
        self.assertEqual([], observation_errors(value))

    def test_observation_missing_freshness_is_rejected(self) -> None:
        value = self.valid_observation()
        value.pop("freshness")
        self.assertTrue(observation_errors(value))

    def test_observation_authority_claim_is_rejected(self) -> None:
        value = self.valid_observation()
        value["trust"]["authority_claim"] = "canonical"
        self.assertTrue(observation_errors(value))

    def test_observation_content_field_is_rejected(self) -> None:
        value = self.valid_observation()
        value["metadata"]["content"] = "fictional content"
        self.assertTrue(observation_errors(value))

    def test_valid_audit_event(self) -> None:
        self.assertEqual([], audit_event_errors(self.valid_audit_event()))

    def test_audit_event_missing_actor_is_rejected(self) -> None:
        value = self.valid_audit_event()
        value.pop("actor")
        self.assertTrue(audit_event_errors(value))

    def test_audit_event_invalid_target_is_rejected(self) -> None:
        value = self.valid_audit_event()
        value["target_ref"] = "/fictional/absolute/path"
        self.assertTrue(audit_event_errors(value))

    def test_valid_recommendation(self) -> None:
        self.assertEqual([], recommendation_errors(self.valid_recommendation()))

    def test_recommendation_missing_evidence_is_rejected(self) -> None:
        value = self.valid_recommendation()
        value["evidence"] = []
        self.assertTrue(recommendation_errors(value))

    def test_recommendation_marked_as_action_is_rejected(self) -> None:
        value = self.valid_recommendation()
        value["action_state"] = "execute_now"
        self.assertTrue(recommendation_errors(value))

    def test_sanitization_removes_absolute_path_and_sensitive_fields(self) -> None:
        policy = load_json(ROOT / "registry/sanitization.json")
        value = self.fixtures["sanitization"]["local_record"]
        result = sanitize_for_cloud(value, policy, allow_relative_path=True)
        self.assertEqual("projects-fictional", result["source"])
        self.assertEqual("Fictional/history", result["relative_path"])
        self.assertNotIn("absolute_path", result)
        self.assertNotIn("filename", result)
        self.assertNotIn("student_data", result)
        self.assertNotIn("content", result["metadata"])

    def test_relative_path_is_omitted_without_explicit_rule(self) -> None:
        policy = load_json(ROOT / "registry/sanitization.json")
        value = self.fixtures["sanitization"]["local_record"]
        result = sanitize_for_cloud(value, policy)
        self.assertNotIn("relative_path", result)
        self.assertIn("item_ref", result)

    def test_student_private_projection_fails_closed(self) -> None:
        policy = load_json(ROOT / "registry/sanitization.json")
        value = self.fixtures["sanitization"]["student_private_record"]
        with self.assertRaises(SanitizationError):
            sanitize_for_cloud(value, policy)

    def test_contract_schema_set_is_complete(self) -> None:
        self.assertEqual(
            {"inventory_run", "observation", "audit_event", "recommendation"},
            set(CONTRACT_SCHEMAS),
        )


if __name__ == "__main__":
    unittest.main()
