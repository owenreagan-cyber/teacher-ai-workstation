"""bin/cos CLI compatibility with daemon routing."""
from __future__ import annotations

import contextlib
import io
import os
import unittest

from support import REPO_ROOT, CosdStateTest, RunningServer

from cos import cli


class CliCompatTests(CosdStateTest):
    def test_ask_json_shape(self):
        os.environ["COS_USE_DAEMON"] = "auto"
        srv = RunningServer(self.state)
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["ask", "--json", "what time is it"])
            self.assertEqual(code, 0)
            body = json_load(out.getvalue())
            self.assertTrue(body.get("ok"))
            self.assertIn("text", body)
        finally:
            srv.stop()

    def test_status_exit_code(self):
        os.environ["COS_USE_DAEMON"] = "disabled"
        code = cli.main(["status", "--json"])
        self.assertEqual(code, 0)


def json_load(raw: str) -> dict:
    import json
    return json.loads(raw)
