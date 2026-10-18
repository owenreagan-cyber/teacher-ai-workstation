"""The shared write guard on the older local servers (phase 22, 23, 26).

Each server's real handler runs on a free loopback port. Its route back ends
are replaced with mocks, so a request that passes the guard reaches the real
handler but never touches real planning state. A refused request must never
reach the mock.

Where binding a local port is not permitted, the same handler is driven over
a connected socket pair instead (as in tests/teacher_workstation). Set
``TW_ROUTE_TEST_REQUIRE_PORT=1`` to fail rather than fall back.

The retired phase-23 teacher workspace must refuse to start.

Run: python3.12 -m unittest discover -s tests/local_http_guard -p 'test_*.py'
"""
from __future__ import annotations

import contextlib
import http.client
import io
import json
import os
import socket
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import local_http_guard  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase23 import phase23_content_engine as p23  # noqa: E402
from scripts.canvas_llm_phase23 import phase23_teacher_workspace as p23ws  # noqa: E402
from scripts.canvas_llm_phase26 import phase26_workstation as p26  # noqa: E402
from scripts.canvas_llm_phase26 import storage as p26_storage  # noqa: E402


class _SocketPairServer:
    """Stands in for the bound server when local port binding is denied."""

    server_address = ("127.0.0.1", 4399)

    def __init__(self, handler_cls) -> None:
        self.handler_cls = handler_cls
        self.request_token = local_http_guard.new_token()

    def open_client(self) -> socket.socket:
        client, srv = socket.socketpair()
        client.settimeout(10)

        def serve() -> None:
            try:
                self.handler_cls(srv, ("127.0.0.1", 0), self)
            except OSError:
                pass
            finally:
                srv.close()

        threading.Thread(target=serve, daemon=True).start()
        return client


