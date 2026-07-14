from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "apps/unified-weekly-production"
APP_DATA = APP_DIR / "data/phase26-demo.json"
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase26 import pipeline, storage  # noqa: E402
from scripts.canvas_llm_phase26.export_package import build_export_package, stable_hash  # noqa: E402
from scripts.canvas_llm_phase26.validate_phase26_state import main as validate_main  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build_workstation_packet(week_code: str | None = None, db_path: Path | None = None) -> dict[str, Any]:
    conn = storage.connect(db_path)
    try:
        packet = pipeline.build_workstation_packet(week_code or storage.get_selected_week_code(conn), db_path)
        if not storage.list_revisions(conn, packet["weekCode"]):
            storage.record_revision(conn, packet["weekCode"], "generated", "initial generation", {"packetHash": stable_hash(packet)})
        return packet
    finally:
        conn.close()


def build_demo_packet(week_code: str = "Q1W5", db_path: Path | None = None) -> dict[str, Any]:
    return build_workstation_packet(week_code, db_path)


def selected_week_code(db_path: Path | None = None) -> str:
    conn = storage.connect(db_path)
    try:
        return storage.get_selected_week_code(conn)
    finally:
        conn.close()


def render_index(packet: dict[str, Any]) -> str:
    weeks = packet["weekSelection"]["weeks"] if "weeks" in packet["weekSelection"] else []
    return (APP_DIR / "index.html").read_text(encoding="utf-8")


class WorkstationHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self):  # noqa: N802
        parsed = self.path.split("?", 1)[0]
        if parsed == "/":
            self.path = "/index.html"
            return super().do_GET()
        if parsed == "/api/health":
            packet = build_workstation_packet()
            self._send_json(
                {
                    "status": "ok",
                    "previewOnly": True,
                    "canvasWritesAllowed": False,
                    "emailSendsAllowed": False,
                    "externalAPIsAllowed": False,
                    "warnCount": packet["validation"]["warnCount"],
                    "failCount": packet["validation"]["failCount"],
                }
            )
            return
        if parsed == "/api/bootstrap":
            packet = build_workstation_packet()
            self._send_json(
                {
                    "weekCode": packet["weekCode"],
                    "weekSelection": packet["weekSelection"],
                    "localState": packet["localState"],
                    "status": "preview-only",
                }
            )
            return
        if parsed == "/api/workstation":
            packet = build_workstation_packet()
            self._send_json(packet)
            return
        if parsed == "/api/local-state":
            from urllib.parse import parse_qs, urlparse

            params = parse_qs(urlparse(self.path).query)
            week_code = params.get("weekCode", [None])[0] or storage.DEFAULT_WEEK_CODE
            conn = storage.connect()
            try:
                self._send_json({"selectedWeekCode": storage.get_selected_week_code(conn), **storage.state_summary(conn, week_code)})
            finally:
                conn.close()
            return
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        parsed = self.path.split("?", 1)[0]
        if parsed == "/api/select-week":
            body = self._read_json()
            week_code = str(body.get("weekCode") or storage.DEFAULT_WEEK_CODE)
            conn = storage.connect()
            try:
                storage.set_selected_week_code(conn, week_code)
                storage.ensure_week_state(conn, week_code)
                self._send_json({"ok": True, "weekCode": week_code})
            finally:
                conn.close()
            return
        if parsed == "/api/correction":
            body = self._read_json()
            conn = storage.connect()
            try:
                saved = storage.save_correction(conn, body)
                storage.record_revision(conn, body.get("weekCode"), "correction", f"correction saved for {body.get('subject')} / {body.get('field')}", {"correction": body})
                self._send_json({"ok": True, "saved": saved})
            finally:
                conn.close()
            return
        if parsed == "/api/approve":
            body = self._read_json()
            conn = storage.connect()
            try:
                result = storage.save_approval(
                    conn,
                    body.get("weekCode"),
                    body.get("scope", "full-week"),
                    body.get("subject"),
                    body.get("status", "approved"),
                    packet_revision=int(body.get("packetRevision") or 0),
                    content_hash=str(body.get("contentHash") or ""),
                )
                storage.record_revision(conn, body.get("weekCode"), "approval", f"approval saved for {body.get('scope')}", {"approval": result})
                self._send_json({"ok": True, "approval": result})
            finally:
                conn.close()
            return
        if parsed == "/api/regenerate":
            body = self._read_json()
            week_code = str(body.get("weekCode") or selected_week_code())
            packet = build_workstation_packet(week_code)
            conn = storage.connect()
            try:
                storage.record_revision(conn, week_code, "regenerate", "week regenerated", {"packetHash": stable_hash(packet)})
            finally:
                conn.close()
            self._send_json({"ok": True, "packet": packet})
            return
        if parsed == "/api/export":
            body = self._read_json()
            week_code = str(body.get("weekCode") or selected_week_code())
            packet = build_workstation_packet(week_code)
            export_root = storage.LOCAL_ROOT / "exports"
            manifest = build_export_package(packet, export_root)
            conn = storage.connect()
            try:
                storage.record_export(conn, week_code, manifest["savedPath"], manifest["packageHash"], packet.get("deploymentManifestPreview", {}))
                storage.record_revision(conn, week_code, "export", "export package written", {"manifest": manifest})
            finally:
                conn.close()
            self._send_json({"ok": True, **manifest})
            return
        self.send_error(404, "unknown endpoint")


def command_build_demo(args: argparse.Namespace) -> int:
    packet = build_demo_packet(args.week, Path(args.db) if args.db else None)
    out = Path(args.output or APP_DATA)
    write_json(out, packet)
    print(f"Phase 26 workstation demo rebuilt: {out}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    original_argv = sys.argv
    try:
        sys.argv = ["validate_phase26_state.py", *args.paths]
        return validate_main()
    finally:
        sys.argv = original_argv


def command_serve(args: argparse.Namespace) -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(APP_DIR)
    packet = build_demo_packet(args.week, Path(args.db) if args.db else None)
    if not APP_DATA.exists():
        try:
            write_json(APP_DATA, packet)
        except OSError:
            pass
    server = ThreadingHTTPServer((args.host, args.port), WorkstationHandler)
    print(f"Phase 26 workstation serving at http://{args.host}:{args.port}")
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 26 unified weekly production workstation")
    parser.add_argument("--db", default=str(storage.DB_PATH))
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_demo = sub.add_parser("build-demo", help="Build the committed demo packet")
    build_demo.add_argument("--week", default="Q1W5")
    build_demo.add_argument("--output", default=str(APP_DATA))
    build_demo.set_defaults(func=command_build_demo)

    validate = sub.add_parser("validate", help="Validate workstation packet JSON files")
    validate.add_argument("--week", default="Q1W5")
    validate.add_argument("paths", nargs="+")
    validate.set_defaults(func=command_validate)

    serve = sub.add_parser("serve", help="Serve the local workstation")
    serve.add_argument("--week", default="Q1W5")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=18776)
    serve.set_defaults(func=command_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
