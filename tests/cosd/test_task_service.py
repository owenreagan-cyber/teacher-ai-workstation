"""Task registry service tests."""
from __future__ import annotations

import unittest

from support import CosdStateTest

from cosd.tasks import TaskError, TaskRegistry, TaskState


class ServiceTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.reg = TaskRegistry.open(self.state)

    def test_create_and_get(self):
        task, reused = self.reg.create_task(kind="demo", title="Hello", payload={"a": 1})
        self.assertFalse(reused)
        self.assertEqual(task["state"], TaskState.QUEUED.value)
        got = self.reg.get_task(task["id"])
        self.assertEqual(got["title"], "Hello")

    def test_idempotency_same_payload(self):
        t1, _ = self.reg.create_task(kind="k", title="t", idempotency_key="idem-1")
        t2, reused = self.reg.create_task(kind="k", title="t", idempotency_key="idem-1")
        self.assertTrue(reused)
        self.assertEqual(t1["id"], t2["id"])

    def test_idempotency_conflict(self):
        self.reg.create_task(kind="k", title="t", idempotency_key="idem-2")
        with self.assertRaises(TaskError) as ctx:
            self.reg.create_task(kind="k", title="other", idempotency_key="idem-2")
        self.assertEqual(ctx.exception.http_status, 409)

    def test_lifecycle_transitions(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        running = self.reg.transition_task(tid, new_state=TaskState.RUNNING.value, event_type="claim")
        self.assertEqual(running["state"], "RUNNING")
        self.assertIsNotNone(running["started_at"])
        done = self.reg.transition_task(
            tid,
            new_state=TaskState.COMPLETED.value,
            event_type="complete",
        )
        self.assertIsNotNone(done["completed_at"])
        with self.assertRaises(TaskError):
            self.reg.transition_task(tid, new_state=TaskState.QUEUED.value)

    def test_cancel_and_retry(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        cancelled = self.reg.cancel_task(tid)
        self.assertEqual(cancelled["state"], "CANCELLED")
        task2, _ = self.reg.create_task(kind="k", title="t2")
        tid2 = task2["id"]
        self.reg.transition_task(tid2, new_state=TaskState.RUNNING.value)
        self.reg.transition_task(tid2, new_state=TaskState.FAILED.value)
        queued = self.reg.retry_task(tid2)
        self.assertEqual(queued["state"], "QUEUED")
        history = self.reg.get_task_history(tid2)
        self.assertGreaterEqual(len(history["events"]), 4)

    def test_list_and_counts(self):
        for i in range(3):
            self.reg.create_task(kind="batch", title=f"t{i}")
        listing = self.reg.list_tasks(kind="batch", limit=2, offset=0)
        self.assertEqual(listing["total"], 3)
        self.assertEqual(len(listing["tasks"]), 2)
        counts = self.reg.get_task_counts()
        self.assertEqual(counts["QUEUED"], 3)
