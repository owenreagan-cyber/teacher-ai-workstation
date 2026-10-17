"""Question / ambiguity model for the intake workspace.

The intake system must never silently guess. Every ambiguity becomes a typed
question with a question_id, source text, recommended default, and risk-if-
guessed. Questions are persisted to ``questions/questions.json`` and rendered
to ``questions/questions.md``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_question_id(subject: str, date: str, source_text: str, reason: str) -> str:
    """A stable, content-derived question ID (deterministic across regeneration).

    The ID is a short sha256 of (subject, date, source_text, reason) prefixed
    with a readable subject token, so teacher answers stay bound to the exact
    ambiguity even when the question set changes between runs.
    """
    key = "\x1f".join([subject, date, source_text, reason])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    slug = subject.replace("_", "-") or "global"
    return f"{slug}-{digest}"


def new_question(
    *,
    subject: str,
    date: str,
    source_text: str,
    reason: str,
    recommended_default: str,
    risk_if_guessed: str,
    question_id: str | None = None,
) -> dict[str, Any]:
    qid = question_id if question_id is not None else stable_question_id(subject, date, source_text, reason)
    return {
        "question_id": qid,
        "subject": subject,
        "date": date,
        "source_text": source_text,
        "reason": reason,
        "recommended_default": recommended_default,
        "risk_if_guessed": risk_if_guessed,
        "status": "OPEN",
    }


def generate_questions(
    *,
    week: dict[str, Any],
    subject_reports: dict[str, dict[str, Any]],
    assessment_events: list[dict[str, Any]],
    reminder_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate the minimal set of intake questions from normalized pacing.

    Standing rules encoded here:
      - Blank pacing stays blank; a full-week blank ACTIVE subject collapses to
        ONE subject-level question (never one question per blank day).
      - An explicit Math "Review" token is an in-class review day (never asked
        "is it a review?"); the only owner decision is whether to add At Home
        review text.
      - Noisy "assessment + lesson same day" and trailing-`*` marker questions
        are suppressed (owner-confirmed).
    """
    questions: list[dict[str, Any]] = []

    # 1. Unresolved tokens from subject translation (dict or bare-string shape).
    for subject, report in subject_reports.items():
        for u in (report or {}).get("unresolved") or []:
            if isinstance(u, dict):
                wd = u.get("weekday", "")
                token = u.get("token", "")
            else:
                wd = ""
                token = str(u)
            # OWNER-CONFIRMED: trailing `*` on a Math assessment token is
            # operationally ignored — never re-ask.
            if "trailing '*' marker" in token:
                continue
            # Explicit Math "Review" is a review day; not a translation ambiguity.
            if subject == "math" and _is_review_token(token):
                continue
            date = _day_date(week, wd)
            questions.append(new_question(
                subject=subject,
                date=date,
                source_text=token,
                reason=f"pacing token {token!r} has no deterministic translation",
                recommended_default="leave verbatim; do not infer meaning",
                risk_if_guessed="inventing lesson/assessment content not in the source",
            ))

    # 2. Blank active rotating subject — collapse to ONE subject-level question.
    rotating = _rotating_subject(week)
    if rotating:
        cells = []
        for wd in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
            day = (week.get("days") or {}).get(wd, {})
            raw = day.get("subjects", {}).get(rotating, {}).get("raw", "")
            cells.append(raw)
        if all(c == "" for c in cells):
            code = week.get("week", {}).get("code", "")
            questions.append(new_question(
                subject=rotating,
                date="",
                source_text="",
                reason=f"{rotating} pacing is completely blank for {code}",
                recommended_default="leave Science out for the week (no content generated)",
                risk_if_guessed="inventing review/lab/test-prep content",
                question_id=f"{rotating}-{code.lower()}-all-blank",
            ))

    # 3. Math "Review" day: one At Home decision question (never "is it review?").
    math_report = subject_reports.get("math") or {}
    for wd, day in (math_report.get("days") or {}).items():
        if _is_review_day(day):
            date = _day_date(week, wd)
            # Find the following day's assessments for the prompt context.
            code = week.get("week", {}).get("code", "")
            questions.append(new_question(
                subject="math",
                date=date,
                source_text="Review",
                reason=(
                    f"{wd} is an explicit Review day. Should the Math page include "
                    "an At Home review/study reminder that evening, or omit At Home?"
                ),
                recommended_default="omit At Home unless Owen explicitly adds review text",
                risk_if_guessed="could invent homework not present in pacing",
                question_id=f"math-{code.lower()}-{wd.lower()}-review-at-home",
            ))

    # 4. Next-week assessment -> advance reminder this week.
    for ev in reminder_events:
        if ev.get("advance_reminder_this_week"):
            questions.append(new_question(
                subject=ev.get("subject", ""),
                date=ev.get("date", ""),
                source_text=ev.get("source_text", ""),
                reason=ev.get("reason", "next-week assessment may need an advance reminder"),
                recommended_default="include advance reminder this week",
                risk_if_guessed="missing an assessment parents should know about",
            ))

    # De-duplicate by question_id (stable) then by content.
    seen: set[str] = set()
    seen_content: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for q in questions:
        if q["question_id"] in seen:
            continue
        key = (q["subject"], q["date"], q["source_text"], q["reason"])
        if key in seen_content:
            continue
        seen.add(q["question_id"])
        seen_content.add(key)
        deduped.append(q)
    return deduped


