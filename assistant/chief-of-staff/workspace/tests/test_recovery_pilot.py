from __future__ import annotations

import copy
import inspect
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import recovery_pilot  # noqa: E402
from recovery_pilot import (  # noqa: E402
    assess_recovery_confidence,
    assess_recovery_risk,
    build_synthetic_scenarios,
    detect_recovery_conflicts,
    load_recovery_configuration,
    load_recovery_evidence_inputs,
    make_recovery_candidate,
    make_recovery_evidence_package,
    make_signal,
    recovery_audit_event,
    recovery_candidate_errors,
    recovery_config_errors,
    recovery_conflict_errors,
    recovery_evidence_errors,
    signal_errors,
    synthetic_scenario_errors,
)
from validate_observation import audit_event_errors  # noqa: E402


class RecoveryPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.subject = "logical-resource:fictional-subject"
        self.candidate_ref = "representation:fictional:candidate"
        self.evidence = [
            {
                "type": "relationship",
                "source": "relationship:fictional:representation",
                "detail": "representation_of connects candidate to subject",
                "strength": "high",
            }
        ]
        self.package = make_recovery_evidence_package(
            "recovery-evidence:fictional-candidate",
            self.subject,
            self.candidate_ref,
            "A fictional relationship supports a candidate.",
            self.evidence,
            ["Candidate availability is unknown."],
        )
        self.candidate = make_recovery_candidate(
            "recovery-candidate:fictional-candidate",
            self.subject,
            self.candidate_ref,
            "alternate_representation_candidate",
            self.package,
        )

    def candidate_errors(self, candidate: dict | None = None, package: dict | None = None) -> list[str]:
        candidate = candidate or self.candidate
        package = package or self.package
        return recovery_candidate_errors(candidate, {package["package_id"]: package})

    def test_valid_candidate(self) -> None:
        self.assertEqual([], self.candidate_errors())

    def test_missing_evidence_package_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        del candidate["evidence_package"]
        self.assertTrue(self.candidate_errors(candidate))

    def test_unresolved_evidence_package_is_rejected(self) -> None:
        self.assertIn(
            "recovery candidate evidence package does not resolve",
            recovery_candidate_errors(self.candidate, {}),
        )

    def test_invalid_candidate_reference_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["candidate_ref"] = "random file"
        self.assertTrue(self.candidate_errors(candidate))

    def test_nonrepresentation_candidate_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["candidate_ref"] = "project:fictional-candidate"
        package = copy.deepcopy(self.package)
        package["candidate"] = "project:fictional-candidate"
        self.assertIn(
            "recovery candidate must identify a representation",
            self.candidate_errors(candidate, package),
        )

    def test_backup_retains_backup_authority_context(self) -> None:
        backup_package = make_recovery_evidence_package(
            "recovery-evidence:fictional-backup",
            self.subject,
            self.candidate_ref,
            "Explicit fictional backup evidence.",
            [{"type": "authority_assertion", "source": "authority-assertion:fictional-backup", "detail": "role=backup scope=backup_recovery explicit declaration", "strength": "high"}],
            ["Canonical authority is unresolved."],
        )
        backup = make_recovery_candidate(
            "recovery-candidate:fictional-backup",
            self.subject,
            self.candidate_ref,
            "backup_candidate",
            backup_package,
            authority_role="backup",
            authority_scope="backup_recovery",
            authority_basis="explicit_backup_declaration",
        )
        self.assertEqual([], recovery_candidate_errors(backup, {backup_package["package_id"]: backup_package}))
        self.assertEqual("backup", backup["authority_context"]["role"])

    def test_backup_cannot_be_recast_as_canonical(self) -> None:
        backup = copy.deepcopy(self.candidate)
        backup["candidate_type"] = "backup_candidate"
        backup["authority_context"]["role"] = "canonical"
        backup["authority_context"]["scope"] = "backup_recovery"
        self.assertTrue(any("backup/backup_recovery" in error for error in self.candidate_errors(backup)))

    def test_mirror_retains_mirror_authority_context(self) -> None:
        mirror_package = make_recovery_evidence_package(
            "recovery-evidence:fictional-mirror",
            self.subject,
            self.candidate_ref,
            "Explicit fictional mirror evidence.",
            [{"type": "authority_assertion", "source": "authority-assertion:fictional-mirror", "detail": "role=mirror scope=backup_recovery explicit declaration", "strength": "high"}],
            ["Canonical authority is unresolved."],
        )
        mirror = make_recovery_candidate(
            "recovery-candidate:fictional-mirror",
            self.subject,
            self.candidate_ref,
            "mirror_candidate",
            mirror_package,
            authority_role="mirror",
            authority_scope="backup_recovery",
        )
        self.assertEqual([], recovery_candidate_errors(mirror, {mirror_package["package_id"]: mirror_package}))

    def test_timestamp_cannot_establish_canonical_authority(self) -> None:
        candidate = copy.deepcopy(self.candidate)
        candidate["authority_context"]["role"] = "canonical"
        candidate["authority_context"]["basis"] = "timestamp"
        self.assertIn("timestamp cannot establish canonical authority", self.candidate_errors(candidate))

    def test_known_representation_relationship_is_high_confidence(self) -> None:
        self.assertEqual("high", assess_recovery_confidence(self.evidence))

    def test_project_relationship_is_medium_confidence(self) -> None:
        evidence = [{"type": "relationship", "source": "relationship:fictional:project", "detail": "belongs_to_project evidence", "strength": "medium"}]
        self.assertEqual("medium", assess_recovery_confidence(evidence))

    def test_filename_similarity_never_becomes_high_confidence(self) -> None:
        evidence = [{"type": "filename_similarity", "source": "synthetic:name", "detail": "same filename", "strength": "high"}]
        self.assertEqual("low", assess_recovery_confidence(evidence))

    def test_insufficient_evidence_is_unknown(self) -> None:
        self.assertEqual("unknown", assess_recovery_confidence([]))

    def test_evidence_confidence_mismatch_is_rejected(self) -> None:
        package = copy.deepcopy(self.package)
        package["confidence"] = "low"
        self.assertIn(
            "recovery evidence confidence does not match deterministic assessment",
            recovery_evidence_errors(package),
        )

    def test_conflicting_candidates_have_no_automatic_winner(self) -> None:
        alternate = copy.deepcopy(self.candidate)
        alternate["candidate_id"] = "recovery-candidate:fictional-alternate"
        alternate["candidate_ref"] = "representation:fictional:alternate"
        alternate["evidence_package"]["package_id"] = "recovery-evidence:fictional-alternate"
        conflicts = detect_recovery_conflicts([self.candidate, alternate])
        self.assertEqual(1, len(conflicts))
        self.assertEqual([], recovery_conflict_errors(conflicts[0]))
        self.assertEqual("unresolved", conflicts[0]["resolution_state"])
        self.assertFalse(conflicts[0]["automatic_winner"])

    def test_all_missing_resource_signal_types_are_supported(self) -> None:
        for index, signal_type in enumerate(sorted(recovery_pilot.SIGNAL_TYPES), start=1):
            signal = make_signal(
                f"recovery-signal:fictional-{index}",
                self.subject,
                signal_type,
                "previous",
                "current",
                [],
                "unknown",
            )
            self.assertEqual([], signal_errors(signal))

    def test_signal_is_review_opportunity_not_failure(self) -> None:
        signal = make_signal(
            "recovery-signal:fictional-review",
            self.subject,
            "representation_missing",
            "available",
            "missing_hypothesis",
            [],
            "unknown",
        )
        self.assertEqual("review_opportunity_not_failure", signal["interpretation"])
        self.assertEqual("synthetic_only", signal["source_mode"])

    def test_four_synthetic_scenarios_satisfy_contracts(self) -> None:
        config, _policy = load_recovery_configuration()
        inputs = load_recovery_evidence_inputs(config)
        scenarios = build_synthetic_scenarios(inputs)
        self.assertEqual([], synthetic_scenario_errors(scenarios))
        insufficient = next(item for item in scenarios if item["scenario_id"] == "insufficient-evidence")
        self.assertEqual([], insufficient["candidates"])
        self.assertEqual([], insufficient["recommendations"])

    def test_all_recovery_audit_event_types_are_supported(self) -> None:
        cases = [
            ("recovery_candidate_created", "recovery-candidate:fictional"),
            ("recovery_candidate_validated", "recovery-candidate:fictional"),
            ("recovery_conflict_detected", "recovery-conflict:fictional"),
            ("recovery_reviewed", "recovery-candidate:fictional"),
        ]
        for index, (event_type, target_ref) in enumerate(cases, start=1):
            event = recovery_audit_event(
                f"audit:recovery-fictional-{index}",
                event_type,
                target_ref,
                actor="teacher:owen" if event_type == "recovery_reviewed" else "system:recovery-intelligence-pilot",
            )
            self.assertEqual([], audit_event_errors(event))

    def test_configuration_forbids_live_and_mutating_capabilities(self) -> None:
        config, policy = load_recovery_configuration()
        self.assertEqual([], recovery_config_errors(config, policy))
        self.assertFalse(config["live_signal_detection_enabled"])
        self.assertFalse(config["live_candidate_generation_enabled"])
        self.assertFalse(config["host_local_output_enabled"])
        self.assertTrue(all(value is False for value in config["prohibitions"].values()))

    def test_recovery_module_has_no_scan_hash_copy_or_subprocess_primitive(self) -> None:
        source = inspect.getsource(recovery_pilot)
        forbidden = ("os.scandir", ".glob(", ".rglob(", "subprocess", "hashlib", "shutil", ".unlink(", ".rename(")
        self.assertFalse(any(token in source for token in forbidden))

    def test_candidates_are_not_actions(self) -> None:
        self.assertEqual("not_an_action", self.candidate["action_state"])
        self.assertEqual("none", self.candidate["authority_effect"])
        self.assertFalse(self.candidate["authority_context"]["canonical_promotion"])

    def test_high_confidence_does_not_imply_low_risk(self) -> None:
        context = {
            "authority_ambiguity": True,
            "candidate_age": "unknown",
            "sensitivity": "teacher_internal",
            "provenance_complete": True,
            "conflicting_relationships": False,
            "scope_uncertainty": False,
        }
        risk, basis = assess_recovery_risk(context)
        self.assertEqual("high", self.candidate["confidence"])
        self.assertEqual("medium", risk)
        self.assertIn("authority_ambiguity", basis)

    def test_missing_provenance_and_conflict_are_high_risk(self) -> None:
        context = {
            "authority_ambiguity": False,
            "candidate_age": "current",
            "sensitivity": "teacher_internal",
            "provenance_complete": False,
            "conflicting_relationships": True,
            "scope_uncertainty": False,
        }
        risk, basis = assess_recovery_risk(context)
        self.assertEqual("high", risk)
        self.assertIn("missing_provenance", basis)
        self.assertIn("conflicting_relationships", basis)

    def test_recovery_candidate_has_required_explanation(self) -> None:
        explanation = self.candidate["explanation"]
        self.assertEqual(self.candidate_ref, explanation["candidate"])
        self.assertTrue(explanation["why_found"])
        self.assertTrue(explanation["supporting_evidence"])
        self.assertTrue(explanation["unknowns"])
        self.assertEqual("review_candidate", explanation["recommended_next_step"])

    def test_recovery_package_embeds_shared_evidence_contract(self) -> None:
        shared = self.package["shared_evidence_package"]
        self.assertEqual("recovery", shared["evidence_type"])
        self.assertEqual(self.subject, shared["subject_ref"])
        self.assertEqual("none", shared["authority_effect"])


if __name__ == "__main__":
    unittest.main()
