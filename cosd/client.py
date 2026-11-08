"""Loopback HTTP client for the cosd daemon (used by bin/cos)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cos.config import state_dir

from .auth import ensure_token
from .constants import ASK_TIMEOUT_S, DEFAULT_HOST, DEFAULT_PORT
from .lifecycle import fetch_health, process_alive, process_is_cosd, read_pid
from .server import validate_bind_host

API_PREFIX = "/v1"
MIN_DAEMON_VERSION = (0, 1, 0)


class DaemonMode(str, Enum):
    AUTO = "auto"
    REQUIRED = "required"
    DISABLED = "disabled"


class CosdClientError(Exception):
    def __init__(self, message: str, *, kind: str = "internal", exit_code: int = 1):
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


@dataclass(frozen=True)
class DaemonEndpoint:
    host: str
    port: int
    version: str
    authenticated: bool


def daemon_mode_from_env() -> DaemonMode:
    raw = (os.environ.get("COS_USE_DAEMON") or "auto").strip().lower()
    try:
        return DaemonMode(raw)
    except ValueError:
        return DaemonMode.AUTO


def _parse_version(text: str) -> tuple[int, int, int]:
    parts = (text or "0.0.0").split(".")
    nums = [int(p) for p in parts[:3]] + [0] * (3 - len(parts[:3]))
    return tuple(nums[:3])  # type: ignore[return-value]


class CosdClient:
    def __init__(self, base=None, *, timeout: float = 5.0):
        self._base = base or state_dir()
        self._timeout = timeout
        self._token: str | None = None

    def _token_value(self) -> str:
        if self._token is None:
            self._token = ensure_token(self._base).token
        return self._token

    def _endpoint(self) -> tuple[str, int] | None:
        record = read_pid(self._base)
        if record is None:
            return None
        if not process_alive(record.pid) or not process_is_cosd(record.pid):
            return None
        try:
            host = validate_bind_host(record.host)
        except ValueError:
            return None
        return host, record.port

    def discover(self) -> DaemonEndpoint | None:
        ep = self._endpoint()
        if not ep:
            return None
        host, port = ep
        health = fetch_health(host, port, timeout=self._timeout)
        if not health or not health.get("ok"):
            return None
        version = str(health.get("version", "0.0.0"))
        if _parse_version(version) < MIN_DAEMON_VERSION:
            return None
        authed = self._probe_auth(host, port)
        return DaemonEndpoint(host=host, port=port, version=version, authenticated=authed)

    def _probe_auth(self, host: str, port: int) -> bool:
        try:
            status, body = self._request(host, port, f"{API_PREFIX}/status", method="GET")
            return status == 200 and body.get("ok")
        except CosdClientError:
            return False

    def is_available(self) -> bool:
        d = self.discover()
        return d is not None and d.authenticated

    def _request(
        self,
        host: str,
        port: int,
        path: str,
        *,
        method: str = "GET",
        body: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, dict[str, Any]]:
        if host not in ("127.0.0.1", "localhost"):
            raise CosdClientError("refusing non-loopback cosd endpoint", kind="usage", exit_code=2)
        data = None
        headers = {"Authorization": f"Bearer {self._token_value()}"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        url = f"http://{host}:{port}{path}"
        req = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(req, timeout=timeout or self._timeout) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            payload = exc.read().decode("utf-8")
            try:
                return exc.code, json.loads(payload)
            except json.JSONDecodeError:
                raise CosdClientError("daemon returned invalid JSON", kind="internal") from exc
        except URLError as exc:
            raise CosdClientError("cosd unreachable", kind="unavailable", exit_code=2) from exc

    def _with_discovery(self, fn) -> tuple[int, dict[str, Any]]:
        d = self.discover()
        if not d:
            raise CosdClientError("cosd is not running", kind="unavailable", exit_code=2)
        if not d.authenticated:
            raise CosdClientError("cosd authentication failed", kind="auth", exit_code=2)
        return fn(d.host, d.port)

    def ask(self, *, question: str, session_id: str | None = None) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {"question": question}
        if session_id is not None:
            payload["session_id"] = session_id

        def run(host, port):
            return self._request(
                host,
                port,
                f"{API_PREFIX}/ask",
                method="POST",
                body=payload,
                timeout=ASK_TIMEOUT_S + 5,
            )

        status, body = self._with_discovery(run)
        code = 0
        if not body.get("ok"):
            ek = body.get("error_kind", "internal")
            if ek == "usage":
                code = 2
            elif ek in ("stopped", "model_unavailable"):
                code = 3 if ek == "stopped" else 4
            else:
                code = 1
        return code, body

    def status(self) -> tuple[int, dict[str, Any]]:
        def run(host, port):
            return self._request(host, port, f"{API_PREFIX}/status", method="GET")

        status, body = self._with_discovery(run)
        if status != 200 or not body.get("ok"):
            raise CosdClientError(body.get("error", "status failed"), kind="internal")
        return status, body

    def create_task(self, **fields) -> tuple[int, dict[str, Any]]:
        def run(host, port):
            return self._request(host, port, f"{API_PREFIX}/tasks", method="POST", body=fields)

        return self._with_discovery(run)

    def list_tasks(self, **query) -> tuple[int, dict[str, Any]]:
        qs = "?" + urlencode(query) if query else ""

        def run(host, port):
            return self._request(host, port, f"{API_PREFIX}/tasks{qs}", method="GET")

        return self._with_discovery(run)