def _is_review_token(token: str) -> bool:
    return (token or "").strip().lower() in ("review",)


def _is_review_day(day: dict[str, Any]) -> bool:
    """True when a Math day plan is an explicit Review (in-class only)."""
    src = (day.get("source") or "").strip()
    return src.lower() == "review"


def _day_date(week: dict[str, Any], weekday: str) -> str:
    return (week.get("days") or {}).get(weekday, {}).get("date", "")


def _rotating_subject(week: dict[str, Any]) -> str:
    code = week.get("week", {}).get("code", "")
    quarter = code[1] if len(code) >= 2 else ""
    if quarter in ("2", "4"):
        return "science"
    if quarter in ("1", "3"):
        return "history"
    return ""


def _day_has_assessment_and_lesson(day: dict[str, Any]) -> bool:
    lines = day.get("in_class") or day.get("lines") or []
    has_assessment = any(_looks_like_assessment(ln) for ln in lines)
    has_lesson = any(_looks_like_lesson(ln) for ln in lines)
    return has_assessment and has_lesson


def _looks_like_assessment(line: str) -> bool:
    low = (line or "").lower()
    return any(k in low for k in ("test", "assessment", "checkout", "quiz"))


def _looks_like_lesson(line: str) -> bool:
    low = (line or "").lower()
    if "lesson" in low:
        return True
    if "chapter" in low:
        # "Chapter N Test/Checkup/Review/Quiz" is an assessment, not a lesson.
        return not any(k in low for k in ("test", "checkup", "review", "quiz"))
    return False


def write_questions(
    quarter: int, week: int, questions: list[dict[str, Any]]
) -> tuple[Path, Path]:
    from .manifest import staging_dir

    d = staging_dir(quarter, week) / "questions"
    d.mkdir(parents=True, exist_ok=True)
    jp = d / "questions.json"
    jp.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mp = d / "questions.md"
    lines = ["# Intake Questions", ""]
    if not questions:
        lines.append("None.")
    for q in questions:
        status = q.get("status", "OPEN")
        answer = q.get("answer", "")
        lines.append(f"- **Q{q['question_id']}** [{status}] ({q['subject']} · {q['date']}): {q['reason']}")
        lines.append(f"  - Source: `{q['source_text']}`")
        lines.append(f"  - Recommended: {q['recommended_default']}")
        lines.append(f"  - Risk if guessed: {q['risk_if_guessed']}")
        if answer:
            lines.append(f"  - Answer: {answer}")
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jp, mp


