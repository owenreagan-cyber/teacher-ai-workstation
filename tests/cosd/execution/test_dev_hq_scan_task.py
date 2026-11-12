"""Development HQ scan V0 through the real task engine, worker, recovery, and HTTP layer."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cosd"))
sys.path.insert(0, str(ROOT / "tests" / "cosd" / "execution"))
from support import CosdStateTest, RunningServer, http_json  # noqa: E402
from test_dev_hq_scan import GIT_ENV, git, make_repo, write_roots  # noqa: E402

from cos.policy import KillSwitch  # noqa: E402
from cosd.execution import dev_hq_scan as scan  # noqa: E402
from cosd.execution.dispatcher import HandlerSpec  # noqa: E402
from cosd.execution.engine import ExecutionEngine  # noqa: E402
from cosd.execution.leases import acquire_lease  # noqa: E402
from cosd.execution.queue import QueueError  # noqa: E402
from cosd.tasks import MAX_JSON_BYTES, TaskState  # noqa: E402


class _BlindActiveLeaseSelect:
    """A connection proxy whose first 'active lease?' SELECT sees nothing: the state a claimer that
    lost a race is in (it read before the winner inserted, then tries to insert itself)."""

    def __init__(self, conn):
        self._conn, self._blinded = conn, False

    def execute(self, sql, params=()):
        if not self._blinded and "FROM worker_leases WHERE task_id = ? AND state = 'active'" in sql:
            self._blinded = True
            return type("Empty", (), {"fetchone": staticmethod(lambda: None)})()
        return self._conn.execute(sql, params)


def _isolate_home(test: CosdStateTest) -> None:
    """The scan resolves the user's global git ignore file from $HOME; never read the real one."""
    home = test.state.parent / "home"
    home.mkdir(exist_ok=True)
    patcher = mock.patch.dict(os.environ, {"HOME": str(home)})
    patcher.start()
    test.addCleanup(patcher.stop)


class TaskTestBase(CosdStateTest):
    def setUp(self):
        super().setUp()
        _isolate_home(self)
        self.base = self.state.parent
        self.projects = Path(os.path.realpath(self.base / "projects"))
        self.projects.mkdir()
        write_roots(self.state, self.projects)
        self.engine = ExecutionEngine.open(self.state)

    def create_scan(self, payload=None, **kw):
        task, _ = self.engine.registry.create_task(
            kind="dev_hq_scan", title="Development scan", payload=payload if payload is not None else {}, **kw
        )
        return task


