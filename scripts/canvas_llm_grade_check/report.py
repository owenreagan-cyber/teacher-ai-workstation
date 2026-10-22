#!/usr/bin/env python3
"""Teacher report and email composition (no side effects, no sending)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.canvas_llm_grade_check import engine, templates
from scripts.canvas_llm_grade_check.engine import Flag, UnresolvedItem

NEW = "NEW"
STILL_ACTIVE = "STILL ACTIVE"
RESOLVED = "RESOLVED"


@dataclass
class ReportEntry:
    flag: Flag
    status: str


@dataclass
class CourseScanSummary:
    name: str
    course_id: int
    students_scanned: int
    average_source: str | None = None


QUARTER_SCOPE = "quarter"
YEAR_SCOPE = "year"


@dataclass
class ScanOutcome:
    quarter: int
    courses: list[CourseScanSummary] = field(default_factory=list)
    missing: list[ReportEntry] = field(default_factory=list)
    low_assessment: list[ReportEntry] = field(default_factory=list)
    low_average: list[ReportEntry] = field(default_factory=list)
    resolved: list[Flag] = field(default_factory=list)
    out_of_scope: list[Flag] = field(default_factory=list)
    not_eligible: list[Flag] = field(default_factory=list)
    unresolved: list[UnresolvedItem] = field(default_factory=list)
    # GC-1 report scope. ``scope_label`` is the header text ("Quarter 2 ·
    # October 12 – December 18, 2026" or "Full year"); None omits the line.
    scope: str = YEAR_SCOPE
    scope_label: str | None = None
    skipped_assignments: int = 0  # due outside the quarter (quarter scope)
    no_due_date: int = 0  # no due date, left out of quarter scope
    inactive_courses: int = 0  # configured courses not active this quarter

    @property
    def is_quarter_scope(self) -> bool:
        return self.scope == QUARTER_SCOPE

    @property
    def skipped_out_of_scope(self) -> int:
        """Items skipped as out of scope: assignments outside the quarter plus
        earlier flags held (not resolved) because they fall outside it."""
        return self.skipped_assignments + len(self.out_of_scope)

    @property
    def total_students(self) -> int:
        return sum(c.students_scanned for c in self.courses)

    @property
    def has_any_flag(self) -> bool:
        return bool(self.missing or self.low_assessment or self.low_average)

    @property
    def has_change(self) -> bool:
        """True when there is at least one NEW or RESOLVED flag.

        Unchanged STILL ACTIVE persistent flags alone are NOT a change. This is
        the scheduler's "email only on meaningful change" gate; it does not
        alter detection, thresholds, or persistence. Out-of-scope suspension is
        NOT a change (it is a quarter rotation, not new information).
        """
        if self.resolved:
            return True
        # New one-time assessment alerts are always NEW by construction.
        if self.low_assessment:
            return True
        return any(
            e.status == NEW for e in (*self.missing, *self.low_average)
        )


def _entry_block(entry: ReportEntry) -> str:
    f = entry.flag
    lines: list[str] = []
    lines.append(f"Student: {f.student_name}")
    lines.append(f"Course: {f.course_name}")
    if f.flag_type in (engine.MISSING_ASSIGNMENT, engine.LOW_ASSESSMENT_SCORE):
        lines.append(f"Assignment: {f.assignment_title or '(unknown)'}")
    if f.flag_type == engine.MISSING_ASSIGNMENT:
        lines.append(f"Status: {f.raw_status or 'missing'}")
        lines.append("Flag: MISSING ASSIGNMENT")
        lines.append(f"Type: {_missing_type_label(f.classification)}")
        lines.append("Behavior: PERSISTENT")
    elif f.flag_type == engine.LOW_ASSESSMENT_SCORE:
        lines.append(f"Score: {templates.format_score(f.score) or f.raw_status or ''}")
        lines.append("Flag: ASSESSMENT 85 OR BELOW")
        lines.append("Behavior: ONE-TIME")
    elif f.flag_type == engine.LOW_COURSE_AVERAGE:
        lines.append(f"Average: {templates.format_score(f.average) or ''}")
        lines.append("Flag: OVERALL AVERAGE 85 OR BELOW")
        lines.append("Behavior: PERSISTENT")
    lines.append(f"State: {entry.status}")
    if entry.status in (NEW, STILL_ACTIVE):
        message = templates.parent_message_for(f)
        if message:
            lines.append("")
            lines.append("COPY/PASTE PARENT MESSAGE:")
            lines.append("-" * 40)
            lines.append(message)
            lines.append("-" * 40)
    return "\n".join(lines)


def _flag_items(entries: list[ReportEntry]) -> str:
    if not entries:
        return "None"
    return "\n\n".join(_entry_block(e) for e in entries)


def _short_due(due_at: str | None) -> str:
    if not due_at:
        return "(no due date)"
    # ISO timestamps like 2026-09-08T23:59:00Z -> date only.
    return due_at[:10] if len(due_at) >= 10 else due_at


def _missing_type_label(classification: str | None) -> str:
    if classification == engine.ASSESSMENT:
        return "test/assessment/checkout"
    if classification == engine.NON_ASSESSMENT:
        return "homework/classwork"
    return "unresolved (neutral)"


def grouped_assessment_review(
    outcome: ScanOutcome,
) -> list[tuple[str, str, str | None, int]]:
    """Group low-assessment flags by (course, assessment, due date) with counts."""
    counts: dict[tuple[str, str, str | None], int] = {}
    for entry in outcome.low_assessment:
        f = entry.flag
        key = (f.course_name, f.assignment_title or "(unknown)", f.assignment_due_at)
        counts[key] = counts.get(key, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or ""))
    return [(k[0], k[1], k[2], v) for k, v in ordered]


def grouped_unresolved_review(
    outcome: ScanOutcome,
) -> list[tuple[str, str, str | None, int]]:
    """Group unresolved low-score items by (course, title, assignment group)."""
    counts: dict[tuple[str, str, str | None], int] = {}
    for u in outcome.unresolved:
        key = (u.course_name, u.assignment_title, u.assignment_group)
        counts[key] = counts.get(key, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or ""))
    return [(k[0], k[1], k[2], v) for k, v in ordered]


def _missing_status_label(raw: str | None) -> str:
    """Compact status label for a missing item (Canvas returns e.g. ``MI``)."""
    text = (raw or "").strip()
    if not text or text.lower() in {"mi", "m", "missing", "missing assignment"}:
        return "missing"
    return text


def _count_status(entries: list[ReportEntry], status: str) -> int:
    return sum(1 for e in entries if e.status == status)


def _resolved_of_type(outcome: ScanOutcome, flag_type: str) -> list[Flag]:
    return [f for f in outcome.resolved if f.flag_type == flag_type]


def _compact_missing_line(entry: ReportEntry) -> str:
    f = entry.flag
    return (
        f"[{entry.status}] {f.student_name} | {f.course_name} | "
        f"{f.assignment_title or '(unknown)'} | {_missing_status_label(f.raw_status)}"
    )


def _compact_assessment_line(entry: ReportEntry) -> str:
    f = entry.flag
    score = templates.format_score(f.score) or (f.raw_status or "")
    return (
        f"[{entry.status}] {f.student_name} | {f.course_name} | "
        f"{f.assignment_title or '(unknown)'} | {score}"
    )


def _compact_average_line(entry: ReportEntry) -> str:
    f = entry.flag
    line = (
        f"[{entry.status}] {f.student_name} | {f.course_name} | "
        f"{templates.format_score(f.average) or ''}"
    )
    if f.average_source:
        line += f" | {f.average_source}"
    return line


def _header_lines(outcome: ScanOutcome) -> list[str]:
    """Scope, quarter, courses, and (when known) each course's average source."""
    lines: list[str] = []
    if outcome.scope_label:
        lines.append(f"Scope: {outcome.scope_label}")
    lines.append(f"Quarter: Q{outcome.quarter}")
    if outcome.courses:
        lines.append("Courses scanned: " + ", ".join(c.name for c in outcome.courses))
    else:
        lines.append("Courses scanned: None")
    sources = [c for c in outcome.courses if c.average_source]
    if sources:
        lines.append(
            "Course averages: "
            + "; ".join(f"{c.name} — {c.average_source}" for c in sources)
        )
    lines.append(f"Students scanned: {outcome.total_students}")
    return lines


