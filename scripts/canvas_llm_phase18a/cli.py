#!/usr/bin/env python3
"""Command-line entry for the canonical WeeklyPlan (Phase 18A).

Read-only. Builds examples, validates, serializes, and inspects plans in memory.
No Canvas writes, no network calls, no secrets, no token access.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase18a.examples import build_example_plan  # noqa: E402
from scripts.canvas_llm_phase18a.models import WeeklyPlan  # noqa: E402
from scripts.canvas_llm_phase18a.precedent import PRECEDENT_CATALOG, PRECEDENT_CLASSES  # noqa: E402
from scripts.canvas_llm_phase18a.source_precedence import SOURCE_LABELS, SOURCE_PRECEDENCE  # noqa: E402
from scripts.canvas_llm_phase18a.validation import validate_plan  # noqa: E402


def render_plan(plan: WeeklyPlan) -> str:
    """Return a human-readable inspection of a canonical WeeklyPlan."""
    lines: list[str] = []
    lines.append(f"WeeklyPlan {plan.week_code} ({plan.school_year})")
    lines.append(f"  schema={plan.schema} version={plan.version}")
    lines.append(f"  quarter={plan.quarter} week={plan.week_number}")
    lines.append(f"  dates={plan.monday_date} .. {plan.friday_date} timezone={plan.timezone}")
    lines.append("")

    if plan.teacher_instructions:
        lines.append("Teacher instructions:")
        for item in plan.teacher_instructions:
            lines.append(f"  - {item}")
        lines.append("")

    if plan.teacher_overrides:
        lines.append("Teacher overrides:")
        for item in plan.teacher_overrides:
            lines.append(f"  - {item}")
        lines.append("")

    lines.append("Courses:")
    for name, course in plan.courses.items():
        flag = " [protected]" if course.protected else ""
        arts = f" artifacts={course.requested_artifacts}" if course.requested_artifacts else ""
        lines.append(f"  {name}{flag}{arts}")
        for day in course.days:
            if day.blank:
                lines.append(f"    {day.weekday:<9} (blank)")
                continue
            content = day.in_class or day.raw or "(unset)"
            homework = day.homework or "-"
            source = day.decided_source or "(none)"
            lines.append(
                f"    {day.weekday:<9} {day.date}  in-class={content!r}  homework={homework!r}  source={source}"
            )
            if day.ambiguity:
                lines.append(f"                ambiguity={day.ambiguity!r}")
        lines.append("")

    if plan.assessments_reminders:
        lines.append("Assessments / reminders:")
        for item in plan.assessments_reminders:
            lines.append(f"  - {item}")
        lines.append("")

    lines.append("Requested artifacts:")
    lines.append(f"  {plan.requested_artifacts.to_dict()}")
    lines.append("")

    if plan.protected_courses:
        lines.append(f"Protected courses/objects: {plan.protected_courses}")
        lines.append("")

    if plan.unresolved_ambiguities:
        lines.append("Unresolved ambiguities:")
        for item in plan.unresolved_ambiguities:
            lines.append(f"  - {item}")
        lines.append("")

    if plan.warnings:
        lines.append("Warnings:")
        for item in plan.warnings:
            lines.append(f"  - {item}")
        lines.append("")

    if plan.provenance:
        lines.append("Provenance:")
        for e in plan.provenance:
            lines.append(
                f"  - [{e.source_class}] {e.reference}" + (f" ({e.note})" if e.note else "")
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _print_precedence() -> None:
    print("Source precedence (highest authority first):")
    for i, source in enumerate(SOURCE_PRECEDENCE, start=1):
        print(f"  {i}. {source} — {SOURCE_LABELS[source]}")
    print()
    print("Precedent classification:")
    for key, label in PRECEDENT_CLASSES.items():
        print(f"  - {key}: {label}")
    print()
    print("Documented August 15 scout findings:")
    for entry in PRECEDENT_CATALOG:
        print(f"  [{entry['classification']}] {entry['description']}")


def _selfcheck() -> int:
    """Run the read-only self-check used by status and tests."""
    failures: list[str] = []
    plan = build_example_plan()
    report = validate_plan(plan)
    if report.ok:
        print("PASS: canonical WeeklyPlan model builds a valid example plan")
    else:
        failures.append("example plan did not validate")
        print("FAIL: canonical WeeklyPlan example plan did not validate")
        for err in report.errors:
            print(f"  ERROR: {err}")

    serialized = plan.to_json()
    restored = WeeklyPlan.from_json(serialized)
    if plan.to_dict() == restored.to_dict():
        print("PASS: serialization round trip preserves the canonical plan")
    else:
        failures.append("serialization round trip")
        print("FAIL: serialization round trip did not preserve the canonical plan")

    # Precedent classification and provenance representation.
    if PRECEDENT_CATALOG and set(PRECEDENT_CLASSES) >= {"operational_behavior", "canvas_configuration", "anomaly"}:
        print("PASS: precedent classification represented (rules / config / anomalies)")
    else:
        failures.append("precedent classification")
        print("FAIL: precedent classification not fully represented")

    # No Canvas write path: this package must not import or call any writer.
    # Tokens are concatenated so the checker does not flag its own source.
    write_markers = [
        "canvas" + "_writer",
        "requests." + "post",
        "requests." + "put",
        "requests." + "patch",
        "requests." + "delete",
    ]
    pkg_dir = Path(__file__).resolve().parent
    for path in sorted(pkg_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in write_markers):
            failures.append(f"write path token in {path.name}")
            print(f"FAIL: unexpected Canvas write token in {path.name}")

    if failures:
        print(f"Self-check failed: {failures}")
        return 1
    print("PASS: no Canvas write path in the Phase 18A package")
    print("Self-check complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_phase18a", description="Canonical WeeklyPlan model (Phase 18A)")
    parser.add_argument("--example", action="store_true", help="print the canonical example plan as JSON")
    parser.add_argument("--inspect", action="store_true", help="print a human-readable inspection")
    parser.add_argument("--validate", action="store_true", help="validate a plan read from --file")
    parser.add_argument("--precedence", action="store_true", help="print source precedence and precedent classification")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--file", type=str, default="", help="path to a WeeklyPlan JSON file")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()

    if args.precedence:
        _print_precedence()
        return 0

    if args.example:
        print(build_example_plan().to_json())
        return 0

    plan: WeeklyPlan
    if args.file:
        plan = WeeklyPlan.from_json(Path(args.file).read_text(encoding="utf-8"))
    else:
        plan = build_example_plan()

    if args.inspect:
        sys.stdout.write(render_plan(plan))
        return 0

    if args.validate:
        report = validate_plan(plan)
        for err in report.errors:
            print(f"ERROR: {err}")
        for warn in report.warnings:
            print(f"WARN: {warn}")
        if report.ok:
            print("PASS: plan validates")
            return 0
        print("FAIL: plan does not validate")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
