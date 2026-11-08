"""COS_USE_DAEMON fallback behavior."""
from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest

from support import REPO_ROOT, CosdStateTest, RunningServer

from cos import cli


class FallbackTests(CosdStateTest):
    def test_auto_fallback_without_daemon(self):
        os.environ.pop("COS_USE_DAEMON", None)
        code, out, err = self._run("ask", "--json", "what time is it")
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', out)

    def test_required_fails_without_daemon(self):
        os.environ["COS_USE_DAEMON"] = "required"
        code, out, err = self._run("status", "--json")
        self.assertNotEqual(code, 0)
        self.assertIn("required", out + err)

    def test_disabled_uses_standalone(self):
        os.environ["COS_USE_DAEMON"] = "disabled"
        code, out, _ = self._run("status", "--json")
        self.assertEqual(code, 0)
        self.assertNotIn("via_daemon", out)

    def test_auto_uses_daemon_when_up(self):
        os.environ["COS_USE_DAEMON"] = "auto"
        srv = RunningServer(self.state)
        try:
            _, out, _ = self._run("status", "--json")
            self.assertIn("via_daemon", out)
        finally:
            srv.stop()

    def _run(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()
