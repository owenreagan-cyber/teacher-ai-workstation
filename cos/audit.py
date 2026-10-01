"""Append-only, hash-chained JSONL audit log.

Each record carries seq, ts, kind, its fields, prev (the previous record's
hash) and hash = sha256 of the canonical JSON of everything else. The first
record's prev is 64 zeros. verify() recomputes the whole chain.

Request text is not stored, only its sha256 and length; chat history holds
the text. Appends hold an exclusive flock so concurrent cos processes chain
correctly.

After the first record is written, a marker file (audit.initialized) is
created next to the log, holding the first record's hash. verify() reports
three states: "ok" (valid chain), "uninitialized" (no log and no marker:
nothing has run yet), and "fail" (tampered chain, the marker exists but the
log is missing or empty, or the log's first record is not the one the marker
recorded, e.g. a replaced log). A marker without first_hash (older runs) is
treated as presence-only, and the result message says so.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cos.config import FILE_MODE

GENESIS = "0" * 64
MARKER_SUFFIX = ".initialized"


def marker_path(log_path: Path) -> Path:
    return Path(log_path).with_suffix(MARKER_SUFFIX)


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
                self._mark_initialized(record)
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        return record

    def _mark_initialized(self, record: dict) -> None:
        marker = marker_path(self.path)
        if marker.exists():
            return
        try:
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, FILE_MODE)
        except FileExistsError:
            return
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"initialized": record["ts"], "first_hash": record["hash"]}) + "\n")

    def __call__(self, kind: str, **fields) -> dict:
        return self.append(kind, **fields)


@dataclass(frozen=True)
class VerifyResult:
    status: str  # "ok" | "uninitialized" | "fail"
    records: int
    message: str

    @property
    def ok(self) -> bool:
        return self.status != "fail"


def _marker_first_hash(marker: Path) -> str | None:
    """first_hash recorded in the marker, or None for a presence-only (older) marker."""
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = data.get("first_hash") if isinstance(data, dict) else None
    return value if isinstance(value, str) and value else None


def verify(path: Path) -> VerifyResult:
    path = Path(path)
    initialized = marker_path(path).exists()
    expected_first = _marker_first_hash(marker_path(path)) if initialized else None
    if not path.exists():
        if initialized:
            return VerifyResult("fail", 0, "audit log is missing but was initialized "
                                           f"({marker_path(path).name} exists)")
        return VerifyResult("uninitialized", 0, "no audit log yet (never initialized)")
    prev, n = GENESIS, 0
    with open(path, "rb") as fh:
        for lineno, raw in enumerate(fh, 1):
            if not raw.strip():
                return VerifyResult("fail", n, f"line {lineno}: blank line")
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                return VerifyResult("fail", n, f"line {lineno}: not valid JSON")
            if not isinstance(rec, dict):
                return VerifyResult("fail", n, f"line {lineno}: not a JSON object")
            if rec.get("seq") != n:
                return VerifyResult("fail", n, f"line {lineno}: seq {rec.get('seq')} != expected {n}")
            if rec.get("prev") != prev:
                return VerifyResult("fail", n, f"line {lineno}: prev hash does not match previous record")
            if rec.get("hash") != record_hash(rec):
                return VerifyResult("fail", n, f"line {lineno}: record hash mismatch (edited record)")
            if n == 0 and expected_first is not None and rec["hash"] != expected_first:
                return VerifyResult("fail", 0, "first record does not match "
                                               f"{marker_path(path).name} first_hash (log replaced)")
            prev, n = rec["hash"], n + 1
    if n == 0:
        if initialized:
            return VerifyResult("fail", 0, "audit log is empty but was initialized")
        return VerifyResult("uninitialized", 0, "audit log is empty (never initialized)")
    if not initialized:
        note = f"; warning: {marker_path(path).name} is missing"
    elif expected_first is None:
        note = f"; note: {marker_path(path).name} has no first_hash (presence-only check)"
    else:
        note = ""
    return VerifyResult("ok", n, f"chain intact ({n} records){note}")
