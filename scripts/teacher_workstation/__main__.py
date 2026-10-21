#!/usr/bin/env python3
"""Teacher Workstation launcher — local UI.

Starts the local-only UI server on 127.0.0.1:4310. Does NOT open a browser by
default; ``--no-open`` is accepted for clarity (browser opening is not
implemented — Owen opens the printed URL himself).

Read-only use: pages and GET ``/api/*`` only read local planning state.

Guarded write workflow: planning edits and approvals write local ``.local``
state; the deploy route is the one path to Canvas writes (approved packet,
fresh preflight, typed owner confirmation). Write requests must be same-origin,
carry the per-start request token, be JSON, and be at most 1 MB. See
``scripts/teacher_workstation/server.py``.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.teacher_workstation import server  # noqa: E402
from scripts.canvas_planner.deep_links import BASE_URL, normalize_route  # noqa: E402


def _healthy() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE_URL}api/status", timeout=1) as response:
            return response.status == 200 and b'"overall"' in response.read()
    except OSError:
        return False


def open_route(route: str) -> int:
    normalized = normalize_route(route)
    if not _healthy():
        subprocess.Popen(
            [sys.executable, "-m", "scripts.teacher_workstation", "--no-open"],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(30):
            if _healthy():
                break
            time.sleep(0.2)
        else:
            print("Teacher Workstation did not become healthy on 127.0.0.1:4310", file=sys.stderr)
            return 1
    url = f"{BASE_URL}#{normalized}"
    if os.environ.get("TEACHER_WORKSTATION_NO_OPEN") != "1":
        webbrowser.open(url)
    print(url)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv:
        print('Usage: bin/teacher-workstation [--no-open] [--open "week/q2w3[/...]"]')
        print("")
        print("Starts the local Teacher Workstation UI at http://127.0.0.1:4310")
        print("Read-only browsing; writes (local planning state, approvals, and the")
        print("confirmed Canvas deploy route) need same-origin requests with the")
        print("per-start request token.")
        return 0
    if "--open" in argv:
        index = argv.index("--open")
        if index + 1 >= len(argv):
            print("--open requires a Canvas Planner route", file=sys.stderr)
            return 2
        try:
            return open_route(argv[index + 1])
        except ValueError as exc:
            print(f"Invalid Canvas Planner route: {exc}", file=sys.stderr)
            return 2
    return server.run()


if __name__ == "__main__":
    raise SystemExit(main())
