"""Recovery and lease expiry tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cosd"))
from support import CosdStateTest  # noqa: E402

from cosd.execution.engine import ExecutionEngine
from cosd.tasks import TaskState


class RecoveryTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.engine = ExecutionEngine.open(self.state)

    def test_running_reclaimed_after_expired_lease(self):
        task, _ = self.engine.registry.create_task(kind="noop", title="rec")
        claim = self.engine.queue.claim_task(task["id"])
        with self.engine.registry.db.transaction() as conn:
            conn.execute(
                "UPDATE worker_leases SET expires_at = ? WHERE lease_id = ?",
                ("2000-01-01T00:00:00.000+00:00", claim["lease_id"]),
            )
        report = self.engine.recovery.run()
        self.assertTrue(report["repaired"])
        updated = self.engine.registry.get_task(task["id"])
        self.assertEqual(updated["state"], TaskState.QUEUED.value)

    def test_calc_completes(self):
        task, _ = self.engine.registry.create_task(
            kind="calc", title="sum", payload={"op": "add", "values": [1, 2, 3]}
        )
        out = self.engine.execute_task(task["id"])
        self.assertTrue(out.get("ok"))
        self.assertEqual(out["result"]["sum"], 6)
