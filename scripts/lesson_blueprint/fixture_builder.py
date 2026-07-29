from __future__ import annotations

import json
from pathlib import Path


def _write(path: Path, package_fixture: str, overrides: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"package_fixture": package_fixture, "overrides": overrides or {}}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_all_fixtures(base: Path) -> None:
    pkg = "fixtures/curriculum-production/passing/math-lesson-package.json"
    shurley = "fixtures/curriculum-production/passing/shurley-lesson-package.json"
    builders = {
        base / "passing" / "well-formed-blueprint.json": (pkg, {}),
        base / "passing" / "shurley-blueprint.json": (shurley, {}),
        base / "warning" / "vocabulary-mismatch.json": (pkg, {"vocabulary_mismatch": True, "worksheet_vocab": ["nonexistent-term"]}),
        base / "warning" / "unused-critical-content.json": (pkg, {"unused_critical": True}),
        base / "warning" / "budget-exceeded.json": (pkg, {"budget_exceeded_for": "presentation"}),
        base / "warning" / "duplicate-terminology.json": (pkg, {"duplicate_sections_for": "worksheet"}),
        base / "failing" / "broken-dependency.json": (pkg, {"broken_dependency_for": "worksheet"}),
        base / "failing" / "missing-blueprint.json": (pkg, {"missing_blueprint_for": "assessment"}),
        base / "failing" / "missing-sections.json": (pkg, {"missing_section_for": "guided_notes"}),
        base / "failing" / "broken-registry.json": (pkg, {"broken_registry_reference": True}),
    }
    for target, (package_fixture, overrides) in builders.items():
        _write(target, package_fixture, overrides)