class DurableTaskTests(TaskTestBase):
    def test_successful_durable_task_result(self):  # 19
        repo = make_repo(self.projects / "alpha")
        (repo / "x.txt").write_text("x")
        task = self.create_scan({"roots": [str(self.projects)]})
        out = self.engine.execute_task(task["id"])
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "completed")
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.COMPLETED.value)
        self.assertEqual(stored["result"]["summary"]["repositories"], 1)
        self.assertEqual(stored["result"]["summary"]["dirty_repositories"], 1)
        self.assertEqual(stored["result"]["status"], "complete")
        self.assertLessEqual(len(json.dumps(stored["result"]).encode()), MAX_JSON_BYTES)
        attempts = self.engine.list_attempts(task["id"])["attempts"]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["state"], "COMPLETED")
        self.assertEqual(attempts[0]["result"]["scan_type"], "dev_hq_scan")
        events = [e["event_type"] for e in self.engine.registry.get_task_history(task["id"])["events"]]
        self.assertEqual(events, ["created", "claimed", "completed"])
        # a fresh engine over the same state sees the same durable result
        again = ExecutionEngine.open(self.state).registry.get_task(task["id"])
        self.assertEqual(again["result"]["summary"], stored["result"]["summary"])

    def test_audit_has_counts_only(self):
        make_repo(self.projects / "alpha-private-name")
        task = self.create_scan()
        self.engine.execute_task(task["id"])
        audit = (self.state / "audit.jsonl").read_text()
        self.assertIn("cosd_dev_hq_scan", audit)
        self.assertNotIn("alpha-private-name", audit)
        self.assertNotIn(str(self.projects), audit)

    def test_failure_then_retry_after_approval(self):  # 20
        (self.state / scan.ROOTS_FILENAME).unlink()
        task = self.create_scan()
        out = self.engine.execute_task(task["id"])
        self.assertFalse(out["ok"])
        self.assertIn("no approved development roots", out["error"]["error"])
        self.assertFalse(out["error"]["retriable"])  # a retry cannot help until the owner approves a root
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.FAILED.value)
        self.assertIsNone(stored["result"])
        with self.assertRaises(QueueError):  # a FAILED task is not silently re-run
            self.engine.execute_task(task["id"])
        make_repo(self.projects / "alpha")
        write_roots(self.state, self.projects)
        self.engine.registry.retry_task(task["id"])
        out = self.engine.execute_task(task["id"])
        self.assertTrue(out["ok"])
        self.assertEqual(self.engine.registry.get_task(task["id"])["state"], TaskState.COMPLETED.value)
        attempts = self.engine.list_attempts(task["id"])["attempts"]
        self.assertEqual([a["state"] for a in attempts], ["FAILED", "COMPLETED"])

    def test_interrupted_scan_is_requeued_not_resumed(self):  # 21
        make_repo(self.projects / "alpha")
        task = self.create_scan()
        claim = self.engine.queue.claim_task(task["id"])  # simulates a daemon that died mid-scan
        with self.engine.registry.db.transaction() as conn:
            conn.execute(
                "UPDATE worker_leases SET expires_at = ? WHERE lease_id = ?",
                ("2000-01-01T00:00:00.000+00:00", claim["lease_id"]),
            )
        report = ExecutionEngine.open(self.state).recovery.run()
        self.assertEqual(report["repaired"], [{"task_id": task["id"], "action": "requeued"}])
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.QUEUED.value)  # nothing auto-runs; owner must press Run
        self.assertEqual(self.engine.list_checkpoints(task["id"])["checkpoints"], [])  # no resume is claimed
        attempts = self.engine.list_attempts(task["id"])["attempts"]
        self.assertEqual(attempts[0]["state"], "RECOVERING")
        self.assertEqual(attempts[0]["error"], {"interrupted": True})
        out = self.engine.execute_task(task["id"])
        self.assertTrue(out["ok"])
        self.assertEqual(out["result"]["status"], "complete")  # a full fresh scan, from scratch
        self.assertEqual(len(self.engine.list_attempts(task["id"])["attempts"]), 2)

    def test_kill_switch_blocks_execution_before_claim(self):  # 22
        make_repo(self.projects / "alpha")
        task = self.create_scan()
        KillSwitch(self.state).stop("test")
        with mock.patch.object(scan, "run_dev_hq_scan") as runner, self.assertRaises(QueueError) as cm:
            self.engine.execute_task(task["id"])
        runner.assert_not_called()
        self.assertEqual(cm.exception.kind, "stopped")
        self.assertEqual(cm.exception.http_status, 503)
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.QUEUED.value)  # not stranded RUNNING
        self.assertEqual(self.engine.list_attempts(task["id"])["attempts"], [])
        KillSwitch(self.state).resume()
        self.assertTrue(self.engine.execute_task(task["id"])["ok"])

    def test_kill_switch_raced_after_claim_fails_cleanly(self):
        task = self.create_scan()
        claim = self.engine.queue.claim_task(task["id"])
        KillSwitch(self.state).stop("test")
        with mock.patch.object(scan, "run_dev_hq_scan") as runner:
            out = self.engine.worker.execute_claimed(
                task_id=task["id"], attempt_id=claim["attempt_id"],
                worker_id=claim["worker_id"], lease_id=claim["lease_id"],
            )
        runner.assert_not_called()
        self.assertFalse(out["ok"])
        self.assertEqual(self.engine.registry.get_task(task["id"])["state"], TaskState.FAILED.value)

    def _register(self, name, *, retryable, max_attempts, execute=lambda payload, cp: {"ok": True}):
        self.engine.handlers._handlers[name] = HandlerSpec(name, 5.0, max_attempts, "safe_replay", retryable, {}, execute)
        task, _ = self.engine.registry.create_task(kind=name, title=name)
        return task

    def test_kill_switch_race_uses_the_handlers_real_retry_policy(self):  # review finding 3
        for name, retryable, max_attempts in (("no-retry", False, 3), ("one-shot", True, 1)):
            with self.subTest(handler=name):
                task = self._register(name, retryable=retryable, max_attempts=max_attempts)
                claim = self.engine.queue.claim_task(task["id"])
                KillSwitch(self.state).stop("test")
                try:
                    out = self.engine.worker.execute_claimed(
                        task_id=task["id"], attempt_id=claim["attempt_id"],
                        worker_id=claim["worker_id"], lease_id=claim["lease_id"],
                    )
                finally:
                    KillSwitch(self.state).resume()
                self.assertFalse(out["ok"])
                self.assertEqual(out["error"]["retriable"], retryable, "the reported flag must match the real spec")
                self.assertIsNone(out["retry_after_at"], "the handler's policy allows no retry")
                self.assertEqual(self.engine.list_attempts(task["id"])["attempts"][0]["state"], "FAILED")
                stored = self.engine.registry.get_task(task["id"])
                self.assertEqual(stored["state"], TaskState.FAILED.value)
        # control: a handler that really is retryable with attempts left is scheduled for retry
        task = self._register("retryable", retryable=True, max_attempts=3)
        claim = self.engine.queue.claim_task(task["id"])
        KillSwitch(self.state).stop("test")
        try:
            out = self.engine.worker.execute_claimed(
                task_id=task["id"], attempt_id=claim["attempt_id"],
                worker_id=claim["worker_id"], lease_id=claim["lease_id"],
            )
        finally:
            KillSwitch(self.state).resume()
        self.assertIsNotNone(out["retry_after_at"])
        self.assertEqual(self.engine.list_attempts(task["id"])["attempts"][0]["state"], "RETRY_WAIT")

    def test_unserialisable_result_fails_the_attempt_instead_of_stranding_it(self):  # review finding 7
        task = self._register("weird", retryable=True, max_attempts=3, execute=lambda p, c: {"x": object()})
        out = self.engine.execute_task(task["id"])
        self.assertFalse(out["ok"])
        self.assertIn("not JSON-serialisable", out["error"]["error"])
        self.assertIsNone(out["retry_after_at"])
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.FAILED.value, "must not stay RUNNING until the lease expires")
        self.assertIsNone(stored["result"])
        self.assertEqual(self.engine.list_attempts(task["id"])["attempts"][0]["state"], "FAILED")
        leases = self.engine.registry.db.query_all("SELECT state FROM worker_leases WHERE task_id = ?", (task["id"],))
        self.assertEqual([r["state"] for r in leases], ["released"])

    def test_oversized_checkpoint_fails_the_attempt_instead_of_stranding_it(self):  # review finding 7 (same class)
        big = {"_checkpoint": {"checkpoint_key": "progress", "data": {"blob": "x" * 20_000}}}
        task = self._register("bigcp", retryable=True, max_attempts=3, execute=lambda p, c: dict(big))
        out = self.engine.execute_task(task["id"])
        self.assertFalse(out["ok"])
        self.assertEqual(self.engine.registry.get_task(task["id"])["state"], TaskState.FAILED.value)
        self.assertEqual(self.engine.list_checkpoints(task["id"])["checkpoints"], [])

    def test_concurrent_claim_loser_gets_the_defined_conflict_error(self):  # review finding 8
        task, _ = self.engine.registry.create_task(kind="noop", title="race")
        claim = self.engine.queue.claim_task(task["id"])  # the winner now holds the active lease
        with self.engine.registry.db.transaction() as conn:
            with self.assertRaises(RuntimeError) as cm:  # NOT sqlite3.IntegrityError
                acquire_lease(_BlindActiveLeaseSelect(conn), task_id=task["id"], worker_id="loser", attempt_id=claim["attempt_id"])
        self.assertIn("already has active lease", str(cm.exception))
        leases = self.engine.registry.db.query_all("SELECT worker_id, state FROM worker_leases WHERE task_id = ?", (task["id"],))
        self.assertEqual([(r["worker_id"], r["state"]) for r in leases], [(claim["worker_id"], "active")], "the winner keeps its lease")

    def test_malformed_payload_task_fails_permanently(self):  # 23
        task = self.create_scan({"command": "echo hi"})
        out = self.engine.execute_task(task["id"])
        self.assertFalse(out["ok"])
        self.assertFalse(out["error"]["retriable"])
        (self.base / "elsewhere").mkdir()
        outside = self.create_scan({"roots": [str(self.base / "elsewhere")]})
        out = self.engine.execute_task(outside["id"])
        self.assertFalse(out["ok"])
        self.assertIn("outside the approved roots", out["error"]["error"])

    def test_oversized_handler_result_is_never_completed(self):  # 17 (worker guard)
        self.engine.handlers._handlers["big"] = HandlerSpec(
            "big", 5.0, 1, "safe_replay", False, {}, lambda p, c: {"blob": "x" * (MAX_JSON_BYTES + 10)}
        )
        task, _ = self.engine.registry.create_task(kind="big", title="big")
        out = self.engine.execute_task(task["id"])
        self.assertFalse(out["ok"])
        stored = self.engine.registry.get_task(task["id"])
        self.assertEqual(stored["state"], TaskState.FAILED.value)
        self.assertIsNone(stored["result"])
        self.assertIn("size limit", stored["error"]["error"])

    def test_second_attempt_of_any_task_can_claim_a_lease(self):
        # Regression: spent lease rows used to violate worker_leases.task_id UNIQUE on re-claim.
        task, _ = self.engine.registry.create_task(kind="calc", title="bad", payload={"op": "mul"})
        self.assertFalse(self.engine.execute_task(task["id"])["ok"])
        self.engine.registry.retry_task(task["id"])
        self.assertFalse(self.engine.execute_task(task["id"])["ok"])  # fails again, but is claimable
        self.assertEqual(len(self.engine.list_attempts(task["id"])["attempts"]), 2)
        leases = self.engine.registry.db.query_all("SELECT state FROM worker_leases WHERE task_id = ?", (task["id"],))
        self.assertEqual([r["state"] for r in leases], ["released"])

    def test_existing_handlers_unaffected(self):  # 24
        self.assertEqual(self.engine.handlers.list_kinds(), ["calc", "dev_hq_scan", "diagnostic", "noop"])
        noop, _ = self.engine.registry.create_task(kind="noop", title="n")
        self.assertEqual(self.engine.execute_task(noop["id"])["result"], {"ok": True, "message": "noop verified"})
        calc, _ = self.engine.registry.create_task(kind="calc", title="c", payload={"op": "add", "values": [1, 2, 3]})
        self.assertEqual(self.engine.execute_task(calc["id"])["result"], {"sum": 6.0})
        phased, _ = self.engine.registry.create_task(
            kind="calc", title="p", payload={"op": "add", "values": [1, 2], "phased": True}
        )
        self.assertEqual(self.engine.execute_task(phased["id"])["status"], "checkpointed")
        diag, _ = self.engine.registry.create_task(kind="diagnostic", title="d")
        self.assertTrue(self.engine.execute_task(diag["id"])["result"]["read_only"])
        for kind, policy in (("noop", "safe_replay"), ("calc", "checkpoint_resume"), ("diagnostic", "safe_replay")):
            self.assertEqual(self.engine.handlers.get(kind).recovery_policy, policy)
        spec = self.engine.handlers.get("dev_hq_scan")
        self.assertEqual(spec.recovery_policy, "safe_replay")
        self.assertGreaterEqual(spec.timeout_s, scan.HARD_CAPS.max_seconds)


