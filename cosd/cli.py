from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cos.config import state_dir

from . import __version__
from .auth import ensure_token, rotate_token
from .constants import DEFAULT_HOST, DEFAULT_PORT
from .lifecycle import (
    clear_pid,
    fetch_health,
    pid_report,
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
    report = pid_report(_state_base())
    if report["state"] == "absent":
        print(json.dumps({"ok": False, "running": False, "reason": "no pid file"}))
        return EXIT_OK
    print(
        json.dumps(
            {
                "ok": True,
                "running": report["running"],
                "state": report["state"],
                "pid": report["pid"],
                "host": report["host"],
                "port": report["port"],
                "health": report["health"],
                "pid_alive": report["pid_alive"],
                "pid_is_cosd": report["pid_is_cosd"],
                "stale_pid": report["pid_alive"] and not report["running"],
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


def _authenticated_request(
    path: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    query: dict | None = None,
) -> tuple[int, dict]:
    record = read_pid(_state_base())
    if record is None:
        raise RuntimeError("cosd is not running")
    token = ensure_token(_state_base()).token
    host, port = _record_endpoint(record)
    q = f"?{urlencode(query)}" if query else ""
    url = f"http://{host}:{port}{path}{q}"
    req = Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"ok": False, "error": payload}


def cmd_stop(_args: argparse.Namespace) -> int:
    record = read_pid(_state_base())
    if record is None:
        print("cosd: not running", file=sys.stderr)
        return EXIT_OK
    try:
        _authenticated_request("/v1/stop", method="POST", body=b"{}")
        # discard status/body
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


def _print_api(status: int, body: dict) -> int:
    print(json.dumps(body))
    return EXIT_OK if body.get("ok") else (EXIT_USAGE if status < 500 else EXIT_ERROR)


def cmd_tasks_list(args: argparse.Namespace) -> int:
    try:
        query = {}
        if args.state:
            query["state"] = args.state
        if args.kind:
            query["kind"] = args.kind
        if args.limit is not None:
            query["limit"] = str(args.limit)
        if args.offset is not None:
            query["offset"] = str(args.offset)
        status, body = _authenticated_request("/v1/tasks", query=query or None)
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_show(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(f"/v1/tasks/{args.task_id}")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_create(args: argparse.Namespace) -> int:
    payload: dict = {}
    if args.payload_json:
        try:
            payload = json.loads(args.payload_json)
        except json.JSONDecodeError:
            print("cosd: invalid --payload-json", file=sys.stderr)
            return EXIT_USAGE
    body = {
        "kind": args.kind,
        "title": args.title,
        "description": args.description or "",
        "priority": args.priority,
        "payload": payload,
        "idempotency_key": args.idempotency_key,
        "data_class": args.data_class,
    }
    if args.requested_by:
        body["requested_by"] = args.requested_by
    try:
        status, resp = _authenticated_request(
            "/v1/tasks",
            method="POST",
            body=json.dumps({k: v for k, v in body.items() if v is not None}).encode("utf-8"),
        )
        return _print_api(status, resp)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_cancel(args: argparse.Namespace) -> int:
    raw = json.dumps({"reason": args.reason or ""}).encode("utf-8")
    try:
        status, body = _authenticated_request(
            f"/v1/tasks/{args.task_id}/cancel", method="POST", body=raw
        )
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_retry(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(
            f"/v1/tasks/{args.task_id}/retry", method="POST", body=b"{}"
        )
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_queue_status(_args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request("/v1/queue")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_queue_list(_args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request("/v1/tasks", query={"state": "QUEUED", "limit": "100"})
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_queue_run(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(
            f"/v1/tasks/{args.task_id}/execute", method="POST", body=b"{}"
        )
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_queue_pause(_args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request("/v1/queue/pause", method="POST", body=b"{}")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_queue_resume(_args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request("/v1/queue/resume", method="POST", body=b"{}")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_workers_list(_args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request("/v1/workers")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_attempts(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(f"/v1/tasks/{args.task_id}/attempts")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_checkpoints(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(f"/v1/tasks/{args.task_id}/checkpoints")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_tasks_history(args: argparse.Namespace) -> int:
    try:
        status, body = _authenticated_request(f"/v1/tasks/{args.task_id}/history")
        return _print_api(status, body)
    except (URLError, RuntimeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_rotate_token(_args: argparse.Namespace) -> int:
    rec = rotate_token(_state_base())
    print(json.dumps({"ok": True, "version": rec.version, "issued_at": rec.issued_at}))
    return EXIT_OK


def _device_call(path: str, *, method: str = "GET", body: dict | None = None) -> int:
    try:
        raw = None if body is None else json.dumps(body).encode("utf-8")
        status, resp = _authenticated_request(path, method=method, body=raw)
        return _print_api(status, resp)
    except (URLError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_devices_list(args: argparse.Namespace) -> int:
    query = {}
    if args.status:
        query["status"] = args.status
    if args.profile:
        query["device_profile"] = args.profile
    if args.limit is not None:
        query["limit"] = str(args.limit)
    if args.offset is not None:
        query["offset"] = str(args.offset)
    try:
        status, body = _authenticated_request("/v1/devices", query=query or None)
        return _print_api(status, body)
    except (URLError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"cosd: {exc}", file=sys.stderr)
        return EXIT_ERROR


def cmd_devices_show(args: argparse.Namespace) -> int:
    return _device_call(f"/v1/devices/{args.device_id}")


def cmd_devices_credentials(args: argparse.Namespace) -> int:
    return _device_call(f"/v1/devices/{args.device_id}/credentials")


def cmd_devices_bootstrap(args: argparse.Namespace) -> int:
    if not args.confirm:
        print("cosd: pass --confirm to register this Mac as the primary owner device", file=sys.stderr)
        return EXIT_USAGE
    body: dict = {"confirm": True}
    if args.name:
        body["display_name"] = args.name
    if args.owner:
        body["owner_id"] = args.owner
    return _device_call("/v1/devices/bootstrap", method="POST", body=body)


def cmd_devices_rename(args: argparse.Namespace) -> int:
    return _device_call(
        f"/v1/devices/{args.device_id}", method="PATCH", body={"display_name": args.name}
    )


def cmd_devices_profile(args: argparse.Namespace) -> int:
    body: dict = {"device_profile": args.profile}
    if args.trust:
        body["trust_level"] = args.trust
    return _device_call(f"/v1/devices/{args.device_id}", method="PATCH", body=body)


def cmd_devices_disable(args: argparse.Namespace) -> int:
    return _device_call(f"/v1/devices/{args.device_id}/disable", method="POST", body={})


def cmd_devices_enable(args: argparse.Namespace) -> int:
    return _device_call(f"/v1/devices/{args.device_id}/enable", method="POST", body={})


def cmd_devices_revoke(args: argparse.Namespace) -> int:
    return _device_call(
        f"/v1/devices/{args.device_id}/revoke",
        method="POST",
        body={"reason": args.reason or ""},
    )


def cmd_devices_remove(args: argparse.Namespace) -> int:
    return _device_call(f"/v1/devices/{args.device_id}", method="DELETE")


def cmd_devices_rotate_credential(args: argparse.Namespace) -> int:
    body = {}
    if args.credential_id:
        body["credential_id"] = args.credential_id
    return _device_call(
        f"/v1/devices/{args.device_id}/credentials/rotate", method="POST", body=body
    )


def cmd_devices_revoke_credential(args: argparse.Namespace) -> int:
    body = {}
    if args.credential_id:
        body["credential_id"] = args.credential_id
    return _device_call(
        f"/v1/devices/{args.device_id}/credentials/revoke", method="POST", body=body
    )


def cmd_devices_recover_primary(args: argparse.Namespace) -> int:
    return _device_call(
        f"/v1/devices/{args.device_id}/recover-primary",
        method="POST",
        body={"confirm_phrase": args.confirm_phrase},
    )


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

    devices = sub.add_parser("devices", help="local device registry (loopback owner only)")
    devices_sub = devices.add_subparsers(dest="devices_command", required=True)

    dlist = devices_sub.add_parser("list", help="list registered devices")
    dlist.add_argument("--status")
    dlist.add_argument("--profile")
    dlist.add_argument("--limit", type=int)
    dlist.add_argument("--offset", type=int)
    dlist.set_defaults(func=cmd_devices_list)

    dshow = devices_sub.add_parser("show", help="show one device")
    dshow.add_argument("device_id")
    dshow.set_defaults(func=cmd_devices_show)

    dcreds = devices_sub.add_parser("credentials", help="list credential metadata")
    dcreds.add_argument("device_id")
    dcreds.set_defaults(func=cmd_devices_credentials)

    dboot = devices_sub.add_parser("bootstrap", help="register this Mac as the primary owner device")
    dboot.add_argument("--confirm", action="store_true")
    dboot.add_argument("--name")
    dboot.add_argument("--owner")
    dboot.set_defaults(func=cmd_devices_bootstrap)

    drename = devices_sub.add_parser("rename", help="rename a device")
    drename.add_argument("device_id")
    drename.add_argument("name")
    drename.set_defaults(func=cmd_devices_rename)

    dprofile = devices_sub.add_parser("profile", help="change a device permission profile")
    dprofile.add_argument("device_id")
    dprofile.add_argument("profile")
    dprofile.add_argument("--trust")
    dprofile.set_defaults(func=cmd_devices_profile)

    for name, func, help_text in (
        ("disable", cmd_devices_disable, "temporarily prevent authentication"),
        ("enable", cmd_devices_enable, "restore a disabled device"),
    ):
        p = devices_sub.add_parser(name, help=help_text)
        p.add_argument("device_id")
        p.set_defaults(func=func)

    drevoke = devices_sub.add_parser("revoke", help="permanently invalidate a device")
    drevoke.add_argument("device_id")
    drevoke.add_argument("--reason", default="")
    drevoke.set_defaults(func=cmd_devices_revoke)

    dremove = devices_sub.add_parser("remove", help="remove a disabled or revoked device")
    dremove.add_argument("device_id")
    dremove.set_defaults(func=cmd_devices_remove)

    drotate = devices_sub.add_parser("rotate-credential", help="rotate a device credential")
    drotate.add_argument("device_id")
    drotate.add_argument("--credential-id", dest="credential_id")
    drotate.set_defaults(func=cmd_devices_rotate_credential)

    drevcred = devices_sub.add_parser("revoke-credential", help="revoke a device credential")
    drevcred.add_argument("device_id")
    drevcred.add_argument("--credential-id", dest="credential_id")
    drevcred.set_defaults(func=cmd_devices_revoke_credential)

    drecover = devices_sub.add_parser(
        "recover-primary", help="release primary-owner protection after explicit confirmation"
    )
    drecover.add_argument("device_id")
    drecover.add_argument("--confirm-phrase", dest="confirm_phrase", required=True)
    drecover.set_defaults(func=cmd_devices_recover_primary)

    tasks = sub.add_parser("tasks", help="task registry via daemon API")
    tasks_sub = tasks.add_subparsers(dest="tasks_command", required=True)

    tlist = tasks_sub.add_parser("list", help="list tasks")
    tlist.add_argument("--state")
    tlist.add_argument("--kind")
    tlist.add_argument("--limit", type=int)
    tlist.add_argument("--offset", type=int)
    tlist.set_defaults(func=cmd_tasks_list)

    tshow = tasks_sub.add_parser("show", help="show one task")
    tshow.add_argument("task_id")
    tshow.set_defaults(func=cmd_tasks_show)

    tcreate = tasks_sub.add_parser("create", help="create task")
    tcreate.add_argument("--kind", required=True)
    tcreate.add_argument("--title", required=True)
    tcreate.add_argument("--description", default="")
    tcreate.add_argument("--priority", type=int, default=0)
    tcreate.add_argument("--idempotency-key", dest="idempotency_key")
    tcreate.add_argument("--payload-json", dest="payload_json", default="")
    tcreate.add_argument("--data-class", dest="data_class", default="internal")
    tcreate.add_argument("--requested-by", dest="requested_by")
    tcreate.set_defaults(func=cmd_tasks_create)

    tcancel = tasks_sub.add_parser("cancel", help="cancel task")
    tcancel.add_argument("task_id")
    tcancel.add_argument("--reason", default="")
    tcancel.set_defaults(func=cmd_tasks_cancel)

    tretry = tasks_sub.add_parser("retry", help="retry failed/blocked task")
    tretry.add_argument("task_id")
    tretry.set_defaults(func=cmd_tasks_retry)

    thist = tasks_sub.add_parser("history", help="task event history")
    thist.add_argument("task_id")
    thist.set_defaults(func=cmd_tasks_history)

    tatt = tasks_sub.add_parser("attempts", help="execution attempts")
    tatt.add_argument("task_id")
    tatt.set_defaults(func=cmd_tasks_attempts)

    tcps = tasks_sub.add_parser("checkpoints", help="execution checkpoints")
    tcps.add_argument("task_id")
    tcps.set_defaults(func=cmd_tasks_checkpoints)

    queue = sub.add_parser("queue", help="execution queue via daemon API")
    queue_sub = queue.add_subparsers(dest="queue_command", required=True)
    queue_sub.add_parser("status").set_defaults(func=cmd_queue_status)
    queue_sub.add_parser("list").set_defaults(func=cmd_queue_list)
    qrun = queue_sub.add_parser("run", help="execute one task")
    qrun.add_argument("--task-id", dest="task_id", required=True)
    qrun.set_defaults(func=cmd_queue_run)
    queue_sub.add_parser("pause").set_defaults(func=cmd_queue_pause)
    queue_sub.add_parser("resume").set_defaults(func=cmd_queue_resume)

    workers = sub.add_parser("workers", help="worker leases")
    workers_sub = workers.add_subparsers(dest="workers_command", required=True)
    workers_sub.add_parser("list").set_defaults(func=cmd_workers_list)

    la = sub.add_parser("launchagent", help="optional LaunchAgent plist (opt-in)")
    la_sub = la.add_subparsers(dest="launchagent_command", required=True)

    def cmd_launchagent_show(_args: argparse.Namespace) -> int:
        from .launchagent import plist_path, render_plist

        print(json.dumps({"ok": True, "plist": render_plist(), "path": str(plist_path())}))
        return EXIT_OK

    def cmd_launchagent_install(args: argparse.Namespace) -> int:
        if sys.platform != "darwin":
            print("cosd: launchagent is macOS only", file=sys.stderr)
            return EXIT_USAGE
        if not args.confirm:
            print("cosd: pass --confirm to install LaunchAgent", file=sys.stderr)
            return EXIT_USAGE
        from .launchagent import install_with_launchctl

        def load(p: str) -> None:
            subprocess.run(["launchctl", "load", "-w", p], check=True)

        path = install_with_launchctl(load, port=args.port)
        print(json.dumps({"ok": True, "installed": str(path), "enabled": False}))
        return EXIT_OK

    def cmd_launchagent_remove(args: argparse.Namespace) -> int:
        if sys.platform != "darwin":
            print("cosd: launchagent is macOS only", file=sys.stderr)
            return EXIT_USAGE
        if not args.confirm:
            print("cosd: pass --confirm to remove LaunchAgent", file=sys.stderr)
            return EXIT_USAGE
        from .launchagent import unload_with_launchctl

        def unload(p: str) -> None:
            subprocess.run(["launchctl", "unload", p], check=False)

        ok = unload_with_launchctl(unload)
        print(json.dumps({"ok": True, "removed": ok}))
        return EXIT_OK

    la_sub.add_parser("show").set_defaults(func=cmd_launchagent_show)
    lain = la_sub.add_parser("install", help="write plist and launchctl load (opt-in)")
    lain.add_argument("--confirm", action="store_true")
    lain.add_argument("--port", type=int, default=DEFAULT_PORT)
    lain.set_defaults(func=cmd_launchagent_install)
    larm = la_sub.add_parser("remove", help="unload and delete plist")
    larm.add_argument("--confirm", action="store_true")
    larm.set_defaults(func=cmd_launchagent_remove)

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
