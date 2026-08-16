#!/usr/bin/env python3
"""Command-line entry for Phase 18E owner policy + execution preconditions.

Read-only. Encodes the owner-approved homework due-time policy, evaluates
execution preconditions, and builds pure data-only future writer requests.
Zero Canvas writes. No mutation HTTP. No token access. No network.
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
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview  # noqa: E402
from scripts.canvas_llm_phase18c.contracts import RuntimeContext  # noqa: E402
from scripts.canvas_llm_phase18d.contracts import CanvasSnapshot, DryRunContext  # noqa: E402
from scripts.canvas_llm_phase18d.deployment import assemble_dry_run_packet  # noqa: E402
from scripts.canvas_llm_phase18e.adapter import build_writer_requests  # noqa: E402
from scripts.canvas_llm_phase18e.contracts import ReadinessState  # noqa: E402
from scripts.canvas_llm_phase18e.policy import (  # noqa: E402
    OwnerCanvasPolicy,
    default_policy,
    due_timestamp,
    policy_hash,
)
from scripts.canvas_llm_phase18e.preconditions import record_approval_bindings  # noqa: E402
from scripts.canvas_llm_phase18e.validation import validate_policy  # noqa: E402

CFG = {
    "math": {"course_id": "COURSE_MATH", "module_id": "MODULE_MATH", "assignment_group_id": "AG_MATH"},
    "reading-spelling": {"course_id": "COURSE_READING", "module_id": "MODULE_READING", "assignment_group_id": "AG_READING"},
    "language-arts": {"course_id": "COURSE_LA", "module_id": "MODULE_LA", "assignment_group_id": "AG_LA"},
    "history": {"course_id": "COURSE_HISTORY", "module_id": "MODULE_HISTORY", "assignment_group_id": "AG_HISTORY"},
}

# Tokens that must never appear in any Phase 18E source file.
WRITE_MARKERS = [
    "canvas" + "_writer",
    "attempt" + "_live_write",
    "requests." + "post",
    "requests." + "put",
    "requests." + "patch",
    "requests." + "delete",
    "urllib." + "request",
    "http." + "client",
]


def _selfcheck() -> int:
    failures: list[str] = []

    # 1. Owner policy is deterministic and valid.
    p = default_policy()
    if len(validate_policy(p)) == 0 and policy_hash(p) == policy_hash(default_policy()):
        print("PASS: owner policy is valid and hash-deterministic")
    else:
        failures.append("policy")
        print("FAIL: owner policy invalid or non-deterministic")

    # 2. Same-day 11:59 due-time with DST awareness.
    summer = due_timestamp("2026-08-24", "America/New_York")
    winter = due_timestamp("2026-01-15", "America/New_York")
    if summer == "2026-08-24T23:59:00-04:00" and winter == "2026-01-15T23:59:00-05:00":
        print("PASS: DST-aware same-day 11:59 due-time (EDT/EST)")
    else:
        failures.append("dst")
        print(f"FAIL: DST derivation wrong: {summer!r} {winter!r}")

    # 3. Friday stays Friday (no next-school-day inference).
    friday = due_timestamp("2026-08-21", "America/New_York")
    if friday == "2026-08-21T23:59:00-04:00":
        print("PASS: Friday homework stays due Friday 11:59")
    else:
        failures.append("friday")
        print(f"FAIL: Friday moved: {friday!r}")

    # 4. Unresolved date fails closed.
    try:
        due_timestamp("", "America/New_York")
        failures.append("unresolved date")
        print("FAIL: blank assignment date produced a due time")
    except ValueError:
        print("PASS: unresolved assignment date blocks due-time generation")

    # 5. Publish policy remains unresolved (no implicit publication).
    if not p.publication_resolved():
        print("PASS: publish-state policy remains unresolved")
    else:
        failures.append("publish")
        print("FAIL: publish policy was implicitly resolved")

    # 6. Static write-safety scan: zero mutation tokens.
    pkg_dir = Path(__file__).resolve().parent
    for path in sorted(pkg_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in WRITE_MARKERS:
            if token in text:
                failures.append(f"write token in {path.name}: {token}")
                print(f"FAIL: mutation token {token!r} in {path.name}")

    # 7. Pure import graph does not load execution modules.
    try:
        import subprocess
        code = (
            "import sys; sys.path.insert(0, '.')\n"
            "from scripts.canvas_llm_phase18e.contracts import ExecutionPreconditionReport, WriterRequest\n"
            "from scripts.canvas_llm_phase18e.policy import default_policy, due_timestamp, policy_hash\n"
            "from scripts.canvas_llm_phase18e.preconditions import evaluate_preconditions\n"
            "from scripts.canvas_llm_phase18e.adapter import build_writer_requests\n"
            "forbidden = ['canvas' + '_writer', 'canvas' + '_connector', 'scripts.canvas_llm_phase22.phase22_workstation']\n"
            "import sys as _s\n"
            "loaded = [m for m in forbidden if m in _s.modules]\n"
            "assert not loaded, loaded\n"
            "print('OK')\n"
        )
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        if out.returncode == 0:
            print("PASS: pure Phase 18E import graph loads no execution modules")
        else:
            failures.append("import safety")
            print(f"FAIL: import safety: {out.stderr.strip()}")
    except Exception as exc:  # pragma: no cover
        failures.append("import safety")
        print(f"FAIL: import safety check error: {exc}")

    # 8. Write gate remains closed.
    try:
        from scripts.canvas_llm_phase22.write_gate import attempt_write, evaluate_write
        decision = evaluate_write("create", "page", "p-1", approved=True, approved_by="Teacher", approved_at="2026-07-25T00:00:00Z")
        if attempt_write(decision).gate_state == "BLOCKED":
            print("PASS: existing write gate remains closed")
        else:
            failures.append("write gate")
            print("FAIL: write gate unexpectedly open")
    except Exception as exc:  # pragma: no cover
        failures.append("write gate")
        print(f"FAIL: write gate check error: {exc}")

    if failures:
        print(f"Self-check failed: {failures}")
        return 1
    print("PASS: zero Canvas writes from Phase 18E")
    print("Self-check complete")
    return 0


def _build_example_packet():
    plan = build_example_plan()
    preview = assemble_teacher_preview(plan, RuntimeContext(canvas_config=CFG, due_time_policy="resolved"))
    context = DryRunContext(
        canvas_config=CFG,
        due_time_policy="resolved",
        resolved_due_time="23:59",
        publish_policy="resolved",
        resolved_publish_state="published",
    )
    snapshot = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty", objects=[])
    packet = assemble_dry_run_packet(preview, snapshot, context)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_phase18e", description="Owner policy + execution preconditions (Phase 18E)")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--example", action="store_true", help="print an example precondition report as JSON")
    parser.add_argument("--policy", action="store_true", help="print the canonical owner policy as JSON")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()
    if args.policy:
        print(json.dumps(default_policy().to_dict(), indent=2, sort_keys=True))
        return 0

    policy = default_policy()
    if args.example:
        packet = _build_example_packet()
        bindings = record_approval_bindings(packet=packet, policy=policy, canvas_config=CFG)
        payload = {
            "packet_hash": packet.packet_hash,
            "canonical_revision": packet.canonical_revision,
            "preview_hash": packet.preview_hash,
            "snapshot_hash": packet.snapshot_hash,
            "target_environment": packet.target_environment,
            "policy_hash": policy_hash(policy),
            "approval_bindings": bindings,
            "write_gate": "CLOSED",
            "max_readiness": ReadinessState.READY_FOR_EXECUTION_REVIEW.value,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"OwnerCanvasPolicy homework_due_time_local={policy.homework_due_time_local} publish_state={policy.publish_state}")
    print(f"policy_hash={policy_hash(policy)}")
    print("Write Gate: CLOSED")
    print(f"Max readiness: {ReadinessState.READY_FOR_EXECUTION_REVIEW.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
