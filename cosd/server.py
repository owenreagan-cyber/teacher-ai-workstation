from __future__ import annotations

import json
import logging
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from cos.audit import AuditLog
from cos.cli import EXIT_MODEL, EXIT_OK, EXIT_STOPPED, EXIT_USAGE, build_runtime
from cos.config import load_config
from cos.service import run_ask, run_status

from . import __version__
from .auth import authorize, ensure_token
from .constants import ASK_TIMEOUT_S, DEFAULT_HOST, MAX_BODY_BYTES, SERVICE_NAME

LOG = logging.getLogger("cosd")


class CosdHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, *, state_base=None):
        self.state_base = state_base
        super().__init__(server_address, RequestHandlerClass)

    def request_shutdown(self) -> None:
        threading.Thread(target=self.shutdown, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server: CosdHTTPServer  # type: ignore[assignment]

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        LOG.info("%s - %s", self.address_string(), format % args)

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _unauthorized(self) -> None:
        AuditLog(load_config().audit_path)(
            "cosd_auth_failure",
            path=self.path,
            reason="missing_or_invalid_token",
        )
        self._send_json(401, {"ok": False, "error": "unauthorized", "error_kind": "auth"})

    def _require_auth(self) -> bool:
        if authorize(self.headers.get("Authorization"), base=self.server.state_base):
            return True
        self._unauthorized()
        return False

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": SERVICE_NAME,
                    "version": __version__,
                },
            )
            return
        if path == "/v1/status":
            if not self._require_auth():
                return
            cfg = load_config()
            self._send_json(200, {"ok": True, "cosd": __version__, **run_status(cfg)})
            return
        self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/v1/stop":
            if not self._require_auth():
                return
            self._send_json(200, {"ok": True, "stopping": True})
            threading.Thread(target=self.server.request_shutdown, daemon=True).start()
            return
        if path == "/v1/ask":
            if not self._require_auth():
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length > MAX_BODY_BYTES:
                self._send_json(413, {"ok": False, "error": "request too large", "error_kind": "usage"})
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"ok": False, "error": "invalid JSON", "error_kind": "usage"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "body must be an object", "error_kind": "usage"})
                return
            question = payload.get("question")
            if not isinstance(question, str):
                self._send_json(400, {"ok": False, "error": "question required", "error_kind": "usage"})
                return
            session_id = payload.get("session_id")
            if session_id is not None and not isinstance(session_id, str):
                self._send_json(400, {"ok": False, "error": "session_id must be a string", "error_kind": "usage"})
                return
            try:
                rt = build_runtime()
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"ok": False, "error": str(exc), "error_kind": "internal"})
                return
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(run_ask, rt, question=question, session_id=session_id)
                try:
                    code, body = future.result(timeout=ASK_TIMEOUT_S)
                except FuturesTimeout:
                    self._send_json(504, {"ok": False, "error": "ask timed out", "error_kind": "timeout"})
                    return
            if code == EXIT_OK and body.get("ok"):
                http_status = 200
            elif code == EXIT_USAGE:
                http_status = 400
            elif code in (EXIT_STOPPED, EXIT_MODEL):
                http_status = 503
            else:
                http_status = 500
            self._send_json(http_status, body)
            return
        self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})

    def do_PUT(self) -> None:  # noqa: N802
        self._send_json(405, {"ok": False, "error": "method not allowed", "error_kind": "method"})


def validate_bind_host(host: str) -> str:
    if host in ("127.0.0.1", "localhost"):
        return "127.0.0.1"
    raise ValueError(f"refusing to bind cosd to non-loopback host {host!r}")


def run_server(*, host: str = DEFAULT_HOST, port: int, state_base=None) -> None:
    host = validate_bind_host(host)
    ensure_token(state_base)
    httpd = CosdHTTPServer((host, port), Handler, state_base=state_base)
    LOG.info("cosd listening on %s:%s", host, port)

    def handle_sigterm(*_args) -> None:
        httpd.request_shutdown()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGINT, handle_sigterm)
    try:
        httpd.serve_forever(poll_interval=0.2)
    finally:
        httpd.server_close()
        LOG.info("cosd stopped")
