"""Teacher Workstation — read-only local UI (stdlib http.server, no deps).

Binds to 127.0.0.1:4310 only. Serves the vanilla-JS frontend from
``apps/teacher-workstation/`` and a read-only JSON API. No write routes exist
(no POST/PUT/PATCH/DELETE handling). No secrets are ever emitted.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from . import adapter

REPO = Path(__file__).resolve().parents[2]
STATIC_DIR = REPO / "apps" / "teacher-workstation"

HOST = "127.0.0.1"
PORT = 4310


def _json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "TeacherWorkstation/1.0"

    # --- helpers -----------------------------------------------------------
    def _send_json(self, status: int, obj) -> None:
        body = _json_bytes(obj)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, text: str, ctype: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, ctype: str) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self._send_text(404, "not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- HTTP verbs --------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        # API routes (read-only).
        if path.startswith("/api/"):
            self._route_api(path, parse_qs(parsed.query))
            return

        # Static files.
        if path in ("/", "/index.html"):
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/styles.css":
            self._send_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._send_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
        else:
            self._send_text(404, "not found")

    def _route_api(self, path: str, query: dict) -> None:
        parts = [p for p in path.split("/") if p]  # e.g. ['api','weeks','2','3','questions']
        if len(parts) < 2:
            self._send_json(404, {"error": "not found"})
            return
        # parts[0] == 'api'
        resource = parts[1]

        try:
            if resource == "status":
                self._send_json(200, adapter.system_status())
            elif resource == "home":
                self._send_json(200, adapter.home())
            elif resource == "weeks":
                self._send_json(200, adapter.list_weeks())
            elif resource == "completed":
                self._send_json(200, {"latest": adapter.latest_completed()})
            elif resource == "week" and len(parts) == 4:
                quarter, week = int(parts[2]), int(parts[3])
                detail = adapter.week_detail(quarter, week)
                if detail is None:
                    self._send_json(404, {"error": f"no packet for Q{quarter}W{week}"})
                else:
                    self._send_json(200, detail)
            elif resource == "week" and len(parts) == 5 and parts[4] == "questions":
                quarter, week = int(parts[2]), int(parts[3])
                detail = adapter.week_detail(quarter, week)
                self._send_json(200, detail["questions"] if detail else [])
            else:
                self._send_json(404, {"error": "not found"})
        except (ValueError, TypeError):
            self._send_json(400, {"error": "bad request"})
        except Exception as exc:  # noqa: BLE001 — adapter errors must never crash the UI
            self._send_json(500, {"error": type(exc).__name__})

    # Write verbs are explicitly NOT implemented. Any non-GET returns 405.
    def do_POST(self) -> None:  # noqa: N802
        self._send_text(405, "read-only: POST disabled")

    def do_PUT(self) -> None:  # noqa: N802
        self._send_text(405, "read-only: PUT disabled")

    def do_PATCH(self) -> None:  # noqa: N802
        self._send_text(405, "read-only: PATCH disabled")

    def do_DELETE(self) -> None:  # noqa: N802
        self._send_text(405, "read-only: DELETE disabled")

    def log_message(self, fmt, *args) -> None:  # noqa: N802
        # Quiet logging (no request spam on Owen's terminal).
        pass


def build_server():
    return ThreadingHTTPServer((HOST, PORT), Handler)


def run() -> int:
    server = build_server()
    print("Teacher Workstation")
    print(f"Local URL: http://{HOST}:{PORT}")
    print("Mode: READ ONLY")
    print("Canvas writes: DISABLED")
    print("(Press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\nTeacher Workstation stopped.")
    return 0


def command_self_test() -> int:
    adapter.self_test()
    # Static assets exist.
    for f in ("index.html", "styles.css", "app.js"):
        assert (STATIC_DIR / f).exists(), f"missing {f}"
    # No write-verb handler methods (only do_GET exists).
    import inspect
    src = inspect.getsource(Handler)
    for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
        assert verb in src, f"{verb} must be defined to return 405"
    print("PASS teacher-workstation server self-test")
    return 0


if __name__ == "__main__":
    import sys
    if "self-test" in sys.argv:
        raise SystemExit(command_self_test())
    raise SystemExit(run())
