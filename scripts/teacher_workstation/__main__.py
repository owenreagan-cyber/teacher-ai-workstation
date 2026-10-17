#!/usr/bin/env python3
"""Teacher Workstation launcher — local read-only UI.

Starts the local-only UI server on 127.0.0.1:4310. Does NOT open a browser by
default; ``--no-open`` is accepted for clarity (browser opening is not
implemented — Owen opens the printed URL himself).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.teacher_workstation import server  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # --no-open / --help are accepted; browser opening is deliberately not implemented.
    if "--help" in argv:
        print("Usage: bin/teacher-workstation [--no-open]")
        print("")
        print("Starts the local read-only Teacher Workstation UI at http://127.0.0.1:4310")
        print("Mode: READ ONLY — no Canvas writes.")
        return 0
    return server.run()


if __name__ == "__main__":
    raise SystemExit(main())
