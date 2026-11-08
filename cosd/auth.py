from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cos.config import open_private, state_dir

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


def _meta_path(base: Path | None = None) -> Path:
    return cosd_state_dir(base) / META_FILENAME


def _token_path(base: Path | None = None) -> Path:
    return cosd_state_dir(base) / TOKEN_FILENAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_token(base: Path | None = None) -> TokenRecord:
    """Load or create the API token (0600 file, never logged)."""
    d = cosd_state_dir(base)
    d.mkdir(parents=True, exist_ok=True)
    tpath = _token_path(base)
    mpath = _meta_path(base)
    if tpath.is_file() and mpath.is_file():
        token = tpath.read_text(encoding="utf-8").strip()
        meta = json.loads(mpath.read_text(encoding="utf-8"))
        return TokenRecord(token=token, version=int(meta["version"]), issued_at=str(meta["issued_at"]))
    return rotate_token(base)


def rotate_token(base: Path | None = None) -> TokenRecord:
    d = cosd_state_dir(base)
    d.mkdir(parents=True, exist_ok=True)
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
