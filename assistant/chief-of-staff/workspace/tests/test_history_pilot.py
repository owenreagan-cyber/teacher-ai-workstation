from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pilot import (  # noqa: E402
    APPROVED_OUTPUT_ROOT,
    MetadataCollector,
    PilotBoundaryError,
    enforce_approved_subtree,
    enforce_exact_source_root,
    enforce_output_root,
    load_pilot_config,
    pilot_config_errors,
    validate_observation_batch,
)
from validate_observation import audit_event_errors  # noqa: E402


RUN_ID = "run:history-project-metadata-pilot-fictional"
SOURCE_ID = "history-project-local"


class HistoryPilotTests(unittest.TestCase):
    def collector(self, root: Path, **overrides: int) -> MetadataCollector:
        limits = {"max_depth": 2, "max_items": 500, "max_duration_seconds": 60}
        limits.update(overrides)
        return MetadataCollector(root, RUN_ID, SOURCE_ID, **limits)

    def test_pilot_configuration_is_valid(self) -> None:
        self.assertEqual([], pilot_config_errors(load_pilot_config()))

    def test_outside_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            approved = base / "approved"
            outside = base / "outside"
            approved.mkdir()
            outside.mkdir()
            with self.assertRaises(PilotBoundaryError):
                enforce_exact_source_root(outside, approved)

    def test_parent_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PilotBoundaryError):
                enforce_approved_subtree(Path(temporary), "../../Documents")

    def test_symlink_is_recorded_but_never_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "approved"
            root.mkdir()
            outside = base / "outside.txt"
            outside.touch()
            (root / "escape-link").symlink_to(outside)
            collector = self.collector(root)
            observations = collector.collect()
            symlinks = [item for item in observations if item["metadata"]["is_symlink"]]
            self.assertEqual(1, len(symlinks))
            self.assertEqual("unavailable_item", symlinks[0]["item_type"])
            self.assertNotIn("outside.txt", {item["relative_path"] for item in observations})

    def test_excessive_depth_is_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one/two/three").mkdir(parents=True)
            observations = self.collector(root, max_depth=2).collect()
            paths = {item["relative_path"] for item in observations}
            self.assertIn("one/two", paths)
            self.assertNotIn("one/two/three", paths)

    def test_excessive_item_count_stops_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(10):
                (root / f"fictional-{index}.txt").touch()
            collector = self.collector(root, max_items=3)
            observations = collector.collect()
            self.assertEqual(3, len(observations))
            self.assertEqual("item_limit_reached", collector.stop_reason)

    def test_content_read_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_pilot_config())
        config["prohibitions"]["content_read"] = True
        self.assertTrue(pilot_config_errors(config))

    def test_hash_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_pilot_config())
        config["prohibitions"]["hashing"] = True
        self.assertTrue(pilot_config_errors(config))

    def test_write_request_is_rejected(self) -> None:
        config = copy.deepcopy(load_pilot_config())
        config["prohibitions"]["writes"] = True
        self.assertTrue(pilot_config_errors(config))

    def test_file_and_directory_metadata_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fictional-directory").mkdir()
            (root / "fictional.txt").touch()
            observations = self.collector(root).collect()
            types = {item["item_type"] for item in observations}
            self.assertIn("file", types)
            self.assertIn("directory", types)

    def test_provenance_and_authority_remain_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            observations = self.collector(Path(temporary)).collect()
            self.assertEqual(
                [],
                validate_observation_batch(
                    observations,
                    run_id=RUN_ID,
                    source_id=SOURCE_ID,
                    max_items=500,
                ),
            )
            self.assertTrue(all(item["run_id"] == RUN_ID for item in observations))
            self.assertTrue(
                all(item["trust"]["authority_claim"] == "none" for item in observations)
            )
            self.assertTrue(all(item["freshness"]["observed_at"] for item in observations))

    def test_output_outside_local_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PilotBoundaryError):
                enforce_output_root(Path(temporary), APPROVED_OUTPUT_ROOT)

    def test_output_boundary_is_gitignored(self) -> None:
        ignore_lines = {
            line.strip()
            for line in (ROOT.parents[2] / ".gitignore")
            .read_text(encoding="utf-8")
            .splitlines()
        }
        self.assertIn(".local/chief-of-staff/workspace/", ignore_lines)

    def test_validation_failed_audit_event_is_supported(self) -> None:
        event = {
            "schema_version": 1,
            "event_id": "audit:fictional-validation-failed",
            "event_type": "validation_failed",
            "timestamp": "2030-01-02T03:04:05Z",
            "actor": "system:history-metadata-pilot",
            "target_ref": RUN_ID,
            "evidence": {
                "refs": [RUN_ID],
                "summary": "Fictional boundary validation failed.",
            },
            "result": "failed",
        }
        self.assertEqual([], audit_event_errors(event))


if __name__ == "__main__":
    unittest.main()
