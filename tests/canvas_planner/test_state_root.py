"""Canvas Planner state-root contract tests (fixtures only)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.canvas_planner import state_root as configured_state_root
from scripts.canvas_planner.state_root import DEFAULT_STATE_ROOT, deployment_root, intake_root


class StateRootTest(unittest.TestCase):
    def test_default_is_installed_main_local_not_checkout_relative(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TAW_STATE_ROOT", None)
            self.assertEqual(configured_state_root(), DEFAULT_STATE_ROOT)
            self.assertEqual(DEFAULT_STATE_ROOT, Path("/Users/owen/Projects/teacher-ai-workstation/.local"))

    def test_fixture_override_controls_all_canvas_packet_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"TAW_STATE_ROOT": tmp}):
            self.assertEqual(configured_state_root(), Path(tmp))
            self.assertEqual(intake_root(), Path(tmp) / "canvas-llm" / "intake")
            self.assertEqual(deployment_root(), Path(tmp) / "canvas-llm" / "deployments")


if __name__ == "__main__":
    unittest.main()
