"""Queue claim and concurrency tests."""
from __future__ import annotations

import threading
import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cosd"))
from support import CosdStateTest  # noqa: E402

from cosd.execution.engine import ExecutionEngine
from cosd.execution.queue import QueueError


class QueueTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.engine = ExecutionEngine.open(self.state)

    def test_atomic_claim_and_execute_noop(self):
        task, _ = self.engine.registry.create_task(kind="noop", title="n")
        out = self.engine.execute_task(task["id"])
        self.assertTrue(out.get("ok"))
        updated = self.engine.registry.get_task(task["id"])
        self.assertEqual(updated["state"], "COMPLETED")

    def test_concurrent_claim(self):
        task, _ = self.engine.registry.create_task(kind="noop", title="race")
        results: list = []
        errors: list = []

        def worker():
            try:
                results.append(self.engine.queue.claim_task(task["id"], worker_id=f"w{threading.get_ident()}"))
            except (QueueError, RuntimeError) as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 3)

    def test_pause_blocks_claim(self):
        task, _ = self.engine.registry.create_task(kind="noop", title="p")
        self.engine.queue.set_paused(True)
        with self.assertRaises(QueueError):
            self.engine.queue.claim_task(task["id"])
