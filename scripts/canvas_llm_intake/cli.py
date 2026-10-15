"""bin/canvas-intake — Canvas Weekly Intake CLI (read-only, local-first).

Commands:
    run           fetch + normalize + draft + questions (persists staging packet)
    review        print REVIEW.md for the target week
    questions     list open questions
    status        PASS/WARN/FAIL status proof
    self-test     deterministic tests (synthetic only)

Resolution:
    --week current | next     (America/New_York)
    --quarter N --week N      (explicit integer week; deterministic)

No Canvas writes. Publishing is a separate guarded deployment workflow.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

from . import intake, manifest as mf
from . import week_resolution as wr


def _resolve(args: argparse.Namespace) -> tuple[int, int]:
    if args.quarter is not None and args.week is not None:
        # `--week` may be an int here (explicit week number) — argparse stores
        # it as str; try int, else treat as current/next choice.
        if isinstance(args.week, int) or str(args.week).isdigit():
            return args.quarter, int(args.week)
    return wr.resolve(args.week if isinstance(args.week, str) else "next",
                      quarter=args.quarter, week=None)


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
    import json

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
    path = mf.staging_dir(quarter, week) / "questions" / "questions.json"
    if not path.exists():
        print("No open questions.")
        return 0
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    for q in data:
        print(f"Q{q['question_id']} [{q['subject']} · {q['date']}] {q['reason']}")
        print(f"    recommended: {q['recommended_default']}")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    from .status import render_status

    status = render_status()
    print(status["text"])
    return 0 if status["ok"] else 1


def cmd_self_test(_args: argparse.Namespace) -> int:
    from . import week_resolution, canvas_readonly, questions, manifest, intake

    week_resolution.command_self_test()
    canvas_readonly.command_self_test()
    questions.command_self_test()
    manifest.command_self_test()
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

    sp = sub.add_parser("questions", help="list open questions")
    _week_target(sp)
    sp.add_argument("--quarter", type=int, default=None)
    sp.set_defaults(func=cmd_questions)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("self-test").set_defaults(func=cmd_self_test)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
