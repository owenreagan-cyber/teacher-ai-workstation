from __future__ import annotations

import copy
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relationship_pilot import (  # noqa: E402
    detect_relationship_conflicts,
    detect_relationship_drift,
    evidence_package_errors,
    load_relationship_configuration,
    make_evidence_package,
    make_relationship_candidate,
    relationship_candidate_errors,
    relationship_audit_event,
    relationship_conflict_errors,
    relationship_config_errors,
    relationship_drift_errors,
)
from validate_observation import audit_event_errors  # noqa: E402


RELATIONSHIP_ID = "relationship:fictional:project-application"
OBSERVATION_REF = "observation:fictional:source"


class RelationshipPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = {
            "project:fictional": {
                "node_id": "project:fictional",
                "node_type": "Project",
            },
            "application-concept:fictional": {
                "node_id": "application-concept:fictional",
                "node_type": "ApplicationConcept",
            },
            "application-concept:alternate": {
                "node_id": "application-concept:alternate",
                "node_type": "ApplicationConcept",
            },
        }
        self.package = make_evidence_package(
            RELATIONSHIP_ID,
            "Fictional project relates to fictional application.",
            ["declared_application_mapping"],
            [OBSERVATION_REF],
        )
        self.candidate = make_relationship_candidate(
            RELATIONSHIP_ID,
            "used_by_application",
            "project:fictional",
            "application-concept:fictional",
            self.package,
            source_phase="F",
            source_observation_ref=OBSERVATION_REF,
            rule_id="declared_application_mapping",
            observed_at="2026-09-12T12:00:00Z",
        )

    def errors(self, candidate: dict | None = None, package: dict | None = None) -> list[str]:
        candidate = candidate or self.candidate
        package = package or self.package
        return relationship_candidate_errors(
            candidate, self.nodes, {package["package_id"]: package}
        )

    def test_valid_candidate(self) -> None:
        self.assertEqual([], self.errors())

    def test_missing_evidence_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        del candidate["evidence"]
        self.assertTrue(self.errors(candidate))

    def test_invalid_target_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["target_ref"] = "registry-system:missing"
        self.assertIn("relationship target does not resolve to a graph node", self.errors(candidate))

    def test_evidence_package_is_required(self) -> None:
        self.assertIn(
            "relationship evidence package does not resolve",
            relationship_candidate_errors(self.candidate, self.nodes, {}),
        )

    def test_evidence_confidence_is_required(self) -> None:
        package = copy.deepcopy(self.package)
        del package["confidence"]
        self.assertTrue(evidence_package_errors(package))

    def test_evidence_review_state_is_required(self) -> None:
        package = copy.deepcopy(self.package)
        del package["review_state"]
        self.assertTrue(evidence_package_errors(package))

    def test_relationship_has_no_authority_or_permission_effect(self) -> None:
        self.assertEqual("none", self.candidate["authority_claim"])
        self.assertEqual("none", self.candidate["ownership_effect"])
        self.assertEqual("none", self.candidate["permission_effect"])
        self.assertEqual("none", self.candidate["action_effect"])

    def test_owner_asserted_requires_explicit_owner_evidence(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["assertion_type"] = "owner_asserted"
        self.assertTrue(any("owner evidence" in error for error in self.errors(candidate)))

    def test_registry_asserted_requires_registry_evidence(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["assertion_type"] = "registry_asserted"
        self.assertTrue(any("registry evidence" in error for error in self.errors(candidate)))

    def test_conflicting_relationships_are_unresolved(self) -> None:
        alternate = copy.deepcopy(self.candidate)
        alternate["relationship_id"] = "relationship:fictional:project-alternate-application"
        alternate["target_ref"] = "application-concept:alternate"
        alternate["evidence"]["package_id"] = "evidence-package:fictional:alternate"
        conflicts = detect_relationship_conflicts([self.candidate, alternate])
        self.assertEqual(1, len(conflicts))
        self.assertEqual([], relationship_conflict_errors(conflicts[0]))
        self.assertEqual("unresolved", conflicts[0]["resolution_state"])
        self.assertFalse(conflicts[0]["automatic_resolution"])

    def test_changed_relationship_detects_drift_without_deletion(self) -> None:
        current = copy.deepcopy(self.candidate)
        current["relationship_id"] = "relationship:fictional:current"
        current["target_ref"] = "application-concept:alternate"
        drift = detect_relationship_drift([self.candidate], [current])
        self.assertEqual(1, len(drift))
        self.assertEqual([], relationship_drift_errors(drift[0]))
        self.assertEqual("relationship_changed", drift[0]["result"])
        self.assertFalse(drift[0]["automatic_deletion"])

    def test_action_relationship_type_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["relationship_type"] = "relationship_execute"
        self.assertTrue(self.errors(candidate))

    def test_configuration_names_only_fixed_existing_inputs(self) -> None:
        config, policy = load_relationship_configuration()
        self.assertEqual([], relationship_config_errors(config, policy))
        changed = copy.deepcopy(config)
        changed["evidence_inputs"][0]["artifact_ref"] = "observations/alternate.json"
        self.assertTrue(relationship_config_errors(changed, policy))

    def test_conflict_and_review_audit_events_are_supported(self) -> None:
        run_id = "run:relationship-intelligence-pilot-fictional"
        timestamp = "2026-09-12T12:00:00Z"
        conflict = relationship_audit_event(
            run_id,
            "relationship-conflict:fictional",
            "relationship_conflict_detected",
            timestamp,
            1,
        )
        reviewed = relationship_audit_event(
            run_id,
            RELATIONSHIP_ID,
            "relationship_reviewed",
            timestamp,
            2,
            actor="teacher:owen",
        )
        self.assertEqual([], audit_event_errors(conflict))
        self.assertEqual([], audit_event_errors(reviewed))


if __name__ == "__main__":
    unittest.main()
