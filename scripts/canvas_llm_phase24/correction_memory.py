from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any


def now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def canonical_week_code(code: str) -> str:
    token = compact(code).upper().replace("_", "").replace("-", "")
    if token.startswith("Q") and "W" in token:
        quarter = token[1]
        week = token.split("W", 1)[1]
        if quarter.isdigit() and week.isdigit():
            return f"Q{quarter}W{int(week)}"
    return compact(code)


def local_root() -> Path:
    from os import environ

    from pathlib import Path

    return Path(environ.get("PHASE24_LOCAL_ROOT") or (Path(__file__).resolve().parents[2] / ".local/canvas-llm/phase-24-predictive-teacher-brain"))


def state_dir() -> Path:
    return local_root() / "corrections"


def quarantine_dir() -> Path:
    return local_root() / "quarantine" / "corrections"


def state_path(week_code: str) -> Path:
    return state_dir() / f"{canonical_week_code(week_code)}.json"


def default_state(week_code: str) -> dict[str, Any]:
    return {
        "weekCode": canonical_week_code(week_code),
        "version": 0,
        "status": "saved",
        "source": "default",
        "records": [],
        "updatedAt": None,
    }


def quarantine_state(path: Path, reason: str) -> Path:
    target = quarantine_dir() / now_utc().replace(":", "").replace("-", "") / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.replace(target)
    except FileNotFoundError:
        pass
    except OSError:
        if path.exists():
            shutil.copy2(path, target)
            try:
                path.unlink()
            except OSError:
                pass
    return target


def load_correction_state(week_code: str) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    path = state_path(canonical)
    if not path.exists():
        return default_state(canonical)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        quarantine_state(path, f"invalid-json:{error}")
        return {**default_state(canonical), "status": "error", "error": "Correction state could not be parsed", "source": "quarantined"}
    try:
        if not isinstance(payload, dict):
            raise ValueError("correction state must be an object")
        if canonical_week_code(payload.get("weekCode", canonical)) != canonical:
            raise ValueError("weekCode mismatch")
        version = int(payload.get("version", 0))
        if version < 0:
            raise ValueError("version must be non-negative")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise ValueError("records must be a list")
    except Exception as error:
        quarantine_state(path, f"invalid-state:{error}")
        return {**default_state(canonical), "status": "error", "error": f"Invalid correction state: {error}", "source": "quarantined"}
    return {
        "weekCode": canonical,
        "version": version,
        "status": "saved",
        "source": "local",
        "records": records,
        "updatedAt": payload.get("updatedAt"),
    }


def save_correction_record(week_code: str, record: dict[str, Any], revision: int | str | None) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    state_dir().mkdir(parents=True, exist_ok=True)
    current = load_correction_state(canonical)
    if current.get("status") == "error":
        raise ValueError(current.get("error") or "Correction state is invalid")
    expected = int(revision if revision is not None else current.get("version", 0))
    if expected != int(current.get("version", 0)):
        return {
            "status": "conflict",
            "weekCode": canonical,
            "version": current["version"],
            "records": current["records"],
            "updatedAt": current.get("updatedAt"),
        }
    next_state = {
        "weekCode": canonical,
        "version": current["version"] + 1,
        "status": "saved",
        "source": "local",
        "records": list(current.get("records", [])) + [record],
        "updatedAt": now_utc(),
    }
    state_path(canonical).write_text(json.dumps(next_state, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return next_state


def save_teacher_correction(correction: dict[str, Any], revision: int | str | None = None) -> dict[str, Any]:
    return save_correction_record(correction["weekCode"], correction, revision)


def load_teacher_corrections(week_code: str) -> list[dict[str, Any]]:
    return list(load_correction_state(week_code).get("records", []))


def apply_teacher_corrections(entry: dict[str, Any], corrections: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [
        item
        for item in corrections
        if compact(item.get("subject")).lower() == compact(entry.get("subject")).lower()
        and compact(item.get("weekCode")) == compact(entry.get("weekCode"))
        and compact(item.get("day")).lower() == compact(entry.get("weekday")).lower()
    ]
    if not matched:
        return entry
    ordered = sorted(matched, key=lambda item: int(item.get("revision", 1)))
    return {**entry, "approvedCorrection": ordered[-1]}
