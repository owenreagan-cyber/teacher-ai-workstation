"""Task HTTP API tests."""
from __future__ import annotations

import unittest

from support import CosdStateTest, RunningServer, http_json


class TaskApiTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def _create(self, **fields):
        body = {"kind": "api", "title": "task", **fields}
        return http_json(self.srv.port, "/v1/tasks", method="POST", token=self.srv.token, body=body)

    def test_create_list_show(self):
        status, created = self._create()
        self.assertEqual(status, 201)
        task_id = created["task"]["id"]
        status, listing = http_json(self.srv.port, "/v1/tasks", token=self.srv.token)
        self.assertEqual(status, 200)
        self.assertEqual(listing["total"], 1)
        status, one = http_json(self.srv.port, f"/v1/tasks/{task_id}", token=self.srv.token)
        self.assertEqual(one["task"]["id"], task_id)

    def test_auth_required(self):
        status, body = http_json(self.srv.port, "/v1/tasks", method="POST", body={"kind": "x", "title": "y"})
        self.assertEqual(status, 401)

    def test_idempotency_via_api(self):
        body = {"kind": "k", "title": "t", "idempotency_key": "key-a"}
        s1, r1 = http_json(self.srv.port, "/v1/tasks", method="POST", token=self.srv.token, body=body)
        s2, r2 = http_json(self.srv.port, "/v1/tasks", method="POST", token=self.srv.token, body=body)
        self.assertEqual(s1, 201)
        self.assertEqual(s2, 200)
        self.assertTrue(r2["reused"])
        body["title"] = "changed"
        s3, r3 = http_json(self.srv.port, "/v1/tasks", method="POST", token=self.srv.token, body=body)
        self.assertEqual(s3, 409)

    def test_cancel_retry_history(self):
        _, created = self._create()
        tid = created["task"]["id"]
        status, cancelled = http_json(
            self.srv.port, f"/v1/tasks/{tid}/cancel", method="POST", token=self.srv.token, body={}
        )
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["task"]["state"], "CANCELLED")
        _, created2 = self._create(title="two")
        tid2 = created2["task"]["id"]
        from cosd.tasks import TaskRegistry, TaskState

        reg = TaskRegistry.open(self.state)
        reg.transition_task(tid2, new_state=TaskState.RUNNING.value)
        reg.transition_task(tid2, new_state=TaskState.FAILED.value)
        status, retried = http_json(
            self.srv.port, f"/v1/tasks/{tid2}/retry", method="POST", token=self.srv.token, body={}
        )
        self.assertEqual(retried["task"]["state"], "QUEUED")
        status, hist = http_json(self.srv.port, f"/v1/tasks/{tid2}/history", token=self.srv.token)
        self.assertGreaterEqual(len(hist["events"]), 3)

    def test_unknown_task(self):
        status, body = http_json(
            self.srv.port, "/v1/tasks/" + "f" * 32, token=self.srv.token
        )
        self.assertEqual(status, 404)

    def test_invalid_payload(self):
        status, _ = self._create(title="")
        self.assertEqual(status, 400)
