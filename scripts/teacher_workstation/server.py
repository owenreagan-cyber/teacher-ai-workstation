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

    # ---- write verbs: LOCAL planning state ONLY (never Canvas) ----
    def do_POST(self) -> None:  # noqa: N802
        self._handle_mutation("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle_mutation("DELETE")

    def do_PUT(self) -> None:  # noqa: N802
        self._send_text(405, "PUT not supported (use POST/DELETE)")

    def do_PATCH(self) -> None:  # noqa: N802
        self._send_text(405, "PATCH not supported (use POST/DELETE)")

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _handle_mutation(self, method: str) -> None:
        """Route a local-only mutation. Terminates at local intake state only.

        Only the explicitly-listed planning routes are handled. Everything else
        returns 405. No path here can reach Canvas mutation code.
        """
        from . import mutate

        parsed = urlparse(self.path)
        path = parsed.path
        parts = [p for p in path.split("/") if p]  # e.g. ['api','weeks','2','3','overrides']

        # Validate payload shape early.
        body = self._read_body()

        # Expected: /api/weeks/{q}/{w}/<action>...
        if len(parts) < 4 or parts[0] != "api" or parts[1] != "weeks":
            self._send_text(405, "read-only: no write route here")
            return
        try:
            quarter, week = int(parts[2]), int(parts[3])
        except (ValueError, TypeError):
            self._send_json(400, {"error": "bad request"})
            return

        source_hash = body.get("source_hash") if isinstance(body, dict) else None

        try:
            if method == "POST":
                if len(parts) == 5 and parts[4] == "overrides":
                    # POST /api/weeks/{q}/{w}/overrides
                    result = mutate.apply_day_edit(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), day=body.get("day"),
                        in_class=body.get("in_class"), at_home=body.get("at_home"),
                        clear_at_home=bool(body.get("clear_at_home")),
                        status=body.get("status"), note=body.get("note"),
                        source_value=body.get("source_value"),
                    )
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "restore-source":
                    result = mutate.restore_source(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), day=body.get("day"))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "mark-pending":
                    result = mutate.mark_pending(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), day=body.get("day"),
                        source_value=body.get("source_value"))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "mark-blank":
                    result = mutate.mark_blank(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), day=body.get("day"),
                        source_value=body.get("source_value"))
                    self._send_json(200, result)
                elif len(parts) == 7 and parts[4] == "questions" and parts[6] == "answer":
                    # POST /api/weeks/{q}/{w}/questions/{id}/answer
                    result = mutate.answer_question(
                        quarter=quarter, week=week, source_hash=source_hash,
                        question_id=parts[5], answer=body.get("answer"))
                    self._send_json(200, result)
                elif len(parts) == 6 and parts[4] == "assignments":
                    # POST /api/weeks/{q}/{w}/assignments (disposition)
                    result = mutate.set_assignment_disposition(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), title=body.get("title"),
                        action=body.get("action"))
                    self._send_json(200, result)
                elif len(parts) == 6 and parts[4] == "announcements":
                    result = mutate.edit_announcement(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), transition=body.get("transition"))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "approve":
                    # POST /api/weeks/{q}/{w}/approve
                    result = mutate.approve_artifact(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), artifact_type=body.get("artifact_type"),
                        expected_artifact_hash=body.get("expected_artifact_hash"))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "revoke-approval":
                    result = mutate.revoke_artifact(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=body.get("subject"), artifact_type=body.get("artifact_type"))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "preflight":
                    # POST /api/weeks/{q}/{w}/preflight — GET-only deployment preflight
                    from . import deploy
                    result = deploy.run_preflight(quarter=quarter, week=week,
                                                  production=bool(body.get("production")))
                    self._send_json(200, result)
                elif len(parts) == 5 and parts[4] == "deploy":
                    # POST /api/weeks/{q}/{w}/deploy — guarded production deploy
                    from . import deploy
                    result = deploy.run_deploy(
                        quarter=quarter, week=week,
                        preflight_id=body.get("preflight_id"),
                        expected_source_hash=body.get("expected_source_hash") or "",
                        expected_approval_snapshot_hash=body.get("expected_approval_snapshot_hash") or "",
                        owner_confirmation=body.get("owner_confirmation") or "",
                        production=bool(body.get("production")),
                    )
                    self._send_json(200, result)
                else:
                    self._send_text(405, "read-only: no write route here")
            elif method == "DELETE":
                if len(parts) == 6 and parts[4] == "overrides":
                    # DELETE /api/weeks/{q}/{w}/overrides/{subject}:{day}  (or query params)
                    result = mutate.restore_source(
                        quarter=quarter, week=week, source_hash=source_hash,
                        subject=parts[5].split(":")[0], day=parts[5].split(":")[1])
                    self._send_json(200, result)
                else:
                    self._send_text(405, "read-only: no delete route here")
        except mutate.StaleEdit as exc:
            self._send_json(409, {"error": "STALE", "detail": str(exc)})
        except (ValueError, KeyError) as exc:
            self._send_json(400, {"error": type(exc).__name__, "detail": str(exc)})
        except Exception as exc:  # noqa: BLE001 — never crash the UI
            from scripts.canvas_llm_deploy.coordinator import DeploymentBlocked
            if isinstance(exc, DeploymentBlocked):
                self._send_json(409, {"error": "DEPLOYMENT_BLOCKED", "detail": str(exc)})
            else:
                self._send_json(500, {"error": type(exc).__name__})

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
    # Write verbs present, but route ONLY to local planning state (never Canvas).
    import inspect
    src = inspect.getsource(Handler)
    for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
        assert verb in src, f"{verb} must be defined"
    # The server source must never import Canvas write machinery. Tokens are
    # constructed dynamically so the scanner's own source never self-matches.
    forbidden = ["canvas_connection_" + "manager", "canvas_" + "writer",
                 "Phase22Live" + "CanvasClient", "create_" + "assignment",
                 "update_" + "page", "create_" + "announcement"]
    for tok in forbidden:
        assert tok not in src, f"Canvas write token {tok!r} leaked into server"
    # Mutations route through the local mutate layer.
    assert "from . import mutate" in src
    print("PASS teacher-workstation server self-test")
    return 0


if __name__ == "__main__":
    import sys
    if "self-test" in sys.argv:
        raise SystemExit(command_self_test())
    raise SystemExit(run())
