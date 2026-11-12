"""LaunchAgent plist tests (no real install, never the real LaunchAgents folder)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from cosd import launchagent
from cosd.launchagent import LABEL, install_with_launchctl, render_plist, unload_with_launchctl


class LaunchAgentTest(unittest.TestCase):
    def setUp(self):
        # Every test in this module points the helper at a throwaway LaunchAgents folder, so the
        # real ~/Library/LaunchAgents is never written, chmod-ed or removed by the test suite.
        self._tmp = tempfile.TemporaryDirectory(prefix="cosd-launchagent-test-")
        self.addCleanup(self._tmp.cleanup)
        self.fake_agent_dir = Path(self._tmp.name) / "LaunchAgents"
        self._old_env = os.environ.get(launchagent.AGENT_DIR_ENV)
        os.environ[launchagent.AGENT_DIR_ENV] = str(self.fake_agent_dir)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._old_env is None:
            os.environ.pop(launchagent.AGENT_DIR_ENV, None)
        else:
            os.environ[launchagent.AGENT_DIR_ENV] = self._old_env

    def test_plist_has_no_secrets(self):
        pl = render_plist()
        raw = str(pl)
        self.assertIn(LABEL, raw)
        self.assertNotIn("Bearer", raw)
        self.assertNotIn("token", raw.lower())
        self.assertEqual(pl["RunAtLoad"], False)

    def test_install_remove_fake_launchctl(self):
        loaded = []
        unloaded = []

        def load(p: str) -> None:
            loaded.append(p)

        def unload(p: str) -> None:
            unloaded.append(p)

        path = install_with_launchctl(load)
        self.assertTrue(loaded)
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent, self.fake_agent_dir)
        unload_with_launchctl(unload)
        self.assertTrue(unloaded)
        self.assertFalse(path.exists())

    def test_the_real_launchagents_folder_is_never_used(self):
        real = launchagent.AGENT_DIR / launchagent.PLIST_NAME
        before = (real.exists(), real.stat().st_mtime_ns if real.exists() else None)

        path = install_with_launchctl(lambda _p: None)
        try:
            self.assertEqual(launchagent.agent_dir(), self.fake_agent_dir)
            self.assertEqual(path, self.fake_agent_dir / launchagent.PLIST_NAME)
            self.assertNotEqual(path, real)
            self.assertNotIn(real.parent, path.parents)
        finally:
            unload_with_launchctl(lambda _p: None)

        after = (real.exists(), real.stat().st_mtime_ns if real.exists() else None)
        self.assertEqual(after, before, "the test must not create, replace, or remove the real plist")

    def test_without_the_override_the_real_folder_is_the_default(self):
        os.environ.pop(launchagent.AGENT_DIR_ENV, None)
        self.assertEqual(launchagent.agent_dir(), Path.home() / "Library" / "LaunchAgents")
        self.assertEqual(launchagent.plist_path(), launchagent.AGENT_DIR / launchagent.PLIST_NAME)


if __name__ == "__main__":
    unittest.main()
