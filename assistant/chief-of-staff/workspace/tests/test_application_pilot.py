from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from application_pilot import (  # noqa: E402
    ReadOnlyApplicationMetadata,
    application_config_errors,
    application_observation_errors,
    build_application_observation,
    enforce_exact_application,
    load_application_config,
    normalize_mdls_value,
)
from pilot import PilotBoundaryError  # noqa: E402


RUN_ID = "run:grade-4-writing-application-pilot-fictional"


def fictional_metadata() -> dict:
    return {
        "exists": True,
        "is_directory": True,
        "is_symlink": False,
        "display_name": "Fictional Writing Tool",
        "bundle_identifier": "org.example.fictional-writing",
        "version": "1.0-fictional",
        "application_type": "macos_application_bundle",
        "content_type": "com.apple.application-bundle",
        "availability": "available",
        "metadata_source": "spotlight_metadata_allowlist",
        "bundle_contents_read": False,
        "signing_inspected": False,
    }


class ApplicationPilotTests(unittest.TestCase):
    def observation(self) -> dict:
        return build_application_observation(
            RUN_ID, load_application_config(), fictional_metadata()
        )

    def test_application_configuration_is_valid(self) -> None:
        self.assertEqual([], application_config_errors(load_application_config()))

    def test_wrong_application_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            approved = base / "Approved.app"
            wrong = base / "Wrong.app"
            approved.mkdir()
            wrong.mkdir()
            with self.assertRaises(PilotBoundaryError):
                enforce_exact_application(wrong, approved)

    def test_alternate_application_is_rejected(self) -> None:
        config = copy.deepcopy(load_application_config())
        config["approved_bundle_ref"] = "applications/alternate.app"
        self.assertTrue(application_config_errors(config))

    def test_application_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            approved = base / "Approved.app"
            alternate = base / "Alternate.app"
            approved.mkdir()
            alternate.mkdir()
            traversal = approved / ".." / "Alternate.app"
            with self.assertRaises(PilotBoundaryError):
                enforce_exact_application(traversal, approved)

    def test_launch_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_application_config())
        config["prohibitions"]["application_launch"] = True
        self.assertTrue(application_config_errors(config))

    def test_modification_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_application_config())
        config["prohibitions"]["application_modification"] = True
        self.assertTrue(application_config_errors(config))

    def test_container_read_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_application_config())
        config["prohibitions"]["container_read"] = True
        self.assertTrue(application_config_errors(config))

    def test_application_identities_are_separate(self) -> None:
        observation = self.observation()
        identities = {
            observation["application_concept_id"],
            observation["application_instance_id"],
            observation["observation_id"],
        }
        self.assertEqual(3, len(identities))
        self.assertEqual([], application_observation_errors(observation))

    def test_relationship_candidates_have_no_authority(self) -> None:
        relationships = self.observation()["relationships"]
        self.assertEqual(2, len(relationships))
        self.assertTrue(all(item["authority_claim"] == "none" for item in relationships))
        self.assertTrue(all(item["review_state"] == "unreviewed" for item in relationships))
        self.assertTrue(all(item["automatic_linking"] is False for item in relationships))

    def test_allowed_metadata_fields_are_accepted(self) -> None:
        observation = self.observation()
        self.assertEqual([], application_observation_errors(observation))
        self.assertEqual("Fictional Writing Tool", observation["metadata"]["display_name"])

    def test_forbidden_application_content_field_is_rejected(self) -> None:
        observation = self.observation()
        observation["metadata"]["application_contents"] = "fictional-content"
        self.assertTrue(application_observation_errors(observation))

    def test_unknown_metadata_key_is_rejected_before_query(self) -> None:
        reader = ReadOnlyApplicationMetadata(
            Path("/fictional/NotObserved.app"), query_limit=4, timeout_seconds=1
        )
        with self.assertRaises(PilotBoundaryError):
            reader.query("kMDItemForbiddenPrivateData")
        self.assertEqual(0, reader.query_count)

    def test_mdls_null_and_string_normalization(self) -> None:
        self.assertIsNone(normalize_mdls_value("(null)"))
        self.assertEqual("Fictional App", normalize_mdls_value('"Fictional App"'))


if __name__ == "__main__":
    unittest.main()
