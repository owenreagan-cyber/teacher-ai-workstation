from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cos.config import ensure_private_dir, open_private, state_dir

from .constants import META_FILENAME, TOKEN_FILENAME


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class TokenRecord:
    token: str
    version: int
    issued_at: str


def cosd_state_dir(base: Path | None = None) -> Path:
    root = base or state_dir()
    return root / "cosd"


def ensure_cosd_state_dir(base: Path | None = None) -> Path:
    """Secure the state root and the cosd subdirectory, then return the latter.

    Both levels are private by definition: the root holds the audit log and
    configuration, and `cosd/` holds the token, auth metadata, pid file and
    SQLite database. Only these two directories are touched; contents keep their
    own modes and are never changed recursively.
    """
    root = base or state_dir()
    ensure_private_dir(root)
    return ensure_private_dir(root / "cosd")


def _meta_path(base: Path | None = None) -> Path:
    return cosd_state_dir(base) / META_FILENAME


def _token_path(base: Path | None = None) -> Path:
    return cosd_state_dir(base) / TOKEN_FILENAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_token(base: Path | None = None) -> TokenRecord:
    """Load or create the API token (0600 file, never logged)."""
    ensure_cosd_state_dir(base)
    tpath = _token_path(base)
    mpath = _meta_path(base)
    if tpath.is_file() and mpath.is_file():
        token = tpath.read_text(encoding="utf-8").strip()
        meta = json.loads(mpath.read_text(encoding="utf-8"))
        return TokenRecord(token=token, version=int(meta["version"]), issued_at=str(meta["issued_at"]))
    return rotate_token(base)


def rotate_token(base: Path | None = None) -> TokenRecord:
    d = ensure_cosd_state_dir(base)
    prev_version = 0
    mpath = _meta_path(base)
    if mpath.is_file():
        try:
            prev_version = int(json.loads(mpath.read_text(encoding="utf-8")).get("version", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            prev_version = 0
    version = prev_version + 1
    issued_at = _now()
    token = secrets.token_hex(32)
    with open_private(_token_path(base), "w") as fh:
        fh.write(token + "\n")
    with open_private(mpath, "w") as fh:
        json.dump({"version": version, "issued_at": issued_at}, fh, sort_keys=True)
        fh.write("\n")
    return TokenRecord(token=token, version=version, issued_at=issued_at)


def revoke_token(base: Path | None = None) -> None:
    """Invalidate current token by rotating to a new secret."""
    rotate_token(base)


def authorize(header_value: str | None, base: Path | None = None) -> bool:
    if not header_value or not header_value.startswith("Bearer "):
        return False
    supplied = header_value[7:].strip()
    if not supplied:
        return False
    try:
        record = ensure_token(base)
    except (OSError, AuthError, json.JSONDecodeError):
        return False
    return secrets.compare_digest(supplied, record.token)
