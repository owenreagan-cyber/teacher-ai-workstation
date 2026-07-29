from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.curriculum_production.fixture_loader import build_from_fixture as build_package_from_fixture
from scripts.curriculum_production.fixture_loader import load_package_fixture

from .workflow import build_lesson_blueprint


def build_blueprint_from_fixture(path: Path):
    raw_overrides: dict[str, Any] = {}
    package_path = path
    if path.suffix == ".json":
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        if "package_fixture" in data:
            root = Path(__file__).resolve().parents[2]
            package_path = root / data["package_fixture"]
            raw_overrides = dict(data.get("overrides") or {})
    package_input = load_package_fixture(package_path)
    package = build_package_from_fixture(package_path)
    return build_lesson_blueprint(package, package_input.content_map, overrides=raw_overrides)
