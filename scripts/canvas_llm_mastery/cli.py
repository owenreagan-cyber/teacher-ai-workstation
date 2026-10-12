#!/usr/bin/env python3
"""Mastery tracker CLI: deterministic local mastery report (GET-only).

Modes:
- --preview          live GET-only scan -> teacher mastery report (never emails)
- --email-preview    render the exact email payload (preview only; never sends)
- --email-send --approve   send via existing approval-gated emailer (NOT run here)
- absence add/clear/list   local teacher absence overrides (no Canvas write)
- --self-test        deterministic tests using synthetic fixtures only

Read-only against Canvas. Never writes grades/assignments/submissions/pages/
announcements/conversations/enrollments. Email body prepared for preview only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import config, reader  # noqa: E402
from scripts.canvas_llm_grade_check.config import ConfigError  # noqa: E402
from scripts.canvas_llm_grade_check.reader import ReaderError  # noqa: E402
from scripts.canvas_llm_mastery import absence, counting, engine as mastery  # noqa: E402

STATE_DIR = REPO_ROOT / ".local" / "canvas-llm" / "mastery"


@dataclass
class MasteryReport:
    quarter: int
    assessment_rows: list[mastery.AssessmentMastery] = field(default_factory=list)
    manual_rows: list[mastery.ManualAssessmentResult] = field(default_factory=list)
    unresolved: list[dict[str, Any]] = field(default_factory=list)


def _group_name_by_id(groups: list[reader.AssignmentGroup]) -> dict[int, str]:
    return {g.id: g.name for g in groups}


def run_mastery_scan(
    grade_reader: reader.GradeReader,
    cfg: config.GradeCheckConfig,
    quarter: int,
    manual_results: list[mastery.ManualAssessmentResult] | None = None,
) -> MasteryReport:
    """Compute mastery for all active subjects. Side-effect free.

    Authoritative absence is read from the local override store
    (``absence_user_ids_for_assignment``); missing scores are never inferred
    as absence.
    """
    report = MasteryReport(quarter=quarter)
    report.manual_rows = list(manual_results or [])

    for subject in config.active_subjects(cfg, quarter):
        students = grade_reader.list_students(subject.course_id)
        assignments = grade_reader.list_assignments(subject.course_id)
        groups = grade_reader.list_assignment_groups(subject.course_id)
        submissions = grade_reader.list_submissions(subject.course_id)

        group_name_by_id = _group_name_by_id(groups)
        submissions_by_assignment: dict[int, list[reader.Submission]] = {}
        for s in submissions:
            submissions_by_assignment.setdefault(s.assignment_id, []).append(s)

        for assignment in assignments:
            group_name = group_name_by_id.get(assignment.assignment_group_id) if assignment.assignment_group_id is not None else None
            classification = mastery.classify_mastery_eligible(subject, group_name, assignment.name, cfg.test_title_keywords)
            if classification == "assessment":
                absence_user_ids = absence.absence_user_ids_for_assignment(assignment.id)
                rollup = mastery.evaluate_assessment_mastery(
                    subject=subject, assignment=assignment, group_name=group_name,
                    students=students, submissions=submissions_by_assignment.get(assignment.id, []),
                    absence_user_ids=absence_user_ids, keywords=cfg.test_title_keywords,
                )
                if rollup.total_expected > 0:
                    report.assessment_rows.append(rollup)
            elif classification == "unresolved" and any(
                s.assignment_id == assignment.id for s in submissions
            ):
                report.unresolved.append({
                    "course": subject.display_name, "course_id": subject.course_id,
                    "assignment": assignment.name, "group": group_name,
                    "reason": "ambiguous classification; no mastery determination",
                })

    return report


def render_report(report: MasteryReport) -> str:
    lines = ["Grade Check Summary", ""]

    lines.append("1. Assessment Mastery")
    for r in report.assessment_rows:
        rate = f"{r.mastery_rate}%" if r.mastery_rate is not None else "n/a"
        lines.append(f"{r.course_name} — {r.assessment_title}")
        lines.append(f"Confirmed mastery: {r.mastery_count}")
        lines.append(f"Provisional absence mastery: {r.provisional_absences}")
        lines.append(f"Total currently counted mastery: {r.mastery_count + r.provisional_absences}/{r.tested_or_provisional_denominator} ({rate})")
        lines.append(f"Non-mastery: {r.non_mastery_count}")
        lines.append(f"Missing grades: {r.missing_grades}")
        lines.append(f"Status: {r.status}")
        lines.append("")

    for m in report.manual_rows:
        rate = f"{m.mastery_rate}%" if m.mastery_rate is not None else "n/a"
        lines.append(f"{m.subject} — {m.assessment_title} (manual)")
        lines.append(f"Confirmed mastery: {m.mastered_count}/{m.tested_count} ({rate})")
        lines.append(f"Provisional absences: {m.provisional_absence_count}")
        lines.append(f"Status: CONFIRMED (source={m.source})")
        lines.append("")

    if report.unresolved:
        lines.append("7. Unresolved Classifications")
        for u in report.unresolved:
            lines.append(f"{u['course']} — {u['assignment']}: {u['reason']}")
        lines.append("")

    return "\n".join(lines)


def render_email_body(report: MasteryReport) -> str:
    """Exact teacher-only email body (sections 1-7). Preview only; no send."""
    lines = ["4A Grade Check - Student Flags", "", "Grade Check Summary", ""]
    lines.append("1. Assessment Mastery")
    for r in report.assessment_rows:
        rate = f"{r.mastery_rate}%" if r.mastery_rate is not None else "n/a"
        lines.append(f"{r.course_name} — {r.assessment_title}")
        lines.append(f"Confirmed mastery: {r.mastery_count}")
        lines.append(f"Provisional absence mastery: {r.provisional_absences}")
        lines.append(f"Total currently counted mastery: {r.mastery_count + r.provisional_absences}/{r.tested_or_provisional_denominator} ({rate})")
        lines.append(f"Missing grades: {r.missing_grades}")
        lines.append(f"Status: {r.status}")
        lines.append("")
    for m in report.manual_rows:
        lines.append(f"{m.subject} — {m.assessment_title} (manual)")
        lines.append(f"Confirmed mastery: {m.mastered_count}/{m.tested_count}")
        lines.append("")
    lines.append("2. Missing Assignments")
    lines.append("(reported by the grade-check flag engine; see bin/grade-check --preview)")
    lines.append("")
    lines.append("3. Assessment Scores 85 or Below")
    lines.append("(reported by the grade-check flag engine)")
    lines.append("")
    lines.append("4. Overall Course Average 85 or Below")
    lines.append("(reported by the grade-check flag engine)")
    lines.append("")
    lines.append("5. Missing Grades / Needs Update")
    lines.append("(see Assessment Mastery above)")
    lines.append("")
    lines.append("6. Provisional Absences")
    for r in report.assessment_rows:
        if r.provisional_absences > 0:
            lines.append(f"{r.course_name} — {r.assessment_title}: {r.provisional_absences}")
    if not any(r.provisional_absences > 0 for r in report.assessment_rows):
        lines.append("None")
    lines.append("")
    lines.append("7. Unresolved Classifications")
    if report.unresolved:
        for u in report.unresolved:
            lines.append(f"{u['course']} — {u['assignment']}: {u['reason']}")
    else:
        lines.append("None")
    return "\n".join(lines)


def _network_block(net: counting.NetworkSummary) -> str:
    d = net.as_dict()
    return (
        "Canvas network activity:\n"
        f"GET = {d['GET']}\n"
        f"errors = {d['errors']}\n"
        f"POST = {d['POST']}\n"
        f"PUT = {d['PUT']}\n"
        f"PATCH = {d['PATCH']}\n"
        f"DELETE = {d['DELETE']}"
    )


def command_preview(cfg: config.GradeCheckConfig, quarter: int) -> int:
    inner = reader.LiveGradeReader.from_env()
    grade_reader = counting.CountingReader(inner)
    manual = [mastery.ManualAssessmentResult(
        subject="Language Arts", assessment_title="Shurley Chapter 5 Test",
        date="2026-10-01", mastered_count=20, tested_count=20,
    )]
    report = run_mastery_scan(grade_reader, cfg, quarter, manual)
    print(render_report(report))
    print("")
    print(_network_block(grade_reader.network))
    print("EMAILS SENT: 0")

    # Persist local summary + email preview (gitignored).
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "quarter": f"Q{quarter}",
        "assessment_rows": [
            {
                "course": r.course_name, "course_id": r.course_id,
                "title": r.assessment_title, "group": r.assessment_group,
                "total_expected": r.total_expected, "scores_present": r.scores_present,
                "confirmed_mastery": r.mastery_count, "non_mastery": r.non_mastery_count,
                "provisional_mastery": r.provisional_absences, "missing": r.missing_grades,
                "mastery_rate": r.mastery_rate, "status": r.status,
            }
            for r in report.assessment_rows
        ],
        "manual_rows": [m.to_dict() for m in report.manual_rows],
        "unresolved": report.unresolved,
        "network": grade_reader.network.as_dict(),
    }
    (STATE_DIR / "latest-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (STATE_DIR / "grade-check.txt").write_text(render_report(report) + "\n", encoding="utf-8")
    (STATE_DIR / "grade-check.html").write_text("<pre>" + render_email_body(report).replace("&", "&amp;").replace("<", "&lt;") + "</pre>\n", encoding="utf-8")
    return 0


def command_email_preview(cfg: config.GradeCheckConfig, quarter: int) -> int:
    inner = reader.LiveGradeReader.from_env()
    grade_reader = counting.CountingReader(inner)
    manual = [mastery.ManualAssessmentResult(
        subject="Language Arts", assessment_title="Shurley Chapter 5 Test",
        date="2026-10-01", mastered_count=20, tested_count=20,
    )]
    report = run_mastery_scan(grade_reader, cfg, quarter, manual)
    print("=== EMAIL PREVIEW (NOT SENT) ===")
    print(f"Recipient: owen.reagan@thalesacademy.org")
    print(f"Subject: 4A Grade Check - Student Flags")
    print("")
    print(render_email_body(report))
    print("")
    print(_network_block(grade_reader.network))
    print("EMAILS SENT: 0")
    return 0


def command_email_send(cfg: config.GradeCheckConfig, quarter: int) -> int:
    """Send via the existing approval-gated emailer. Refuses unless approved."""
    from scripts.canvas_llm_grade_check import emailer

    if not emailer.send_approved():
        print("BLOCKER: email send not approved (CANVAS_LLM_GRADE_CHECK_SEND_APPROVED not set).")
        print("EMAILS SENT: 0")
        return 1
    inner = reader.LiveGradeReader.from_env()
    grade_reader = counting.CountingReader(inner)
    manual = [mastery.ManualAssessmentResult(
        subject="Language Arts", assessment_title="Shurley Chapter 5 Test",
        date="2026-10-01", mastered_count=20, tested_count=20,
    )]
    report = run_mastery_scan(grade_reader, cfg, quarter, manual)
    body = render_email_body(report)
    result = emailer.send_teacher_report(subject="4A Grade Check - Student Flags", body=body, recipient="owen.reagan@thalesacademy.org")
    print(f"EMAILS SENT: {1 if result.sent else 0}")
    if not result.sent:
        print(f"EMAIL BLOCKER: {result.reason}")
        return 1
    print(f"SENT to: {result.recipients}")
    print(_network_block(grade_reader.network))
    return 0


def command_absence(args: argparse.Namespace) -> int:
    if args.absence_action == "add":
        rec = absence.add_absence(
            course_id=args.course_id, student_id=args.student_id,
            assignment_id=args.assignment_id, effective_date=args.date,
            notes=args.notes or "",
        )
        print(json.dumps(rec, indent=2))
    elif args.absence_action == "clear":
        res = absence.clear_absence(
            course_id=args.course_id, student_id=args.student_id,
            assignment_id=args.assignment_id,
        )
        print(json.dumps(res, indent=2))
    elif args.absence_action == "list":
        rows = absence.list_absences()
        if not rows:
            print("No active absence overrides.")
        for r in rows:
            print(f"{r['course_id']}:{r['student_id']}:{r['assignment_id']} "
                  f"{r['status']} (since {r['effective_date']})")
    else:
        print("BLOCKER: unknown absence action")
        return 1
    print("CANVAS WRITES PERFORMED: 0")
    return 0


def command_self_test() -> int:
    config.command_self_test()
    reader.command_self_test()
    mastery.command_self_test()
    absence.command_self_test()
    counting.command_self_test()

    class Synthetic(reader.GradeReader):
        def list_students(self, course_id):
            return [reader.Student(user_id=i, name=f"S{i}", current_score=90) for i in range(1, 5)]
        def list_assignments(self, course_id):
            return [reader.Assignment(id=1, name="Written Assessment 6", assignment_group_id=10, due_at="2026-10-20T03:59:00Z")]
        def list_assignment_groups(self, course_id):
            return [reader.AssignmentGroup(id=10, name="Written Assessments")]
        def list_submissions(self, course_id):
            return [
                reader.Submission(id=1, user_id=1, assignment_id=1, score=92),
                reader.Submission(id=2, user_id=2, assignment_id=1, score=70),
                reader.Submission(id=3, user_id=3, assignment_id=1, score=86),
                reader.Submission(id=4, user_id=4, assignment_id=1, score=None, grade=""),
            ]

    cfg = config.load_config()
    rep = run_mastery_scan(Synthetic(), cfg, 1, manual_results=[mastery.ManualAssessmentResult(
        "Language Arts", "Shurley Chapter 5 Test", "2026-10-01", 20, 20)])
    assert len(rep.assessment_rows) >= 1
    math_row = next((r for r in rep.assessment_rows if r.assessment_title == "Written Assessment 6"), None)
    assert math_row is not None
    assert math_row.mastery_count == 2 and math_row.non_mastery_count == 1 and math_row.missing_grades == 1

    # Email body contains all 7 sections + teacher-only header.
    body = render_email_body(rep)
    assert "4A Grade Check - Student Flags" in body
    for s in ("1. Assessment Mastery", "2. Missing Assignments", "3. Assessment Scores 85 or Below",
              "4. Overall Course Average 85 or Below", "5. Missing Grades / Needs Update",
              "6. Provisional Absences", "7. Unresolved Classifications"):
        assert s in body, s

    print("PASS mastery CLI self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assessment Mastery Tracker (read-only)")
    parser.add_argument("--preview", action="store_true", help="live GET-only mastery scan + report (no email)")
    parser.add_argument("--email-preview", action="store_true", help="render exact email payload (no send)")
    parser.add_argument("--email-send", action="store_true", help="send via approval-gated emailer (not run here)")
    parser.add_argument("--approve", action="store_true", help="explicit send approval flag (with --email-send)")
    parser.add_argument("--quarter", type=int, help="explicit quarter (1-4); auto-detected otherwise")
    parser.add_argument("--self-test", action="store_true", help="run deterministic self-tests")

    sub = parser.add_subparsers(dest="cmd")
    absence_p = sub.add_parser("absence", help="local teacher absence overrides")
    absence_p.add_argument("absence_action", choices=["add", "clear", "list"])
    absence_p.add_argument("--course-id", type=int)
    absence_p.add_argument("--student-id", type=int)
    absence_p.add_argument("--assignment-id", type=int)
    absence_p.add_argument("--date")
    absence_p.add_argument("--notes", default="")
    absence_p.set_defaults(func=command_absence)

    args = parser.parse_args(argv)

    if args.self_test:
        return command_self_test()
    if args.cmd == "absence":
        return command_absence(args)

    try:
        cfg = config.load_config()
        quarter = config.resolve_quarter(explicit_quarter=args.quarter)
    except ConfigError as exc:
        print(f"BLOCKER: {exc}")
        return 1

    try:
        if args.email_preview:
            return command_email_preview(cfg, quarter)
        if args.email_send:
            if not args.approve:
                print("BLOCKER: --email-send requires --approve (explicit approval).")
                print("EMAILS SENT: 0")
                return 1
            return command_email_send(cfg, quarter)
        return command_preview(cfg, quarter)
    except ReaderError as exc:
        print(f"BLOCKER: {exc}")
        print("CANVAS WRITES PERFORMED: 0")
        print("EMAILS SENT: 0")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