def _scope_footer_lines(outcome: ScanOutcome) -> list[str]:
    """Quarter scope only: the no-due-date note and the one out-of-scope line."""
    if not outcome.is_quarter_scope:
        return []
    lines = [
        f"No due date: {outcome.no_due_date} assignments left out of quarter scope.",
        f"Skipped as out of scope: {outcome.skipped_out_of_scope} items "
        f"({outcome.skipped_assignments} assignments due outside the quarter, "
        f"{len(outcome.out_of_scope)} earlier flags held — not resolved; "
        f"{outcome.inactive_courses} courses not active this quarter).",
    ]
    return lines


def _resolved_line(f: Flag) -> str:
    return (
        f"  - {f.student_name} | {f.course_name} | {f.flag_type} | "
        f"{f.assignment_title or 'course average'}"
    )


def _summary_count_lines(outcome: ScanOutcome) -> list[str]:
    lines = [
        "Summary counts",
        f"NEW missing: {_count_status(outcome.missing, NEW)}",
        f"STILL ACTIVE missing: {_count_status(outcome.missing, STILL_ACTIVE)}",
        f"RESOLVED missing: {len(_resolved_of_type(outcome, engine.MISSING_ASSIGNMENT))}",
        f"NEW assessment <=85: {len(outcome.low_assessment)}",
        f"STILL ACTIVE low averages: {_count_status(outcome.low_average, STILL_ACTIVE)}",
        f"RESOLVED low averages: {len(_resolved_of_type(outcome, engine.LOW_COURSE_AVERAGE))}",
    ]
    # Quarter scope reports out-of-scope items once, in the footer line.
    if not outcome.is_quarter_scope:
        lines.append(f"OUT OF SCOPE (quarter rotation): {len(outcome.out_of_scope)}")
    lines += [
        f"NOT ELIGIBLE (late enrollment / no grades): {len(outcome.not_eligible)}",
        f"Unresolved low-score items: {len(outcome.unresolved)}",
    ]
    return lines


