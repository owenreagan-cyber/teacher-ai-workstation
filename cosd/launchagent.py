"""Optional macOS LaunchAgent helpers (opt-in only)."""
from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

LABEL = "com.owenreagan.chief-of-staff.cosd"
AGENT_DIR = Path.home() / "Library" / "LaunchAgents"
AGENT_DIR_ENV = "COSD_AGENT_DIR"
PLIST_NAME = f"{LABEL}.plist"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def agent_dir() -> Path:
    """Where the plist lives.

    ``COSD_AGENT_DIR`` exists so a test (or a dry run) can point the helper at a temporary folder:
    without it, importing and exercising this module would write into the user's real
    ``~/Library/LaunchAgents``. Unset, the real location is used, exactly as before.
    """
    override = os.environ.get(AGENT_DIR_ENV)
    return Path(override).expanduser() if override else AGENT_DIR


def plist_path() -> Path:
    return agent_dir() / PLIST_NAME


def render_plist(*, python: str | None = None, port: int = 8765) -> dict:
    py = python or sys.executable
    root = str(repo_root())
    return {
        "Label": LABEL,
        "ProgramArguments": [
            py,
            "-s",
            "-E",
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); from cosd.cli import main; "
            "raise SystemExit(main(['serve', '--host', '127.0.0.1', '--port', sys.argv[2]]))",
            root,
            str(port),
        ],
        "RunAtLoad": False,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 30,
        "StandardOutPath": str(Path.home() / "Library" / "Application Support" / "ChiefOfStaff" / "cosd" / "launchagent.stdout.log"),
        "StandardErrorPath": str(Path.home() / "Library" / "Application Support" / "ChiefOfStaff" / "cosd" / "launchagent.stderr.log"),
    }


def write_plist(*, python: str | None = None, port: int = 8765) -> Path:
    agent_dir().mkdir(parents=True, exist_ok=True)
    path = plist_path()
    data = render_plist(python=python, port=port)
    path.write_bytes(plistlib.dumps(data))
    path.chmod(0o600)
    return path


def remove_plist() -> bool:
    path = plist_path()
    if path.is_file():
        path.unlink()
        return True
    return False


def install_with_launchctl(load_fn, *, python: str | None = None, port: int = 8765) -> Path:
    path = write_plist(python=python, port=port)
    load_fn(str(path))
    return path


def unload_with_launchctl(unload_fn) -> bool:
    path = plist_path()
    if not path.is_file():
        return False
    unload_fn(str(path))
    return remove_plist()
