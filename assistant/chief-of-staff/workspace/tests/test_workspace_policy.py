from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validate import (  # noqa: E402
    REGISTRY_SCHEMAS,
    SchemaValidationError,
    authority_errors,
    classification_assignment_errors,
    load_json,
    permission_errors,
    project_errors,
    run_validation,
    validate_schema,
)


class WorkspacePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(
            (ROOT / "tests/fixtures/policy-cases.json").read_text(encoding="utf-8")
        )

    def test_all_six_registries_match_closed_schemas(self) -> None:
        for registry_name, schema_name in REGISTRY_SCHEMAS.items():
            with self.subTest(registry=registry_name):
                validate_schema(
                    load_json(ROOT / "registry" / registry_name),
                    load_json(ROOT / "schemas" / schema_name),
                )

    def test_static_policy_semantics_pass(self) -> None:
        checks = run_validation()
        self.assertEqual([], [check for check in checks if check.level != "PASS"])

    def test_schema_rejects_additional_properties(self) -> None:
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        with self.assertRaises(SchemaValidationError):
            validate_schema({"unexpected": True}, schema)

    def test_schema_rejects_unsupported_keywords(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_schema("fixture", {"format": "uri"})

    def test_home_root_is_never_recursive_scan_root(self) -> None:
        workspace = load_json(ROOT / "registry/workspace.json")
        policy = workspace["recursive_scan_policy"]
        self.assertFalse(policy["implicit_recursion_allowed"])
        self.assertIn("/Users/owen", policy["never_recursive_scan_roots"])

    def test_storage_sources_are_unobserved_and_disconnected(self) -> None:
        storage = load_json(ROOT / "registry/storage-sources.json")
        self.assertFalse(storage["runtime_connections_enabled"])
        self.assertTrue(
            all(source["connection_state"] == "unknown" for source in storage["sources"])
        )
        self.assertTrue(
            all(source["freshness"]["observed_at"] is None for source in storage["sources"])
        )

    def test_valid_backup_and_unknown_authority_are_allowed(self) -> None:
        values = self.fixtures["authority"]["valid_sources"]
        self.assertEqual([], authority_errors(values))

    def test_conflicting_canonical_claims_are_rejected(self) -> None:
        values = self.fixtures["authority"]["canonical_conflict"]
        self.assertTrue(any("conflicting canonical" in item for item in authority_errors(values)))

    def test_backup_cannot_claim_canonical(self) -> None:
        values = self.fixtures["authority"]["backup_claims_canonical"]
        self.assertTrue(any("backup source" in item for item in authority_errors(values)))

    def test_deployment_cannot_claim_source_authority(self) -> None:
        values = self.fixtures["authority"]["deployment_claims_source"]
        self.assertTrue(any("deployment cannot" in item for item in authority_errors(values)))

    def test_classification_basis_with_evidence_is_valid(self) -> None:
        value = self.fixtures["classification"]["valid"]
        self.assertEqual([], classification_assignment_errors(value))

    def test_classification_without_basis_is_rejected(self) -> None:
        value = self.fixtures["classification"]["missing_basis"]
        self.assertTrue(classification_assignment_errors(value))

    def test_classification_without_evidence_is_rejected(self) -> None:
        value = self.fixtures["classification"]["empty_evidence"]
        self.assertTrue(classification_assignment_errors(value))

    def test_abandoned_requires_owner_confirmation(self) -> None:
        values = self.fixtures["projects"]["timestamp_only_abandoned"]
        self.assertTrue(project_errors(values))

    def test_owner_confirmed_abandoned_is_valid(self) -> None:
        values = self.fixtures["projects"]["owner_confirmed_abandoned"]
        self.assertEqual([], project_errors(values))

    def test_level_zero_cannot_gain_mutating_capability(self) -> None:
        policy = load_json(ROOT / "registry/permissions.json")
        invalid = copy.deepcopy(policy)
        capability = next(
            item for item in invalid["capabilities"] if item["id"] == "file.move"
        )
        capability["minimum_level"] = 0
        invalid["levels"][0]["allowed_capabilities"].append("file.move")
        self.assertTrue(any("level 0" in item for item in permission_errors(invalid)))

    def test_level_four_requires_scoped_grants_approval_and_stops(self) -> None:
        policy = load_json(ROOT / "registry/permissions.json")
        invalid = copy.deepcopy(policy)
        invalid["levels"][4]["scoped_grants_required"] = False
        self.assertTrue(any("level 4" in item for item in permission_errors(invalid)))

    def test_phase_b_contains_concepts_but_no_application_instances(self) -> None:
        applications = load_json(ROOT / "registry/applications.json")
        self.assertGreater(len(applications["concepts"]), 0)
        self.assertEqual([], applications["installed_instances"])


if __name__ == "__main__":
    unittest.main()