def _compact_flag_lines(entries: list[ReportEntry], render_line) -> str:
    if not entries:
        return "None"
    return "\n".join(render_line(e) for e in entries)


def _resolved_section_lines(outcome: ScanOutcome) -> list[str]:
    lines: list[str] = []
    lines.append("--- RESOLVED PERSISTENT FLAGS SINCE LAST SCAN ---")
    if outcome.resolved:
        for f in outcome.resolved:
            lines.append(_resolved_line(f))
    else:
        lines.append("None")
    return lines


def _out_of_scope_line(f: Flag) -> str:
    return (
        f"  - {f.student_name} | {f.course_name} | {f.flag_type} | "
        f"{f.assignment_title or 'course average'} | (course out of quarter scope — NOT resolved)"
    )


def _out_of_scope_section_lines(outcome: ScanOutcome) -> list[str]:
    lines: list[str] = []
    lines.append("--- OUT OF SCOPE (QUARTER ROTATION — NOT RESOLVED) ---")
    if outcome.out_of_scope:
        for f in outcome.out_of_scope:
            lines.append(_out_of_scope_line(f))
    else:
        lines.append("None")
    return lines


def _not_eligible_line(f: Flag) -> str:
    return (
        f"  - {f.student_name} | {f.course_name} | {f.flag_type} | "
        f"{f.assignment_title or 'course average'} | (student not eligible — NOT resolved)"
    )


def _not_eligible_section_lines(outcome: ScanOutcome) -> list[str]:
    lines: list[str] = []
    lines.append("--- NOT ELIGIBLE (LATE ENROLLMENT / NO GRADES — NOT RESOLVED) ---")
    if outcome.not_eligible:
        for f in outcome.not_eligible:
            lines.append(_not_eligible_line(f))
    else:
        lines.append("None")
    return lines


