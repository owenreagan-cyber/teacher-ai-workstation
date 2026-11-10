"""Runtime provenance: which code is actually running, and whether it is stale.

The snapshot is taken once, when the module is imported by the daemon process.
It deliberately never re-reads the checkout, so a `git pull` cannot make an old
process claim it is current. `checkout_drift()` compares that frozen snapshot
with the checkout on disk *for reporting only*.

Provenance is best-effort. A missing checkout must never stop the daemon, and
when a commit cannot be established the value is `None` rather than a guess.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_GIT_TIMEOUT_S = 2.0


def _git(*args: str) -> str | None:
    """Run a git query against the checkout, or return None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = (result.stdout or "").strip()
    return value or None


def checkout_commit() -> str | None:
    return _git("rev-parse", "--short=12", "HEAD")


def checkout_branch() -> str | None:
    return _git("rev-parse", "--abbrev-ref", "HEAD")


def checkout_dirty() -> bool | None:
    """True when tracked files differ from HEAD. Untracked files are ignored."""
    out = _git("status", "--porcelain", "--untracked-files=no")
    if out is None:
        return None
    return bool(out.strip())


def _python_version() -> str:
    return ".".join(str(part) for part in sys.version_info[:3])


def _environment() -> str:
    return "venv" if sys.prefix != getattr(sys, "base_prefix", sys.prefix) else "system"


@dataclass(frozen=True)
class Provenance:
    """What the running process actually loaded. Never includes filesystem paths."""

    version: str
    python: str
    environment: str
    loaded_commit: str | None
    loaded_branch: str | None
    loaded_dirty: bool | None
    source_available: bool
    started_at: str

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def snapshot(version: str) -> Provenance:
    commit = checkout_commit()
    branch = checkout_branch()
    dirty = checkout_dirty() if commit else None
    return Provenance(
        version=version,
        python=_python_version(),
        environment=_environment(),
        loaded_commit=commit,
        loaded_branch=branch,
        loaded_dirty=dirty,
        source_available=commit is not None,
        started_at=datetime.now(timezone.utc).isoformat(),
    )


def drift(snapshot_value: Provenance) -> dict[str, Any]:
    """Compare the frozen snapshot with the checkout as it is now.

    Returns `restart_required` only when the difference can actually be
    established. If either side is unknown, it reports None and never guesses.
    """
    current = checkout_commit()
    if snapshot_value.loaded_commit is None or current is None:
        return {
            "current_commit": current,
            "restart_required": None,
            "reason": "provenance unavailable (no source checkout)",
        }
    restart = current != snapshot_value.loaded_commit
    reason = "checkout moved since this process started" if restart else ""
    if not restart:
        current_dirty = checkout_dirty()
        if current_dirty and not snapshot_value.loaded_dirty:
            restart = True
            reason = "working tree changed since this process started"
    return {
        "current_commit": current,
        "restart_required": restart,
        "reason": reason,
    }
