from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from cos.config import state_dir

from . import __version__
from .auth import ensure_token, rotate_token
from .constants import DEFAULT_HOST, DEFAULT_PORT
from .lifecycle import (
    clear_pid,
    fetch_health,
    process_alive,
    process_is_cosd,
    read_pid,
    spawn_server,
    stop_process,
)
from .server import run_server, validate_bind_host

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_ERROR = 1


def _state_base() -> Path:
    return state_dir()


def cmd_serve(args: argparse.Namespace) -> int:
    host = validate_bind_host(args.host)
    run_server(host=host, port=args.port, state_base=_state_base())
    return EXIT_OK


def cmd_start(args: argparse.Namespace) -> int:
    try:
        if args.foreground:
            return cmd_serve(args)
        pid = spawn_server(host=args.host, port=args.port, base=_state_base())
        print(json.dumps({"ok": True, "pid": pid, "host": args.host, "port": args.port}))
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def _record_endpoint(record) -> tuple[str, int]:
    return record.host, record.port


def cmd_status(_args: argparse.Namespace) -> int:
    record = read_pid(_state_base())
    if record is None:
        print(json.dumps({"ok": False, "running": False, "reason": "no pid file"}))
        return EXIT_OK
    host, port = _record_endpoint(record)
    alive = process_alive(record.pid) and process_is_cosd(record.pid)
    health = fetch_health(host, port) if alive else None
    print(
        json.dumps(
            {
                "ok": True,
                "running": bool(health and health.get("ok")),
                "pid": record.pid,
                "host": host,
                "port": port,
                "health": health,
                "stale_pid": alive and not (health and health.get("ok")),
            }
        )
    )
    return EXIT_OK


def cmd_health(_args: argparse.Namespace) -> int:
    record = read_pid(_state_base())
    if record is None:
        print(json.dumps({"ok": False, "error": "not running"}))
        return EXIT_ERROR
    host, port = _record_endpoint(record)
    health = fetch_health(host, port)
    if not health:
        print(json.dumps({"ok": False, "error": "unreachable"}))
        return EXIT_ERROR
    print(json.dumps(health))
    return EXIT_OK


def _authenticated_request(path: str, *, method: str = "GET", body: bytes | None = None) -> dict:
    record = read_pid(_state_base())
    if record is None:
        raise RuntimeError("cosd is not running")
    token = ensure_token(_state_base()).token
    host, port = _record_endpoint(record)
    url = f"http://{host}:{port}{path}"
    req = Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_stop(_args: argparse.Namespace) -> int:
    record = read_pid(_state_base())
    if record is None:
        print("cosd: not running", file=sys.stderr)
        return EXIT_OK
    try:
        _authenticated_request("/v1/stop", method="POST", body=b"{}")
    except (URLError, RuntimeError, json.JSONDecodeError):
        if not stop_process(record, base=_state_base()):
            print("cosd: failed to stop", file=sys.stderr)
            return EXIT_ERROR
    else:
        stop_process(record, base=_state_base(), timeout=5)
    clear_pid(_state_base())
    print(json.dumps({"ok": True, "stopped": True}))
    return EXIT_OK


def cmd_restart(args: argparse.Namespace) -> int:
    cmd_stop(args)
    return cmd_start(args)


def cmd_rotate_token(_args: argparse.Namespace) -> int:
    rec = rotate_token(_state_base())
    print(json.dumps({"ok": True, "version": rec.version, "issued_at": rec.issued_at}))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 12):
        print("cosd: Python 3.12+ required", file=sys.stderr)
        return EXIT_USAGE
    parser = argparse.ArgumentParser(prog="cosd", description="Chief of Staff local daemon")
    parser.add_argument("--version", action="version", version=f"cosd {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run HTTP server (foreground)")
    serve.add_argument("--host", default=DEFAULT_HOST)
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--foreground", action="store_true", help=argparse.SUPPRESS)
    serve.set_defaults(func=cmd_serve)

    start = sub.add_parser("start", help="start daemon in background")
    start.add_argument("--host", default=DEFAULT_HOST)
    start.add_argument("--port", type=int, default=DEFAULT_PORT)
    start.add_argument("--foreground", action="store_true", help="run in foreground (tests)")
    start.set_defaults(func=cmd_start)

    for name, func in (
        ("status", cmd_status),
        ("health", cmd_health),
        ("stop", cmd_stop),
        ("restart", cmd_restart),
    ):
        sub.add_parser(name).set_defaults(func=func)

    sub.add_parser("rotate-token").set_defaults(func=cmd_rotate_token)

    args = parser.parse_args(argv)
    if hasattr(args, "host"):
        try:
            validate_bind_host(args.host)
        except ValueError as exc:
            print(f"cosd: {exc}", file=sys.stderr)
            return EXIT_ERROR
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