def _grouped_unresolved_lines(outcome: ScanOutcome) -> list[str]:
    lines: list[str] = []
    lines.append("--- UNRESOLVED LOW-SCORE ITEMS (grouped) ---")
    groups = grouped_unresolved_review(outcome)
    if groups:
        for course, title, group, count in groups:
            lines.append(f"[{course}] {title} | {group or '(none)'} | {count} students")
    else:
        lines.append("None")
    return lines


def render_preview(
    outcome: ScanOutcome, *, writes: int = 0, emails: int = 0, details: bool = False
) -> str:
    """Routine teacher preview.

    Default mode is compact: one line per active item, grouped unresolved items,
    and no inline parent templates. ``details=True`` expands to full flag
    metadata plus copy/paste parent templates and per-student unresolved items.
    """
    if details:
        return render_preview_detailed(outcome, writes=writes, emails=emails)
    return render_preview_compact(outcome, writes=writes, emails=emails)


def render_preview_compact(outcome: ScanOutcome, *, writes: int = 0, emails: int = 0) -> str:
    """Concise routine preview for daily teacher review."""
    lines: list[str] = []
    lines.append("=== 4A GRADE CHECK — TEACHER REVIEW ===")
    lines.extend(_header_lines(outcome))
    lines.append("")
    lines.extend(_summary_count_lines(outcome))

    lines.append("")
    lines.append("--- MISSING ASSIGNMENTS ---")
    lines.append(_compact_flag_lines(outcome.missing, _compact_missing_line))

    lines.append("")
    lines.append("--- ASSESSMENT SCORES 85 OR BELOW (NEW) ---")
    lines.append(_compact_flag_lines(outcome.low_assessment, _compact_assessment_line))

    lines.append("")
    lines.append("--- OVERALL COURSE AVERAGES 85 OR BELOW ---")
    lines.append(_compact_flag_lines(outcome.low_average, _compact_average_line))

    lines.append("")
    lines.extend(_resolved_section_lines(outcome))

    if not outcome.is_quarter_scope:
        lines.append("")
        lines.extend(_out_of_scope_section_lines(outcome))

    lines.append("")
    lines.extend(_not_eligible_section_lines(outcome))

    lines.append("")
    lines.extend(_grouped_unresolved_lines(outcome))

    if outcome.is_quarter_scope:
        lines.append("")
        lines.extend(_scope_footer_lines(outcome))

    lines.append("")
    lines.append(f"CANVAS WRITES PERFORMED: {writes}")
    lines.append(f"EMAILS SENT: {emails}")
    return "\n".join(lines)


def render_preview_detailed(outcome: ScanOutcome, *, writes: int = 0, emails: int = 0) -> str:
    """Expanded preview: full flag metadata, parent templates, per-student detail."""
    lines: list[str] = []
    lines.append("=== 4A GRADE CHECK — TEACHER REVIEW (DETAILED) ===")
    lines.extend(_header_lines(outcome))
    lines.append("")
    lines.extend(_summary_count_lines(outcome))

    lines.append("")
    lines.append("--- MISSING ASSIGNMENTS (active) ---")
    lines.append(_flag_items(outcome.missing))

    lines.append("")
    lines.append("--- ASSESSMENT SCORES 85 OR BELOW (new) ---")
    lines.append(_flag_items(outcome.low_assessment))

    lines.append("")
    lines.append("--- OVERALL COURSE AVERAGES 85 OR BELOW (active) ---")
    lines.append(_flag_items(outcome.low_average))

    lines.append("")
    lines.append("--- ASSESSMENT <=85 GROUPED REVIEW ---")
    assessment_groups = grouped_assessment_review(outcome)
    if assessment_groups:
        for course, title, due, count in assessment_groups:
            lines.append(f"[{course}] {title} (due {_short_due(due)}) — {count} students")
    else:
        lines.append("None")

    lines.append("")
    lines.extend(_resolved_section_lines(outcome))

    if not outcome.is_quarter_scope:
        lines.append("")
        lines.extend(_out_of_scope_section_lines(outcome))

    lines.append("")
    lines.extend(_not_eligible_section_lines(outcome))

    lines.append("")
    lines.extend(_grouped_unresolved_lines(outcome))

    lines.append("")
    lines.append("--- UNRESOLVED LOW-SCORE ITEMS (individual students) ---")
    if outcome.unresolved:
        for u in outcome.unresolved:
            lines.append(
                f"  - {u.student_name} | {u.course_name} | {u.assignment_title} | "
                f"{u.assignment_group or '(none)'} | {u.reason}"
            )
    else:
        lines.append("None")

    if outcome.is_quarter_scope:
        lines.append("")
        lines.extend(_scope_footer_lines(outcome))

    lines.append("")
    lines.append(f"CANVAS WRITES PERFORMED: {writes}")
    lines.append(f"EMAILS SENT: {emails}")
    return "\n".join(lines)


