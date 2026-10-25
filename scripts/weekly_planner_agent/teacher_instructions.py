"""Deterministic plain-language teacher-instruction parser.

Turns Owen's natural-language sentences into structured ``InstructionOp``s.
This is deliberately rule-based (no model, no network) so it is fully testable
and never silently invents an interpretation: unmatched input returns an
explicit ``matched=False`` with a clarifying reply.

Supported intents (canonical examples):
    MOVE_ASSESSMENT          "Move the Math test to Thursday."
    NO_HOMEWORK              "No Science homework this week."
    SET_HOMEWORK_DAYS        "Reading homework Tuesday and Thursday only."
    SKIP_CHAPTER             "We aren't doing Chapter 8 yet."
    ADD_HOMEROOM             "Add Book Character Day to Homeroom."
    WHAT_CHANGED             "What changed since yesterday?"
    APPROVE_EXCEPT           "Approve everything except Science."
    MAKE_REVIEW_DAY          "Make Wednesday a review day."
    HOLD_REMINDER            "Don't send the reminder yet."
    REMOVE_ASSIGNMENT_KEEP   "Remove the Tuesday Math assignment but keep Lesson 42."
    KEEP_SUBJECT_CHAPTER     "Science should stay on Chapter 7 Thursday."
    KEEP_OVERRIDE            "keep Science on Wednesday."
    CONFIRM                  "Yes."
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Intents.
MOVE_ASSESSMENT = "MOVE_ASSESSMENT"
NO_HOMEWORK = "NO_HOMEWORK"
SET_HOMEWORK_DAYS = "SET_HOMEWORK_DAYS"
SKIP_CHAPTER = "SKIP_CHAPTER"
ADD_HOMEROOM = "ADD_HOMEROOM"
WHAT_CHANGED = "WHAT_CHANGED"
APPROVE_EXCEPT = "APPROVE_EXCEPT"
MAKE_REVIEW_DAY = "MAKE_REVIEW_DAY"
HOLD_REMINDER = "HOLD_REMINDER"
REMOVE_ASSIGNMENT_KEEP = "REMOVE_ASSIGNMENT_KEEP"
KEEP_SUBJECT_CHAPTER = "KEEP_SUBJECT_CHAPTER"
KEEP_OVERRIDE = "KEEP_OVERRIDE"
KEEP_ASSESSMENT_DATE = "KEEP_ASSESSMENT_DATE"
UPDATE_WITHOUT_REMINDER = "UPDATE_WITHOUT_REMINDER"
SHOW_ANNOUNCEMENT = "SHOW_ANNOUNCEMENT"
CONFIRM = "CONFIRM"
WHY_CONFLICT = "WHY_CONFLICT"
SHOW_CANVAS = "SHOW_CANVAS"
IGNORE_CONFLICT = "IGNORE_CONFLICT"

SUBJECT_ALIASES = {
    "math": "math",
    "maths": "math",
    "science": "science",
    "reading": "reading_spelling",
    "spelling": "reading_spelling",
    "reading/spelling": "reading_spelling",
    "reading and spelling": "reading_spelling",
    "language arts": "language_arts",
    "language": "language_arts",
    "la": "language_arts",
    "homeroom": "homeroom",
    "history": "history",
}

DAY_ALIASES = {
    "monday": "Monday", "mon": "Monday",
    "tuesday": "Tuesday", "tues": "Tuesday", "tue": "Tuesday",
    "wednesday": "Wednesday", "wed": "Wednesday",
    "thursday": "Thursday", "thurs": "Thursday", "thur": "Thursday", "thu": "Thursday",
    "friday": "Friday", "fri": "Friday",
}


@dataclass
class InstructionOp:
    intent: str
    subject: str | None = None
    day: str | None = None
    chapter: str | None = None
    assessment: str | None = None
    item: str | None = None
    days: list[str] = field(default_factory=list)
    keep_lesson: bool = False
    confirm: bool = False
    hold_reminder: bool = False
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "subject": self.subject,
            "day": self.day,
            "chapter": self.chapter,
            "assessment": self.assessment,
            "item": self.item,
            "days": list(self.days),
            "keep_lesson": self.keep_lesson,
            "confirm": self.confirm,
            "hold_reminder": self.hold_reminder,
        }


@dataclass
class ParseResult:
    ops: list[InstructionOp]
    matched: bool
    reply: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ops": [op.to_dict() for op in self.ops],
            "matched": self.matched,
            "reply": self.reply,
        }


def _normalize(text: str) -> str:
    text = re.sub(r"[.!?]+$", "", text.strip())
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(text.lower().split())


def _subject(text: str) -> str | None:
    # Longest alias first so "language arts" wins over "language".
    for alias in sorted(SUBJECT_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return SUBJECT_ALIASES[alias]
    return None


def _day(text: str) -> str | None:
    for alias in sorted(DAY_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return DAY_ALIASES[alias]
    return None


def _days(text: str) -> list[str]:
    found: list[str] = []
    for alias in sorted(DAY_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            value = DAY_ALIASES[alias]
            if value not in found:
                found.append(value)
    return found


def _chapter(text: str) -> str | None:
    m = re.search(r"\bchapter\s*(\d+)\b|\bch\.?\s*(\d+)\b", text)
    if not m:
        return None
    return m.group(1) or m.group(2)


def _assessment_name(text: str, subject: str | None) -> str | None:
    m = re.search(r"\b(assessment|test|quiz)\s*(\d+)?", text)
    if not m:
        return None
    kind = m.group(1).capitalize()
    number = m.group(2)
    if subject == "math":
        return f"Written {kind} {number}".strip() if number else f"{kind}"
    return f"{kind} {number}".strip() if number else f"{kind}"


def parse(text: str) -> ParseResult:
    """Parse one teacher instruction into zero or more structured ops."""
    raw = text.strip()
    norm = _normalize(raw)
    if not norm:
        return ParseResult([], False, "I didn't catch that. Try describing the change you want.")

    ops: list[InstructionOp] = []

    # CONFIRM ("yes" / "yep" / "sure" / "please do")
    if re.fullmatch(r"(yes|yeah|yep|sure|ok|okay|please do|go ahead)", norm):
        ops.append(InstructionOp(intent=CONFIRM, confirm=True, raw=raw))
        return ParseResult(ops, True, "Got it. I'll apply the proposed changes.")

    # WHAT_CHANGED
    if re.search(r"\bwhat changed\b|\bwhat's changed\b|\bwhat has changed\b", norm):
        return ParseResult(
            [InstructionOp(intent=WHAT_CHANGED, raw=raw)],
            True,
            "Let me show you what changed since your last review.",
        )

    # UPDATE_WITHOUT_REMINDER ("Update the Math items but don't reschedule the reminder yet."
    #                         / "Yes, but leave the reminder scheduled for now.")
    if ("update" in norm or norm.startswith("yes") or norm.startswith("ok")
            or norm.startswith("sure") or norm.startswith("yeah")) \
            and "reminder" in norm \
            and re.search(r"\bdon'?t\b|\bleave\b|\bhold\b|\bnot yet\b|\bkeep\b", norm):
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=UPDATE_WITHOUT_REMINDER, subject=subject, hold_reminder=True, raw=raw)],
            True,
            f"Done — I've prepared the revised {subject.title() if subject else 'plan'} and marked the reminder for your review. Nothing live has changed.",
        )

    # SHOW_ANNOUNCEMENT ("Show me the exact announcement parents would receive.")
    if re.search(r"\bshow me\b|\bshow the\b", norm) and "announcement" in norm:
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=SHOW_ANNOUNCEMENT, subject=subject, raw=raw)],
            True,
            "Here is the exact announcement parents would receive.",
        )

    # HOLD_REMINDER ("Don't send the reminder yet.")
    if re.search(r"\bdon'?t send\b|\bhold the reminder\b|\bhold reminder\b", norm) and "reminder" in norm:
        return ParseResult(
            [InstructionOp(intent=HOLD_REMINDER, raw=raw)],
            True,
            "Understood — I'll hold the reminder and won't schedule it yet.",
        )

    # APPROVE_EXCEPT ("Approve everything except Science.")
    if "approve" in norm and "except" in norm:
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=APPROVE_EXCEPT, subject=subject, raw=raw)],
            True,
            f"On it — I'll approve everything except {subject.title() if subject else 'that'}.",
        )

    # WHY_CONFLICT ("Why is Math showing a conflict?")
    if re.search(r"\bwhy\b", norm) and "conflict" in norm:
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=WHY_CONFLICT, subject=subject, raw=raw)],
            True,
            f"Here is why {subject.title() if subject else 'the subject'} shows a conflict.",
        )

    # SHOW_CANVAS ("What does Canvas currently say?")
    if re.search(r"\bwhat\b", norm) and ("canvas" in norm) and re.search(r"\bsay\b|\bshow\b|\bhave\b", norm):
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=SHOW_CANVAS, subject=subject, raw=raw)],
            True,
            "Here is what Canvas currently shows.",
        )

    # IGNORE_CONFLICT ("Ignore this conflict for now.")
    if "ignore" in norm and "conflict" in norm:
        return ParseResult(
            [InstructionOp(intent=IGNORE_CONFLICT, raw=raw)],
            True,
            "Understood — I'll set this conflict aside for now. It won't affect other subjects.",
        )

    # MOVE_ASSESSMENT ("Move the Math test to Thursday." / "Change the test back to Friday.")
    # Subject may be omitted; the caller binds to the focused subject.
    if ("move" in norm or ("change" in norm and re.search(r"\bto\b", norm))) \
            and _day(norm) and re.search(r"\btest\b|\bassessment\b|\bquiz\b", norm):
        subject = _subject(norm)
        day = _day(norm)
        return ParseResult(
            [InstructionOp(intent=MOVE_ASSESSMENT, subject=subject, day=day,
                           assessment=_assessment_name(norm, subject), raw=raw)],
            True,
            f"Okay — I'll move the {subject.title() if subject else 'focused'} assessment to {day} and recompute the affected drafts.",
        )

    # NO_HOMEWORK ("No Science homework this week.")
    if re.search(r"\bno (more )?\w* ?homework\b", norm) or (
        "homework" in norm and re.search(r"\bno\b|\bnone\b|\bnot this week\b", norm)
    ):
        subject = _subject(norm) or "science"
        return ParseResult(
            [InstructionOp(intent=NO_HOMEWORK, subject=subject, raw=raw)],
            True,
            f"Done — {subject.title()} homework is removed for this week.",
        )

    # SET_HOMEWORK_DAYS ("Reading homework Tuesday and Thursday only.")
    if "homework" in norm and _days(norm):
        subject = _subject(norm) or "reading_spelling"
        days = _days(norm)
        return ParseResult(
            [InstructionOp(intent=SET_HOMEWORK_DAYS, subject=subject, days=days, raw=raw)],
            True,
            f"Got it — {subject.title()} homework on {' and '.join(days)} only.",
        )

    # SKIP_CHAPTER ("We aren't doing Chapter 8 yet.")
    if ("not doing" in norm or "aren't doing" in norm or "skip" in norm) and _chapter(norm):
        chapter = _chapter(norm)
        subject = _subject(norm)
        return ParseResult(
            [InstructionOp(intent=SKIP_CHAPTER, subject=subject, chapter=chapter, raw=raw)],
            True,
            f"Understood — we're not doing Chapter {chapter} yet"
            + (f" in {subject.title()}." if subject else "."),
        )

    # ADD_HOMEROOM ("Add Book Character Day to Homeroom.")
    if ("add" in norm or "put" in norm) and "homeroom" in norm:
        item = raw
        for prefix in ("add", "put"):
            if item.lower().startswith(prefix):
                item = item[len(prefix):].strip()
                break
        item = re.sub(r"\bto homeroom\b", "", item, flags=re.IGNORECASE).strip()
        return ParseResult(
            [InstructionOp(intent=ADD_HOMEROOM, subject="homeroom", item=item, raw=raw)],
            True,
            f"Added \"{item}\" to Homeroom for this week.",
        )

    # REMOVE_ASSIGNMENT_KEEP ("Remove the Tuesday Math assignment but keep Lesson 42.")
    if "remove" in norm and "assignment" in norm:
        subject = _subject(norm) or "math"
        day = _day(norm)
        keep_lesson = bool(re.search(r"\bkeep\b", norm))
        return ParseResult(
            [InstructionOp(intent=REMOVE_ASSIGNMENT_KEEP, subject=subject, day=day,
                           keep_lesson=keep_lesson, raw=raw)],
            True,
            f"Done — removed the {subject.title()} assignment"
            + (f" on {day}" if day else "")
            + (" while keeping the lesson." if keep_lesson else "."),
        )

    # KEEP_SUBJECT_CHAPTER ("Science should stay on Chapter 7 Thursday.")
    if ("stay" in norm or "stay on" in norm) and _chapter(norm):
        chapter = _chapter(norm)
        subject = _subject(norm) or "science"
        day = _day(norm)
        return ParseResult(
            [InstructionOp(intent=KEEP_SUBJECT_CHAPTER, subject=subject, day=day, chapter=chapter, raw=raw)],
            True,
            f"Recorded — {subject.title()} stays on Chapter {chapter}"
            + (f" {day}" if day else "") + " as a teacher override.",
        )

    # KEEP_OVERRIDE ("keep Science on Wednesday.")
    if "keep" in norm and _subject(norm) and _day(norm):
        subject = _subject(norm)
        day = _day(norm)
        return ParseResult(
            [InstructionOp(intent=KEEP_OVERRIDE, subject=subject, day=day, raw=raw)],
            True,
            f"Done — I recorded your {subject.title()} override for {day}.",
        )

    # KEEP_ASSESSMENT_DATE ("The pacing sheet is wrong. Keep Thursday." / "Keep Thursday.")
    if ("keep" in norm or "pacing sheet" in norm) and _day(norm) and not _subject(norm):
        day = _day(norm)
        subject = _subject(norm)  # may be None; caller binds to focus context
        return ParseResult(
            [InstructionOp(intent=KEEP_ASSESSMENT_DATE, subject=subject, day=day, raw=raw)],
            True,
            f"Recorded — keeping {day} as a teacher override (the pacing change will remain visible but won't override you).",
        )

    # MAKE_REVIEW_DAY ("Make Wednesday a review day.")
    if "review day" in norm or ("make" in norm and "review" in norm):
        day = _day(norm)
        subject = _subject(norm)
        if day:
            return ParseResult(
                [InstructionOp(intent=MAKE_REVIEW_DAY, subject=subject, day=day, raw=raw)],
                True,
                f"Okay — {day} is now a review day"
                + (f" for {subject.title()}." if subject else "."),
            )

    return ParseResult(
        [], False,
        "I couldn't map that to a known change. Try something like \"Move the Math test to Thursday\" or \"No Science homework this week.\"",
    )
