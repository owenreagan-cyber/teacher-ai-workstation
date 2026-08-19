#!/usr/bin/env python3
"""Persistent Canvas credential loader — env-first, private file fallback, no token leakage.

Resolution order:
1. If CANVAS_BASE_URL and CANVAS_TOKEN are already in the environment, use them.
2. Otherwise load them from ~/.config/teacher-ai-workstation/canvas.env.

Safety guarantees:
- The private config file must be mode 0600 or loading is refused.
- CANVAS_TOKEN is never printed, logged, or included in any error message.
- The file is parsed as KEY=VALUE lines (with optional ``export `` prefix); it is
  never shell-evaluated, so a stray ``$(...)`` or backtick cannot run code.
"""
from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path
from typing import Any

PRIVATE_ENV_FILE = Path.home() / ".config" / "teacher-ai-workstation" / "canvas.env"
REQUIRED_MODE = 0o600
REQUIRED_KEYS = ("CANVAS_BASE_URL", "CANVAS_TOKEN")


class CredentialError(RuntimeError):
    """Raised when Canvas credentials cannot be resolved safely."""


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE env file without shell evaluation."""
    result: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            result[key] = _strip_quotes(value)
    return result


def _env_credentials(environ: dict[str, str]) -> dict[str, str]:
    return {
        "CANVAS_BASE_URL": (environ.get("CANVAS_BASE_URL") or "").strip(),
        "CANVAS_TOKEN": (environ.get("CANVAS_TOKEN") or "").strip(),
    }


def env_credentials_present(environ: dict[str, str] | None = None) -> bool:
    env = dict(os.environ if environ is None else environ)
    creds = _env_credentials(env)
    return bool(creds["CANVAS_BASE_URL"] and creds["CANVAS_TOKEN"])


def file_mode_is_secure(path: Path) -> bool:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return False
    return mode == REQUIRED_MODE


def resolve_credentials(
    *,
    env_file: Path | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve Canvas credentials. Env takes precedence over the private file."""
    env = dict(os.environ if environ is None else environ)
    creds = _env_credentials(env)
    if creds["CANVAS_BASE_URL"] and creds["CANVAS_TOKEN"]:
        return creds

    path = Path(env_file) if env_file is not None else PRIVATE_ENV_FILE
    if not path.exists():
        raise CredentialError(
            "missing Canvas credentials: CANVAS_BASE_URL/CANVAS_TOKEN are not set in the "
            f"environment and the private config was not found at {path}"
        )
    if not file_mode_is_secure(path):
        actual = stat.S_IMODE(path.stat().st_mode)
        raise CredentialError(
            f"refusing to load Canvas credentials: private config {path} has unsafe "
            f"permissions {oct(actual)} (expected {oct(REQUIRED_MODE)}). Fix with: chmod 600 {path}"
        )

    parsed = parse_env_file(path)
    creds = _env_credentials(parsed)
    if not creds["CANVAS_BASE_URL"] or not creds["CANVAS_TOKEN"]:
        raise CredentialError(
            f"private config {path} is missing required keys: {' and '.join(REQUIRED_KEYS)}"
        )
    return creds


def load_credentials(
    *,
    env_file: Path | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve credentials and export them into os.environ for downstream modules.

    Precedence (env > private file) is applied during resolution; the resolved
    non-empty values are then exported so env-reading modules see them.
    """
    creds = resolve_credentials(env_file=env_file, environ=environ)
    os.environ["CANVAS_BASE_URL"] = creds["CANVAS_BASE_URL"]
    os.environ["CANVAS_TOKEN"] = creds["CANVAS_TOKEN"]
    return creds


def redacted_status(creds: dict[str, str]) -> str:
    """Human-readable status line that never includes the token."""
    if creds.get("CANVAS_BASE_URL") and creds.get("CANVAS_TOKEN"):
        return "credentials: configured (token hidden)"
    return "credentials: missing"


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        env_file = tmp_path / "canvas.env"
        env_file.write_text(
            "CANVAS_BASE_URL=https://file.example.com\nCANVAS_TOKEN=file-secret-token\n"
        )
        env_file.chmod(REQUIRED_MODE)

        # 1. Env precedence.
        env_creds = resolve_credentials(
            env_file=env_file,
            environ={
                "CANVAS_BASE_URL": "https://env.example.com",
                "CANVAS_TOKEN": "env-secret-token",
            },
        )
        assert env_creds["CANVAS_TOKEN"] == "env-secret-token"
        assert env_creds["CANVAS_BASE_URL"] == "https://env.example.com"
        assert env_credentials_present({"CANVAS_BASE_URL": "x", "CANVAS_TOKEN": "y"}) is True

        # 2. Private config loads when env is absent.
        file_creds = resolve_credentials(env_file=env_file, environ={})
        assert file_creds["CANVAS_TOKEN"] == "file-secret-token"
        assert file_creds["CANVAS_BASE_URL"] == "https://file.example.com"
        assert file_mode_is_secure(env_file) is True

        # 3. Missing credentials block.
        missing = tmp_path / "missing.env"
        missing.write_text("CANVAS_BASE_URL=https://missing.example.com\n")
        missing.chmod(REQUIRED_MODE)
        try:
            resolve_credentials(env_file=missing, environ={})
            raise AssertionError("missing credentials should block")
        except CredentialError:
            pass

        # 4. Bad file permissions block.
        bad = tmp_path / "bad.env"
        bad.write_text("CANVAS_BASE_URL=https://bad.example.com\nCANVAS_TOKEN=bad-token\n")
        bad.chmod(0o644)
        assert file_mode_is_secure(bad) is False
        try:
            resolve_credentials(env_file=bad, environ={})
            raise AssertionError("unsafe permissions should block")
        except CredentialError:
            pass

        # Token never leaks into status or error output.
        assert "file-secret-token" not in redacted_status(file_creds)
        try:
            resolve_credentials(env_file=bad, environ={})
        except CredentialError as exc:
            assert "bad-token" not in str(exc)

    print("PASS canvas credentials self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canvas credential loader")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test").set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