def load_questions(quarter: int, week: int) -> list[dict[str, Any]]:
    from .manifest import staging_dir

    path = staging_dir(quarter, week) / "questions" / "questions.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def apply_question_answers(
    questions: list[dict[str, Any]],
    answers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Mark questions ANSWERED from teacher-input answers (preserving history).

    A question becomes ANSWERED when a matching ``question_answers[question_id]``
    entry exists. The answer + answered_at + source are recorded on the question;
    the original question text is preserved (never deleted).
    """
    for q in questions:
        ans = answers.get(str(q.get("question_id")))
        if ans is not None:
            q["status"] = "ANSWERED"
            q["answer"] = ans.get("answer")
            q["answered_at"] = ans.get("answered_at")
            q["answer_source"] = ans.get("source", "OWNER_INPUT")
    return questions


def unresolved_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Questions that remain OPEN (i.e. not yet answered)."""
    return [q for q in questions if q.get("status", "OPEN") == "OPEN"]


def command_self_test() -> int:
    q = new_question(subject="math", date="2026-10-15", source_text="WA3+L42",
                     reason="same-day assessment+lesson", recommended_default="x",
                     risk_if_guessed="y")
    assert q["status"] == "OPEN" and isinstance(q["question_id"], str)
    assert q["reason"] == "same-day assessment+lesson"

    # Stable IDs: same content -> same ID across regeneration.
    q2 = new_question(subject="math", date="2026-10-15", source_text="WA3+L42",
                      reason="same-day assessment+lesson", recommended_default="x",
                      risk_if_guessed="y")
    assert q["question_id"] == q2["question_id"]
    # Different content -> different ID.
    q3 = new_question(subject="math", date="2026-10-15", source_text="WA3+L43",
                      reason="same-day assessment+lesson", recommended_default="x",
                      risk_if_guessed="y")
    assert q["question_id"] != q3["question_id"]

    # Partial blank week (Science has content Tuesday) -> NO blank question
    # (the collapse rule only fires on a FULL-week blank).
    partial = {
        "week": {"code": "Q2W1"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"science": {"raw": ""}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"science": {"raw": "Ch. 1"}}},
        },
    }
    qs = generate_questions(week=partial, subject_reports={}, assessment_events=[], reminder_events=[])
    assert qs == [], qs  # not fully blank -> no collapse question

    # Full-week blank active subject -> exactly ONE subject-level question.
    full_blank = {
        "week": {"code": "Q2W3"},
        "days": {wd: {"date": f"2026-10-{26+i}", "subjects": {"science": {"raw": ""}}}
                 for i, wd in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"))},
    }
    qs2 = generate_questions(week=full_blank, subject_reports={}, assessment_events=[], reminder_events=[])
    assert len(qs2) == 1, qs2
    assert qs2[0]["question_id"] == "science-q2w3-all-blank", qs2
    assert "completely blank" in qs2[0]["reason"]

    # Math Review day -> one At Home question (stable id), never "is it review?".
    math_report = {
        "math": {"days": {"Wednesday": {"source": "Review", "in_class": ["Review"]}}}
    }
    week_review = {
        "week": {"code": "Q2W3"},
        "days": {"Wednesday": {"date": "2026-10-28", "subjects": {"math": {"raw": "Review"}}}},
    }
    qs3 = generate_questions(week=week_review, subject_reports=math_report,
                             assessment_events=[], reminder_events=[])
    review_q = [q for q in qs3 if q["subject"] == "math"]
    assert len(review_q) == 1, qs3
    assert review_q[0]["question_id"] == "math-q2w3-wednesday-review-at-home", review_q
    assert "At Home" in review_q[0]["reason"]

    # apply_question_answers marks ANSWERED by stable ID.
    answers = {q["question_id"]: {"answer": "x", "answered_at": "x", "source": "OWNER_INPUT"}
               for q in qs2 + qs3}
    all_q = apply_question_answers(qs2 + qs3, answers)
    assert all(q["status"] == "ANSWERED" for q in all_q)

    print("PASS intake questions self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