def parent_template_groups(
    outcome: ScanOutcome,
) -> list[tuple[str, list[tuple[str, str]]]]:
    """Group copy/paste parent drafts by student.

    Includes only: active missing assignments, NEW assessment <=85 flags, and
    active low-course-average flags. Returns ``[(student_name, [(label, message)])]``
    sorted by student name. Never sends anything.
    """
    by_student: dict[str, list[tuple[str, str]]] = {}
    order: list[str] = []

    def _add(entry: ReportEntry, label: str) -> None:
        f = entry.flag
        message = templates.parent_message_for(f)
        if not message:
            return
        if f.student_name not in by_student:
            by_student[f.student_name] = []
            order.append(f.student_name)
        by_student[f.student_name].append((label, message))

    for entry in outcome.missing:
        if entry.status in (NEW, STILL_ACTIVE):
            f = entry.flag
            _add(entry, f"MISSING ASSIGNMENT | {f.course_name} | "
                       f"{f.assignment_title or '(unknown)'}")

    for entry in outcome.low_assessment:
        f = entry.flag
        score = templates.format_score(f.score) or (f.raw_status or "")
        _add(entry, f"ASSESSMENT 85 OR BELOW | {f.course_name} | "
                    f"{f.assignment_title or '(unknown)'} | {score}")

    for entry in outcome.low_average:
        if entry.status in (NEW, STILL_ACTIVE):
            f = entry.flag
            avg = templates.format_score(f.average) or ""
            _add(entry, f"OVERALL AVERAGE 85 OR BELOW | {f.course_name} | {avg}")

    return [(name, by_student[name]) for name in sorted(order, key=str.lower)]


def render_parent_templates(
    outcome: ScanOutcome, *, writes: int = 0, emails: int = 0
) -> str:
    """Copy/paste parent drafts only, grouped by student. Sends nothing."""
    lines: list[str] = []
    lines.append("=== 4A GRADE CHECK — PARENT MESSAGE DRAFTS (COPY/PASTE ONLY) ===")
    if outcome.scope_label:
        lines.append(f"Scope: {outcome.scope_label}")
    lines.append(f"Quarter: Q{outcome.quarter}")
    lines.append("No message is sent automatically. Copy and send manually as needed.")

    groups = parent_template_groups(outcome)
    if not groups:
        lines.append("")
        lines.append("None")
    for student_name, items in groups:
        lines.append("")
        lines.append(f"--- {student_name} ---")
        for label, message in items:
            lines.append(f"[{label}]")
            lines.append("-" * 40)
            lines.append(message)
            lines.append("-" * 40)

    lines.append("")
    lines.append(f"CANVAS WRITES PERFORMED: {writes}")
    lines.append(f"EMAILS SENT: {emails}")
    return "\n".join(lines)


