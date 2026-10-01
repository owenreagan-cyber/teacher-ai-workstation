"""Append-only, hash-chained JSONL audit log.

Each record carries seq, ts, kind, its fields, prev (the previous record's
hash) and hash = sha256 of the canonical JSON of everything else. The first
record's prev is 64 zeros. verify() recomputes the whole chain.

Request text is not stored, only its sha256 and length; chat history holds
the text. Appends hold an exclusive flock so concurrent cos processes chain
correctly.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cos.config import FILE_MODE

GENESIS = "0" * 64


def _canonical(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      default=str).encode("utf-8")


def record_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(_canonical(body)).hexdigest()


def text_digest(text: str) -> dict:
    return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "chars": len(text)}


def _last_record(fh) -> dict | None:
    fh.seek(0, os.SEEK_END)
    end = fh.tell()
    if end == 0:
        return None
    pos, chunk, buf = end, 4096, b""
    while pos > 0:
        step = min(chunk, pos)
        pos -= step
        fh.seek(pos)
        buf = fh.read(step) + buf
        lines = buf.rstrip(b"\n").split(b"\n")
        if len(lines) > 1 or pos == 0:
            return json.loads(lines[-1])
    return None


class AuditLog:
    def __init__(self, path: Path, clock=None):
        self.path = Path(path)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def append(self, kind: str, **fields) -> dict:
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND, FILE_MODE)
        with os.fdopen(fd, "r+b") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                last = _last_record(fh)
                record = {
                    "seq": (last["seq"] + 1) if last else 0,
                    "ts": self._clock().isoformat(timespec="milliseconds"),
                    "kind": kind,
                    **fields,
                    "prev": last["hash"] if last else GENESIS,
                }
                record["hash"] = record_hash(record)
                fh.seek(0, os.SEEK_END)
                fh.write(_canonical(record) + b"\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        return record

    def __call__(self, kind: str, **fields) -> dict:
        return self.append(kind, **fields)


def verify(path: Path) -> tuple[bool, int, str]:
    """Return (ok, records_checked, message)."""
    path = Path(path)
    if not path.exists():
        return True, 0, "no audit log yet"
    prev, n = GENESIS, 0
    with open(path, "rb") as fh:
        for lineno, raw in enumerate(fh, 1):
            if not raw.strip():
                return False, n, f"line {lineno}: blank line"
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                return False, n, f"line {lineno}: not valid JSON"
            if not isinstance(rec, dict):
                return False, n, f"line {lineno}: not a JSON object"
            if rec.get("seq") != n:
                return False, n, f"line {lineno}: seq {rec.get('seq')} != expected {n}"
            if rec.get("prev") != prev:
                return False, n, f"line {lineno}: prev hash does not match previous record"
            if rec.get("hash") != record_hash(rec):
                return False, n, f"line {lineno}: record hash mismatch (edited record)"
            prev, n = rec["hash"], n + 1
    return True, n, f"chain intact ({n} records)"
