from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ALLOWED_SCOPES = {
    "this occurrence only",
    "this week",
    "this lesson",
    "lesson range",
    "parity family",
    "assessment family",
    "curriculum sequence",
    "global reusable resource",
}

LOCAL_ROOT = Path(os.environ.get("PHASE25_LOCAL_ROOT") or ".local/canvas-llm/phase-25-curriculum-source-intelligence")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(path: Path | None = None) -> Path:
    return path or (LOCAL_ROOT / "resource-corrections.json")


def quarantine_path(reason: str) -> Path:
    stamp = now_iso().replace(":", "").replace("-", "")
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    path = LOCAL_ROOT / "quarantine" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path / f"resource-corrections-{compact(reason)[:40]}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class ResourceCorrection:
    subject: str
    week_code: str
    day: str
    required_resource_class: str
    predicted_resource_id: str
    approved_resource_id: str
    correction_scope: str
    timestamp: str
    reason: str = ""
    source_rule: str = ""
    revision: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["weekCode"] = payload.pop("week_code")
        payload["requiredResourceClass"] = payload.pop("required_resource_class")
        payload["predictedResourceId"] = payload.pop("predicted_resource_id")
        payload["approvedResourceId"] = payload.pop("approved_resource_id")
        payload["correctionScope"] = payload.pop("correction_scope")
        payload["sourceRule"] = payload.pop("source_rule")
        return payload


def load_correction_state(path: Path | None = None) -> dict[str, Any]:
    path = state_path(path)
    if not path.exists():
        return {"status": "saved", "version": 0, "records": []}
    try:
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ValueError("state must be an object")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        for record in records:
            if compact(record.get("correctionScope")) not in {compact(scope) for scope in ALLOWED_SCOPES}:
                raise ValueError("invalid correction scope")
        return {"status": "saved", "version": int(payload.get("version", 0)), "records": list(records)}
    except Exception as error:
        quarantine = quarantine_path("invalid-state")
        try:
            path.replace(quarantine)
        except Exception:
            pass
        return {"status": "error", "error": str(error), "version": 0, "records": []}


def save_resource_correction(record: dict[str, Any], expected_version: int, path: Path | None = None) -> dict[str, Any]:
    path = state_path(path)
    current = load_correction_state(path)
    if current.get("status") == "error":
        raise ValueError(current.get("error") or "Invalid correction state")
    if int(current.get("version", 0)) != int(expected_version):
        return {"status": "conflict", "version": int(current.get("version", 0)), "records": list(current.get("records", []))}
    payload = {
        "version": int(current.get("version", 0)) + 1,
        "records": list(current.get("records", [])) + [dict(record)],
        "updatedAt": now_iso(),
    }
    write_json(path, payload)
    return {"status": "saved", **payload}


def find_correction(
    corrections: list[dict[str, Any]],
    subject: str,
    week_code: str,
    day: str,
    required_resource_class: str,
) -> dict[str, Any] | None:
    for record in corrections:
        if (
            compact(record.get("subject")).lower() == compact(subject).lower()
            and compact(record.get("weekCode")).upper() == compact(week_code).upper()
            and compact(record.get("day")).lower() == compact(day).lower()
            and compact(record.get("requiredResourceClass")).lower() == compact(required_resource_class).lower()
        ):
            return record
    return None