def render_email_body(outcome: ScanOutcome) -> str:
    lines: list[str] = []
    lines.append("4A Grade Check - Student Flags")
    if outcome.scope_label:
        lines.append(f"Scope: {outcome.scope_label}")
    sources = [c for c in outcome.courses if c.average_source]
    if sources:
        lines.append(
            "Course averages: "
            + "; ".join(f"{c.name} — {c.average_source}" for c in sources)
        )
    lines.append("")
    lines.append(
        f"Summary: missing={len(outcome.missing)}, "
        f"assessment<=85={len(outcome.low_assessment)}, "
        f"average<=85={len(outcome.low_average)}, "
        f"resolved={len(outcome.resolved)}"
    )
    lines.append("")
    lines.append("MISSING ASSIGNMENTS")
    lines.append("-------------------")
    lines.append(_flag_items(outcome.missing))

    lines.append("")
    lines.append("ASSESSMENT SCORES 85 OR BELOW")
    lines.append("-----------------------------")
    lines.append(_flag_items(outcome.low_assessment))

    lines.append("")
    lines.append("OVERALL COURSE AVERAGES 85 OR BELOW")
    lines.append("------------------------------------")
    lines.append(_flag_items(outcome.low_average))

    lines.append("")
    lines.append("UNRESOLVED LOW-SCORE ITEMS — INFORMATIONAL ONLY")
    lines.append("------------------------------------------------")
    unresolved_groups = grouped_unresolved_review(outcome)
    if unresolved_groups:
        for course, title, group, count in unresolved_groups:
            lines.append(f"- [{course}] {title} (group: {group or '(none)'}) — {count} students")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("RESOLVED SINCE LAST SCAN")
    lines.append("------------------------")
    if outcome.resolved:
        for f in outcome.resolved:
            lines.append(
                f"- {f.student_name} | {f.course_name} | {f.flag_type} | "
                f"{f.assignment_title or 'course average'}"
            )
    else:
        lines.append("- None")

    if not outcome.is_quarter_scope:
        lines.append("")
        lines.append("OUT OF SCOPE (QUARTER ROTATION — NOT RESOLVED)")
        lines.append("----------------------------------------------")
        if outcome.out_of_scope:
            for f in outcome.out_of_scope:
                lines.append(
                    f"- {f.student_name} | {f.course_name} | {f.flag_type} | "
                    f"{f.assignment_title or 'course average'}"
                )
        else:
            lines.append("- None")

    lines.append("")
    lines.append("NOT ELIGIBLE (LATE ENROLLMENT / NO GRADES — NOT RESOLVED)")
    lines.append("---------------------------------------------------------")
    if outcome.not_eligible:
        for f in outcome.not_eligible:
            lines.append(
                f"- {f.student_name} | {f.course_name} | {f.flag_type} | "
                f"{f.assignment_title or 'course average'}"
            )
    else:
        lines.append("- None")

    footer = _scope_footer_lines(outcome)
    if footer:
        lines.append("")
        lines.extend(footer)
    return "\n".join(lines)


BASELINE_SUBJECT = "4A Grade Check - Initial Baseline Student Flags"

BASELINE_INTRO = (
    "This is the initial Grade Check baseline for the current quarter. "
    "Because this is the first run, the report includes previously recorded "
    "assessment scores that meet the alert criteria. Future Grade Check emails "
    "will suppress these already-issued one-time assessment alerts and focus on "
    "new, resolved, and still-active persistent concerns."
)


def render_baseline_email_body(outcome: ScanOutcome) -> str:
    """Initial-baseline email body: intro + four sections.

    Missing / assessment / average flags include copy/paste parent templates;
    unresolved low-score items are informational only (no parent templates).
    """
    lines: list[str] = []
    lines.append(BASELINE_SUBJECT)
    if outcome.scope_label:
        lines.append(f"Scope: {outcome.scope_label}")
    lines.append("")
    lines.append(BASELINE_INTRO)
    lines.append("")
    lines.append("MISSING ASSIGNMENTS")
    lines.append("-------------------")
    lines.append(_flag_items(outcome.missing))

    lines.append("")
    lines.append("ASSESSMENT SCORES 85 OR BELOW")
    lines.append("-----------------------------")
    lines.append(_flag_items(outcome.low_assessment))

    lines.append("")
    lines.append("OVERALL COURSE AVERAGES 85 OR BELOW")
    lines.append("------------------------------------")
    lines.append(_flag_items(outcome.low_average))

    lines.append("")
    lines.append("UNRESOLVED LOW-SCORE ITEMS — INFORMATIONAL ONLY")
    lines.append("------------------------------------------------")
    unresolved_groups = grouped_unresolved_review(outcome)
    if unresolved_groups:
        for course, title, group, count in unresolved_groups:
            lines.append(f"- [{course}] {title} (group: {group or '(none)'}) — {count} students")
    else:
        lines.append("- None")

    return "\n".join(lines)


