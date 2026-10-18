"""reminders.due: incomplete reminders due today or overdue (read-only)."""
from __future__ import annotations

from datetime import datetime

from cos.registry import Tool
from cos.tools.calendar import TITLE_CAP, HelperError, call_helper

KEYWORDS = ("remind", "reminder", "reminders", "todo", "to-do", "task", "tasks", "due",
            "overdue", "deadline", "list")


def normalize(rem: dict, now: datetime) -> dict:
    due_iso = rem.get("due")
    due_text, overdue = None, False
    if due_iso:
        try:
            due = datetime.fromisoformat(str(due_iso).replace("Z", "+00:00")).astimezone()
            overdue = due.date() < now.date()
            due_text = due.strftime("%a %b ") + str(due.day) if overdue else (
                "today" if rem.get("date_only") else due.strftime("%I:%M %p").lstrip("0"))
        except ValueError:
            pass
    return {"title": str(rem.get("title") or "(no title)")[:TITLE_CAP],
            "due": due_text, "overdue": overdue, "list": str(rem.get("list") or "")[:60],
            "due_iso": due_iso}


def due(ctx, args: dict) -> dict:
    try:
        data = call_helper(ctx, ["reminders", "--due-within-days", "1"])
    except HelperError as e:
        return {"error": str(e)}
    return reminders_result(ctx, data)


def reminders_result(ctx, data: dict) -> dict:
    """The tool result for helper output (also used by fixture mode)."""
    now = ctx.clock()
    items = [normalize(r, now) for r in data.get("reminders", []) if isinstance(r, dict)]
    items.sort(key=lambda r: (not r["overdue"], r["due_iso"] or "~"))
    return {"count": len(items), "overdue": sum(r["overdue"] for r in items), "reminders": items}


def tools(ctx):
    return [Tool(
        name="reminders.due",
        description="Owen's incomplete reminders that are due today or overdue (read-only).",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        side_effect="none", data_class="P1", timeout_s=20,
        func=lambda args: due(ctx, args), keywords=KEYWORDS,
    )]
