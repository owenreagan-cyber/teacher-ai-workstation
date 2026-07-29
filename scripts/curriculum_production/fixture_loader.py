#!/usr/bin/env python3
"""Load lesson package fixtures and build package plans."""
from __future__ import annotations

import json
from pathlib import Path

from .approval_workflow import ApprovalWorkflow
from .intake_validation import validate_lesson_package_plan
from .lesson_package import LessonPackageInput, LessonPackagePlan
from .relationship_graph import RelationshipGraph
from .reporting import format_lesson_package_status
from .workflow import build_lesson_package


def load_package_fixture(path: Path) -> LessonPackageInput:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return LessonPackageInput.from_dict(raw)


def build_from_fixture(path: Path) -> LessonPackagePlan:
    package_input = load_package_fixture(path)
    package = build_lesson_package(package_input)
    if package_input.broken_graph:
        package.relationship_graph = RelationshipGraph(lesson_id=package.lesson_id)
        workflow = package_input.approval or ApprovalWorkflow(state=package_input.intake.approval_status)
        package.validation_summary = validate_lesson_package_plan(
            intake=package_input.intake,
            content_map=package_input.content_map,
            lesson=package_input.intake.to_lesson_model(),
            plan=package.artifact_plan,
            graph=package.relationship_graph,
            workflow=workflow,
            sequence=package.instructional_sequence,
        )
        package.status_report = format_lesson_package_status(package)
    return package
