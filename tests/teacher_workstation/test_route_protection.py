"""HTTP integration tests for Teacher Workstation route protection (D-022).

Starts a real server instance on a free loopback port. The route handlers in
``mutate`` / ``deploy`` / ``adapter`` are replaced with mocks, so a request
that passes the guards reaches the real dispatcher but never touches real
planning state or Canvas. A rejected request must never reach a handler.

Where binding a local port is not permitted (the Claude Code sandbox), the
same real ``Handler`` is driven over a connected socket pair instead, with the
same HTTP client code; only the two bind-specific tests are skipped. Set
``TW_ROUTE_TEST_REQUIRE_PORT=1`` to fail rather than fall back.

Run: python3.12 -m unittest discover -s tests/teacher_workstation -p 'test_*.py'
"""
from __future__ import annotations

import http.client
import json
import os
import secrets
import socket
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.teacher_workstation import adapter, deploy, mutate, server  # noqa: E402
from scripts.canvas_planner import ai_review, approval_bundle, source_sync  # noqa: E402

MB = 1024 * 1024

# (method, path, body, handler module, handler name)
MUTATING_ROUTES = [
    ("POST", "/api/weeks/2/3/overrides", {"source_hash": "h", "subject": "math", "day": "Monday"}, mutate, "apply_day_edit"),
    ("POST", "/api/weeks/2/3/restore-source", {"source_hash": "h", "subject": "math", "day": "Monday"}, mutate, "restore_source"),
    ("POST", "/api/weeks/2/3/mark-pending", {"source_hash": "h", "subject": "math", "day": "Monday"}, mutate, "mark_pending"),
    ("POST", "/api/weeks/2/3/mark-blank", {"source_hash": "h", "subject": "math", "day": "Monday"}, mutate, "mark_blank"),
    ("POST", "/api/weeks/2/3/questions/q1/answer", {"source_hash": "h", "answer": "a"}, mutate, "answer_question"),
    ("POST", "/api/weeks/2/3/assignments/x", {"source_hash": "h", "subject": "math", "title": "t", "action": "REJECT"}, mutate, "set_assignment_disposition"),
    ("POST", "/api/weeks/2/3/announcements/x", {"source_hash": "h", "subject": "math", "transition": "x"}, mutate, "edit_announcement"),
    ("POST", "/api/weeks/2/3/approve", {"source_hash": "h", "subject": "math", "artifact_type": "page", "expected_artifact_hash": "a"}, mutate, "approve_artifact"),
    ("POST", "/api/weeks/2/3/revoke-approval", {"source_hash": "h", "subject": "math", "artifact_type": "page"}, mutate, "revoke_artifact"),
    ("POST", "/api/weeks/2/3/resync-source", {"source_hash": "h"}, source_sync, "resync"),
    ("POST", "/api/weeks/2/3/apply-source", {"source_hash": "h"}, source_sync, "decide"),
    ("POST", "/api/weeks/2/3/keep-source", {"source_hash": "h"}, source_sync, "decide"),
    ("POST", "/api/weeks/2/3/undo-plan", {"source_hash": "h"}, mutate, "undo_last_plan_edit"),
    ("POST", "/api/weeks/2/3/approve-course", {"source_hash": "h", "course": "math", "expected_hashes": {}}, approval_bundle, "approve_course"),
    ("POST", "/api/weeks/2/3/ai-findings/f1", {"source_hash": "h", "answer": "DECLINE"}, ai_review, "answer_finding"),
    ("POST", "/api/weeks/2/3/preflight", {"production": False}, deploy, "run_preflight"),
    ("POST", "/api/weeks/2/3/deploy", {"preflight_id": "p", "owner_confirmation": "DEPLOY Q2W3", "production": True}, deploy, "run_deploy"),
    ("DELETE", "/api/weeks/2/3/overrides/math:Monday", None, mutate, "restore_source"),
]

