#!/usr/bin/env python3
"""Command-line entry for the Phase 18C read-only Teacher Preview assembly.

Read-only. Assembles a deterministic Teacher Preview from a canonical WeeklyPlan
with no Canvas writes, no network calls, and no token access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase18a.examples import build_example_plan  # noqa: E402
from scripts.canvas_llm_phase18a.models import WeeklyPlan  # noqa: E402
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview  # noqa: E402
from scripts.canvas_llm_phase18c.contracts import ReadinessState, RuntimeContext  # noqa: E402


def _example_context() -> RuntimeContext:
    return RuntimeContext(
        canvas_config={
            "math": {"course_id": "COURSE_MATH", "module_id": "MODULE_MATH", "assignment_group_id": "AG_MATH"},
            "reading-spelling": {"course_id": "COURSE_READING", "module_id": "MODULE_READING", "assignment_group_id": "AG_READING"},
            "language-arts": {"course_id": "COURSE_LA", "module_id": "MODULE_LA", "assignment_group_id": "AG_LA"},
            "history": {"course_id": "COURSE_HISTORY", "module_id": "MODULE_HISTORY", "assignment_group_id": "AG_HISTORY"},
        },
        due_time_policy="resolved",
    )


def _selfcheck() -> int:
    failures: list[str] = []
    plan = build_example_plan()
    preview = assemble_teacher_preview(plan, _example_context())

    if preview.week_code == "Q1W3":
        print("PASS: canonical WeeklyPlan assembles into a Teacher Preview")
    else:
        failures.append("preview assembly")
        print("FAIL: preview assembly failed")

    if len(preview.courses) == 5:
        print("PASS: all five course previews constructed")
    else:
        failures.append("course fidelity")
        print(f"FAIL: expected 5 courses, got {len(preview.courses)}")

    if preview.readiness in {r.value for r in ReadinessState}:
        print(f"PASS: readiness state is {preview.readiness}")
    else:
        failures.append("readiness")
        print(f"FAIL: unexpected readiness {preview.readiness!r}")

    drift = preview.drift
    if drift.get("invalid_drift") == []:
        print("PASS: drift detector reports no invalid drift")
    else:
        failures.append("drift")
        print(f"FAIL: invalid drift: {drift.get('invalid_drift')}")

    # Protected Science remains blocked.
    science = next((c for c in preview.courses if c.course == "Science"), None)
    if science is not None and science.assignment_policy == "disabled" and science.readiness == "Blocked":
        print("PASS: protected Science remains write-blocked")
    else:
        failures.append("protected")
        print("FAIL: protected Science not blocked")

    # Missing config blocks (empty context).
    bare = assemble_teacher_preview(plan, RuntimeContext())
    if bare.readiness == "BLOCKED_MISSING_CONFIG":
        print("PASS: missing Canvas config blocks preview (no guessed IDs)")
    else:
        failures.append("missing config")
        print(f"FAIL: expected BLOCKED_MISSING_CONFIG, got {bare.readiness!r}")

    # Idempotence.
    a = json.dumps(assemble_teacher_preview(plan, _example_context()).to_dict(), sort_keys=True)
    b = json.dumps(assemble_teacher_preview(plan, _example_context()).to_dict(), sort_keys=True)
    if a == b:
        print("PASS: preview assembly is deterministic")
    else:
        failures.append("idempotence")
        print("FAIL: preview assembly is not deterministic")

    # Invalid plan rejected.
    bad = build_example_plan()
    bad.friday_date = "2026-08-08"
    try:
        assemble_teacher_preview(bad, _example_context())
        failures.append("invalid plan")
        print("FAIL: invalid plan was not rejected")
    except ValueError:
        print("PASS: invalid WeeklyPlan rejected before preview assembly")

    # No write path in this package.
    pkg_dir = Path(__file__).resolve().parent
    write_markers = [
        "canvas" + "_writer",
        "canvas_" + "connector",
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
    print("PASS: no Canvas write path in the Phase 18C package")
    print("Self-check complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_phase18c", description="Read-only Teacher Preview assembly (Phase 18C)")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--preview", type=str, default="", help="assemble a Teacher Preview from a WeeklyPlan JSON file")
    parser.add_argument("--example", action="store_true", help="print the example Teacher Preview as JSON")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()

    plan = build_example_plan()
    if args.preview:
        plan = WeeklyPlan.from_json(Path(args.preview).read_text(encoding="utf-8"))

    preview = assemble_teacher_preview(plan, _example_context())

    if args.example:
        print(json.dumps(preview.to_dict(), indent=2, sort_keys=True))
        return 0

    print(f"TeacherPreview week={preview.week_code} readiness={preview.readiness}")
    print(f"  courses={len(preview.courses)}")
    print(f"  unresolved={len(preview.unresolved)}")
    print(f"  protected={preview.protected}")
    print(f"  missing_config={len(preview.missing_config)}")
    print(f"  unresolved_policy={preview.unresolved_policy}")
    print(f"  warnings={len(preview.warnings)}")
    print(f"  drift.invalid={len(preview.drift.get('invalid_drift', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
