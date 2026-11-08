"""Ask stream adapter tests (fixture mode)."""
from __future__ import annotations

import os
import unittest

from cos.service import iter_ask_stream
from cos.cli import build_runtime


class AskStreamTest(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("COS_FIXTURE_DIR")
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        os.environ["COS_FIXTURE_DIR"] = os.path.join(root, "evals", "fixtures", "default")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("COS_FIXTURE_DIR", None)
        else:
            os.environ["COS_FIXTURE_DIR"] = self._old

    def test_chunks_then_done(self):
        rt = build_runtime()
        items = list(iter_ask_stream(rt, question="what time is it"))
        self.assertGreaterEqual(len(items), 2)
        self.assertEqual(items[-1]["type"], "done")
        self.assertTrue(items[-1].get("ok"))
        self.assertTrue(any(i.get("type") == "chunk" for i in items))
