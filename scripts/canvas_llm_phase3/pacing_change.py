"""Part B — pacing change detection.

Stores local snapshots under ``.local/pacing/`` and computes a deterministic
diff (ADDED / REMOVED / CHANGED / UNCHANGED) between the latest and previous
normalized weeks. No LLM judgment in the diff engine: exact source changes only.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from . import pacing_extractor as pe


def _latest_path() -> Path:
    return C.PACING_DIR / "latest.json"


def _previous_path() -> Path:
    return C.PACING_DIR / "previous.json"


def _history_dir() -> Path:
    return C.PACING_DIR / "history"


def save_snapshot(week: dict[str, Any]) -> Path:
    """Persist a normalized week as the latest snapshot, rotating the prior one."""
    C.PACING_DIR.mkdir(parents=True, exist_ok=True)
    _history_dir().mkdir(parents=True, exist_ok=True)
    latest = _latest_path()
    prev = _previous_path()
    if latest.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        _history_dir().mkdir(parents=True, exist_ok=True)
        (_history_dir() / f"{stamp}.json").write_text(
            json.dumps(latest_json := json.loads(latest.read_text(encoding="utf-8")), indent=2),
            encoding="utf-8",
        )
        prev.write_text(json.dumps(latest_json, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(week, indent=2), encoding="utf-8")
    return latest


def load_latest() -> dict[str, Any] | None:
    if _latest_path().exists():
        return json.loads(_latest_path().read_text(encoding="utf-8"))
    return None


def load_previous() -> dict[str, Any] | None:
    if _previous_path().exists():
        return json.loads(_previous_path().read_text(encoding="utf-8"))
    return None


def _subjects(week: dict[str, Any]) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for wd, day in (week.get("days") or {}).items():
        for subject, cell in (day.get("subjects") or {}).items():
            out[(wd, subject)] = cell.get("raw", "")
    return out


def diff_weeks(previous: dict[str, Any] | None, latest: dict[str, Any] | None) -> dict[str, Any]:
    """Deterministic raw-value diff. Returns categorized per-cell changes."""
    if latest is None:
        return {"error": "no latest snapshot"}
    if previous is None:
        added = [
            {"weekday": wd, "subject": s, "value": raw}
            for (wd, s), raw in sorted(_subjects(latest).items())
            if raw != ""
        ]
        return {"changed": [], "added": added, "removed": [], "unchanged": 0, "note": "no previous snapshot; all non-blank cells counted as ADDED"}

    prev = _subjects(previous)
    curr = _subjects(latest)
    changed: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    unchanged = 0
    for key in sorted(set(prev) | set(curr)):
        wd, subject = key
        p = prev.get(key, "")
        c = curr.get(key, "")
        if p == c:
            unchanged += 1
        elif p == "" and c != "":
            added.append({"weekday": wd, "subject": subject, "value": c})
        elif p != "" and c == "":
            removed.append({"weekday": wd, "subject": subject, "value": p})
        else:
            changed.append({"weekday": wd, "subject": subject, "from": p, "to": c})
    return {"changed": changed, "added": added, "removed": removed, "unchanged": unchanged}


def snapshot_and_diff(week_code: str, fresh: bool = True) -> dict[str, Any]:
    """Extract the week, persist it, and diff against the previous snapshot."""
    week = pe.extract_week_json(week_code, fresh=fresh)
    previous = load_previous()
    path = save_snapshot(week)
    diff = diff_weeks(previous, week)
    return {"week": week, "snapshot_path": str(path), "diff": diff}


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        # Use a temp dir by monkeypatching paths.
        C.PACING_DIR = Path(tmp)

        prev = {
            "week": {"code": "Q2W1"},
            "days": {
                "Monday": {"subjects": {"math": {"raw": "L30"}, "science": {"raw": ""}}},
                "Tuesday": {"subjects": {"math": {"raw": "L31"}, "science": {"raw": "CH1"}}},
            },
        }
        curr = {
            "week": {"code": "Q2W1"},
            "days": {
                "Monday": {"subjects": {"math": {"raw": "L31"}, "science": {"raw": ""}}},
                "Tuesday": {"subjects": {"math": {"raw": "L31"}, "science": {"raw": ""}}},
            },
        }
        diff = diff_weeks(prev, curr)
        # Monday math CHANGED L30 -> L31.
        assert any(d["weekday"] == "Monday" and d["subject"] == "math" and d["from"] == "L30" and d["to"] == "L31" for d in diff["changed"]), diff
        # Tuesday science REMOVED (was CH1, now blank).
        assert any(d["weekday"] == "Tuesday" and d["subject"] == "science" and d["value"] == "CH1" for d in diff["removed"]), diff
        # No ADDED.
        assert diff["added"] == [], diff
        # Tuesday math UNCHANGED (both L31).
        assert diff["unchanged"] >= 1, diff

        # No-previous case.
        d2 = diff_weeks(None, curr)
        assert len(d2["added"]) >= 1, d2

    print("PASS pacing change detection self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
