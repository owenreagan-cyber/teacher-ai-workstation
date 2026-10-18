from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_compatibility import ai_view_errors, project_ai_compatibility_view  # noqa: E402
from chief import main as chief_main  # noqa: E402
from query_layer import (  # noqa: E402
    DeterministicQueryLayer,
    QUERY_TYPES,
    QuerySecurityError,
    SCOPES,
    explanation_errors,
    load_query_model,
    load_query_policy,
    make_query,
    query_errors,
    query_policy_errors,
    response_errors,
    uncertainty_errors,
)


class QueryLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_model = load_query_model()

    def setUp(self) -> None:
        self.layer = DeterministicQueryLayer(self.base_model)

    def test_policy_is_fixed_closed_and_non_executable(self) -> None:
        policy = load_query_policy()
        self.assertEqual([], query_policy_errors(policy))
        self.assertEqual(QUERY_TYPES, set(policy["query_types"]))
        self.assertEqual(SCOPES, set(policy["scopes"]))
        self.assertFalse(policy["ai_enabled"])
        self.assertFalse(policy["live_recovery_candidates_enabled"])
        self.assertEqual([], policy["action_capabilities"])

    def test_valid_query_contract(self) -> None:
        query = make_query(
            "entity_lookup", "project:history", query_id="query:test:history",
            created_at="2026-09-13T12:00:00Z",
        )
        self.assertEqual([], query_errors(query))
        self.assertEqual([], response_errors(self.layer.execute(query)))

    def test_every_query_type_is_supported(self) -> None:
        targets = {
            "entity_lookup": "project:history",
            "relationship_lookup": "project:history",
            "evidence_lookup": "project:history",
            "recovery_candidate_lookup": "project:history",
            "project_lookup": "project:history",
            "application_lookup": "application:grade-4-writing-launcher",
            "resource_lookup": "resource:writing",
        }
        for query_type, target in targets.items():
            with self.subTest(query_type=query_type):
                response = self.layer.execute(make_query(query_type, target))
                self.assertEqual(query_type, response["query_type"])
                self.assertEqual("none", response["authority_effect"])
                self.assertEqual("none", response["action_authority"])

    def test_unknown_entity_is_uncertainty_not_failure(self) -> None:
        explanation = self.layer.explain("application:unknown")
        self.assertEqual("unknown", explanation["subject_type"])
        self.assertEqual("unknown", explanation["confidence"])
        self.assertTrue(explanation["uncertainties"])
        self.assertEqual([], explanation_errors(explanation))

    def test_application_explanation_has_required_context(self) -> None:
        explanation = self.layer.explain("application:grade-4-writing-launcher")
        self.assertEqual("application", explanation["subject_type"])
        self.assertEqual("high", explanation["confidence"])
        self.assertEqual("unreviewed", explanation["review_state"])
        self.assertTrue(explanation["sources"])
        self.assertTrue(explanation["evidence_packages"])
        self.assertTrue(explanation["relationships"])
        self.assertTrue(explanation["uncertainties"])
        self.assertEqual("unknown", explanation["authority_context"]["role"])
        self.assertEqual("none", explanation["action_authority"])

    def test_project_explanation_preserves_static_authority_basis(self) -> None:
        explanation = self.layer.explain("project:history")
        self.assertEqual("project", explanation["subject_type"])
        self.assertEqual("canonical", explanation["authority_context"]["role"])
        self.assertEqual("source_code", explanation["authority_context"]["scope"])
        self.assertEqual("approved_policy", explanation["authority_context"]["basis"])
        self.assertEqual("none", explanation["action_authority"])

    def test_resource_explanation_uses_registry_alias(self) -> None:
        explanation = self.layer.explain("resource:writing")
        self.assertEqual("registry-system:writing", explanation["subject_ref"])
        self.assertEqual("registry_entry", explanation["subject_type"])
        self.assertTrue(explanation["evidence_packages"])

    def test_evidence_includes_provenance_confidence_and_review(self) -> None:
        evidence = self.layer.why("project:history")
        self.assertTrue(evidence)
        for package in evidence:
            self.assertTrue(package["provenance"])
            self.assertIn(package["confidence"], {"high", "medium", "low", "unknown"})
            self.assertIn(package["review_state"], {"unreviewed", "reviewed", "rejected"})
            self.assertEqual("none", package["authority_effect"])
            self.assertEqual("none", package["action_authority"])

    def test_missing_evidence_is_visible(self) -> None:
        model = copy.deepcopy(self.base_model)
        model["entities"]["project:history"]["evidence_package_ids"] = []
        layer = DeterministicQueryLayer(model)
        explanation = layer.explain("project:history")
        self.assertIn("No evidence package is linked to this entity.", explanation["uncertainties"])
        self.assertEqual([], layer.why("project:history"))

    def test_relationships_are_ordered_and_preserve_provenance(self) -> None:
        first = self.layer.related_to("application:grade-4-writing-launcher")
        second = self.layer.related_to("application:grade-4-writing-launcher")
        self.assertEqual(first, second)
        self.assertEqual(
            sorted(item["relationship_id"] for item in first),
            [item["relationship_id"] for item in first],
        )
        self.assertTrue(all(item["provenance"]["rule_id"] for item in first))
        self.assertTrue(all(item["authority_effect"] == "none" for item in first))

    def test_relationship_filter_is_deterministic(self) -> None:
        related = self.layer.related_to(
            "application:grade-4-writing-launcher",
            filters={"relationship_type": "used_by_application"},
        )
        self.assertEqual(1, len(related))
        self.assertEqual("used_by_application", related[0]["relationship_type"])

    def test_scope_and_classification_filter_related_entities(self) -> None:
        self.assertEqual(
            [],
            self.layer.related_to(
                "application:grade-4-writing-launcher", scope="teacher_only"
            ),
        )
        response = self.layer.execute(make_query(
            "application_lookup", "", filters={"classification": "teacher_internal"}
        ))
        self.assertTrue(response["results"])
        self.assertTrue(
            all(item["classification"] == "teacher_internal" for item in response["results"])
        )

    def test_query_responses_preserve_result_uncertainty(self) -> None:
        entity = self.layer.execute(make_query(
            "application_lookup", "application:grade-4-writing-launcher"
        ))
        relationship = self.layer.execute(make_query(
            "relationship_lookup", "project:history"
        ))
        evidence = self.layer.execute(make_query("evidence_lookup", "project:history"))
        self.assertTrue(entity["uncertainties"])
        self.assertTrue(any("unreviewed" in item for item in relationship["uncertainties"]))
        self.assertTrue(any("unreviewed" in item for item in evidence["uncertainties"]))

    def test_conflict_is_an_uncertainty_and_not_an_authority_decision(self) -> None:
        model = copy.deepcopy(self.base_model)
        relationship_id = model["relationships"][0]["relationship_id"]
        model["conflicts"] = [{
            "conflict_id": "relationship-conflict:synthetic",
            "subject_ref": "project:history",
            "candidate_refs": [relationship_id, "relationship:synthetic:b"],
        }]
        layer = DeterministicQueryLayer(model)
        conflicts = [item for item in layer.uncertain() if item["uncertainty_type"] == "conflict"]
        self.assertEqual(1, len(conflicts))
        self.assertEqual("review_opportunity_not_failure", conflicts[0]["interpretation"])
        self.assertEqual("none", conflicts[0]["action_authority"])
        self.assertEqual([], uncertainty_errors(conflicts[0]))
        related = layer.related_to("project:history")
        self.assertTrue(any("relationship-conflict:synthetic" in item["conflicts"] for item in related))
        explanation = layer.explain("project:history")
        self.assertTrue(any("relationship-conflict:synthetic" in item for item in explanation["uncertainties"]))

    def test_uncertainty_order_is_stable(self) -> None:
        first = self.layer.uncertain()
        second = self.layer.uncertain()
        self.assertEqual(first, second)
        self.assertEqual(
            sorted((item["uncertainty_type"], item["item_ref"], item["detail"]) for item in first),
            [(item["uncertainty_type"], item["item_ref"], item["detail"]) for item in first],
        )

    def test_recovery_is_empty_for_live_model_and_has_no_action(self) -> None:
        response = self.layer.execute(make_query("recovery_candidate_lookup", "resource:writing"))
        self.assertEqual([], response["results"])
        self.assertIn("disabled", response["uncertainties"][0])
        self.assertEqual("none", response["action_authority"])

    def test_synthetic_recovery_candidate_displays_risk_without_restore(self) -> None:
        model = copy.deepcopy(self.base_model)
        model["recovery_candidates"] = [{
            "candidate_id": "recovery-candidate:synthetic",
            "subject_ref": "registry-system:writing",
            "candidate_ref": "representation:synthetic:backup",
            "evidence": ["explicit_backup_relationship"],
            "confidence": "high",
            "risk": "medium",
            "next_step": "Teacher review required before any separately authorized action.",
            "review_state": "unreviewed",
        }]
        result = DeterministicQueryLayer(model).recovery_candidates("resource:writing")
        self.assertEqual("medium", result[0]["risk"])
        self.assertEqual("none", result[0]["action_authority"])
        self.assertNotIn("restore", result[0])

    def test_restricted_entity_and_scope_fail_closed(self) -> None:
        model = copy.deepcopy(self.base_model)
        model["entities"]["project:history"]["classification"] = "restricted"
        layer = DeterministicQueryLayer(model)
        with self.assertRaises(QuerySecurityError):
            layer.explain("project:history")
        with self.assertRaises(QuerySecurityError):
            self.layer.uncertain(scope="restricted")
        allowed = layer.explain(
            "project:history", permission_grants=["workspace.restricted.read"]
        )
        self.assertEqual("project:history", allowed["subject_ref"])

    def test_all_scopes_are_accepted_without_changing_authority(self) -> None:
        for scope in sorted(SCOPES - {"restricted"}):
            with self.subTest(scope=scope):
                response = self.layer.execute(make_query("project_lookup", "", scope=scope))
                self.assertEqual("none", response["authority_effect"])
                self.assertEqual("none", response["action_authority"])

    def test_phase_i_projection_consumes_explanation_shape(self) -> None:
        internal = self.layer.ai_compatibility_input("application:grade-4-writing-launcher")
        view = project_ai_compatibility_view(internal)
        self.assertEqual([], ai_view_errors(view))
        self.assertFalse(view["trust"]["authoritative"])
        self.assertFalse(view["trust"]["executable"])
        self.assertEqual([], view["action_capabilities"])

    def test_status_is_non_executable(self) -> None:
        status = self.layer.status()
        self.assertFalse(status["ai_enabled"])
        self.assertFalse(status["live_recovery_candidates_enabled"])
        self.assertEqual([], status["action_capabilities"])

    def test_cli_commands(self) -> None:
        commands = [
            ["explain", "project:history", "--json"],
            ["related", "project:history", "--json"],
            ["evidence", "project:history", "--json"],
            ["uncertain", "--json"],
            ["recovery", "project:history", "--json"],
            ["status", "--json"],
        ]
        for command in commands:
            with self.subTest(command=command), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, chief_main(command, layer=self.layer))

    def test_implementation_has_no_discovery_network_or_execution_primitives(self) -> None:
        source = (ROOT / "query_layer.py").read_text(encoding="utf-8")
        for forbidden in (
            "os.walk", ".rglob(", ".glob(", ".iterdir(", "subprocess", "requests",
            "urllib", "socket", "shutil", "os.remove", "os.rename", "os.replace",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
