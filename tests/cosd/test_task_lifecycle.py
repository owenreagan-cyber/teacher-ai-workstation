"""Centralized lifecycle rules."""
from __future__ import annotations

import unittest

from support import CosdStateTest

from cosd.tasks import TaskError, TaskRegistry, TaskState


class LifecycleRulesTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.reg = TaskRegistry.open(self.state)

    def test_terminal_states(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        self.reg.transition_task(tid, new_state=TaskState.RUNNING.value)
        self.reg.transition_task(tid, new_state=TaskState.COMPLETED.value)
        with self.assertRaises(TaskError):
            self.reg.cancel_task(tid)

    def test_failed_only_retry(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        with self.assertRaises(TaskError):
            self.reg.retry_task(tid)

    def test_blocked_to_queued_via_retry(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        self.reg.transition_task(tid, new_state=TaskState.RUNNING.value)
        self.reg.transition_task(tid, new_state=TaskState.BLOCKED.value)
        out = self.reg.retry_task(tid)
        self.assertEqual(out["state"], "QUEUED")

    def test_every_transition_has_event(self):
        task, _ = self.reg.create_task(kind="k", title="t")
        tid = task["id"]
        self.reg.transition_task(tid, new_state=TaskState.RUNNING.value)
        hist = self.reg.get_task_history(tid)
        types = [e["event_type"] for e in hist["events"]]
        self.assertIn("created", types)
        self.assertIn("transition", types)
