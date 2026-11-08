"""Ask stream adapter tests (fixture mode)."""
from __future__ import annotations

import os
import tempfile
import unittest

from cos.service import iter_ask_stream
from cos.cli import build_runtime

from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "evals" / "fixtures" / "default"


class AskStreamTest(unittest.TestCase):
    def setUp(self):
        self._old_fixture = os.environ.get("COS_FIXTURE_DIR")
        self._old_state = os.environ.get("COS_STATE_DIR")
        self._state = tempfile.mkdtemp(prefix="cosd-ask-stream-")
        os.environ["COS_STATE_DIR"] = self._state
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)

    def tearDown(self):
        if self._old_fixture is None:
            os.environ.pop("COS_FIXTURE_DIR", None)
        else:
            os.environ["COS_FIXTURE_DIR"] = self._old_fixture
        if self._old_state is None:
            os.environ.pop("COS_STATE_DIR", None)
        else:
            os.environ["COS_STATE_DIR"] = self._old_state

    def test_chunks_then_done(self):
        rt = build_runtime()
        items = list(iter_ask_stream(rt, question="what time is it"))
        self.assertGreaterEqual(len(items), 2)
        self.assertEqual(items[-1]["type"], "done")
        self.assertTrue(items[-1].get("ok"))
        self.assertTrue(any(i.get("type") == "chunk" for i in items))
