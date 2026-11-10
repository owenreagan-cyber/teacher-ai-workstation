from __future__ import annotations

import json
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from cos.audit import AuditLog
from cos.cli import EXIT_MODEL, EXIT_OK, EXIT_STOPPED, EXIT_USAGE, build_runtime
from cos.config import load_config, state_dir
from cos.policy import KillSwitch
from cos.service import iter_ask_stream, run_ask, run_status

from . import __version__
from .auth import authorize, ensure_token
from .health import classify
from .provenance import drift, snapshot
from .constants import ASK_TIMEOUT_S, DEFAULT_HOST, MAX_BODY_BYTES, SERVICE_NAME
from .devices import (
    AuthorizationDenied,
    DeviceAuthenticationError,
    DeviceAuthorizationService,
    DeviceRegistry,
    LOCAL_OWNER_PRINCIPAL,
    default_credential_provider,
)
from .devices.http import dispatch_device_request
from .devices.pairing import PairingService, default_envelope_cipher
from .devices.pairing.http import dispatch_pairing_request
from .event_bus import get_event_bus
from .execution.engine import ExecutionEngine
from .execution_http import dispatch_execution_request
from .monitor import runtime_snapshot
from .task_http import dispatch_task_request
from .tasks import TaskRegistry

LOG = logging.getLogger("cosd")


def _audit_path(state_base=None) -> Path:
    root = Path(state_base) if state_base is not None else state_dir()
    return root / "audit.jsonl"


class CosdHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        *,
        state_base=None,
        credential_provider=None,
        envelope_cipher=None,
    ):
        self.state_base = state_base
        self.audit = AuditLog(_audit_path(state_base))
        self.task_registry = TaskRegistry.open(state_base)
        self.execution = ExecutionEngine(self.task_registry)
        # Captured once so /v1/runtime can report what startup actually repaired.
        self.recovery_report = self.execution.startup_recovery()
        self.recovery_at = time.monotonic()
        self.provenance = snapshot(__version__)
        self.started_monotonic = time.monotonic()
        self.event_bus = get_event_bus()
        self._sse_clients = 0
        self._sse_lock = threading.Lock()
        self.device_registry = None
        self.device_auth = None
        self.device_unavailable = None
        self.pairing_service = None
        self.pairing_unavailable = None
        try:
            self.device_registry = DeviceRegistry.open(
                state_base,
                credential_provider=credential_provider or default_credential_provider(),
                audit=self.audit,
            )
            root = Path(state_base) if state_base is not None else state_dir()
            self.device_auth = DeviceAuthorizationService(
                self.device_registry,
                kill_switch=KillSwitch(root),
                audit=self.audit,
            )
        except Exception as exc:  # noqa: BLE001 - local daemon must keep serving
            self.device_unavailable = str(exc)
            LOG.warning("device registry unavailable: %s", exc)
        if self.device_registry is not None:
            try:
                self.pairing_service = PairingService(
                    self.device_registry,
                    cipher=envelope_cipher or default_envelope_cipher(),
                )
            except Exception as exc:  # noqa: BLE001 - pairing must not take cosd down
                self.pairing_unavailable = str(exc)
                LOG.warning("device pairing unavailable: %s", exc)
        super().__init__(server_address, RequestHandlerClass)

    def request_shutdown(self) -> None:
        self.execution.prepare_shutdown()
        threading.Thread(target=self.shutdown, daemon=True).start()

    def drift_report(self) -> dict[str, Any]:
        """Checkout drift, cached briefly so polling does not shell out constantly."""
        now = time.monotonic()
        cached = getattr(self, "_drift_cache", None)
        if cached is not None and now - cached[0] < 5.0:
            return cached[1]
        value = drift(self.provenance)
        self._drift_cache = (now, value)
        return value

    def health_report(self) -> dict[str, Any]:
        try:
            self.task_registry.db.query_one("SELECT 1")
            db_ok = True
        except Exception:  # noqa: BLE001 - health must report, never crash
            db_ok = False
        recovered = len((self.recovery_report or {}).get("repaired") or [])
        return classify(
            db_ok=db_ok,
            kill_switch=bool(run_status(load_config()).get("kill_switch")),
            queue_paused=self.execution.queue.is_paused(),
            device_registry_available=self.device_registry is not None,
            restart_required=self.drift_report().get("restart_required"),
            recovered_count=recovered,
            recovery_age_s=max(0.0, time.monotonic() - self.recovery_at),
        )


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
        try:
            self.server.audit(
                "cosd_auth_failure",
                path=self.path,
                reason="missing_or_invalid_token",
            )
        except Exception:  # noqa: BLE001 - an audit outage must not mask 401
            LOG.error("could not audit authentication failure")
        self._send_json(401, {"ok": False, "error": "unauthorized", "error_kind": "auth"})

    def _device_unauthorized(self) -> None:
        # The authorization service already audited device.auth_failed.
        self._send_json(401, {"ok": False, "error": "unauthorized", "error_kind": "auth"})

    def _forbidden(self, exc: AuthorizationDenied, *, audit: bool = True) -> None:
        if audit:
            try:
                self.server.audit(
                    "authorization.denied",
                    path=self.path,
                    permission=exc.permission,
                    reason=exc.reason,
                    device_id=exc.device_id,
                    profile=exc.profile,
                    result="denied",
                )
            except Exception:  # noqa: BLE001
                LOG.error("could not audit authorization denial")
        self._send_json(
            403,
            {
                "ok": False,
                "error": "forbidden",
                "error_kind": "forbidden",
                "permission": exc.permission,
            },
        )

    def _unavailable(self) -> None:
        try:
            self.server.audit(
                "device.registry_unavailable",
                path=self.path,
                reason="device_registry_unavailable",
                result="unavailable",
            )
        except Exception:  # noqa: BLE001
            LOG.error("could not audit device registry outage")
        self._send_json(
            503,
            {"ok": False, "error": "device registry unavailable", "error_kind": "unavailable"},
        )

    def _require_permission(self, permission: str):
        """Resolve the caller and authorize one permission. Fail closed.

        A master bearer token is the trusted local owner context. A
        ``Chief-Device`` token is an independently authenticated device and is
        never allowed to fall back to the master token.
        """
        header = self.headers.get("Authorization") or ""
        if header.startswith("Chief-Device "):
            token = header[len("Chief-Device ") :].strip()
            if self.server.device_auth is None:
                self._unavailable()
                return None
            try:
                principal = self.server.device_auth.authenticate_device_token(token)
            except DeviceAuthenticationError as exc:
                if exc.unavailable:
                    self._unavailable()
                else:
                    self._device_unauthorized()
                return None
            try:
                self.server.device_auth.authorize(principal, permission)
            except AuthorizationDenied as exc:
                self._forbidden(exc, audit=False)  # service audited it
                return None
            return principal
        if authorize(header, base=self.server.state_base):
            principal = LOCAL_OWNER_PRINCIPAL
            if permission not in principal.permissions:
                self._forbidden(
                    AuthorizationDenied(permission, "not_permitted"), audit=True
                )
                return None
            return principal
        self._unauthorized()
        return None

    @staticmethod
    def _task_permission(path: str, method: str) -> str:
        if path == "/v1/queue":
            return "tasks.read" if method == "GET" else "runtime.manage"
        if path == "/v1/workers":
            return "runtime.manage"
        if path.startswith("/v1/tasks/"):
            if path.endswith("/cancel"):
                return "tasks.cancel"
            if path.endswith("/retry"):
                return "tasks.retry"
            if path.endswith("/execute"):
                return "tasks.execute"
            if path.endswith(("/history", "/attempts", "/checkpoints")):
                return "history.read"
            return "tasks.read"
        if path == "/v1/tasks":
            return "tasks.read" if method == "GET" else "tasks.create"
        return "tasks.read"

    @staticmethod
    def _device_permission(path: str, method: str) -> str:
        if path == "/v1/devices/bootstrap":
            return "devices.manage"
        if path == "/v1/devices":
            return "devices.read" if method == "GET" else "devices.manage"
        if path.endswith("/credentials") and method == "GET":
            return "devices.read"
        if path.endswith(("/credentials/rotate", "/credentials/revoke")):
            return "credentials.manage"
        if path.startswith("/v1/devices/"):
            if method in ("PATCH", "DELETE"):
                return "devices.manage"
            if method == "POST":
                return "devices.manage"
            return "devices.read"
        return "devices.read"

    def _route_pairing(self) -> bool:
        path = urlparse(self.path).path
        if not (
            path == "/v1/enroll/request"
            or path == "/v1/enroll/redeem"
            or path.startswith("/v1/enroll/status/")
            or path == "/v1/devices/pending"
            or path.startswith("/v1/devices/pending/")
        ):
            return False
        if self.server.pairing_service is None:
            self._unavailable()
            return True
        owner_actor = None
        if path == "/v1/devices/pending" or path.startswith("/v1/devices/pending/"):
            permission = "devices.read" if self.command == "GET" else "devices.manage"
            principal = self._require_permission(permission)
            if principal is None:
                return True
            owner_actor = (
                "local_owner" if principal.is_local_owner else f"device:{principal.device_id}"
            )
        elif path == "/v1/enroll/request":
            principal = self._require_permission("devices.manage")
            if principal is None:
                return True
            owner_actor = (
                "local_owner" if principal.is_local_owner else f"device:{principal.device_id}"
            )
        # /v1/enroll/redeem authenticates with the one-time code.
        # /v1/enroll/status/* authenticates with the Enrollment request token.
        routed = dispatch_pairing_request(
            self,
            pairing=self.server.pairing_service,
            max_body=MAX_BODY_BYTES,
            owner_actor=owner_actor,
        )
        if routed is None:
            self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})
            return True
        status, body = routed
        self._send_json(status, body)
        return True

    def _route_devices(self) -> bool:
        path = urlparse(self.path).path
        if path != "/v1/devices" and not path.startswith("/v1/devices/"):
            return False
        permission = self._device_permission(path, self.command)
        principal = self._require_permission(permission)
        if principal is None:
            return True
        if self.server.device_registry is None:
            self._unavailable()
            return True
        routed = dispatch_device_request(
            self,
            registry=self.server.device_registry,
            max_body=MAX_BODY_BYTES,
            principal=principal,
        )
        if routed is None:
            self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})
            return True
        status, body = routed
        self._send_json(status, body)
        return True

    def _route_tasks_and_execution(self) -> bool:
        path = urlparse(self.path).path
        if not (
            path == "/v1/tasks"
            or path.startswith("/v1/tasks/")
            or path.startswith("/v1/queue")
            or path == "/v1/workers"
        ):
            return False
        if self._require_permission(self._task_permission(path, self.command)) is None:
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
        if self._require_permission("status.read") is None:
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
        if self._route_pairing():
            return
        if self._route_devices():
            return
        if path == "/v1/status":
            if self._require_permission("status.read") is None:
                return
            cfg = load_config()
            counts = self.server.task_registry.get_task_counts()
            health = self.server.health_report()
            drift = self.server.drift_report()
            self._send_json(
                200,
                {
                    "ok": True,
                    "cosd": __version__,
                    "task_counts": counts,
                    **run_status(cfg),
                    "state": health["state"],
                    "state_reasons": health["reasons"],
                    "runtime": {
                        **self.server.provenance.public_dict(),
                        "current_commit": drift.get("current_commit"),
                        "restart_required": drift.get("restart_required"),
                        "restart_reason": drift.get("reason", ""),
                    },
                },
            )
            return
        if path == "/v1/runtime":
            if self._require_permission("runtime.manage") is None:
                return
            cfg = load_config()
            body = runtime_snapshot(
                registry=self.server.task_registry,
                engine=self.server.execution,
                cfg=cfg,
                state_base=self.server.state_base,
                started_monotonic=self.server.started_monotonic,
                provenance=self.server.provenance.public_dict(),
                drift=self.server.drift_report(),
                health=self.server.health_report(),
                recovery=self.server.recovery_report,
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
        if self._route_pairing():
            return
        if self._route_devices():
            return
        if self._route_tasks_and_execution():
            return
        if path == "/v1/stop":
            if self._require_permission("runtime.manage") is None:
                return
            self._send_json(200, {"ok": True, "stopping": True})
            threading.Thread(target=self.server.request_shutdown, daemon=True).start()
            return
        if path == "/v1/ask":
            if self._require_permission("ask") is None:
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
            if self._require_permission("ask") is None:
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

    def do_PATCH(self) -> None:  # noqa: N802
        if self._route_devices():
            return
        self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        if self._route_devices():
            return
        self._send_json(404, {"ok": False, "error": "not found", "error_kind": "not_found"})


def validate_bind_host(host: str) -> str:
    if host in ("127.0.0.1", "localhost"):
        return "127.0.0.1"
    raise ValueError(f"refusing to bind cosd to non-loopback host {host!r}")


def run_server(
    *,
    host: str = DEFAULT_HOST,
    port: int,
    state_base=None,
    credential_provider=None,
    envelope_cipher=None,
) -> None:
    host = validate_bind_host(host)
    ensure_token(state_base)
    httpd = CosdHTTPServer(
        (host, port),
        Handler,
        state_base=state_base,
        credential_provider=credential_provider,
        envelope_cipher=envelope_cipher,
    )
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
