"""Restart and persistence boundaries."""
from __future__ import annotations

import unittest

from support import CosdStateTest, RunningServer, http_json

from cosd.storage import TaskDatabase, database_path
from cosd.tasks import TaskRegistry, TaskState


class PersistenceTests(CosdStateTest):
    def test_survives_registry_reopen(self):
        reg = TaskRegistry.open(self.state)
        task, _ = reg.create_task(kind="persist", title="stay", idempotency_key="p1")
        reg.db.close()
        reg2 = TaskRegistry.open(self.state)
        same = reg2.get_task(task["id"])
        self.assertEqual(same["title"], "stay")
        again, reused = reg2.create_task(kind="persist", title="stay", idempotency_key="p1")
        self.assertTrue(reused)
        self.assertEqual(again["id"], task["id"])

    def test_running_state_after_restart(self):
        reg = TaskRegistry.open(self.state)
        task, _ = reg.create_task(kind="k", title="run")
        tid = task["id"]
        reg.transition_task(tid, new_state=TaskState.RUNNING.value)
        reg.db.close()
        reg2 = TaskRegistry.open(self.state)
        self.assertEqual(reg2.get_task(tid)["state"], "RUNNING")
        self.assertEqual(TaskDatabase(self.state).integrity_check(), "ok")

    def test_daemon_restart_via_api(self):
        srv = RunningServer(self.state)
        try:
            _, body = http_json(
                srv.port,
                "/v1/tasks",
                method="POST",
                token=srv.token,
                body={"kind": "k", "title": "daemon"},
            )
            task_id = body["task"]["id"]
        finally:
            srv.stop()
        srv2 = RunningServer(self.state)
        try:
            _, got = http_json(srv2.port, f"/v1/tasks/{task_id}", token=srv2.token)
            self.assertEqual(got["task"]["id"], task_id)
        finally:
            srv2.stop()
        self.assertTrue(database_path(self.state).is_file())
