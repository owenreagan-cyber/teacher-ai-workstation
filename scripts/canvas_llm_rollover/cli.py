"""Manual fallback command for the Friday weekly rollover.

Usage:
    bin/canvas-weekly-rollover --from q2w2 --to q2w3 --preflight
    bin/canvas-weekly-rollover --week q2w3 --dry-run
    bin/canvas-weekly-rollover --dry-run --live-readonly
    bin/canvas-weekly-rollover --week q2w3 --execute --production \
        --confirm "ROLLOVER Q2W3"

Manual execution uses the SAME engine as scheduled execution — there is no
second code path. ``--dry-run``/``--preflight`` perform zero Canvas writes.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from scripts.canvas_llm_rollover import manifest as rollover_manifest
from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_rollover import schedule


def _parse_week(token: str) -> tuple[int, int]:
    token = token.lower().replace(" ", "")
    token = token.removeprefix("q")
    q, w = token.split("w")
    return int(q), int(w)


def _resolve(from_tok: str | None, to_tok: str | None, week_tok: str | None):
    if week_tok:
        to_q, to_w = _parse_week(week_tok)
        # from week = the instructional week immediately before to week.
        from scripts.canvas_llm_intake import week_resolution as wr
        weeks = sorted(
            (w for w in wr.load_weeks() if wr._week_start(w) is not None),
            key=lambda w: wr._week_start(w),
        )
        to_code = wr.week_code_for(to_q, to_w)
        idx = next(i for i, w in enumerate(weeks) if w.get("code") == to_code)
        if idx == 0:
            raise SystemExit(f"no prior week for {to_code}")
        prev = weeks[idx - 1]
        return int(prev["quarter"]), int(prev["week"]), to_q, to_w
    if from_tok and to_tok:
        fq, fw = _parse_week(from_tok)
        tq, tw = _parse_week(to_tok)
        return fq, fw, tq, tw
    from scripts.canvas_llm_intake import week_resolution as wr
    tq, tw = wr.next_week()
    return _resolve(None, None, wr.week_code_for(tq, tw))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas-weekly-rollover")
    parser.add_argument("--from", dest="from_week", help="from week (e.g. q2w2)")
    parser.add_argument("--to", dest="to_week", help="to week (e.g. q2w3)")
    parser.add_argument("--week", help="target upcoming week (e.g. q2w3)")
    parser.add_argument("--preflight", action="store_true", help="GET-only readiness + plan")
    parser.add_argument("--dry-run", action="store_true", help="deterministic plan only (no Canvas)")
    parser.add_argument("--live-readonly", action="store_true",
                        help="with --dry-run, use Canvas GETs to classify every planned write")
    parser.add_argument("--execute", action="store_true", help="execute the rollover")
    parser.add_argument("--production", action="store_true", help="use live Canvas")
    parser.add_argument("--confirm", help="owner confirmation 'ROLLOVER Q2W3'")
    parser.add_argument("--scheduled", action="store_true",
                        help="run the single Friday 1 PM/4 PM LaunchAgent action")
    args = parser.parse_args(argv)

    if args.live_readonly and not args.dry_run:
        parser.error("--live-readonly requires --dry-run")

    if args.scheduled:
        from scripts.canvas_planner.friday import scheduled_run
        result = scheduled_run()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        action = result.get("action")
        return 0 if action in ("REMINDER", "ROLLOVER", "ROLLOVER_DISABLED", "NOOP") else 2

    fq, fw, tq, tw = _resolve(args.from_week, args.to_week, args.week)

    if args.dry_run:
        if args.live_readonly:
            from scripts.canvas_llm_deploy.client import LiveDeployClient
            rec = rollover.run_preflight(fq, fw, tq, tw, LiveDeployClient())
            view = _dry_run_view(rec["manifest"])
            view.update({
                "MODE": "LIVE_READONLY",
                "READY": rec["ready"],
                "BLOCKERS": rec["blockers"],
                "WARNINGS": rec["warnings"],
                "CANVAS_WRITES_PERFORMED": rec["canvas_writes"],
            })
            print(json.dumps(view, indent=2, ensure_ascii=False))
            return 0 if rec["ready"] else 2
        plan = rollover_manifest.build_rollover_manifest(fq, fw, tq, tw)
        print(json.dumps(_dry_run_view(plan), indent=2, ensure_ascii=False))
        return 0

    if args.preflight:
        client = None
        if args.production:
            from scripts.canvas_llm_deploy.client import LiveDeployClient
            client = LiveDeployClient()
        rec = rollover.run_preflight(fq, fw, tq, tw, client)
        print(json.dumps(_dry_run_view(rec["manifest"]), indent=2, ensure_ascii=False))
        print("READY:", rec["ready"])
        if rec["blockers"]:
            print("BLOCKERS:")
            for b in rec["blockers"]:
                print(f"  - {b}")
        return 0 if rec["ready"] else 2

    if args.execute:
        if not args.production:
            print("BLOCKED: execute requires --production (use --dry-run/--preflight to preview)")
            return 2
        try:
            from scripts.canvas_llm_deploy.client import LiveDeployClient
            client = LiveDeployClient()
        except Exception as exc:  # noqa: BLE001
            print(f"BLOCKED: Canvas transport unavailable: {type(exc).__name__}")
            return 2
        try:
            report = rollover.publish_weekly_package(
                fq, fw, tq, tw, client=client, owner_confirmation=args.confirm or "")
        except rollover.RolloverBlocked as exc:
            print(f"BLOCKED: {exc}")
            return 2
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report.get("lifecycle") == schedule.PUBLISHED_VERIFIED else 1

    # Default: show status.
    s = rollover.status(fq, fw, tq, tw)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def _dry_run_view(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "PYTHON_EXECUTABLE": sys.executable,
        "PYTHON_VERSION": sys.version.split()[0],
        "FROM": plan.get("from_week"),
        "TO": plan.get("to_week"),
        "SCHEDULED": plan.get("scheduled_at"),
        "TIMEZONE": plan.get("timezone"),
        "ACADEMIC_HOMEPAGES": [
            {"subject": c["subject"], "course_id": c["course_id"],
             "page_slug": c["to_page_slug"], "page_body_action": c.get("page_body_action", "UPDATE"),
             "front_page_action": c["front_page_action"]}
            for c in plan.get("academic_courses", [])
        ],
        "HOMEROOM": {
            "course_id": plan["homeroom"]["course_id"],
            "page_slug": plan["homeroom"]["to_page_slug"],
            "action": plan["homeroom"]["front_page_action"],
            "page_body_action": plan["homeroom"].get("page_body_action", "UPDATE"),
            "proposed_content_hash": plan["homeroom"]["proposed_content_hash"],
        },
        "WEEKLY_UPDATES": [
            {"subject": a["subject"], "title": a["title"],
             "delayed_post_at": a["delayed_post_at"], "agenda_hash": a["agenda_hash"],
             "action": a.get("action", "CREATE"), "classification": a.get("classification", "NOT_CHECKED")}
            for a in plan.get("weekly_announcements", [])
        ],
        "ASSIGNMENTS": [
            {"course": a.get("course"), "course_id": a.get("course_id"), "title": a.get("title"),
             "action": a.get("action", "CREATE"), "classification": a.get("classification", "NOT_CHECKED")}
            for a in plan.get("assignments", [])
        ],
        "ASSESSMENT_REMINDERS": [
            {"subject": a.get("subject"), "course_id": a.get("course_id"), "title": a.get("title"),
             "action": a.get("action", "CREATE"), "classification": a.get("classification", "NOT_CHECKED")}
            for a in plan.get("assessment_reminders", [])
        ],
        "WRITES_IF_EXECUTED": {
            "front_page_put": sum(c.get("front_page_action") != "SKIP" for c in plan.get("academic_courses", []))
                + int(plan.get("homeroom", {}).get("front_page_action") != "SKIP"),
            "page_update_put": sum(c.get("page_body_action", "UPDATE") != "SKIP" for c in plan.get("academic_courses", []))
                + int(plan.get("homeroom", {}).get("page_body_action", "UPDATE") != "SKIP"),
            "assignment_post": sum(a.get("action", "CREATE") != "SKIP" for a in plan.get("assignments", [])),
            "announcement_post": sum(a.get("action", "CREATE") != "SKIP" for a in plan.get("weekly_announcements", [])),
            "reminder_post": sum(a.get("action", "CREATE") != "SKIP" for a in plan.get("assessment_reminders", [])),
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