class NoSecretsTests(TaskTestBase):
    def test_no_secrets_in_task_attempt_history_or_audit(self):  # 25
        repo = make_repo(self.projects / "alpha")
        (repo / ".env").write_text("API_TOKEN=SUPERSECRETVALUE123\n")
        (repo / "notes.txt").write_text("FILECONTENTMARKER\n")
        git(repo, "remote", "add", "origin", "https://user:URLTOKEN987@example.invalid/x.git")
        git(repo, "config", "user.email", "private-person@example.invalid")
        task = self.create_scan({"include_processes": True})
        with mock.patch.object(scan, "_real_ps", lambda _t: "  1  0  100  01:00 /sbin/launchd\n  9 1 900 2-00:00:00 /usr/bin/node\n"):
            self.engine.execute_task(task["id"])
        blob = json.dumps(
            [
                self.engine.registry.get_task(task["id"]),
                self.engine.list_attempts(task["id"]),
                self.engine.registry.get_task_history(task["id"]),
            ]
        )
        blob += (self.state / "audit.jsonl").read_text()
        for secret in ("SUPERSECRETVALUE123", "FILECONTENTMARKER", "URLTOKEN987", "private-person", "API_TOKEN"):
            self.assertNotIn(secret, blob)


class HttpTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        _isolate_home(self)
        self.base = self.state.parent
        self.projects = Path(os.path.realpath(self.base / "projects"))
        self.projects.mkdir()
        write_roots(self.state, self.projects)
        make_repo(self.projects / "alpha")
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def _create(self, payload):
        status, body = http_json(
            self.srv.port, "/v1/tasks", method="POST", token=self.srv.token,
            body={"kind": "dev_hq_scan", "title": "Development scan", "payload": payload},
        )
        self.assertEqual(status, 201)
        return body["task"]["id"]

    def test_create_execute_and_read_result_over_http(self):
        tid = self._create({"roots": [str(self.projects)]})
        status, body = http_json(
            self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", token=self.srv.token, body={}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["summary"]["repositories"], 1)
        _, task = http_json(self.srv.port, f"/v1/tasks/{tid}", token=self.srv.token)
        self.assertEqual(task["task"]["state"], "COMPLETED")
        self.assertEqual(task["task"]["result"]["scan_type"], "dev_hq_scan")

    def test_unauthenticated_execute_denied(self):
        tid = self._create({})
        status, _ = http_json(self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", body={})
        self.assertEqual(status, 401)

    def test_http_client_cannot_widen_scope(self):
        (self.base / "elsewhere").mkdir()
        tid = self._create({"roots": [str(self.base / "elsewhere")]})
        status, body = http_json(
            self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", token=self.srv.token, body={}
        )
        self.assertEqual(status, 500)
        self.assertFalse(body["ok"])
        self.assertIn("outside the approved roots", body["error"]["error"])

    def test_kill_switch_blocks_http_execute_and_task_stays_queued(self):
        tid = self._create({})
        KillSwitch(self.state).stop("test")
        status, body = http_json(
            self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", token=self.srv.token, body={}
        )
        KillSwitch(self.state).resume()
        self.assertEqual(status, 503)
        self.assertEqual(body["error_kind"], "stopped")
        _, task = http_json(self.srv.port, f"/v1/tasks/{tid}", token=self.srv.token)
        self.assertEqual(task["task"]["state"], "QUEUED")


if __name__ == "__main__":
    unittest.main()
