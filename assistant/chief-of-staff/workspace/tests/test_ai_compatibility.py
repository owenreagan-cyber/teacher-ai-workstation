from __future__ import annotations

import copy
import inspect
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ai_compatibility  # noqa: E402
from ai_compatibility import (  # noqa: E402
    AIProjectionError,
    ai_policy_errors,
    ai_view_errors,
    explain,
    load_ai_policy,
    project_ai_compatibility_view,
    synthetic_internal_model,
)


class AICompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_ai_policy()
        self.internal = synthetic_internal_model()

    def test_ai_trust_policy_is_valid_and_disconnected(self) -> None:
        self.assertEqual([], ai_policy_errors(self.policy))
        self.assertFalse(self.policy["ai_connection_enabled"])
        self.assertFalse(self.policy["raw_observation_export_enabled"])

    def test_safe_synthetic_projection_is_valid(self) -> None:
        view = project_ai_compatibility_view(self.internal, self.policy)
        self.assertEqual([], ai_view_errors(view, self.policy))
        self.assertEqual("sanitized_metadata_projection", view["projection_kind"])

    def test_absolute_path_leakage_is_rejected(self) -> None:
        internal = copy.deepcopy(self.internal)
        internal["entities"][0]["metadata"]["notes"] = "/Users/fictional/private/notes"
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)

    def test_username_and_home_directory_fields_are_rejected(self) -> None:
        for field, value in (("username", "fictional-user"), ("home_directory", "/Users/fictional")):
            internal = copy.deepcopy(self.internal)
            internal[field] = value
            with self.assertRaises(AIProjectionError):
                project_ai_compatibility_view(internal, self.policy)

    def test_raw_filename_leakage_is_rejected(self) -> None:
        internal = copy.deepcopy(self.internal)
        internal["entities"][0]["label"] = "private-notes.docx"
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)

    def test_content_and_private_document_fields_are_rejected(self) -> None:
        for field in ("content", "document_text", "private_document", "raw_observation"):
            internal = copy.deepcopy(self.internal)
            internal["entities"][0][field] = "fictional sensitive text"
            with self.assertRaises(AIProjectionError):
                project_ai_compatibility_view(internal, self.policy)

    def test_credential_and_token_leakage_is_rejected(self) -> None:
        internal = copy.deepcopy(self.internal)
        internal["credentials"] = {"api_key": "sk-fictionalsecret123"}
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)
        internal = copy.deepcopy(self.internal)
        internal["entities"][0]["metadata"]["status"] = "Bearer fictional-token"
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)

    def test_student_private_restricted_and_unknown_are_rejected(self) -> None:
        for sensitivity in ("student_private", "restricted", "unknown"):
            internal = copy.deepcopy(self.internal)
            internal["entities"][0]["classification"] = sensitivity
            with self.assertRaises(AIProjectionError):
                project_ai_compatibility_view(internal, self.policy)

    def test_student_data_field_is_rejected_even_with_safe_classification(self) -> None:
        internal = copy.deepcopy(self.internal)
        internal["entities"][0]["student_data"] = {"name": "Fictional Student"}
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)

    def test_action_capabilities_are_rejected_and_never_exported(self) -> None:
        internal = copy.deepcopy(self.internal)
        internal["action_capabilities"] = ["restore"]
        with self.assertRaises(AIProjectionError):
            project_ai_compatibility_view(internal, self.policy)
        view = project_ai_compatibility_view(self.internal, self.policy)
        self.assertEqual([], view["action_capabilities"])
        self.assertFalse(view["trust"]["executable"])

    def test_authority_or_action_effect_request_is_rejected(self) -> None:
        for field in ("authority_effect", "permission_effect", "action_effect"):
            internal = copy.deepcopy(self.internal)
            internal["entities"][0][field] = "promote"
            with self.assertRaises(AIProjectionError):
                project_ai_compatibility_view(internal, self.policy)

    def test_unknown_and_unreviewed_are_preserved(self) -> None:
        view = project_ai_compatibility_view(self.internal, self.policy)
        entity = view["entities"][0]
        self.assertEqual("unknown", entity["authority"])
        self.assertEqual("unreviewed", entity["review_state"])
        self.assertEqual("high", entity["confidence"])

    def test_projection_contains_summaries_not_raw_observation_identifiers(self) -> None:
        view = project_ai_compatibility_view(self.internal, self.policy)
        summary = view["evidence_summaries"][0]
        self.assertIn("1 observation reference(s)", summary["evidence"])
        self.assertFalse(any(item.startswith("observation:") for item in summary["evidence"]))

    def test_explain_preserves_sources_evidence_and_uncertainty(self) -> None:
        view = project_ai_compatibility_view(self.internal, self.policy)
        explanation = explain(view, "application-concept:grade-4-writing-launcher")
        self.assertEqual("none", explanation["action_authority"])
        self.assertEqual("unknown", explanation["authority"])
        self.assertEqual("high", explanation["confidence"])
        self.assertEqual("unreviewed", explanation["review_state"])
        self.assertTrue(explanation["source_systems"])
        self.assertTrue(explanation["evidence"])
        self.assertTrue(explanation["uncertainty"])

    def test_ai_module_has_no_network_model_agent_scan_or_execution_primitive(self) -> None:
        source = inspect.getsource(ai_compatibility)
        forbidden = (
            "subprocess",
            "requests",
            "urllib",
            "openai",
            "anthropic",
            "os.scandir",
            ".glob(",
            ".rglob(",
            "hashlib",
            "shutil",
        )
        self.assertFalse(any(token in source for token in forbidden))


if __name__ == "__main__":
    unittest.main()
