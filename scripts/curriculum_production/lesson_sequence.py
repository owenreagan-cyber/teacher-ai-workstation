from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class InstructionalSequence:
    sequence_id: str
    subject: str
    name: str
    steps: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "subject": self.subject,
            "name": self.name,
            "steps": self.steps,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, sequence_id: str, raw: dict[str, Any]) -> InstructionalSequence:
        return cls(
            sequence_id=sequence_id,
            subject=str(raw.get("subject") or ""),
            name=str(raw.get("name") or sequence_id),
            steps=[str(step) for step in raw.get("steps") or []],
            description=str(raw.get("description") or ""),
        )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sequences_dir() -> Path:
    return _repo_root() / "configs" / "curriculum-production"


def _load_structured_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Sequence catalog must be a mapping: {path}")
    return data


def load_sequence_catalog(path: Path | None = None) -> dict[str, InstructionalSequence]:
    catalog_path = path or (sequences_dir() / "instructional-sequences.yaml")
    raw = _load_structured_file(catalog_path)
    sequences: dict[str, InstructionalSequence] = {}
    for key, value in raw.items():
        if key.startswith("_") or not isinstance(value, dict):
            continue
        sequences[key] = InstructionalSequence.from_dict(key, value)
    return sequences


def get_sequence(sequence_id: str, path: Path | None = None) -> InstructionalSequence:
    catalog = load_sequence_catalog(path)
    if sequence_id not in catalog:
        raise KeyError(f"Unknown instructional sequence: {sequence_id}")
    return catalog[sequence_id]
