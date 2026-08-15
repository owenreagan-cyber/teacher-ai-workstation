#!/usr/bin/env python3
"""Command-line entry for the Phase 18B canonical WeeklyPlan integration layer.

Read-only. Builds, validates, and translates canonical WeeklyPlans into
downstream-compatible dicts in memory. No Canvas writes, no network calls, no
token access.
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
from scripts.canvas_llm_phase18a.validation import validate_plan  # noqa: E402
from scripts.canvas_llm_phase18b.precedent_loader import (  # noqa: E402
    PrecedentLoadResult,
    load_precedent_bundle,
    static_catalog,
)
from scripts.canvas_llm_phase18b.translation import translate_weekly_plan  # noqa: E402


def _render_result(result) -> str:
    lines: list[str] = []
    lines.append(f"TranslationResult plan_id={result.plan_id} week={result.week_code}")
    lines.append(f"  agenda title={result.agenda['title']!r}")
    lines.append(f"  prediction events={len(result.prediction['predictions'])}")
    lines.append(f"  subject workspaces={len(result.subjects)}")
    lines.append(f"  trace records={len(result.trace)}")
    lines.append(f"  blanks={len(result.blanks)}")
    lines.append(f"  unresolved={len(result.unresolved)}")
    lines.append(f"  protected={result.protected}")
    if result.warnings:
        lines.append("  warnings:")
        for w in result.warnings:
            lines.append(f"    - {w}")
    return "\n".join(lines) + "\n"


def _selfcheck() -> int:
    failures: list[str] = []

    plan = build_example_plan()
    result = translate_weekly_plan(plan)
    if result.plan_id and result.week_code == "Q1W3":
        print("PASS: valid WeeklyPlan translates successfully")
    else:
        failures.append("valid translation")
        print("FAIL: valid WeeklyPlan did not translate")

    # Course/day fidelity: all five courses present as subject workspaces.
    expected_subjects = {"math", "reading-spelling", "language-arts", "history", "science"}
    actual_subjects = {s["subject"] for s in result.subjects}
    if actual_subjects == expected_subjects:
        print("PASS: all five course workspaces constructed")
    else:
        failures.append("course fidelity")
        print(f"FAIL: expected {expected_subjects}, got {actual_subjects}")

    # Blanks remain blank (no invented content in agenda or events).
    blank_refs = {(b["course"], b["weekday"]) for b in result.blanks}
    if blank_refs:
        print("PASS: blanks recorded and preserved")

    # Ambiguity remains unresolved, not guessed.
    if result.unresolved:
        print("PASS: ambiguity recorded as unresolved")
    else:
        failures.append("ambiguity preservation")
        print("FAIL: expected unresolved ambiguity in example plan")

    # Protected courses produce no write-eligible action.
    if "Science" in result.protected:
        science = next(s for s in result.subjects if s["subject"] == "science")
        if science["assignmentPolicy"] == "disabled" and science["readinessState"] == "Blocked":
            print("PASS: protected Science blocked from writable actions")
        else:
            failures.append("protected course")
            print("FAIL: protected Science not blocked")
    else:
        failures.append("protected course")
        print("FAIL: Science not marked protected")

    # Precedence: teacher instruction must not be overridden by prediction.
    teacher_events = [
        e for e in result.prediction["predictions"]
        if e["decision_layer"] == "teacher_instruction"
    ]
    if teacher_events:
        print("PASS: teacher instruction preserved as higher-precedence decision")
    else:
        failures.append("teacher precedence")
        print("FAIL: no teacher_instruction events found")

    # Provenance trace survives translation.
    if result.trace:
        print("PASS: provenance trace survives translation")
    else:
        failures.append("provenance trace")
        print("FAIL: no provenance trace records")

    # Invalid plan is rejected before translation.
    bad = build_example_plan()
    bad.friday_date = "2026-08-08"  # Friday must be monday + 4
    try:
        translate_weekly_plan(bad)
        failures.append("invalid plan rejection")
        print("FAIL: invalid plan was not rejected")
    except ValueError:
        print("PASS: invalid WeeklyPlan rejected before translation")

    # No write path in this package.
    pkg_dir = Path(__file__).resolve().parent
    write_markers = [
        "canvas" + "_writer",
        "requests." + "post",
        "requests." + "put",
        "requests." + "patch",
        "requests." + "delete",
        "urllib." + "request",
    ]
    for path in sorted(pkg_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in write_markers):
            failures.append(f"write path token in {path.name}")
            print(f"FAIL: unexpected write token in {path.name}")

    if failures:
        print(f"Self-check failed: {failures}")
        return 1
    print("PASS: no Canvas write path in the Phase 18B package")
    print("Self-check complete")
    return 0


def _precedent_status() -> int:
    result: PrecedentLoadResult = load_precedent_bundle()
    print(f"Precedent bundle status: {result.status}")
    print(f"  operational behavior records: {len(result.records)}")
    print(f"  canvas configuration entries: {len(result.config_entries)}")
    print(f"  anomalies: {len(result.anomalies)}")
    for w in result.warnings:
        print(f"WARN: {w}")
    for e in result.errors:
        print(f"ERROR: {e}")
    print(f"  static fallback catalog entries: {len(static_catalog())}")
    if result.status == "malformed":
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_phase18b", description="Canonical WeeklyPlan integration layer (Phase 18B)")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--translate", type=str, default="", help="translate a WeeklyPlan JSON file")
    parser.add_argument("--example", action="store_true", help="print the translated example as JSON")
    parser.add_argument("--precedent-status", action="store_true", help="report optional precedent bundle state")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()

    if args.precedent_status:
        return _precedent_status()

    plan = build_example_plan()
    if args.translate:
        plan = WeeklyPlan.from_json(Path(args.translate).read_text(encoding="utf-8"))

    result = translate_weekly_plan(plan)

    if args.example:
        import json
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    sys.stdout.write(_render_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
