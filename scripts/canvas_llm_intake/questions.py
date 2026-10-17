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
    """Generate the set of intake questions from normalized pacing + drafts.

    Sources of ambiguity:
      - unresolved tokens from deterministic translation (subject reports)
      - same-day assessment + lesson conflicts
      - blank cells (only flagged, never inferred)
      - next-week assessments requiring an advance reminder this week
    """
    questions: list[dict[str, Any]] = []

    # 1. Unresolved tokens from subject translation. Two shapes are possible:
    #    dict {"weekday", "token"} (math/translation) or a bare string (reading).
    for subject, report in subject_reports.items():
        for u in (report or {}).get("unresolved") or []:
            if isinstance(u, dict):
                wd = u.get("weekday", "")
                token = u.get("token", "")
            else:
                wd = ""
                token = str(u)
            # OWNER-CONFIRMED (Q2W2): a trailing `*` on a Math assessment token
            # (e.g. FA6* / FA7*) is operationally ignored — treat as the plain
            # assessment, do not expose the marker, and do not re-ask.
            if "trailing '*' marker" in token:
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

    # 2. Blank science/history cells (flag, don't infer).
    rotating = _rotating_subject(week)
    if rotating:
        for wd in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
            day = (week.get("days") or {}).get(wd, {})
            cell = day.get("subjects", {}).get(rotating, {}).get("raw", "")
            if cell == "":
                date = _day_date(week, wd)
                questions.append(new_question(
                    subject=rotating,
                    date=date,
                    source_text="",
                    reason=f"{rotating} pacing cell is blank on {wd}",
                    recommended_default="leave blank (no content generated)",
                    risk_if_guessed="inventing review/lab/worksheet content",
                ))

    # 3. Next-week assessment -> advance reminder this week.
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

    # 4. Same-day assessment + lesson conflict (generic).
    for subject, report in subject_reports.items():
        for wd, day in (report.get("days") or {}).items():
            if _day_has_assessment_and_lesson(day):
                date = _day_date(week, wd)
                questions.append(new_question(
                    subject=subject,
                    date=date,
                    source_text=day.get("source", ""),
                    reason=f"assessment and lesson both present on {wd}",
                    recommended_default="show both; assessment takes priority for grading",
                    risk_if_guessed="omitting one element",
                ))

    # De-duplicate by (subject, date, source_text, reason).
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for q in questions:
        key = (q["subject"], q["date"], q["source_text"], q["reason"])
        if key not in seen:
            seen.add(key)
            deduped.append(q)
    return deduped


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

    week = {
        "week": {"code": "Q2W1"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"science": {"raw": ""}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"science": {"raw": "Ch. 1"}}},
        },
    }
    # Blank science cell produces a question; blank preservation verified.
    qs = generate_questions(week=week, subject_reports={}, assessment_events=[], reminder_events=[])
    assert any(q["subject"] == "science" and "blank" in q["reason"] for q in qs), qs
    assert all(q["status"] == "OPEN" for q in qs)

    # apply_question_answers marks ANSWERED by stable ID.
    answers = {q["question_id"]: {"answer": "leave blank", "answered_at": "x", "source": "OWNER_INPUT"}
               for q in qs}
    qs = apply_question_answers(qs, answers)
    assert all(q["status"] == "ANSWERED" for q in qs)

    print("PASS intake questions self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
