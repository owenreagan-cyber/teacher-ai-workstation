"""Teacher-input model for the Canvas Weekly Intake workspace.

Teacher input is stored locally (gitignored) and applied on regeneration without
overwriting the pacing source or the normalized interpretation. The invariant is:

    SOURCE + NORMALIZED SOURCE + TEACHER INPUT = REGENERATED DRAFT

Input is keyed by stable IDs so regeneration is deterministic and auditable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from . import manifest as mf


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def input_path(quarter: int, week: int) -> Path:
    return mf.staging_dir(quarter, week) / "teacher-input.json"


def new_input() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "question_answers": {},
        "subjects": {},
        "updated_at": _now(),
    }


def load_input(quarter: int, week: int) -> dict[str, Any]:
    path = input_path(quarter, week)
    if not path.exists():
        return new_input()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_input()
    data.setdefault("question_answers", {})
    data.setdefault("subjects", {})
    return data


def save_input(quarter: int, week: int, data: dict[str, Any]) -> Path:
    data["updated_at"] = _now()
    path = input_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def answer_question(quarter: int, week: int, question_id: int, answer: str) -> dict[str, Any]:
    """Record a teacher answer to an open question (append to history)."""
    data = load_input(quarter, week)
    data["question_answers"][str(question_id)] = {
        "answer": answer,
        "answered_at": _now(),
        "source": "OWNER_INPUT",
    }
    save_input(quarter, week, data)
    return data["question_answers"][str(question_id)]


def subject_input(data: dict[str, Any], subject: str) -> dict[str, Any]:
    """Return the mutable subject-input block (create if absent)."""
    data.setdefault("subjects", {})
    data["subjects"].setdefault(subject, {})
    return data["subjects"][subject]


def apply_input(
    *,
    quarter: int,
    week: int,
    subject: str,
    op: str,
    value: Any,
) -> dict[str, Any]:
    """Apply one teacher-input operation to the local input store.

    Supported ops:
      - add_reminder       value: str  (append a reminder line)
      - remove_assignment  value: str  (assignment title to reject)
      - reject_assignment  value: str  (assignment title to reject)
      - restore_assignment value: str  (remove a rejection)
      - add_note           value: str  (append a subject note)
      - add_special_event  value: str  (append a special-event note)
      - add_assessment_note value: str (append an assessment note)
      - replace_announcement value: str (override announcement wording)
    """
    data = load_input(quarter, week)
    block = subject_input(data, subject)

    list_ops = ("add_reminder", "add_note", "add_special_event", "add_assessment_note")
    if op in list_ops:
        block.setdefault(op, []).append(value)
    elif op in ("remove_assignment", "reject_assignment"):
        block.setdefault("reject_assignments", []).append(value)
    elif op == "restore_assignment":
        rej = block.setdefault("reject_assignments", [])
        if value in rej:
            rej.remove(value)
    elif op == "replace_announcement":
        block["replace_announcement"] = value
    else:
        raise ValueError(f"unknown teacher-input op {op!r}")
    save_input(quarter, week, data)
    return block


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        # Use a temp staging root by monkeypatching.
        import scripts.canvas_llm_intake.manifest as mf
        orig = mf.staging_dir
        mf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            empty = load_input(2, 2)
            assert empty["question_answers"] == {} and empty["subjects"] == {}
            answer_question(2, 2, 1, "Interpret as Lesson 41")
            d = load_input(2, 2)
            assert d["question_answers"]["1"]["answer"] == "Interpret as Lesson 41"
            assert d["question_answers"]["1"]["source"] == "OWNER_INPUT"

            apply_input(quarter=2, week=2, subject="math", op="add_reminder", value="Test reminder")
            apply_input(quarter=2, week=2, subject="math", op="reject_assignment", value="SM5: Lesson 36 Homework")
            apply_input(quarter=2, week=2, subject="math", op="restore_assignment", value="SM5: Lesson 36 Homework")
            d2 = load_input(2, 2)
            assert "Test reminder" in d2["subjects"]["math"]["add_reminder"]
            assert d2["subjects"]["math"]["reject_assignments"] == []  # restored

            # Unknown op fails closed.
            try:
                apply_input(quarter=2, week=2, subject="math", op="bogus", value="x")
                raise AssertionError("expected ValueError")
            except ValueError:
                pass
        finally:
            mf.staging_dir = orig
    print("PASS intake teacher-input self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
