from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chief import main as chief_main  # noqa: E402
from human_interface import (  # noqa: E402
    COMMANDS,
    EXPLANATION_SECTIONS,
    REVIEW_STATES,
    build_interface_status,
    build_review_queue,
    interface_policy_errors,
    interface_status_errors,
    load_interface_policy,
    make_review_item,
    render_evidence,
    render_explanation,
    render_recovery,
    render_relationships,
    render_review_queue,
    render_status,
    review_item_errors,
)
from query_layer import DeterministicQueryLayer, QuerySecurityError, load_query_model  # noqa: E402


class HumanInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = load_query_model()

    def setUp(self) -> None:
        self.layer = DeterministicQueryLayer(self.model)

    def test_interface_policy_is_cli_only_and_non_executable(self) -> None:
        policy = load_interface_policy()
        self.assertEqual([], interface_policy_errors(policy))
        self.assertEqual(COMMANDS, set(policy["commands"]))
        self.assertEqual(EXPLANATION_SECTIONS, set(policy["explanation_sections"]))
        self.assertEqual(REVIEW_STATES, set(policy["review_states"]))
        self.assertFalse(policy["web_interface_enabled"])
        self.assertFalse(policy["persistent_service_enabled"])
        self.assertFalse(policy["natural_language_enabled"])
        self.assertFalse(policy["ai_enabled"])
        self.assertFalse(policy["source_write_enabled"])
        self.assertEqual([], policy["action_capabilities"])

    def test_status_contract_reports_health_authority_and_no_actions(self) -> None:
        status = build_interface_status(self.layer)
        self.assertEqual([], interface_status_errors(status))
        self.assertEqual(
            ["Resource Registry", "Workspace Model", "Relationships", "Recovery"],
            [item["name"] for item in status["systems"]],
        )
        self.assertEqual("PASS", status["validation_status"])
        self.assertEqual(13, status["known_entities"])
        self.assertGreater(status["unresolved_items"], 0)
        self.assertEqual(13, status["authority_state"]["assigned"] + status["authority_state"]["unknown"])
        self.assertEqual([], status["actions"])

    def test_status_render_is_deterministic_and_distinguishes_sections(self) -> None:
        value = build_interface_status(self.layer)
        first = render_status(value)
        self.assertEqual(first, render_status(value))
        for section in ("SYSTEMS", "KNOWN", "EVIDENCE", "CONFIDENCE", "AUTHORITY", "UNKNOWNS", "ACTIONS"):
            self.assertIn(section, first)
        self.assertIn("None available.", first)

    def test_explanation_formatter_has_every_required_section(self) -> None:
        explanation = self.layer.explain("application:grade-4-writing-launcher")
        evidence = self.layer.why("application:grade-4-writing-launcher")
        relationships = self.layer.related_to("application:grade-4-writing-launcher")
        rendered = render_explanation(explanation, evidence, relationships)
        headings = [
            "IDENTITY", "KNOWN", "SOURCES", "EVIDENCE", "RELATIONSHIPS",
            "CONFIDENCE", "AUTHORITY", "REVIEW STATE", "UNKNOWNS", "ACTIONS",
        ]
        positions = [rendered.index(heading) for heading in headings]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("High", rendered)
        self.assertIn("Unreviewed", rendered)
        self.assertIn("None available.", rendered)

    def test_unknown_explanation_is_readable_not_failure(self) -> None:
        explanation = self.layer.explain("entity:not-present")
        rendered = render_explanation(explanation, [], [])
        self.assertIn("Type: unknown", rendered)
        self.assertIn("Entity identity or scope membership remains unknown.", rendered)
        self.assertIn("ACTIONS\nNone available.", rendered)

    def test_relationship_formatter_shows_type_direction_evidence_and_confidence(self) -> None:
        related = self.layer.related_to("project:history")
        rendered = render_relationships("project:history", related, ["Relationships remain unreviewed."])
        self.assertIn("representation_of", rendered)
        self.assertIn("outgoing", rendered)
        self.assertIn("EVIDENCE", rendered)
        self.assertIn("CONFIDENCE", rendered)
        self.assertIn("Relationships create no authority.", rendered)

    def test_evidence_formatter_shows_sources_provenance_and_uncertainty(self) -> None:
        evidence = self.layer.why("project:history")
        rendered = render_evidence("project:history", evidence, ["Evidence remains unreviewed."])
        self.assertIn("SOURCES / OBSERVATIONS", rendered)
        self.assertIn("PROVENANCE", rendered)
        self.assertIn("CONFIDENCE", rendered)
        self.assertIn("Evidence creates no authority.", rendered)

    def test_review_queue_is_ordered_and_contains_human_judgment_items(self) -> None:
        first = build_review_queue(self.layer)
        second = build_review_queue(self.layer)
        self.assertEqual(first, second)
        self.assertEqual(sorted(item["item_id"] for item in first), [item["item_id"] for item in first])
        self.assertTrue(any(item["reason_type"] == "unknown_authority" for item in first))
        self.assertTrue(any(item["reason_type"] == "unreviewed_relationship" for item in first))
        self.assertTrue(all(item["recommendation_state"] == "not_an_action" for item in first))
        self.assertTrue(all(item["action_authority"] == "none" for item in first))

    def test_synthetic_review_queue_supports_every_reason(self) -> None:
        model = copy.deepcopy(self.model)
        model["entities"]["project:history"]["evidence_package_ids"] = []
        model["conflicts"] = [{
            "conflict_id": "relationship-conflict:interface-test",
            "subject_ref": "project:history",
            "candidate_refs": [],
        }]
        model["missing_representations"] = [{
            "signal_id": "missing-representation:interface-test",
            "detail": "Synthetic expected representation is missing.",
            "confidence": "medium",
            "review_state": "unreviewed",
        }]
        model["recovery_candidates"] = [{
            "candidate_id": "recovery-candidate:interface-test",
            "subject_ref": "registry-system:writing",
            "candidate_ref": "representation:synthetic:backup",
            "evidence": ["explicit_backup_relationship"],
            "confidence": "high",
            "risk": "medium",
            "next_step": "Teacher review required.",
            "review_state": "unreviewed",
        }]
        queue = build_review_queue(DeterministicQueryLayer(model))
        self.assertEqual(
            {
                "conflict", "unknown_authority", "missing_evidence",
                "missing_representation", "recovery_candidate", "unreviewed_relationship",
            },
            {item["reason_type"] for item in queue},
        )

    def test_review_queue_respects_scope(self) -> None:
        queue = build_review_queue(self.layer, scope="teacher_only")
        self.assertTrue(queue)
        self.assertTrue(all(item["reason_type"] != "unreviewed_relationship" for item in queue))

    def test_all_five_review_states_are_distinct_from_confidence(self) -> None:
        items = []
        for state in sorted(REVIEW_STATES):
            item = make_review_item(
                f"review-item:state:{state}",
                f"entity:{state}",
                "unknown_authority",
                f"Synthetic {state} review state.",
                confidence="high",
                review_state=state,
            )
            self.assertEqual([], review_item_errors(item))
            items.append(item)
        self.assertEqual(REVIEW_STATES, {item["review_state"] for item in items})
        self.assertEqual({"high"}, {item["confidence"] for item in items})

    def test_review_state_filter_does_not_mutate_items(self) -> None:
        unreviewed = build_review_queue(self.layer, review_state="unreviewed")
        approved = build_review_queue(self.layer, review_state="approved")
        self.assertTrue(unreviewed)
        self.assertEqual([], approved)
        self.assertTrue(all(item["review_state"] == "unreviewed" for item in unreviewed))

    def test_review_queue_renderer_keeps_recommendations_non_actions(self) -> None:
        rendered = render_review_queue(build_review_queue(self.layer))
        self.assertIn("RECOMMENDATIONS", rendered)
        self.assertIn("the interface creates no authority", rendered)
        self.assertIn("ACTIONS\nNone available.", rendered)

    def test_recovery_formatter_displays_risk_and_no_capability(self) -> None:
        candidate = {
            "candidate": "representation:synthetic:backup",
            "evidence": ["explicit_backup_relationship"],
            "confidence": "high",
            "risk": "medium",
            "next_step": "Teacher review required.",
            "review_state": "unreviewed",
            "action_authority": "none",
        }
        rendered = render_recovery("resource:synthetic", [candidate], [])
        self.assertIn("confidence high; risk medium", rendered)
        self.assertIn("Teacher review required.", rendered)
        self.assertIn("restore, copy, and move are not implemented", rendered)

    def test_restricted_review_queue_fails_closed(self) -> None:
        model = copy.deepcopy(self.model)
        model["entities"]["project:history"]["classification"] = "restricted"
        with self.assertRaises(QuerySecurityError):
            build_review_queue(DeterministicQueryLayer(model))

    def test_every_cli_command_has_human_and_json_output(self) -> None:
        commands = [
            ["status"],
            ["explain", "project:history"],
            ["related", "project:history"],
            ["evidence", "project:history"],
            ["uncertain"],
            ["recovery", "project:history"],
        ]
        for command in commands:
            with self.subTest(command=command):
                human = io.StringIO()
                with redirect_stdout(human), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, chief_main(command, layer=self.layer))
                self.assertIn("ACTIONS", human.getvalue())
                json_output = io.StringIO()
                with redirect_stdout(json_output), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, chief_main(command + ["--json"], layer=self.layer))
                self.assertTrue(json_output.getvalue().lstrip().startswith(("{", "[")))

    def test_interface_module_has_no_server_ai_scan_or_execution_primitive(self) -> None:
        source = (ROOT / "human_interface.py").read_text(encoding="utf-8")
        for forbidden in (
            "http.server", "flask", "fastapi", "django", "socket", "subprocess",
            "requests", "urllib", "os.walk", ".rglob(", ".glob(", ".iterdir(",
            "os.remove", "os.rename", "os.replace", "shutil", "openai",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source.lower())


if __name__ == "__main__":
    unittest.main()
