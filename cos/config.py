"""Configuration and the Chief of Staff state directory.

State lives in ~/Library/Application Support/ChiefOfStaff/ (0700). It holds
chat history, the audit log, the kill-switch flag, caches, and config.json.
COS_STATE_DIR overrides the location; tests always use a temp directory.

COS_FIXTURE_DIR turns on fixture mode (synthetic tool data for the evals/
harness; see cos/fixture.py). It is honored only when COS_STATE_DIR is also
set and does not resolve to the real state directory; otherwise every command
refuses to start. The check runs before the state directory is created.

Weather places ("places"): {"<key>": {"name", "latitude", "longitude"}}. A
written places.home is used as written. Otherwise legacy top-level latitude and
longitude become places.home named "Home" (Chief never invents a city name).
When "places" is not written at all, the defaults fill in what is missing:
home Sims, NC and work Clayton, NC. Unknown keys are refused, inside a place too.

auto_search (default true): a question that needs the web is searched without
Owen typing "search". `cos auto-search on|off` (and the desktop tray toggle)
changes it with write_config_value, which keeps every other key as written.

model and fallback_model must be local: a name ending in ":cloud" or containing
"-cloud" (an Ollama cloud model) is refused (CloudModelError). ModelClient also
asks /api/show before every call and refuses a model that reports a remote host.
"""
from __future__ import annotations

import json
import os
import re
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
    "model_think": False,
    "model_num_ctx": 16384,
    "model_keep_alive": "2h",
    "latitude": None,
    "longitude": None,
    "places": None,
    "search_daily_limit": 30,
    "search_monthly_limit": 600,
    "auto_search": True,
}


DEFAULT_PLACES = {
    "home": {"name": "Sims, NC", "latitude": 35.76, "longitude": -78.06},
    "work": {"name": "Clayton, NC", "latitude": 35.65, "longitude": -78.46},
}
LEGACY_HOME_NAME = "Home"
PLACE_KEY_RE = re.compile(r"[a-z][a-z0-9_]{0,19}")
PLACE_FIELDS = ("name", "latitude", "longitude")
MAX_PLACES = 10
MAX_PLACE_NAME = 60
MAX_MODEL_NAME = 100

# Ollama keep_alive: "0" (unload right after the request) or a duration such as "30m", "2h", "1h30m".
KEEP_ALIVE_RE = re.compile(r"0|(?:\d+(?:\.\d+)?(?:ms|s|m|h))+")


class ConfigError(Exception):
    pass


class CloudModelError(ConfigError):
    """model or fallback_model names an Ollama cloud model. cos uses local models only;
    the CLI refuses with error_kind "internal" and audits the refusal."""

    def __init__(self, field_name: str, model: str, state_dir: Path, fixture: bool):
        super().__init__(f"{field_name} {model!r} is an Ollama cloud model; cos uses local models only")
        self.field_name, self.model, self.state_dir, self.fixture = field_name, model, state_dir, fixture


def is_cloud_model_name(name) -> bool:
    """Ollama cloud models are named <model>:cloud or <model>:<size>-cloud."""
    n = str(name or "").strip().lower()
    return n.endswith(":cloud") or "-cloud" in n


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


@dataclass(frozen=True)
class Place:
    key: str
    name: str
    latitude: float
    longitude: float

    @property
    def short_name(self) -> str:
        """ "Sims" for "Sims, NC"."""
        return self.name.split(",", 1)[0].strip() or self.name


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
    fixture_dir: Path | None = None
    model_think: bool = False
    model_num_ctx: int = 16384
    model_keep_alive: str = "2h"
    search_daily_limit: int = 30
    search_monthly_limit: int = 600
    places: dict[str, Place] = field(default_factory=dict)
    auto_search: bool = True

    @property
    def audit_path(self) -> Path:
        return self.state_dir / "audit.jsonl"


def weather_places(cfg: Config) -> dict[str, Place]:
    """The places weather can report on, home first. A Config built without places (tests,
    older callers) falls back to its latitude/longitude as home."""
    if cfg.places:
        return cfg.places
    if cfg.latitude is not None and cfg.longitude is not None:
        return {"home": Place("home", LEGACY_HOME_NAME, cfg.latitude, cfg.longitude)}
    return {}