class _GuardedServerCase:
    """Shared checks; subclasses set the handler and one write route."""

    handler_cls = None
    token_header = ""
    write_method = "POST"
    write_path = ""
    write_body: dict = {}

    def route_patches(self) -> list:
        """Patchers for the write route's back end; the first is the one asserted."""
        raise NotImplementedError

    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.server = ThreadingHTTPServer(("127.0.0.1", 0), cls.handler_cls)
            cls.server.request_token = local_http_guard.new_token()
            cls.port_mode = True
        except PermissionError:
            if os.environ.get("TW_ROUTE_TEST_REQUIRE_PORT") == "1":
                raise
            cls.server = _SocketPairServer(cls.handler_cls)
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

    def setUp(self) -> None:
        self.mocks = []
        for p in self.route_patches():
            self.mocks.append(p.start())
            self.addCleanup(p.stop)
        self.route = self.mocks[0]

    # --- helpers -------------------------------------------------------------
    def good_headers(self) -> dict:
        return {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": f"http://127.0.0.1:{self.port}",
            self.token_header: self.token,
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        if not self.port_mode:
            conn.sock = self.server.open_client()
        try:
            data = None if body is None else json.dumps(body).encode()
            hdrs = dict(headers or {})
            if data is None and method != "GET":
                hdrs.setdefault("Content-Length", "0")
            conn.request(method, path, body=data, headers=hdrs)
            resp = conn.getresponse()
            return resp.status, resp.read()
        finally:
            conn.close()

    def write(self, headers: dict):
        return self.request(self.write_method, self.write_path, self.write_body, headers)

    def assert_refused(self, headers: dict, status: int, error: str) -> None:
        got, raw = self.write(headers)
        self.assertEqual(got, status, raw)
        self.assertEqual(json.loads(raw)["error"], error)
        self.route.assert_not_called()

    # --- the checks ------------------------------------------------------------
    def test_valid_same_origin_write_works(self) -> None:
        status, raw = self.write(self.good_headers())
        self.assertEqual(status, 200, raw)
        self.route.assert_called()

    def test_referer_stands_in_for_missing_origin(self) -> None:
        headers = self.good_headers()
        del headers["Origin"]
        headers["Referer"] = f"http://127.0.0.1:{self.port}/"
        status, raw = self.write(headers)
        self.assertEqual(status, 200, raw)

    def test_foreign_origin_refused(self) -> None:
        self.assert_refused({**self.good_headers(), "Origin": "http://evil.example"}, 403, "ORIGIN_REJECTED")

    def test_missing_origin_and_referer_refused(self) -> None:
        headers = self.good_headers()
        del headers["Origin"]
        self.assert_refused(headers, 403, "ORIGIN_REJECTED")

    def test_missing_token_refused(self) -> None:
        headers = self.good_headers()
        del headers[self.token_header]
        self.assert_refused(headers, 403, "TOKEN_REJECTED")

    def test_wrong_token_refused(self) -> None:
        self.assert_refused({**self.good_headers(), self.token_header: "x" * 43}, 403, "TOKEN_REJECTED")

    def test_wrong_content_type_refused(self) -> None:
        self.assert_refused({**self.good_headers(), "Content-Type": "text/plain"}, 415, "CONTENT_TYPE_REJECTED")

    def test_wrong_host_refused(self) -> None:
        self.assert_refused({**self.good_headers(), "Host": f"evil.example:{self.port}"}, 403, "HOST_REJECTED")
        status, _ = self.request("GET", "/", headers={"Host": "evil.example"})
        self.assertEqual(status, 403)

    def test_oversized_body_refused(self) -> None:
        headers = {**self.good_headers(), "Content-Length": str(local_http_guard.MAX_BODY_BYTES + 1)}
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        if not self.port_mode:
            conn.sock = self.server.open_client()
        try:
            conn.putrequest(self.write_method, self.write_path, skip_host=True, skip_accept_encoding=True)
            for k, v in headers.items():
                conn.putheader(k, v)
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
        finally:
            conn.close()
        self.route.assert_not_called()

    def test_page_carries_this_start_token(self) -> None:
        status, raw = self.request("GET", "/", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(status, 200)
        page = raw.decode()
        self.assertIn(self.token, page)
        self.assertNotIn(self.handler_module.TOKEN_PLACEHOLDER, page)


class Phase22ServerTest(_GuardedServerCase, unittest.TestCase):
    handler_cls = p22.Handler
    handler_module = p22
    token_header = p22.TOKEN_HEADER
    write_method = "PATCH"
    write_path = "/api/daily-entries/x"
    write_body = {"version": 1, "fields": {"title": "t"}}

    def route_patches(self) -> list:
        def fake_api(handler, method, parsed):
            return handler.sendj({"ok": True, "method": method})

        return [mock.patch.object(p22.Handler, "api", autospec=True, side_effect=fake_api)]


class Phase23ServerTest(_GuardedServerCase, unittest.TestCase):
    handler_cls = p23.PacketHandler
    handler_module = p23
    token_header = p23.TOKEN_HEADER
    write_path = "/api/local-state"
    write_body = {"weekCode": "Q1W5", "approvalState": "reviewed", "version": 0}

    def route_patches(self) -> list:
        return [mock.patch.object(p23, "save_local_state_record", return_value={"status": "saved", "version": 1})]


class Phase26ServerTest(_GuardedServerCase, unittest.TestCase):
    handler_cls = p26.WorkstationHandler
    handler_module = p26
    token_header = p26.TOKEN_HEADER
    write_path = "/api/select-week"
    write_body = {"weekCode": "Q1W5"}

    def route_patches(self) -> list:
        return [
            mock.patch.object(p26_storage, "set_selected_week_code"),
            mock.patch.object(p26_storage, "connect", return_value=mock.MagicMock()),
            mock.patch.object(p26_storage, "ensure_week_state"),
        ]


class RetiredServerTest(unittest.TestCase):
    def test_phase23_teacher_workspace_refuses_to_start(self) -> None:
        err = io.StringIO()
        with mock.patch.object(p23ws, "ThreadingHTTPServer") as srv, contextlib.redirect_stderr(err):
            rc = p23ws.main(["serve"])
        self.assertEqual(rc, 1)
        srv.assert_not_called()
        self.assertIn("bin/teacher-workstation", err.getvalue())


if __name__ == "__main__":
    unittest.main()
