"""bin/canvas-intake — Canvas Weekly Intake CLI (read-only, local-first).

Commands:
    run                  fetch + normalize + draft + questions (persists staging)
    review               print REVIEW.md (primary Owen-facing view)
    questions            list questions (OPEN default; --status answered|all)
    apply-teacher-input  answer a question / add reminder / reject assignment
    approve              approve a subject page/assignments/announcement
    status               PASS/WARN/FAIL status proof
    self-test            deterministic tests (synthetic only)

Resolution:
    --week current | next | N   (N is an explicit week number; requires --quarter)
    --quarter N

No Canvas writes. Publishing is a separate guarded deployment workflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import intake, manifest as mf
from . import week_resolution as wr


def _resolve(args: argparse.Namespace) -> tuple[int, int]:
    week_raw = getattr(args, "week", "next")
    if args.quarter is not None and isinstance(week_raw, str) and week_raw.isdigit():
        return args.quarter, int(week_raw)
    if args.quarter is not None and week_raw is not None and str(week_raw).isdigit():
        return args.quarter, int(week_raw)
    mode = week_raw if week_raw in ("current", "next") else "next"
    return wr.resolve(mode, quarter=args.quarter, week=None)


def cmd_run(args: argparse.Namespace) -> int:
    quarter, week = _resolve(args)
    from .canvas_readonly import CanvasReadOnly

    canvas = None
    if args.live_context:
        try:
            canvas = CanvasReadOnly.from_env()
        except Exception:  # noqa: BLE001 - live context is optional
            print("WARN: Canvas credentials unavailable; skipping page lookup / duplicate check")
            canvas = None
    summary = intake.build_intake(
        quarter=quarter,
        week=week,
        fresh=args.fresh,
        canvas=canvas,
        include_canvas_context=canvas is not None,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    quarter, week = _resolve(args)
    path = mf.staging_dir(quarter, week) / "REVIEW.md"
    if not path.exists():
        print(f"BLOCKED: no intake staged for Q{quarter}W{week}. Run `bin/canvas-intake run` first.")
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def cmd_questions(args: argparse.Namespace) -> int:
    quarter, week = _resolve(args)
    from . import questions as qs

    data = qs.load_questions(quarter, week)
    if args.status in ("answered", "all"):
        filtered = [q for q in data if q.get("status") != "OPEN"] if args.status == "answered" else data
    else:
        filtered = qs.unresolved_questions(data)
    if not filtered:
        print("No matching questions.")
        return 0
    for q in filtered:
        status = q.get("status", "OPEN")
        print(f"Q{q['question_id']} [{status}] ({q['subject']} · {q['date']}) {q['reason']}")
        print(f"    recommended: {q['recommended_default']}")
        if q.get("answer"):
            print(f"    answer: {q['answer']}")
    return 0


def cmd_apply_teacher_input(args: argparse.Namespace) -> int:
    quarter, week = _resolve(args)
    from . import teacher_input as ti
    from . import questions as qs

    if args.answer is not None:
        ti.answer_question(quarter, week, args.question_id, args.answer)
        print(f"Recorded answer for Q{args.question_id}.")
    if args.subject and args.op:
        if args.op in ("add_reminder", "add_note", "add_special_event", "add_assessment_note",
                       "remove_assignment", "reject_assignment", "restore_assignment",
                       "replace_announcement"):
            ti.apply_input(quarter=quarter, week=week, subject=args.subject, op=args.op, value=args.value)
            print(f"Applied {args.op} to {args.subject}.")
        else:
            print(f"BLOCKED: unknown op {args.op!r}")
            return 2
    # Regenerate drafts with input applied.
    intake.build_intake(quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False)
    print("Drafts regenerated deterministically.")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    quarter, week = _resolve(args)
    from . import approval as ap
    from . import constants as C

    # Rebuild (read-only, no Canvas) to obtain the CURRENT draft hashes, so
    # approval binds to exactly the artifact being reviewed.
    summary = intake.build_intake(quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False)
    active = summary["active_subjects"]
    if args.subject not in active:
        print(f"BLOCKED: subject {args.subject!r} not active for Q{quarter}W{week}")
        return 2

    targets = ["page", "assignments", "announcement"] if args.all else (
        [args.granularity] if args.granularity else []
    )
    if not targets:
        print("BLOCKED: specify --granularity or --all")
        return 2

    hashes = summary["draft_hashes"].get(args.subject, {})
    for g in targets:
        ap.set_state(quarter, week, args.subject, g, "APPROVED",
                     draft_hash=hashes.get(g, ""), subjects=active)

    # Recompute the gate now that approvals changed.
    intake.build_intake(quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False)
    print(f"Approved {args.subject} {', '.join(targets)}.")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    from .status import render_status

    status = render_status()
    print(status["text"])
    return 0 if status["ok"] else 1


def cmd_self_test(_args: argparse.Namespace) -> int:
    intake.command_self_test()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bin/canvas-intake", description="Canvas Weekly Intake (read-only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def _week_target(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--week", default="next", help="'current' | 'next' | explicit week number (with --quarter)")

    sp = sub.add_parser("run", help="fetch + normalize + draft + questions")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.add_argument("--fresh", action="store_true", default=True)
    sp.add_argument("--live-context", action="store_true", default=False,
                    help="GET-only page lookup + duplicate assignment check")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("review", help="print REVIEW.md")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("questions", help="list questions")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.add_argument("--status", choices=["open", "answered", "all"], default="open")
    sp.set_defaults(func=cmd_questions)

    sp = sub.add_parser("apply-teacher-input", help="record teacher input + regenerate")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.add_argument("--question-id", type=str, default=None)
    sp.add_argument("--answer", default=None)
    sp.add_argument("--subject", default=None)
    sp.add_argument("--op", default=None,
                    help="add_reminder|add_note|add_special_event|add_assessment_note|"
                         "reject_assignment|remove_assignment|restore_assignment|replace_announcement")
    sp.add_argument("--value", default="")
    sp.set_defaults(func=cmd_apply_teacher_input)

    sp = sub.add_parser("approve", help="approve a subject artifact")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.add_argument("--subject", required=True)
    sp.add_argument("--granularity", choices=["page", "assignments", "announcement"], default=None)
    sp.add_argument("--all", action="store_true", help="approve page+assignments+announcement")
    sp.set_defaults(func=cmd_approve)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("self-test").set_defaults(func=cmd_self_test)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