def _place(key, value) -> Place:
    if not isinstance(key, str) or not PLACE_KEY_RE.fullmatch(key):
        raise ConfigError(f"places: key {key!r} must be lowercase letters, digits, or _ (at most 20)")
    if not isinstance(value, dict):
        raise ConfigError(f"places.{key} must be an object with name, latitude, longitude")
    unknown = set(value) - set(PLACE_FIELDS)
    if unknown:
        raise ConfigError(f"unknown config keys in places.{key}: {sorted(unknown)}")
    missing = [f for f in PLACE_FIELDS if f not in value]
    if missing:
        raise ConfigError(f"places.{key} is missing {missing}")
    name = value["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > MAX_PLACE_NAME:
        raise ConfigError(f"places.{key}.name must be text of 1-{MAX_PLACE_NAME} characters")
    lat = _coord(value["latitude"], -90, 90, f"places.{key}.latitude")
    lon = _coord(value["longitude"], -180, 180, f"places.{key}.longitude")
    if lat is None or lon is None:
        raise ConfigError(f"places.{key} needs a latitude and a longitude")
    return Place(key, name.strip(), lat, lon)


def resolve_places(user_places, latitude: float | None, longitude: float | None) -> dict[str, Place]:
    """Named places, home first (see the module docstring for the rules)."""
    if user_places is not None and not isinstance(user_places, dict):
        raise ConfigError("places must be an object of named places")
    if user_places is not None and len(user_places) > MAX_PLACES:
        raise ConfigError(f"places: at most {MAX_PLACES} places")
    places = {k: _place(k, v) for k, v in (user_places or {}).items()}
    if "home" not in places:
        if latitude is not None and longitude is not None:
            places["home"] = Place("home", LEGACY_HOME_NAME, latitude, longitude)
        elif user_places is None:
            places["home"] = _place("home", DEFAULT_PLACES["home"])
    if user_places is None:
        for key, value in DEFAULT_PLACES.items():
            places.setdefault(key, _place(key, value))
    return dict(sorted(places.items(), key=lambda kv: (kv[0] != "home", kv[0] != "work", kv[0])))


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


def _is_real_state_dir(path: Path) -> bool:
    """True if path is, or is inside, the real state directory (symlinks resolved;
    compared case-insensitively, as APFS is by default)."""
    real = DEFAULT_STATE_DIR.expanduser().resolve()
    candidate = path.expanduser().resolve()
    folded = str(real).casefold()
    if str(candidate).casefold() == folded:
        return True
    if any(str(parent).casefold() == folded for parent in candidate.parents):
        return True
    try:
        return candidate.exists() and real.exists() and os.path.samefile(candidate, real)
    except OSError:
        return True  # cannot tell -> treat as the real directory


def fixture_dir_from_env(root: Path | None = None) -> Path | None:
    """The fixture directory if fixture mode is requested and allowed, else None.

    Raises ConfigError (refuse to start) if COS_FIXTURE_DIR is set but COS_STATE_DIR
    is not, the state directory is the real one, or the fixture directory is missing."""
    raw = os.environ.get("COS_FIXTURE_DIR")
    if raw is None:
        return None
    if not raw.strip():
        raise ConfigError("fixture mode refused: COS_FIXTURE_DIR is set but empty")
    if root is None and not (os.environ.get("COS_STATE_DIR") or "").strip():
        raise ConfigError("fixture mode refused: COS_FIXTURE_DIR requires COS_STATE_DIR "
                          "set to a temporary state directory")
    if _is_real_state_dir(Path(root) if root is not None else state_dir()):
        raise ConfigError("fixture mode refused: COS_STATE_DIR resolves to the real Chief of "
                          f"Staff state directory ({DEFAULT_STATE_DIR})")
    fixtures = Path(raw).expanduser().resolve()
    if not fixtures.is_dir():
        raise ConfigError(f"fixture mode refused: fixture directory not found: {fixtures}")
    return fixtures


def read_config_file(root: Path) -> dict:
    """config.json as written ({} when there is none). Refuses unknown keys."""
    cfg_file = root / "config.json"
    if not cfg_file.exists():
        return {}
    try:
        user = json.loads(cfg_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"config.json unreadable: {e}")
    if not isinstance(user, dict):
        raise ConfigError("config.json must be a JSON object")
    unknown = set(user) - set(DEFAULTS)
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    return user


def load_config(root: Path | None = None) -> Config:
    fixtures = fixture_dir_from_env(root)  # before anything is created
    root = ensure_state_dir(root)
    return config_from(read_config_file(root), root, fixtures)


def config_from(user: dict, root: Path, fixtures: Path | None = None) -> Config:
    """Validate config.json's keys (as written) over the defaults and build the Config."""
    data = dict(DEFAULTS)
    data.update(user)
    for name in ("model", "fallback_model"):
        if data[name] and is_cloud_model_name(data[name]):
            raise CloudModelError(name, str(data[name]), root, fixtures is not None)
    if not isinstance(data["model"], str) or not data["model"].strip() or len(data["model"]) > MAX_MODEL_NAME:
        raise ConfigError(f"model must be a model name of 1-{MAX_MODEL_NAME} characters")
    if not isinstance(data["model_think"], bool):
        raise ConfigError("model_think must be true or false")
    num_ctx = data["model_num_ctx"]
    if not isinstance(num_ctx, int) or isinstance(num_ctx, bool) or num_ctx <= 0:
        raise ConfigError("model_num_ctx must be a positive integer")
    keep_alive = data["model_keep_alive"]
    if not isinstance(keep_alive, str) or not KEEP_ALIVE_RE.fullmatch(keep_alive):
        raise ConfigError('model_keep_alive must be an Ollama duration such as "30m", "2h", or "0"')
    if not isinstance(data["auto_search"], bool):
        raise ConfigError("auto_search must be true or false")
    for name in ("search_daily_limit", "search_monthly_limit"):
        v = data[name]
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ConfigError(f"{name} must be a whole number of searches (0 turns search off)")
    latitude = _coord(data["latitude"], -90, 90, "latitude")
    longitude = _coord(data["longitude"], -180, 180, "longitude")
    return Config(
        model=str(data["model"]),
        fallback_model=str(data["fallback_model"]) if data["fallback_model"] else None,
        ollama_url=str(data["ollama_url"]),
        model_timeout_s=float(data["model_timeout_s"]),
        latitude=latitude,
        longitude=longitude,
        state_dir=root,
        fixture_dir=fixtures,
        model_think=data["model_think"],
        model_num_ctx=num_ctx,
        model_keep_alive=keep_alive,
        search_daily_limit=data["search_daily_limit"],
        search_monthly_limit=data["search_monthly_limit"],
        places=resolve_places(data["places"], latitude, longitude),
        auto_search=data["auto_search"],
    )


def write_config_value(key: str, value, root: Path | None = None) -> Path:
    """Set one known key in config.json, keeping every other key as written. The result is
    validated exactly as load_config would read it, then the file is replaced atomically
    (0600). Refuses (ConfigError) if config.json is unreadable or the result would not load."""
    if key not in DEFAULTS:
        raise ConfigError(f"unknown config key {key!r}")
    root = ensure_state_dir(root)
    path = root / "config.json"
    data = read_config_file(root)
    data[key] = value
    config_from(data, root)  # raises before anything is written
    tmp = root / f".config.json.{os.getpid()}.tmp"
    with open_private(tmp, "w") as fh:
        fh.write(json.dumps(data, indent=2) + "\n")
    try:
        os.chmod(tmp, FILE_MODE)
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise
    return path


# What `cos config set` (and so the Settings screen) may change. Everything else stays a hand edit.
SETTABLE = ("places", "auto_search", "model", "model_keep_alive")


def config_values(cfg: Config) -> dict:
    """The effective settings the Settings screen shows (defaults filled in)."""
    return {
        "places": {k: {"name": p.name, "latitude": p.latitude, "longitude": p.longitude}
                   for k, p in weather_places(cfg).items()},
        "auto_search": cfg.auto_search,
        "model": cfg.model,
        "fallback_model": cfg.fallback_model,
        "model_keep_alive": cfg.model_keep_alive,
        "search_daily_limit": cfg.search_daily_limit,
        "search_monthly_limit": cfg.search_monthly_limit,
    }
