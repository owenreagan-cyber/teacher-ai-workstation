"""LaunchAgent plist tests (no real install)."""
from __future__ import annotations

import unittest

from cosd.launchagent import LABEL, install_with_launchctl, render_plist, unload_with_launchctl


class LaunchAgentTest(unittest.TestCase):
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
        try:
            unload_with_launchctl(unload)
            self.assertTrue(unloaded)
        finally:
            from cosd.launchagent import plist_path

            if plist_path().is_file():
                plist_path().unlink()
