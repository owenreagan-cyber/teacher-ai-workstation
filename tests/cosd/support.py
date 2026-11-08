"""Hermetic helpers for cosd tests (temp state, ephemeral ports)."""
from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until(predicate, timeout: float = 5.0, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def http_json(
    port: int,
    path: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    raw_body: bytes | None = None,
) -> tuple[int, dict]:
    data = raw_body
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"http://127.0.0.1:{port}{path}", data=data, method=method, headers=headers)
    if token is not None:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"ok": False, "error": payload}
    except OSError:
        raise


class CosdStateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="cosd-test-")
        self.state = Path(self._tmp.name) / "ChiefOfStaff"
        self.state.mkdir(parents=True, exist_ok=True)
        self._old = {k: os.environ.get(k) for k in ("COS_STATE_DIR", "COS_FIXTURE_DIR")}
        os.environ["COS_STATE_DIR"] = str(self.state)
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()


class RunningServer:
    def __init__(self, state_base: Path, port: int | None = None, *, use_subprocess: bool = True):
        import os
        import subprocess
        import sys
        from datetime import datetime, timezone

        from cosd.auth import ensure_token
        from cosd.lifecycle import PidRecord, clear_pid, write_pid

        self.state_base = state_base
        self.port = port or free_port()
        self.token = ensure_token(state_base).token
        self._proc = None
        self._thread = None
        if not use_subprocess:
            from cosd.server import run_server

            self._thread = threading.Thread(
                target=run_server,
                kwargs={"host": "127.0.0.1", "port": self.port, "state_base": state_base},
                daemon=True,
            )
            self._thread.start()

            def health_ok() -> bool:
                try:
                    _, body = http_json(self.port, "/health")
                except (OSError, URLError):
                    return False
                return bool(body.get("ok"))

            if not wait_until(health_ok):
                raise RuntimeError("cosd test server failed to start")
            return

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        env["COS_STATE_DIR"] = str(state_base)
        if FIXTURES.is_dir():
            env["COS_FIXTURE_DIR"] = str(FIXTURES)
        self._proc = subprocess.Popen(
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
                str(self.port),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        write_pid(
            PidRecord(
                pid=self._proc.pid,
                host="127.0.0.1",
                port=self.port,
                started_at=datetime.now(timezone.utc).isoformat(),
            ),
            state_base,
        )

        def health_ok() -> bool:
            try:
                _, body = http_json(self.port, "/health")
            except (OSError, URLError):
                return False
            return bool(body.get("ok"))

        if not wait_until(health_ok):
            self._proc.terminate()
            clear_pid(state_base)
            raise RuntimeError("cosd test server failed to start")

    def stop(self) -> None:
        from cosd.lifecycle import clear_pid, read_pid, stop_process

        try:
            http_json(self.port, "/v1/stop", method="POST", body={}, token=self.token)
        except (OSError, URLError, Exception):
            pass
        if self._thread is not None:
            return
        rec = read_pid(self.state_base)
        if rec:
            stop_process(rec, base=self.state_base, timeout=3)
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
        clear_pid(self.state_base)