def command_self_test() -> int:
    cfg = __import__("scripts.canvas_llm_grade_check.config", fromlist=["load_config"]).load_config()
    subject = cfg.subjects["math"]
    missing = Flag(
        key="26404:1:10:MISSING_ASSIGNMENT", flag_type=engine.MISSING_ASSIGNMENT,
        course_id=26404, course_name="Math", student_id=1, student_name="Student Alpha",
        first_name="Student", assignment_id=10, assignment_title="SM5: Lesson 26 Homework",
        raw_status="MI", classification=engine.NON_ASSESSMENT,
    )
    outcome = ScanOutcome(
        quarter=1,
        courses=[CourseScanSummary("Math", 26404, 20)],
        missing=[ReportEntry(missing, NEW)],
    )
    preview = render_preview(outcome)
    assert "=== 4A GRADE CHECK — TEACHER REVIEW ===" in preview
    assert "MISSING ASSIGNMENTS" in preview
    assert "Student Alpha" in preview
    # Default (routine) preview is compact: no inline parent templates.
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." not in preview
    assert "COPY/PASTE PARENT MESSAGE" not in preview
    assert "CANVAS WRITES PERFORMED: 0" in preview
    assert "EMAILS SENT: 0" in preview
    # Compact one-line format.
    assert "[NEW] Student Alpha | Math | SM5: Lesson 26 Homework | missing" in preview
    # Summary counts block.
    assert "Summary counts" in preview
    assert "NEW missing: 1" in preview
    assert "STILL ACTIVE low averages: 0" in preview
    # Grouped unresolved section present; individual students not listed.
    assert "UNRESOLVED LOW-SCORE ITEMS (grouped)" in preview

    # Detailed mode expands to full metadata + parent templates.
    detailed = render_preview(outcome, details=True)
    assert "(DETAILED)" in detailed
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in detailed
    assert "COPY/PASTE PARENT MESSAGE" in detailed
    assert "homework/classwork" in detailed

    # Parent-template mode prints drafts only, grouped by student.
    parent_only = render_parent_templates(outcome)
    assert "PARENT MESSAGE DRAFTS (COPY/PASTE ONLY)" in parent_only
    assert "--- Student Alpha ---" in parent_only
    assert "MISSING ASSIGNMENT | Math | SM5: Lesson 26 Homework" in parent_only
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in parent_only
    assert "CANVAS WRITES PERFORMED: 0" in parent_only
    assert "EMAILS SENT: 0" in parent_only

    # Assessment one-time state stays suppressed: no low_assessment entries.
    assert "ASSESSMENT SCORES 85 OR BELOW (NEW)" in preview
    assert "NEW assessment <=85: 0" in preview

    body = render_email_body(outcome)
    assert "4A Grade Check - Student Flags" in body
    assert "MISSING ASSIGNMENTS" in body
    # The teacher email remains detailed and keeps parent templates.
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in body

    # Baseline body has the custom subject, intro, and four sections.
    baseline = render_baseline_email_body(outcome)
    assert BASELINE_SUBJECT in baseline
    assert "initial Grade Check baseline" in baseline
    assert "previously recorded assessment scores" in baseline
    assert "UNRESOLVED LOW-SCORE ITEMS — INFORMATIONAL ONLY" in baseline

    # No parent message invented for low average beyond the template.
    avg = Flag(
        key="26404:1:LOW_COURSE_AVERAGE", flag_type=engine.LOW_COURSE_AVERAGE,
        course_id=26404, course_name="Math", student_id=1, student_name="Student Alpha",
        first_name="Student", average=80.0,
    )
    avg_outcome = ScanOutcome(quarter=1, courses=[], low_average=[ReportEntry(avg, STILL_ACTIVE)])
    avg_preview = render_preview(avg_outcome)
    assert "OVERALL COURSE AVERAGES 85 OR BELOW" in avg_preview
    # Compact line for the average (no inline template).
    assert "[STILL ACTIVE] Student Alpha | Math | 80" in avg_preview
    assert "current average in Math is 80" not in avg_preview
    # Detailed mode includes the parent template wording.
    assert "current average in Math is 80" in render_preview(avg_outcome, details=True)

    print("PASS grade-check report self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
