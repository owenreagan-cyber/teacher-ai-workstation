"""Daemon lifecycle and CLI integration (hermetic)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import REPO_ROOT, CosdStateTest, free_port, wait_until

from cosd import cli
from cosd.lifecycle import PidRecord, clear_pid, process_alive, process_is_cosd, read_pid, spawn_server, stop_process, write_pid
from support import http_json


class LifecycleCliTests(CosdStateTest):
    def test_foreground_start_and_stop(self):
        port = free_port()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        proc = subprocess.Popen(
            [
                sys.executable,
                "-s",
                "-E",
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); from cosd.cli import main; "
                "raise SystemExit(main(sys.argv[2:]))",
                str(REPO_ROOT),
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(lambda: proc.poll() or proc.terminate())
        def up() -> bool:
            try:
                return bool(http_json(port, "/health")[1].get("ok"))
            except (OSError, Exception):
                return False

        self.assertTrue(wait_until(up))
        write_pid(
            PidRecord(pid=proc.pid, host="127.0.0.1", port=port, started_at="2026-01-01T00:00:00+00:00"),
            self.state,
        )
        code = cli.main(["stop"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIsNone(read_pid(self.state))

    def test_already_running_detection(self):
        port = free_port()
        pid1 = spawn_server(host="127.0.0.1", port=port, base=self.state)
        self._spawned = pid1

        def _stop_spawned():
            rec = read_pid(self.state)
            if rec and rec.pid == self._spawned:
                stop_process(rec, base=self.state)
            elif process_alive(self._spawned) and process_is_cosd(self._spawned):
                os.kill(self._spawned, signal.SIGTERM)

        self.addCleanup(_stop_spawned)
        with self.assertRaises(RuntimeError):
            spawn_server(host="127.0.0.1", port=port, base=self.state)
        self.assertEqual(read_pid(self.state).pid, pid1)

    def test_stale_pid_cleared_on_stop(self):
        port = free_port()
        write_pid(
            PidRecord(pid=999999, host="127.0.0.1", port=port, started_at="2026-01-01T00:00:00+00:00"),
            self.state,
        )
        self.assertTrue(stop_process(read_pid(self.state), base=self.state))
        self.assertIsNone(read_pid(self.state))

    def test_invalid_process_identity_refused(self):
        port = free_port()
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], stdout=fh, stderr=fh)
        self.addCleanup(lambda: proc.poll() or proc.kill())
        record = PidRecord(pid=proc.pid, host="127.0.0.1", port=port, started_at="x")
        write_pid(record, self.state)
        with mock.patch("cosd.lifecycle.process_is_cosd", return_value=False):
            self.assertFalse(stop_process(record, base=self.state))
        clear_pid(self.state)
        proc.terminate()

    def test_status_json(self):
        code = cli.main(["status"])
        self.assertEqual(code, 0)
        # no server — still exits 0 with running=false

    def test_non_loopback_cli_rejected(self):
        code = cli.main(["start", "--host", "0.0.0.0"])
        self.assertEqual(code, cli.EXIT_ERROR)


class PidRecordTests(unittest.TestCase):
    def test_wrong_service_rejected(self):
        data = {"pid": 1, "host": "127.0.0.1", "port": 1, "started_at": "x", "service": "other"}
        with self.assertRaises(ValueError):
            PidRecord.from_dict(data)
