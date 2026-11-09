from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from cos.config import FILE_MODE, ensure_private_dir, open_private, state_dir

from .constants import DEFAULT_HOST, DEFAULT_PORT, PID_FILENAME, SERVICE_NAME
from .server import validate_bind_host


@dataclass
class PidRecord:
    pid: int
    host: str
    port: int
    started_at: str
    service: str = SERVICE_NAME

    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "host": self.host,
            "port": self.port,
            "started_at": self.started_at,
            "service": self.service,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PidRecord:
        if data.get("service") != SERVICE_NAME:
            raise ValueError("pid file is not for cosd")
        return cls(
            pid=int(data["pid"]),
            host=str(data["host"]),
            port=int(data["port"]),
            started_at=str(data["started_at"]),
        )


def pid_path(base: Path | None = None) -> Path:
    root = base or state_dir()
    return root / "cosd" / PID_FILENAME


def write_pid(record: PidRecord, base: Path | None = None) -> None:
    path = pid_path(base)
    ensure_private_dir(path.parent)
    with open_private(path, "w") as fh:
        json.dump(record.to_dict(), fh, sort_keys=True)
        fh.write("\n")


def read_pid(base: Path | None = None) -> PidRecord | None:
    path = pid_path(base)
    if not path.is_file():
        return None
    try:
        return PidRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def clear_pid(base: Path | None = None) -> None:
    path = pid_path(base)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def process_is_cosd(pid: int) -> bool:
    """Best-effort identity check before signaling."""
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
            cmd = (out.stdout or "").strip()
            return SERVICE_NAME in cmd or "cosd" in cmd
        except (OSError, subprocess.TimeoutExpired):
            return False
    return process_alive(pid)


def fetch_health(host: str, port: int, timeout: float = 2.0) -> dict[str, Any] | None:
    url = f"http://{host}:{port}/health"
    try:
        with urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, TimeoutError):
        return None


def stop_process(record: PidRecord, *, base: Path | None = None, timeout: float = 10.0) -> bool:
    if not process_alive(record.pid):
        clear_pid(base)
        return True
    if not process_is_cosd(record.pid):
        return False
    try:
        os.kill(record.pid, signal.SIGTERM)
    except OSError:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_alive(record.pid):
            clear_pid(base)
            return True
        time.sleep(0.1)
    if process_alive(record.pid):
        try:
            os.kill(record.pid, signal.SIGKILL)
        except OSError:
            return False
    clear_pid(base)
    return not process_alive(record.pid)


def spawn_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    foreground: bool = False,
    base: Path | None = None,
) -> int:
    host = validate_bind_host(host)
    existing = read_pid(base)
    if existing and process_alive(existing.pid) and fetch_health(existing.host, existing.port):
        raise RuntimeError("cosd is already running")
    repo = str(Path(__file__).resolve().parents[1])
    cmd = [
        sys.executable,
        "-s",
        "-E",
        "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); from cosd.cli import main; "
        "raise SystemExit(main(sys.argv[2:]))",
        repo,
        "serve",
        "--host",
        host,
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    if foreground:
        os.execve(cmd[0], cmd, env)
    proc = subprocess.Popen(
        cmd,
        cwd=repo,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        health = fetch_health(host, port)
        if health and health.get("ok"):
            write_pid(
                PidRecord(
                    pid=proc.pid,
                    host=host,
                    port=port,
                    started_at=datetime.now(timezone.utc).isoformat(),
                ),
                base,
            )
            return proc.pid
        if proc.poll() is not None:
            err = (proc.stderr.read().decode("utf-8", "replace") if proc.stderr else "").strip()
            raise RuntimeError(f"cosd failed to start{(': ' + err) if err else ''}")
        time.sleep(0.15)
    raise RuntimeError("cosd health check timed out")
