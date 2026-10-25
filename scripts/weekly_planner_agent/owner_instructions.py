"""Owner instructions — Owen's explicit teacher-authority decisions.

These are *data*, not business logic. Each record is a specific, named decision
that outranks Google pacing and Canvas via the existing authority hierarchy
(``Authority.OWNER_INSTRUCTION``) and is applied through the existing
``DayPlan.teacher_override`` mechanism. Because the records live here (committed
and auditable), an explicit owner decision survives local-state rebuild and
remains visible to the cross-source consistency engine.

Adding a decision here does NOT invent a general rule: each entry is scoped to
one week + subject + the exact days/lessons Owen chose, with a reason.
"""
from __future__ import annotations

from typing import Any

from .models import Assessment, Authority, Confidence, DayPlan, PlanStatus, WeeklyPlan

# --------------------------------------------------------------------------- #
# Owner instruction records (auditable data).
# --------------------------------------------------------------------------- #

OWNER_INSTRUCTIONS: list[dict[str, Any]] = [
    {
        "id": "q2w3-math-thursday-assessments",
        "week_id": "Q2W3",
        "subject": "math",
        "authority": "OWNER_INSTRUCTION",
        "reason": (
            "The assessments were intentionally moved to Thursday because "
            "Friday is the classroom's Halloween-ish day."
        ),
        "days": [
            {
                "day": "Thursday",
                "date": "2026-10-29",
                "lesson": "WA7 / FA7",
                "assessments": ["Written Assessment 7", "Fact Assessment 7"],
            },
            {
                "day": "Friday",
                "date": "2026-10-30",
                "lesson": "INV 4",
                "assessments": [],
            },
        ],
    },
]


def instructions_for(week_id: str, subject: str) -> list[dict[str, Any]]:
    """Return the owner-instruction records matching a week + subject."""
    return [
        inst for inst in OWNER_INSTRUCTIONS
        if inst.get("week_id") == week_id and inst.get("subject") == subject
    ]


def apply_owner_instructions(plan: WeeklyPlan) -> WeeklyPlan:
    """Apply matching owner instructions to a plan in place (auditable override).

    Each matched day becomes ``OWNER_INSTRUCTION`` authority with a
    ``teacher_override`` record carrying the reason. Never deletes other
    subjects/days and never lowers an existing owner override.
    """
    for inst in OWNER_INSTRUCTIONS:
        if inst.get("week_id") != plan.week_id:
            continue
        subject = inst["subject"]
        for day_spec in inst.get("days") or []:
            day = day_spec["day"]
            date = day_spec.get("date")
            lesson = day_spec.get("lesson")
            assessments = day_spec.get("assessments") or []

            existing = plan.day(subject, day)
            if existing is not None:
                # Only apply when the existing day is the exact instructional
                # date the owner decision targets. Never stomp a same-named day
                # that carries a different (or absent) date — e.g. a synthetic
                # or alternate scenario.
                if existing.date != date:
                    continue
                # Never lower an existing owner override with a weaker one.
                if existing.authority == Authority.OWNER_INSTRUCTION and existing.teacher_override:
                    continue
                existing.lesson = lesson if lesson is not None else existing.lesson
                existing.authority = Authority.OWNER_INSTRUCTION
                existing.confidence = Confidence.CONFIRMED
                existing.status = PlanStatus.PLANNED
                existing.teacher_override = _override_record(inst, day_spec)
                if assessments:
                    existing.assessment = Assessment(
                        name=", ".join(assessments),
                        subject=subject,
                        day=day,
                        date=date,
                        authority=Authority.OWNER_INSTRUCTION,
                        confidence=Confidence.CONFIRMED,
                    )
                continue

            plan.upsert_day(DayPlan(
                subject=subject,
                day=day,
                date=date,
                lesson=lesson,
                classwork=[lesson] if lesson else [],
                assessment=Assessment(
                    name=", ".join(assessments), subject=subject, day=day, date=date,
                    authority=Authority.OWNER_INSTRUCTION, confidence=Confidence.CONFIRMED,
                ) if assessments else None,
                authority=Authority.OWNER_INSTRUCTION,
                confidence=Confidence.CONFIRMED,
                status=PlanStatus.PLANNED,
                teacher_override=_override_record(inst, day_spec),
            ))
    return plan


def _override_record(inst: dict[str, Any], day_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "owner_instruction",
        "instruction_id": inst.get("id"),
        "reason": inst.get("reason"),
        "day": day_spec.get("day"),
        "assessment_date": day_spec.get("date"),
        "lesson": day_spec.get("lesson"),
        "assessments": day_spec.get("assessments") or [],
    }


def command_self_test() -> int:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
    apply_owner_instructions(plan)
    thu = plan.day("math", "Thursday")
    fri = plan.day("math", "Friday")
    assert thu is not None and thu.authority == Authority.OWNER_INSTRUCTION
    assert thu.teacher_override["reason"] and "Halloween" in thu.teacher_override["reason"]
    assert thu.assessment is not None and thu.assessment.date == "2026-10-29"
    assert "Written Assessment 7" in thu.assessment.name and "Fact Assessment 7" in thu.assessment.name
    assert fri is not None and fri.lesson == "INV 4"
    assert fri.authority == Authority.OWNER_INSTRUCTION
    # Idempotent + never lowers an existing override.
    apply_owner_instructions(plan)
    assert plan.day("math", "Thursday").authority == Authority.OWNER_INSTRUCTION
    # Non-matching week is untouched.
    other = WeeklyPlan(week_id="Q2W4", quarter=2, week=4)
    apply_owner_instructions(other)
    assert other.subjects == {}
    print("PASS weekly-planner-agent owner-instructions self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