GET_API = [
    ("/api/status", "system_status", {"overall": "PASS"}),
    ("/api/home", "home", {"today": "x", "weeks": []}),
    ("/api/weeks", "list_weeks", []),
    ("/api/completed", "latest_completed", None),
    ("/api/week/2/3", "week_detail", {"week_code": "Q2W3", "questions": []}),
]


class _SocketPairServer:
    """Stands in for the bound server when local port binding is denied.

    Each client connection is one end of a socket pair; the real ``Handler``
    serves the other end in a thread, exactly as ThreadingHTTPServer would.
    """

    server_address = ("127.0.0.1", 4310)

    def __init__(self) -> None:
        self.request_token = secrets.token_urlsafe(32)

    def open_client(self) -> socket.socket:
        client, srv = socket.socketpair()
        client.settimeout(10)

        def serve() -> None:
            try:
                server.Handler(srv, ("127.0.0.1", 0), self)
            except OSError:
                pass
            finally:
                srv.close()

        threading.Thread(target=serve, daemon=True).start()
        return client


class RouteProtectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.patchers = []
        cls.handlers = {}
        for _, _, _, module, name in MUTATING_ROUTES:
            key = (module.__name__, name)
            if key in cls.handlers:
                continue
            p = mock.patch.object(module, name, return_value={"ok": True, "handler": name})
            cls.handlers[key] = p.start()
            cls.patchers.append(p)
        for _, name, value in GET_API:
            p = mock.patch.object(adapter, name, return_value=value)
            p.start()
            cls.patchers.append(p)

        try:
            cls.server = server.build_server(port=0)
            cls.port_mode = True
        except PermissionError:
            if os.environ.get("TW_ROUTE_TEST_REQUIRE_PORT") == "1":
                raise
            cls.server = _SocketPairServer()
            cls.port_mode = False
        cls.port = cls.server.server_address[1]
        cls.token = cls.server.request_token
        if cls.port_mode:
            cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
            cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.port_mode:
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)
        for p in cls.patchers:
            p.stop()

    def setUp(self) -> None:
        for m in self.handlers.values():
            m.reset_mock()

    # --- helpers -------------------------------------------------------------
    def own_origin(self, host: str = "127.0.0.1") -> str:
        return f"http://{host}:{self.port}"

    def good_headers(self, host: str = "127.0.0.1") -> dict:
        return {
            "Host": f"{host}:{self.port}",
            "Origin": self.own_origin(host),
            "X-Teacher-Workstation-Token": self.token,
            "Content-Type": "application/json",
        }

    def connect(self) -> http.client.HTTPConnection:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        if not self.port_mode:
            conn.sock = self.server.open_client()
        return conn

    def request(self, method: str, path: str, body=None, headers=None):
        conn = self.connect()
        try:
            data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
            hdrs = dict(headers or {})
            if data is None and method != "GET":
                hdrs.setdefault("Content-Length", "0")
            conn.request(method, path, body=data, headers=hdrs)
            resp = conn.getresponse()
            raw = resp.read()
            return resp.status, raw
        finally:
            conn.close()

    def json_error(self, raw: bytes) -> str:
        return json.loads(raw.decode()).get("error", "")

    def assert_no_handler_called(self) -> None:
        for (mod, name), m in self.handlers.items():
            self.assertFalse(m.called, f"{mod}.{name} ran for a rejected request")

    # --- bind ------------------------------------------------------------------
    def test_binds_loopback_only(self) -> None:
        self.assertEqual(server.HOST, "127.0.0.1")
        if not self.port_mode:
            self.skipTest("local port binding not permitted here")
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_token_is_random_per_server_start(self) -> None:
        if not self.port_mode:
            self.skipTest("local port binding not permitted here")
        other = server.build_server(port=0)
        try:
            self.assertNotEqual(other.request_token, self.token)
            self.assertGreaterEqual(len(self.token), 32)
        finally:
            other.server_close()

    def test_planner_status_route_uses_local_projection(self) -> None:
        with mock.patch(
            "scripts.canvas_planner.service.CanvasPlannerService.weekly_status",
            return_value={"domain": "canvas_weekly_planning", "contract_version": 1},
        ) as projected:
            status, raw = self.request(
                "GET", "/api/planner-status/2/3", headers={"Host": f"127.0.0.1:{self.port}"}
            )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["domain"], "canvas_weekly_planning")
        projected.assert_called_once_with(2, 3)

    # --- Host ------------------------------------------------------------------
    def test_wrong_host_rejected_on_get_and_mutations(self) -> None:
        for host in (f"evil.example:{self.port}", "127.0.0.1:1", f"127.0.0.1.nip.io:{self.port}", ""):
            status, raw = self.request("GET", "/api/status", headers={"Host": host})
            self.assertEqual(status, 403, host)
            self.assertEqual(self.json_error(raw), "HOST_REJECTED")
            hdrs = self.good_headers()
            hdrs["Host"] = host
            status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
            self.assertEqual(status, 403, host)
        self.assert_no_handler_called()

    # --- Origin ----------------------------------------------------------------
    def test_foreign_origin_rejected(self) -> None:
        for origin in ("http://evil.example", f"http://localhost:{self.port}", "null",
                       f"https://127.0.0.1:{self.port}", f"http://127.0.0.1:{self.port + 1}"):
            hdrs = self.good_headers()
            hdrs["Origin"] = origin
            status, raw = self.request("POST", "/api/weeks/2/3/deploy", {"production": True}, hdrs)
            self.assertEqual(status, 403, origin)
            self.assertEqual(self.json_error(raw), "ORIGIN_REJECTED")
        self.assert_no_handler_called()

    def test_referer_used_only_when_origin_missing(self) -> None:
        hdrs = self.good_headers()
        del hdrs["Origin"]
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 403, "no Origin and no Referer must be rejected")
        hdrs["Referer"] = f"http://evil.example/?u={self.own_origin()}/"
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 403)
        hdrs["Referer"] = f"{self.own_origin()}.evil.example/"
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 403)
        self.assert_no_handler_called()
        hdrs["Referer"] = f"{self.own_origin()}/"
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 200)

    # --- token -----------------------------------------------------------------
    def test_missing_or_wrong_token_rejected(self) -> None:
        hdrs = self.good_headers()
        del hdrs["X-Teacher-Workstation-Token"]
        status, raw = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 403)
        self.assertEqual(self.json_error(raw), "TOKEN_REJECTED")
        hdrs["X-Teacher-Workstation-Token"] = self.token[:-1] + ("A" if self.token[-1] != "A" else "B")
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 403)
        status, _ = self.request("DELETE", "/api/weeks/2/3/overrides/math:Monday", None,
                                 {k: v for k, v in self.good_headers().items()
                                  if k != "X-Teacher-Workstation-Token"})
        self.assertEqual(status, 403)
        self.assert_no_handler_called()

    # --- content type ----------------------------------------------------------
    def test_wrong_content_type_rejected(self) -> None:
        for ctype in ("text/plain", "application/x-www-form-urlencoded", "multipart/form-data; boundary=x", None):
            hdrs = self.good_headers()
            if ctype is None:
                del hdrs["Content-Type"]
            else:
                hdrs["Content-Type"] = ctype
            status, raw = self.request("POST", "/api/weeks/2/3/deploy", b'{"production": true}', hdrs)
            self.assertEqual(status, 415, ctype)
            self.assertEqual(self.json_error(raw), "CONTENT_TYPE_REJECTED")
        self.assert_no_handler_called()
        hdrs = self.good_headers()
        hdrs["Content-Type"] = "application/json; charset=utf-8"
        status, _ = self.request("POST", "/api/weeks/2/3/approve", {"source_hash": "h"}, hdrs)
        self.assertEqual(status, 200)

    # --- size ------------------------------------------------------------------
    def test_oversized_body_rejected_with_413(self) -> None:
        conn = self.connect()
        try:
            conn.putrequest("POST", "/api/weeks/2/3/approve", skip_host=True)
            for k, v in self.good_headers().items():
                conn.putheader(k, v)
            conn.putheader("Content-Length", str(MB + 1))
            conn.endheaders()  # body is never sent; the server must not wait for it
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
            self.assertEqual(self.json_error(resp.read()), "BODY_TOO_LARGE")
        finally:
            conn.close()
        self.assert_no_handler_called()

    def test_body_at_limit_accepted(self) -> None:
        prefix = b'{"source_hash": "h", "pad": "'
        suffix = b'"}'
        body = prefix + b"x" * (MB - len(prefix) - len(suffix)) + suffix
        self.assertEqual(len(body), MB)
        status, _ = self.request("POST", "/api/weeks/2/3/approve", body, self.good_headers())
        self.assertEqual(status, 200)

    def test_chunked_body_rejected(self) -> None:
        hdrs = self.good_headers()
        hdrs["Transfer-Encoding"] = "chunked"
        conn = self.connect()
        try:
            conn.putrequest("POST", "/api/weeks/2/3/approve", skip_host=True)
            for k, v in hdrs.items():
                conn.putheader(k, v)
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 411)
        finally:
            conn.close()
        self.assert_no_handler_called()

    # --- valid same-origin requests still work ---------------------------------
    def test_valid_same_origin_request_works_for_each_route(self) -> None:
        for host in ("127.0.0.1", "localhost"):
            for method, path, body, module, name in MUTATING_ROUTES:
                with self.subTest(host=host, method=method, path=path):
                    handler = self.handlers[(module.__name__, name)]
                    handler.reset_mock()
                    status, raw = self.request(method, path, body, self.good_headers(host))
                    self.assertEqual(status, 200, raw)
                    self.assertTrue(handler.called, f"{name} not reached")
                    self.assertEqual(json.loads(raw)["handler"], name)

    def test_put_patch_still_405_after_guards(self) -> None:
        for verb in ("PUT", "PATCH"):
            status, _ = self.request(verb, "/api/weeks", {}, self.good_headers())
            self.assertEqual(status, 405)
            hdrs = self.good_headers()
            hdrs["Origin"] = "http://evil.example"
            status, _ = self.request(verb, "/api/weeks", {}, hdrs)
            self.assertEqual(status, 403)

    def test_unknown_write_route_still_405(self) -> None:
        status, _ = self.request("POST", "/api/weeks", {}, self.good_headers())
        self.assertEqual(status, 405)

    # --- GET-only pages unaffected ---------------------------------------------
    def test_get_pages_need_no_token_or_origin(self) -> None:
        host = {"Host": f"127.0.0.1:{self.port}"}
        for path, ctype in (("/", "text/html"), ("/index.html", "text/html"),
                            ("/styles.css", "text/css"), ("/app.js", "application/javascript")):
            status, _ = self.request("GET", path, headers=host)
            self.assertEqual(status, 200, path)
        for path, _, value in GET_API:
            status, raw = self.request("GET", path, headers={"Host": f"localhost:{self.port}"})
            self.assertEqual(status, 200, path)
            if path == "/api/completed":
                self.assertEqual(json.loads(raw), {"latest": None})
            else:
                self.assertEqual(json.loads(raw), value)
        status, _ = self.request("GET", "/nope", headers=host)
        self.assertEqual(status, 404)

    def test_page_carries_this_servers_token(self) -> None:
        status, raw = self.request("GET", "/", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(status, 200)
        html = raw.decode()
        self.assertIn(f'name="teacher-workstation-token" content="{self.token}"', html)
        self.assertNotIn(server.TOKEN_PLACEHOLDER, html)


if __name__ == "__main__":
    unittest.main()
