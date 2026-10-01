"""Configuration and the Chief of Staff state directory.

State lives in ~/Library/Application Support/ChiefOfStaff/ (0700). It holds
chat history, the audit log, the kill-switch flag, caches, and config.json.
COS_STATE_DIR overrides the location; tests always use a temp directory.
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = Path.home() / "Library" / "Application Support" / "ChiefOfStaff"
STATE_DIR_MODE = 0o700
FILE_MODE = 0o600

DEFAULTS = {
    "model": "qwen3.6:35b",
    "fallback_model": "gpt-oss:20b",
    "ollama_url": "http://127.0.0.1:11434",
    "model_timeout_s": 300,
    "latitude": None,
    "longitude": None,
}


class ConfigError(Exception):
    pass


def state_dir() -> Path:
    override = os.environ.get("COS_STATE_DIR")
    return Path(override).expanduser() if override else DEFAULT_STATE_DIR


def ensure_state_dir(path: Path | None = None) -> Path:
    """Create the state directory with 0700 and tighten it if it is wider."""
    path = path or state_dir()
    path.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)
    if stat.S_IMODE(path.stat().st_mode) != STATE_DIR_MODE:
        os.chmod(path, STATE_DIR_MODE)
    return path


def ensure_private_subdir(name: str, root: Path | None = None) -> Path:
    sub = ensure_state_dir(root) / name
    sub.mkdir(exist_ok=True, mode=STATE_DIR_MODE)
    if stat.S_IMODE(sub.stat().st_mode) != STATE_DIR_MODE:
        os.chmod(sub, STATE_DIR_MODE)
    return sub


def open_private(path: Path, mode: str = "a"):
    """Open a file inside the state directory, created 0600."""
    flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if "a" in mode else os.O_TRUNC)
    fd = os.open(path, flags, FILE_MODE)
    return os.fdopen(fd, mode, encoding="utf-8")


@dataclass
class Config:
    model: str
    fallback_model: str | None
    ollama_url: str
    model_timeout_s: float
    latitude: float | None
    longitude: float | None
    state_dir: Path
    repo_root: Path = field(default=REPO_ROOT)

    @property
    def audit_path(self) -> Path:
        return self.state_dir / "audit.jsonl"


def _coord(value, lo, hi, name):
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{name} must be a number")
    if not lo <= v <= hi:
        raise ConfigError(f"{name} out of range")
    return v


def load_config(root: Path | None = None) -> Config:
    root = ensure_state_dir(root)
    data = dict(DEFAULTS)
    cfg_file = root / "config.json"
    if cfg_file.exists():
        try:
            user = json.loads(cfg_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise ConfigError(f"config.json unreadable: {e}")
        if not isinstance(user, dict):
            raise ConfigError("config.json must be a JSON object")
        unknown = set(user) - set(DEFAULTS)
        if unknown:
            raise ConfigError(f"unknown config keys: {sorted(unknown)}")
        data.update(user)
    return Config(
        model=str(data["model"]),
        fallback_model=str(data["fallback_model"]) if data["fallback_model"] else None,
        ollama_url=str(data["ollama_url"]),
        model_timeout_s=float(data["model_timeout_s"]),
        latitude=_coord(data["latitude"], -90, 90, "latitude"),
        longitude=_coord(data["longitude"], -180, 180, "longitude"),
        state_dir=root,
    )
