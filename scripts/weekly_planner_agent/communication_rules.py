"""Standing assessment communication rules.

Formalizes the first-announcement / day-before-reminder / date-change logic so
it is deterministic and testable. No live Canvas write and no scheduling here:
these functions only compute the planned communication artifacts and the
required actions for a date change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from .models import Assessment


def _day_index(day: str) -> int:
    order = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    return order.index(day) if day in order else 0


def first_announcement_plan(
    assessment: Assessment, *, week_start: date, now: date | None = None
) -> dict[str, Any]:
    """FIRST ANNOUNCEMENT: ~one weekend in advance, no later than the Friday before.

    The Friday before the assessment is the hard deadline. The weekend before
    (Saturday/Sunday) is the ideal window. Returns the target date and whether
    it is late.
    """
    if assessment.day is None and assessment.date is None:
        return {"error": "assessment has no day/date"}
    if assessment.day is not None:
        test_day_index = _day_index(assessment.day)
        # The Monday of the assessment week is week_start.
        test_date = week_start + timedelta(days=test_day_index)
    else:
        test_date = date.fromisoformat(assessment.date)
    # Friday of the assessment week: the deadline.
    days_to_friday = 4 - test_date.weekday()
    friday_before = test_date + timedelta(days=days_to_friday - 7)
    # Ideal: the weekend before that Friday (the preceding Saturday).
    ideal = friday_before - timedelta(days=1)
    now = now or date.today()
    return {
        "assessment": assessment.name,
        "test_date": test_date.isoformat(),
        "deadline": friday_before.isoformat(),
        "ideal": ideal.isoformat(),
        "late": now > friday_before,
    }


def day_before_reminder_plan(assessment: Assessment) -> dict[str, Any]:
    """DAY-BEFORE REMINDER: scheduled for the day before the test.

    When a first announcement is created, the reminder must be automatically
    created/scheduled alongside it (delayed send for the day before the test).
    """
    if assessment.day is None and assessment.date is None:
        return {"error": "assessment has no day/date"}
    if assessment.day is not None:
        order = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        test_index = order.index(assessment.day)
        reminder_day = order[(test_index - 1) % 7]
        return {
            "assessment": assessment.name,
            "reminder_day": reminder_day,
            "delayed_send": True,
        }
    test_date = date.fromisoformat(assessment.date)
    return {
        "assessment": assessment.name,
        "reminder_date": (test_date - timedelta(days=1)).isoformat(),
        "delayed_send": True,
    }


@dataclass
class DateChangeAction:
    action: str
    requires_approval: bool
    detail: str
    duplicate_reminder: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "requires_approval": self.requires_approval,
            "detail": self.detail,
            "duplicate_reminder": self.duplicate_reminder,
        }


def handle_date_change(
    *,
    first_announcement_posted: bool,
    reminder_posted: bool,
) -> DateChangeAction:
    """DATE CHANGE LOGIC (four cases, deterministic).

    - before reminder posts  -> reschedule existing planned reminder (no duplicate)
    - before first announcement posts -> update planned/scheduled announcement (no duplicate)
    - first announcement already posted -> propose a correction (requires approval)
    - reminder already posted -> propose corrective communication (requires approval)
    """
    if not reminder_posted and not first_announcement_posted:
        return DateChangeAction(
            action="reschedule_reminder_and_update_announcement",
            requires_approval=False,
            detail="Nothing has posted; reschedule the existing reminder and update the planned announcement.",
        )
    if not reminder_posted and first_announcement_posted:
        return DateChangeAction(
            action="reschedule_reminder_and_correction_announcement",
            requires_approval=True,
            detail="First announcement already posted; propose a correction and reschedule the reminder.",
        )
    if reminder_posted and not first_announcement_posted:
        return DateChangeAction(
            action="update_announcement_and_correction_reminder",
            requires_approval=True,
            detail="Reminder already posted; propose a corrective communication and update the announcement.",
        )
    return DateChangeAction(
        action="corrective_communication",
        requires_approval=True,
        detail="Both first announcement and reminder already posted; propose a corrective communication.",
    )
