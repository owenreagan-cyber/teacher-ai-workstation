"""Named conversation sessions for surfaces such as the desktop shell.

A session is a JSONL file at <state dir>/sessions/<id>.jsonl (directory 0700,
file 0600), one completed turn per line:

  {"ts", "question", "answer", "tools_used", "fast_path", "model", "notices", "total_ms"}

Session ids must fully match [a-z0-9-]{1,40}, so an id can never name a path
outside the sessions directory. Reading never creates anything; only a
completed turn is appended (a stopped or failed ask appends nothing). If the
last line is torn (no trailing newline), a newline is written first so the torn
line stays a separate, skipped line and the new turn survives.

Every turn is shape-checked (check_turn) before it is written, and every line
is checked again on read: a line that is not JSON or not a valid turn is
skipped and counted, never passed on.

Prior turns are offered to the model as history, capped at MAX_TURNS turns and
MAX_HISTORY_CHARS characters (oldest turns dropped first).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
from pathlib import Path

from cos.config import FILE_MODE, ensure_private_subdir

SESSION_ID_RE = re.compile(r"[a-z0-9-]{1,40}")
SUBDIR = "sessions"
MAX_TURNS = 10
MAX_HISTORY_CHARS = 12_000
TURN_FIELDS = ("ts", "question", "answer", "tools_used", "fast_path", "model", "notices", "total_ms")


class SessionIdError(ValueError):
    pass


class TurnError(ValueError):
    pass


def _is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def check_turn(turn) -> dict:
    """Return the turn with exactly TURN_FIELDS, or raise TurnError if any field has the wrong type."""
    if not isinstance(turn, dict):
        raise TurnError("turn is not an object")
    checks = {
        "ts": lambda v: isinstance(v, str),
        "question": lambda v: isinstance(v, str),
        "answer": lambda v: isinstance(v, str),
        "tools_used": _is_str_list,
        "fast_path": lambda v: isinstance(v, bool),
        "model": lambda v: v is None or isinstance(v, str),
        "notices": _is_str_list,
        # bool is a subclass of int; a duration is never a bool
        "total_ms": lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0,
    }
    for name, ok in checks.items():
        if name not in turn:
            raise TurnError(f"turn is missing {name}")
        if not ok(turn[name]):
            raise TurnError(f"turn field {name} has the wrong type")
    return {k: turn[k] for k in TURN_FIELDS}


def check_session_id(session_id) -> str:
    if not isinstance(session_id, str) or not SESSION_ID_RE.fullmatch(session_id):
        raise SessionIdError("session id must be 1-40 characters of a-z, 0-9, or '-'")
    return session_id


def session_path(state_dir: Path, session_id: str) -> Path:
    return Path(state_dir) / SUBDIR / f"{check_session_id(session_id)}.jsonl"


def read_session(state_dir: Path, session_id: str) -> tuple[list[dict], int]:
    """(valid turns oldest first, number of skipped lines). ([], 0) if missing. Never writes."""
    path = session_path(state_dir, session_id)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return [], 0
    turns, skipped = [], 0
    with os.fdopen(fd, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                turns.append(check_turn(json.loads(line)))
            except (json.JSONDecodeError, TurnError):
                skipped += 1  # a torn, edited, or wrongly typed line is skipped, not fatal
    return turns, skipped


def read_turns(state_dir: Path, session_id: str) -> list[dict]:
    """Valid turns of a session, oldest first; [] if it does not exist. Never writes."""
    return read_session(state_dir, session_id)[0]


def append_turn(state_dir: Path, session_id: str, turn: dict) -> None:
    """Append one turn; raises TurnError (and writes nothing) if its shape is wrong."""
    record = check_turn(turn)
    path = session_path(state_dir, session_id)
    ensure_private_subdir(SUBDIR, Path(state_dir))
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, FILE_MODE)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        os.fchmod(fh.fileno(), FILE_MODE)
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            size = os.fstat(fd).st_size
            # A torn last line (no newline) stays its own, skipped line; the new turn starts fresh.
            lead = "\n" if size and os.pread(fd, 1, size - 1) != b"\n" else ""
            fh.write(lead + json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def history_messages(turns: list[dict], max_turns: int = MAX_TURNS,
                     max_chars: int = MAX_HISTORY_CHARS) -> list[dict]:
    """Chat messages for the most recent turns that fit both caps."""
    kept: list[dict] = []
    used = 0
    for turn in reversed(turns[-max_turns:] if max_turns > 0 else []):
        q, a = str(turn.get("question") or ""), str(turn.get("answer") or "")
        if used + len(q) + len(a) > max_chars:
            break
        used += len(q) + len(a)
        kept.append(turn)
    messages = []
    for turn in reversed(kept):
        messages.append({"role": "user", "content": str(turn.get("question") or "")})
        messages.append({"role": "assistant", "content": str(turn.get("answer") or "")})
    return messages
