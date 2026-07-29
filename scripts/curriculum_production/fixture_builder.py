from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _base_math_intake(**overrides: Any) -> dict[str, Any]:
    payload = {
        "lesson_id": "pass-g4-math-u1-l03",
        "subject": "math",
        "grade": 4,
        "unit": "Unit 1 — Place Value",
        "chapter": "Chapter 3",
        "lesson_number": 3,
        "title": "Comparing Multi-Digit Numbers (Fictional Sample)",
        "objective": "Students will compare multi-digit numbers using place value reasoning.",
        "standards": ["Sample.MATH.4.NBT.A.2"],
        "vocabulary": ["place value", "compare", "greater than", "less than"],
        "assessment_targets": ["Compare two four-digit numbers with justification"],
        "teacher_notes": "Fictional planning sample only.",
        "source_references": [{"ref_id": "manual-1", "label": "Teacher notes packet", "note": "Sample"}],
        "approval_status": "draft",
        "instructional_sequence_id": "math",
        "required_artifacts": ["presentation", "guided_notes", "worksheet", "assessment", "teacher_key"],
    }
    payload.update(overrides)
    return payload


def _math_content_items(**overrides: Any) -> list[dict[str, Any]]:
    items = [
        {
            "content_id": "crit-compare",
            "title": "Compare multi-digit numbers",
            "description": "Core comparison procedure",
            "priority": "critical",
            "source_ref": "manual-1",
            "supports_objective": True,
            "supports_assessment_target": "Compare two four-digit numbers with justification",
            "linked_sequence_step": "Guided",
            "subject": "math",
            "tags": ["procedure"],
        },
        {
            "content_id": "crit-place-value",
            "title": "Place value positions",
            "description": "Ones, tens, hundreds, thousands",
            "priority": "critical",
            "source_ref": "manual-1",
            "supports_objective": True,
            "linked_sequence_step": "Concrete",
            "subject": "math",
        },
    ]
    if overrides.get("extra_items"):
        items.extend(overrides.pop("extra_items"))
    return items


def build_pass_math(path: Path) -> None:
    _write_package(
        path,
        intake=_base_math_intake(),
        content_map={"lesson_id": "pass-g4-math-u1-l03", "items": _math_content_items()},
    )


def build_pass_shurley(path: Path) -> None:
    lesson_id = "pass-g4-shurley-u2-l01"
    _write_package(
        path,
        intake=_base_math_intake(
            lesson_id=lesson_id,
            subject="shurley",
            unit="Unit 2 — Sentence Classification",
            title="Sample Shurley Classification Lesson",
            objective="Students will classify sample sentence patterns.",
            instructional_sequence_id="ela",
            vocabulary=["noun", "verb", "adjective"],
            assessment_targets=["Classify a sample sentence"],
        ),
        content_map={
            "lesson_id": lesson_id,
            "items": [
                {
                    "content_id": "crit-pattern",
                    "title": "Sentence pattern A",
                    "priority": "critical",
                    "supports_objective": True,
                    "supports_assessment_target": "Classify a sample sentence",
                    "linked_sequence_step": "Guided Practice",
                    "source_ref": "manual-shurley",
                    "subject": "shurley",
                }
            ],
        },
    )


def build_pass_history(path: Path) -> None:
    lesson_id = "pass-g4-history-u3-l02"
    _write_package(
        path,
        intake=_base_math_intake(
            lesson_id=lesson_id,
            subject="history",
            unit="Unit 3 — Colonial America",
            title="Sample History Timeline Lesson",
            objective="Students will sequence fictional timeline events.",
            instructional_sequence_id="history",
            assessment_targets=["Order three timeline events"],
        ),
        content_map={
            "lesson_id": lesson_id,
            "items": [
                {
                    "content_id": "crit-timeline",
                    "title": "Timeline event ordering",
                    "priority": "critical",
                    "supports_objective": True,
                    "supports_assessment_target": "Order three timeline events",
                    "linked_sequence_step": "Practice",
                    "source_ref": "manual-history",
                    "subject": "history",
                }
            ],
        },
    )


def build_warn_missing_objective(path: Path) -> None:
    _write_package(
        path,
        intake=_base_math_intake(objective=""),
        content_map={"lesson_id": "pass-g4-math-u1-l03", "items": _math_content_items()},
    )


def build_warn_critical_unlinked(path: Path) -> None:
    items = _math_content_items()
    items[0]["supports_objective"] = False
    items[0]["supports_assessment_target"] = ""
    _write_package(
        path,
        intake=_base_math_intake(),
        content_map={"lesson_id": "pass-g4-math-u1-l03", "items": items},
    )


def build_warn_assessment_missing(path: Path) -> None:
    _write_package(
        path,
        intake=_base_math_intake(assessment_targets=[]),
        content_map={"lesson_id": "pass-g4-math-u1-l03", "items": _math_content_items()},
    )


def build_warn_too_many_supporting(path: Path) -> None:
    extras = [
        {
            "content_id": f"sup-{i}",
            "title": f"Supporting idea {i}",
            "priority": "supporting",
            "source_ref": "",
            "subject": "math",
        }
        for i in range(1, 16)
    ]
    _write_package(
        path,
        intake=_base_math_intake(),
        content_map={
            "lesson_id": "pass-g4-math-u1-l03",
            "items": _math_content_items(extra_items=extras),
        },
    )


def build_warn_omit_in_plan(path: Path) -> None:
    items = _math_content_items()
    items.append(
        {
            "content_id": "omit-extra",
            "title": "Omit but referenced",
            "priority": "omit",
            "artifact_plan_refs": ["worksheet"],
        }
    )
    _write_package(
        path,
        intake=_base_math_intake(),
        content_map={"lesson_id": "pass-g4-math-u1-l03", "items": items},
    )


def build_fail_invalid_intake(path: Path) -> None:
    _write_package(
        path,
        intake={"lesson_id": "fail-invalid", "subject": "math", "grade": 4},
        content_map={"lesson_id": "fail-invalid", "items": []},
    )


def build_fail_broken_graph(path: Path) -> None:
    _write_package(
        path,
        intake=_base_math_intake(lesson_id="fail-graph"),
        content_map={
            "lesson_id": "fail-graph",
            "items": _math_content_items(),
        },
        broken_graph=True,
    )


def _write_package(
    path: Path,
    *,
    intake: dict[str, Any],
    content_map: dict[str, Any],
    broken_graph: bool = False,
) -> None:
    payload = {
        "intake": intake,
        "content_map": content_map,
        "approval": {"state": intake.get("approval_status", "draft"), "history": []},
    }
    if broken_graph:
        payload["broken_graph"] = True
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_all_fixtures(base: Path) -> None:
    builders = {
        base / "passing" / "math-lesson-package.json": build_pass_math,
        base / "passing" / "shurley-lesson-package.json": build_pass_shurley,
        base / "passing" / "history-lesson-package.json": build_pass_history,
        base / "warning" / "missing-objective.json": build_warn_missing_objective,
        base / "warning" / "critical-unlinked.json": build_warn_critical_unlinked,
        base / "warning" / "assessment-missing.json": build_warn_assessment_missing,
        base / "warning" / "too-many-supporting.json": build_warn_too_many_supporting,
        base / "warning" / "omit-in-plan.json": build_warn_omit_in_plan,
        base / "failing" / "invalid-intake.json": build_fail_invalid_intake,
        base / "failing" / "broken-graph.json": build_fail_broken_graph,
    }
    for target, builder in builders.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        builder(target)

    legacy = base / "sample-lesson-package.json"
    if not legacy.is_file():
        build_pass_math(legacy)
