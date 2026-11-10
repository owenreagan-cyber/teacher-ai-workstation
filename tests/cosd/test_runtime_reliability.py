"""Runtime provenance, health classification and lifecycle state (hermetic)."""
from __future__ import annotations

import json
import os
import socket
import unittest
from pathlib import Path
from unittest import mock

from support import CosdStateTest, RunningServer, free_port, http_json

import cosd.provenance as provenance
from cosd import health
from cosd.auth import ensure_token
from cosd.lifecycle import (
    _looks_like_cosd_command,
    PidRecord,
    pid_report,
    port_in_use,
    process_alive,
    read_pid,
    spawn_server,
    write_pid,
)


class ProvenanceTests(unittest.TestCase):
    def test_snapshot_is_frozen_and_reports_loaded_commit(self):
        with mock.patch.object(provenance, "checkout_commit", return_value="abc123def456"), \
             mock.patch.object(provenance, "checkout_branch", return_value="main"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            snap = provenance.snapshot("0.1.0")
        self.assertEqual(snap.loaded_commit, "abc123def456")
        self.assertEqual(snap.loaded_branch, "main")
        self.assertTrue(snap.source_available)
        with self.assertRaises(Exception):
            snap.loaded_commit = "changed"  # frozen dataclass

    def test_missing_checkout_does_not_guess(self):
        with mock.patch.object(provenance, "checkout_commit", return_value=None), \
             mock.patch.object(provenance, "checkout_branch", return_value=None), \
             mock.patch.object(provenance, "checkout_dirty", return_value=None):
            snap = provenance.snapshot("0.1.0")
            report = provenance.drift(snap)
        self.assertFalse(snap.source_available)
        self.assertIsNone(snap.loaded_commit)
        self.assertIsNone(report["restart_required"])

    def test_head_advance_marks_running_process_stale(self):
        with mock.patch.object(provenance, "checkout_commit", return_value="aaaaaaaaaaaa"), \
             mock.patch.object(provenance, "checkout_branch", return_value="main"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            snap = provenance.snapshot("0.1.0")
        with mock.patch.object(provenance, "checkout_commit", return_value="bbbbbbbbbbbb"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            report = provenance.drift(snap)
        self.assertTrue(report["restart_required"])
        # The frozen snapshot must not have moved.
        self.assertEqual(snap.loaded_commit, "aaaaaaaaaaaa")
        self.assertEqual(report["current_commit"], "bbbbbbbbbbbb")

    def test_unchanged_head_is_not_stale(self):
        with mock.patch.object(provenance, "checkout_commit", return_value="cccccccccccc"), \
             mock.patch.object(provenance, "checkout_branch", return_value="main"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            snap = provenance.snapshot("0.1.0")
        with mock.patch.object(provenance, "checkout_commit", return_value="cccccccccccc"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            report = provenance.drift(snap)
        self.assertFalse(report["restart_required"])

    def test_new_dirty_work_requests_restart(self):
        with mock.patch.object(provenance, "checkout_commit", return_value="dddddddddddd"), \
             mock.patch.object(provenance, "checkout_branch", return_value="main"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=False):
            snap = provenance.snapshot("0.1.0")
        with mock.patch.object(provenance, "checkout_commit", return_value="dddddddddddd"), \
             mock.patch.object(provenance, "checkout_dirty", return_value=True):
            report = provenance.drift(snap)
        self.assertTrue(report["restart_required"])

    def test_snapshot_has_no_absolute_paths(self):
        snap = provenance.snapshot("0.1.0")
        payload = json.dumps(snap.public_dict())
        self.assertNotIn(str(Path.home()), payload)
        self.assertNotIn("/Users/", payload)


class HealthClassificationTests(unittest.TestCase):
    def test_healthy_requires_state_not_just_a_socket(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=False,
        )
        self.assertEqual(out["state"], health.HEALTHY)

    def test_kill_switch_blocks(self):
        out = health.classify(
            db_ok=True, kill_switch=True, queue_paused=False,
            device_registry_available=True, restart_required=False,
        )
        self.assertEqual(out["state"], health.BLOCKED)

    def test_database_unavailable_blocks(self):
        out = health.classify(
            db_ok=False, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=False,
        )
        self.assertEqual(out["state"], health.BLOCKED)

    def test_stale_runtime_degrades(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=True,
        )
        self.assertEqual(out["state"], health.DEGRADED)
        self.assertIn("restart", " ".join(out["reasons"]))

    def test_paused_queue_degrades(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=True,
            device_registry_available=True, restart_required=False,
        )
        self.assertEqual(out["state"], health.DEGRADED)

    def test_recent_recovery_reports_recovering(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=False,
            recovered_count=2, recovery_age_s=1.0,
        )
        self.assertEqual(out["state"], health.RECOVERING)
        self.assertIn("2 interrupted", " ".join(out["reasons"]))

    def test_recovery_plus_attention_degrades(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=True,
            recovered_count=1, recovery_age_s=1.0,
        )
        self.assertEqual(out["state"], health.DEGRADED)

    def test_old_recovery_is_not_recovering(self):
        out = health.classify(
            db_ok=True, kill_switch=False, queue_paused=False,
            device_registry_available=True, restart_required=False,
            recovered_count=3, recovery_age_s=999.0,
        )
        self.assertEqual(out["state"], health.HEALTHY)


class PidReportTests(CosdStateTest):
    def test_absent(self):
        self.assertEqual(pid_report(self.state)["state"], "absent")

    def test_not_running(self):
        write_pid(PidRecord(pid=999999, host="127.0.0.1", port=1, started_at="x"), self.state)
        self.assertEqual(pid_report(self.state)["state"], "not_running")

    def test_unrelated_live_pid_is_stale_not_running(self):
        write_pid(PidRecord(pid=os.getpid(), host="127.0.0.1", port=local_free_port(), started_at="x"), self.state)
        with mock.patch("cosd.lifecycle.process_is_cosd", return_value=False):
            report = pid_report(self.state)
        self.assertEqual(report["state"], "stale_pid")
        self.assertFalse(report["running"])
        self.assertTrue(report["pid_alive"])

    def test_running_when_identity_and_health_agree(self):
        port = local_free_port()
        write_pid(PidRecord(pid=os.getpid(), host="127.0.0.1", port=port, started_at="x"), self.state)
        with mock.patch("cosd.lifecycle.process_is_cosd", return_value=True), \
             mock.patch("cosd.lifecycle.fetch_health", return_value={"ok": True}):
            report = pid_report(self.state)
        self.assertEqual(report["state"], "running")
        self.assertTrue(report["running"])


class SpawnSafetyTests(CosdStateTest):
    def test_refuses_pid_file_pointing_at_unrelated_process(self):
        write_pid(PidRecord(pid=os.getpid(), host="127.0.0.1", port=local_free_port(), started_at="x"), self.state)
        with mock.patch("cosd.lifecycle.process_is_cosd", return_value=False):
            with self.assertRaises(RuntimeError) as caught:
                spawn_server(port=local_free_port(), base=self.state)
        self.assertIn("unrelated process", str(caught.exception))

    def test_refuses_occupied_port(self):
        port = local_free_port()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", port))
            sock.listen(1)
            self.assertTrue(port_in_use("127.0.0.1", port))
            with self.assertRaises(RuntimeError) as caught:
                spawn_server(port=port, base=self.state)
        self.assertIn("already in use", str(caught.exception))


class RuntimeApiTests(CosdStateTest):
    def test_status_exposes_state_and_provenance_without_paths(self):
        server = RunningServer(self.state, use_subprocess=False)
        token = server.token
        try:
            from urllib.request import Request, urlopen

            req = Request(
                f"http://127.0.0.1:{server.port}/v1/status",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode())
        finally:
            server.stop()
        self.assertIn(body["state"], {health.HEALTHY, health.DEGRADED, health.RECOVERING, health.BLOCKED})
        self.assertIn("runtime", body)
        self.assertIn("loaded_commit", body["runtime"])
        self.assertIn("restart_required", body["runtime"])
        self.assertNotIn("/Users/", json.dumps(body))

    def test_runtime_snapshot_exposes_recovery_and_provenance(self):
        server = RunningServer(self.state, use_subprocess=False)
        token = server.token
        try:
            from urllib.request import Request, urlopen

            req = Request(
                f"http://127.0.0.1:{server.port}/v1/runtime",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode())
        finally:
            server.stop()
        self.assertTrue(body["ok"])
        self.assertIn("provenance", body)
        self.assertIn("recovery", body)
        self.assertIn("state", body)


class CommandIdentityTests(unittest.TestCase):
    """Identity must be positive, not a bare substring match."""

    def test_spawned_daemon_command_is_recognised(self):
        cmd = (
            "/usr/bin/python3.12 -s -E -c import sys; sys.path.insert(0, sys.argv[1]); "
            "from cosd.cli import main; raise SystemExit(main(sys.argv[2:])) /repo serve"
        )
        self.assertTrue(_looks_like_cosd_command(cmd))

    def test_module_invocation_is_recognised(self):
        self.assertTrue(_looks_like_cosd_command("python3.12 -m cosd serve --port 8765"))

    def test_unrelated_command_that_mentions_cosd_is_refused(self):
        self.assertFalse(_looks_like_cosd_command("bash -c echo cosd"))
        self.assertFalse(_looks_like_cosd_command("/usr/bin/sleep 30"))
        self.assertFalse(_looks_like_cosd_command(""))


def local_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
