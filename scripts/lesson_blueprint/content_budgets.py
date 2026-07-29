from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ContentBudget:
    artifact_type: str
    label: str
    min_slides: int | None = None
    max_slides: int | None = None
    pages: int | None = None
    meaningful_blanks: int | None = None
    activity_sections: int | None = None
    instructional_stages: int | None = None
    mirrored: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_content_budgets(path: Path | None = None) -> dict[str, ContentBudget]:
    catalog_path = path or (_repo_root() / "configs" / "lesson-blueprint" / "content-budgets.yaml")
    text = catalog_path.read_text(encoding="utf-8")
    try:
        import yaml

        raw = yaml.safe_load(text)
    except ImportError:  # pragma: no cover
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"Content budgets must be a mapping: {catalog_path}")
    budgets: dict[str, ContentBudget] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        budgets[key] = ContentBudget(
            artifact_type=key,
            label=str(value.get("label") or key),
            min_slides=value.get("min_slides"),
            max_slides=value.get("max_slides"),
            pages=value.get("pages"),
            meaningful_blanks=value.get("meaningful_blanks"),
            activity_sections=value.get("activity_sections"),
            instructional_stages=value.get("instructional_stages"),
            mirrored=bool(value.get("mirrored", False)),
        )
    return budgets
