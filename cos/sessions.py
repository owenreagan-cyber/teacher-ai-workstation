"""Named conversation sessions for surfaces such as the desktop shell.

A session is a JSONL file at <state dir>/sessions/<id>.jsonl (directory 0700,
file 0600), one completed turn per line:

  {"ts", "question", "answer", "tools_used", "fast_path", "model", "notices", "total_ms"}

Session ids must fully match [a-z0-9-]{1,40}, so an id can never name a path
outside the sessions directory. Reading never creates anything; only a
completed turn is appended (a stopped or failed ask appends nothing).

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


def check_session_id(session_id) -> str:
    if not isinstance(session_id, str) or not SESSION_ID_RE.fullmatch(session_id):
        raise SessionIdError("session id must be 1-40 characters of a-z, 0-9, or '-'")
    return session_id


def session_path(state_dir: Path, session_id: str) -> Path:
    return Path(state_dir) / SUBDIR / f"{check_session_id(session_id)}.jsonl"


def read_turns(state_dir: Path, session_id: str) -> list[dict]:
    """All turns of a session, oldest first; [] if it does not exist. Never writes."""
    path = session_path(state_dir, session_id)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return []
    turns = []
    with os.fdopen(fd, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn or edited line is skipped, not fatal
            if isinstance(rec, dict):
                turns.append({k: rec.get(k) for k in TURN_FIELDS})
    return turns


def append_turn(state_dir: Path, session_id: str, turn: dict) -> None:
    path = session_path(state_dir, session_id)
    ensure_private_subdir(SUBDIR, Path(state_dir))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, FILE_MODE)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        os.fchmod(fh.fileno(), FILE_MODE)
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(json.dumps({k: turn.get(k) for k in TURN_FIELDS}, ensure_ascii=False) + "\n")
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
