from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pilot import (  # noqa: E402
    PilotBoundaryError,
    enforce_approved_subtree,
    enforce_exact_source_root,
)
from project_pilot import (  # noqa: E402
    build_project_observation,
    git_operation_args,
    load_project_config,
    project_config_errors,
    project_observation_errors,
    summarize_porcelain,
)


RUN_ID = "run:history-project-intelligence-pilot-fictional"


def fictional_git_metadata() -> dict:
    return {
        "repository_detected": True,
        "repository_root_matches_approved": True,
        "current_branch": "fictional-main",
        "head_ref": "0" * 40,
        "dirty_summary": {
            "is_dirty": True,
            "staged_changes": 0,
            "tracked_worktree_changes": 1,
            "untracked_items": 1,
            "conflicted_items": 0,
            "status_records_observed": 2,
            "truncated": False,
        },
        "metadata_method": "read_only_git_allowlist",
        "history_inspected": False,
        "other_branches_inspected": False,
    }


class ProjectPilotTests(unittest.TestCase):
    def observation(self) -> dict:
        return build_project_observation(
            RUN_ID, load_project_config(), fictional_git_metadata()
        )

    def test_project_configuration_is_valid(self) -> None:
        self.assertEqual([], project_config_errors(load_project_config()))

    def test_wrong_project_is_rejected(self) -> None:
        config = copy.deepcopy(load_project_config())
        config["project_id"] = "project:fictional-other"
        self.assertTrue(project_config_errors(config))

    def test_outside_project_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            approved = base / "history"
            outside = base / "other"
            approved.mkdir()
            outside.mkdir()
            with self.assertRaises(PilotBoundaryError):
                enforce_exact_source_root(outside, approved)

    def test_project_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PilotBoundaryError):
                enforce_approved_subtree(Path(temporary), "../other-project")

    def test_repository_metadata_is_accepted(self) -> None:
        observation = self.observation()
        self.assertEqual([], project_observation_errors(observation))
        self.assertTrue(observation["git"]["repository_detected"])
        self.assertEqual("fictional-main", observation["git"]["current_branch"])

    def test_dirty_summary_is_count_only(self) -> None:
        summary = summarize_porcelain(
            " M fictional.py\n?? fictional-new.py\nA  fictional-stage.py\n", 10
        )
        self.assertTrue(summary["is_dirty"])
        self.assertEqual(1, summary["tracked_worktree_changes"])
        self.assertEqual(1, summary["untracked_items"])
        self.assertEqual(1, summary["staged_changes"])
        self.assertNotIn("paths", summary)

    def test_git_mutation_operation_is_rejected(self) -> None:
        for operation in ("checkout", "reset", "pull", "commit", "stash", "branch_create"):
            with self.subTest(operation=operation):
                with self.assertRaises(PilotBoundaryError):
                    git_operation_args(operation)

    def test_active_state_evidence_is_accepted(self) -> None:
        observation = self.observation()
        observation["state_evidence"][0]["state_candidate"] = "active"
        self.assertEqual([], project_observation_errors(observation))

    def test_unknown_state_evidence_is_accepted(self) -> None:
        observation = self.observation()
        self.assertEqual("unknown", observation["state_evidence"][0]["state_candidate"])
        self.assertEqual([], project_observation_errors(observation))

    def test_abandoned_without_owner_is_rejected(self) -> None:
        observation = self.observation()
        observation["state_evidence"][0]["state_candidate"] = "abandoned"
        self.assertTrue(project_observation_errors(observation))

    def test_readme_read_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_project_config())
        config["prohibitions"]["read_readme"] = True
        self.assertTrue(project_config_errors(config))

    def test_source_read_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_project_config())
        config["prohibitions"]["source_content_read"] = True
        self.assertTrue(project_config_errors(config))

    def test_secret_field_is_rejected(self) -> None:
        observation = self.observation()
        observation["secret"] = "fictional-secret"
        self.assertTrue(project_observation_errors(observation))

    def test_relationship_candidate_has_no_authority(self) -> None:
        candidate = self.observation()["relationships"][0]
        self.assertEqual("approved_project_mapping", candidate["basis"]["rule"])
        self.assertEqual("none", candidate["authority_claim"])
        self.assertFalse(candidate["automatic_linking"])

    def test_project_and_observation_identities_are_separate(self) -> None:
        observation = self.observation()
        self.assertEqual("project:history", observation["project_id"])
        self.assertNotEqual(observation["project_id"], observation["observation_id"])
        self.assertEqual(
            "representation:history:local-git",
            observation["path_ref"]["representation_id"],
        )


if __name__ == "__main__":
    unittest.main()
