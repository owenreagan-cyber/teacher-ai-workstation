from __future__ import annotations

import json
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from cos.audit import AuditLog
from cos.cli import EXIT_MODEL, EXIT_OK, EXIT_STOPPED, EXIT_USAGE, build_runtime
from cos.config import load_config
from cos.service import iter_ask_stream, run_ask, run_status

from . import __version__
from .auth import authorize, ensure_token
from .constants import ASK_TIMEOUT_S, DEFAULT_HOST, MAX_BODY_BYTES, SERVICE_NAME
from .event_bus import get_event_bus
from .execution.engine import ExecutionEngine
from .execution_http import dispatch_execution_request
from .monitor import runtime_snapshot
from .task_http import dispatch_task_request
from .tasks import TaskRegistry

LOG = logging.getLogger("cosd")


class CosdHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, *, state_base=None):
        self.state_base = state_base
        self.task_registry = TaskRegistry.open(state_base)
        self.execution = ExecutionEngine(self.task_registry)
        self.execution.startup_recovery()
        self.started_monotonic = time.monotonic()
        self.event_bus = get_event_bus()
        self._sse_clients = 0
        self._sse_lock = threading.Lock()
        super().__init__(server_address, RequestHandlerClass)

    def request_shutdown(self) -> None:
        self.execution.prepare_shutdown()
        threading.Thread(target=self.shutdown, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server: CosdHTTPServer  # type: ignore[assignment]

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        LOG.info("%s - %s", self.address_string(), format % args)

    def _send_sse_event(self, data: dict[str, Any]) -> None:
        raw = f"data: {json.dumps(data, separators=(',', ':'), ensure_ascii=False)}\n\n".encode("utf-8")
        self.wfile.write(raw)
        self.wfile.flush()

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

    def _route_tasks_and_execution(self) -> bool:
        path = urlparse(self.path).path
        if not (
            path == "/v1/tasks"
            or path.startswith("/v1/tasks/")
            or path.startswith("/v1/queue")
            or path == "/v1/workers"
        ):
            return False
        if not self._require_auth():
            return True
        routed = dispatch_execution_request(
            self,
            registry=self.server.task_registry,
            engine=self.server.execution,
            max_body=MAX_BODY_BYTES,
        )
        if routed is not None:
            status, body = routed
            self._send_json(status, body)
            return True
        routed = dispatch_task_request(
            self, registry=self.server.task_registry, max_body=MAX_BODY_BYTES
        )
        if routed is not None:
            status, body = routed
            self._send_json(status, body)
            return True
        if path.startswith("/v1/tasks") or path.startswith("/v1/queue") or path == "/v1/workers":
            self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})
            return True
        return False

    def _handle_events_sse(self, query: dict[str, list[str]]) -> None:
        if not self._require_auth():
            return
        srv = self.server
        unsub = lambda: None  # noqa: E731
        with srv._sse_lock:
            if srv._sse_clients >= 8:
                self._send_json(503, {"ok": False, "error": "too many streams", "error_kind": "usage"})
                return
            srv._sse_clients += 1
        last_id = 0
        try:
            last_id = int((query.get("since") or ["0"])[0])
        except ValueError:
            last_id = 0
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for ev in srv.event_bus.since(last_id):
                self._send_sse_event(ev.sse_payload())
                last_id = ev.id
            stop = threading.Event()
            lock = threading.Lock()
            latest = last_id

            def on_event(ev) -> None:
                nonlocal latest
                with lock:
                    latest = ev.id
                try:
                    self._send_sse_event(ev.sse_payload())
                except OSError:
                    stop.set()

            unsub = srv.event_bus.subscribe(on_event)
            while not stop.is_set():
                time.sleep(1.0)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            try:
                unsub()
            except Exception:  # noqa: BLE001
                pass
            with srv._sse_lock:
                srv._sse_clients = max(0, srv._sse_clients - 1)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
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
            counts = self.server.task_registry.get_task_counts()
            self._send_json(
                200,
                {"ok": True, "cosd": __version__, "task_counts": counts, **run_status(cfg)},
            )
            return
        if path == "/v1/runtime":
            if not self._require_auth():
                return
            cfg = load_config()
            body = runtime_snapshot(
                registry=self.server.task_registry,
                engine=self.server.execution,
                cfg=cfg,
                state_base=self.server.state_base,
                started_monotonic=self.server.started_monotonic,
            )
            self._send_json(200, body)
            return
        if path == "/v1/events":
            self._handle_events_sse(query)
            return
        if not self._route_tasks_and_execution():
            self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if self._route_tasks_and_execution():
            return
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
        if path == "/v1/ask/stream":
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
            try:
                rt = build_runtime()
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"ok": False, "error": str(exc), "error_kind": "internal"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                for item in iter_ask_stream(rt, question=question, session_id=session_id):
                    line = json.dumps(item, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    self.wfile.write(line + b"\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
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
