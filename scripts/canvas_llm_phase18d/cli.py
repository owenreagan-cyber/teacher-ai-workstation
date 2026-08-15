#!/usr/bin/env python3
"""Command-line entry for Phase 18D read-only dry-run deployment planning.

Read-only. Builds a deterministic Dry-Run Deployment Packet + Safety Diff from a
Teacher Preview and a live Canvas snapshot with no Canvas writes, no mutation
HTTP calls, no token access, and no network.
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
from scripts.canvas_llm_phase18c.contracts import RuntimeContext  # noqa: E402
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview  # noqa: E402
from scripts.canvas_llm_phase18d.contracts import CanvasSnapshot, DryRunContext, PacketReadiness  # noqa: E402
from scripts.canvas_llm_phase18d.deployment import assemble_dry_run_packet, build_safety_diff  # noqa: E402


def _resolved_context() -> DryRunContext:
    return DryRunContext(
        canvas_config={
            "math": {"course_id": "COURSE_MATH", "module_id": "MODULE_MATH", "assignment_group_id": "AG_MATH"},
            "reading-spelling": {"course_id": "COURSE_READING", "module_id": "MODULE_READING", "assignment_group_id": "AG_READING"},
            "language-arts": {"course_id": "COURSE_LA", "module_id": "MODULE_LA", "assignment_group_id": "AG_LA"},
            "history": {"course_id": "COURSE_HISTORY", "module_id": "MODULE_HISTORY", "assignment_group_id": "AG_HISTORY"},
        },
        due_time_policy="resolved",
        resolved_due_time="15:00",
        publish_policy="resolved",
        resolved_publish_state="published",
    )


def _preview_context() -> RuntimeContext:
    ctx = _resolved_context()
    return RuntimeContext(canvas_config=ctx.canvas_config, due_time_policy="resolved")


def _clear_history_ambiguity(plan: WeeklyPlan) -> WeeklyPlan:
    """Return a copy of the example plan with no unresolved content (test-only)."""
    import copy

    plan = copy.deepcopy(plan)
    for day in plan.courses["History"].days:
        if day.weekday == "Wednesday":
            day.ambiguity = ""
            day.in_class = "Unit 1 Lesson 2 (resolved)"
            day.raw = "Unit 1 Lesson 2"
    return plan


def _report(packet, diffs) -> str:
    lines: list[str] = [f"Week {packet.week_code} — Dry-Run Deployment Packet", ""]
    by_course: dict[str, list] = {}
    for item in diffs:
        by_course.setdefault(item.course, []).append(item)
    for course, items in by_course.items():
        lines.append(course)
        for item in items:
            lines.append(f"  {item.object_type} ({item.locator})")
            lines.append(f"    {item.operation} [{item.classification} / risk {item.risk}]")
            for blocker in item.blockers:
                lines.append(f"      BLOCKED: {blocker}")
            for fd in item.field_diffs:
                if fd.change != "NO_CHANGE":
                    lines.append(f"      {fd.field}: {fd.current!r} -> {fd.desired!r} ({fd.change})")
        lines.append("")
    lines.append(f"Readiness: {packet.readiness}")
    if packet.blocked:
        lines.append("Blocked:")
        for b in packet.blocked:
            lines.append(f"  - {b}")
    if packet.no_change:
        lines.append(f"No change: {len(packet.no_change)} intent(s)")
    return "\n".join(lines)


def _selfcheck() -> int:
    failures: list[str] = []
    plan = build_example_plan()
    preview = assemble_teacher_preview(plan, _preview_context())

    # 1. Default context fails closed (policy + unresolved).
    bare_pkt = assemble_dry_run_packet(preview, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty"), DryRunContext(canvas_config=_preview_context().canvas_config))
    if bare_pkt.readiness != PacketReadiness.READY_FOR_OWNER_REVIEW.value:
        print(f"PASS: default context fails closed (readiness={bare_pkt.readiness})")
    else:
        failures.append("fail-closed")
        print("FAIL: default context unexpectedly write-ready")

    # 2. Resolved context + clean plan -> READY_FOR_OWNER_REVIEW.
    clean = assemble_teacher_preview(_clear_history_ambiguity(plan), _preview_context())
    ready_pkt = assemble_dry_run_packet(clean, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty"), _resolved_context())
    if ready_pkt.readiness == PacketReadiness.READY_FOR_OWNER_REVIEW.value:
        print("PASS: resolved context yields READY_FOR_OWNER_REVIEW")
    else:
        failures.append("ready path")
        print(f"FAIL: expected READY_FOR_OWNER_REVIEW, got {ready_pkt.readiness!r} ({ready_pkt.blocked})")

    # 3. Determinism / idempotence.
    a = json.dumps(assemble_dry_run_packet(clean, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty"), _resolved_context()).to_dict(), sort_keys=True)
    b = json.dumps(assemble_dry_run_packet(clean, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty"), _resolved_context()).to_dict(), sort_keys=True)
    if a == b:
        print("PASS: dry-run packet is deterministic")
    else:
        failures.append("idempotence")
        print("FAIL: dry-run packet not deterministic")

    # 4. Protected Science produces no writable intent.
    if all(i.operation in ("SKIP",) or i.course != "science" for i in bare_pkt.intents):
        writable = [i for i in bare_pkt.intents if i.course == "science" and i.operation not in ("SKIP",)]
        if not writable:
            print("PASS: protected Science produces zero writable intents")
        else:
            failures.append("protected")
            print("FAIL: protected Science produced writable intents")
    else:
        failures.append("protected")
        print("FAIL: protected Science intent check failed")

    # 5. No write path / mutation HTTP in this package.
    pkg_dir = Path(__file__).resolve().parent
    write_markers = [
        "canvas" + "_writer",
        "canvas_" + "connector",
        "requests." + "post",
        "requests." + "put",
        "requests." + "patch",
        "requests." + "delete",
        "urllib." + "request",
        "http." + "client",
    ]
    for path in sorted(pkg_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in write_markers:
            if token in text:
                failures.append(f"write token in {path.name}: {token}")
                print(f"FAIL: write-path token {token!r} in {path.name}")

    if failures:
        print(f"Self-check failed: {failures}")
        return 1
    print("PASS: no Canvas write path in the Phase 18D package")
    print("Self-check complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_phase18d", description="Read-only dry-run deployment planning (Phase 18D)")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--example", action="store_true", help="print the example dry-run packet as JSON")
    parser.add_argument("--report", action="store_true", help="print a human-readable dry-run report")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()

    plan = build_example_plan()
    preview = assemble_teacher_preview(plan, _preview_context())
    snapshot = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-example", objects=[])
    packet = assemble_dry_run_packet(preview, snapshot, _resolved_context())
    diffs = build_safety_diff(packet)

    if args.example:
        print(json.dumps({"packet": packet.to_dict(), "safetyDiff": [d.to_dict() for d in diffs]}, indent=2, sort_keys=True))
        return 0
    if args.report:
        print(_report(packet, diffs))
        return 0

    print(f"DryRunPacket week={packet.week_code} readiness={packet.readiness}")
    print(f"  intents={len(packet.intents)} blocked={len(packet.blocked)} no_change={len(packet.no_change)}")
    print(f"  snapshot={packet.snapshot_identity} preview={packet.preview_identity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
