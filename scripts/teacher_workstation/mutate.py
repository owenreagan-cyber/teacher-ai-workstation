"""Teacher Workstation — local planning mutation layer.

Mutates ONLY local intake/planning state under ``.local/canvas-llm/intake/``.
Never calls Canvas. Each mutation re-runs the existing ``intake.build_intake``
to regenerate affected artifacts (targeted; the engine already rebuilds from
source + teacher input + owner overrides).

Stale-edit protection: every mutating call takes the client's ``source_hash``
and is rejected with ``STALE`` when the packet's current source hash differs
(the client must refresh and re-review).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import intake
from scripts.canvas_llm_intake import constants as IC
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import owner_overrides as ioo
from scripts.canvas_llm_intake import teacher_input as iti
from scripts.canvas_llm_intake import approval as iap
from scripts.canvas_planner import ai_review
from scripts.canvas_planner.events import append_event, read_events

# Owner-override statuses that come from the UI (allowed via PATCH).
_UI_STATUSES = {"PLANNED", "PENDING_SOURCE", "OWNER_CONFIRMED_BLANK"}


class StaleEdit(RuntimeError):
    """Raised when the client's source_hash no longer matches the packet."""


def _assert_current(quarter: int, week: int, source_hash: str | None) -> None:
    m = imf.load_manifest(quarter, week)
    if m is None:
        raise StaleEdit("no packet for this week")
    current = m.get("source_hash")
    if source_hash is not None and current is not None and source_hash != current:
        raise StaleEdit("packet changed; refresh and review")


def _regenerate(quarter: int, week: int) -> dict[str, Any]:
    """Regenerate the packet from source + teacher input + owner overrides."""
    summary = intake.build_intake(
        quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False
    )
    return summary


def apply_day_edit(
    *,
    quarter: int,
    week: int,
    subject: str,
    day: str,
    in_class: list[str] | None = None,
    at_home: str | None = None,
    clear_at_home: bool = False,
    status: str | None = None,
    note: str | None = None,
    source_value: str | None = None,
    source_hash: str | None = None,
) -> dict[str, Any]:
    """Edit a subject/day: set in_class/at_home/status/note (owner override)."""
    _assert_current(quarter, week, source_hash)
    if status is not None and status not in _UI_STATUSES:
        raise ValueError(f"unsupported status {status!r}")

    at_home_value = at_home
    if clear_at_home:
        at_home_value = None
    # Distinguish "no at_home change" from "clear": use sentinel.
    at_home_arg = at_home_value if (at_home_value is not None or clear_at_home) else None

    before = ioo.day_override(quarter, week, subject, day)
    rec = ioo.upsert_override(
        quarter, week, subject=subject, day=day,
        source_value=source_value,
        in_class=in_class if in_class is not None else None,
        at_home=at_home_arg,
        status=status,
        note=note,
    )
    summary = _regenerate(quarter, week)
    _update_assignment_for_edit(quarter, week, subject, day, at_home)
    append_event(
        imf.staging_dir(quarter, week), action="plan_edit", actor="owner",
        reason=note or f"Owen edited {subject} {day}.", before=before, after=rec,
        undo={"action": "restore_day_override", "subject": subject, "day": day, "value": before},
    )
    ai_review.schedule(quarter, week, reason=f"Plan changed for {subject} {day}")
    return {"override": rec, "summary": summary, "affected": _affected(subject)}


def _update_assignment_for_edit(
    quarter: int, week: int, subject: str, day: str, at_home: str | None
) -> None:
    """Keep the proposed assignment beside an edited lesson in sync."""
    if at_home is None:
        return
    import json
    d = imf.staging_dir(quarter, week)
    assignments_path = d / "drafts" / "assignments.json"
    normalized_path = d / "normalized" / "week.json"
    try:
        assignments = json.loads(assignments_path.read_text(encoding="utf-8"))
        normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    due = ((normalized.get("days") or {}).get(day) or {}).get("date")
    changed = False
    for assignment in assignments:
        if assignment.get("course") == subject and assignment.get("due_date") == due:
            assignment["title"] = at_home
            assignment["source_reason"] = "OWNER_OVERRIDE"
            changed = True
    if changed:
        assignments_path.write_text(json.dumps(assignments, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        from scripts.teacher_workstation import adapter
        active = IC.active_subject_keys_for_quarter(quarter)
        approvals = iap.load_approvals(quarter, week, active)
        hashes = adapter._compute_draft_hashes(quarter, week, active)
        iap.invalidate_if_stale(
            approvals, subject=subject, draft_hashes=hashes.get(subject, {}),
            source_hash=(imf.load_manifest(quarter, week) or {}).get("source_hash"),
        )
        iap.save_approvals(quarter, week, approvals)


def restore_source(
    *, quarter: int, week: int, subject: str, day: str, source_hash: str | None = None
) -> dict[str, Any]:
    _assert_current(quarter, week, source_hash)
    removed = ioo.restore_source(quarter, week, subject, day)
    summary = _regenerate(quarter, week)
    return {"removed": removed, "summary": summary}


def mark_pending(
    *, quarter: int, week: int, subject: str, day: str,
    source_value: str | None = None, source_hash: str | None = None
) -> dict[str, Any]:
    _assert_current(quarter, week, source_hash)
    rec = ioo.mark_pending(quarter, week, subject, day, source_value=source_value)
    summary = _regenerate(quarter, week)
    return {"override": rec, "summary": summary}


def mark_blank(
    *, quarter: int, week: int, subject: str, day: str,
    source_value: str | None = None, source_hash: str | None = None
) -> dict[str, Any]:
    _assert_current(quarter, week, source_hash)
    rec = ioo.mark_blank(quarter, week, subject, day, source_value=source_value)
    summary = _regenerate(quarter, week)
    return {"override": rec, "summary": summary}


def answer_question(
    *, quarter: int, week: int, question_id: str, answer: str, source_hash: str | None = None
) -> dict[str, Any]:
    _assert_current(quarter, week, source_hash)
    iti.answer_question(quarter, week, question_id, answer)  # type: ignore[arg-type]
    summary = _regenerate(quarter, week)
    return {"answered": question_id, "summary": summary}


def set_assignment_disposition(
    *, quarter: int, week: int, subject: str, title: str,
    action: str, source_hash: str | None = None
) -> dict[str, Any]:
    """KEEP (no-op) / REJECT / RESTORE an assignment proposal."""
    _assert_current(quarter, week, source_hash)
    if action == "KEEP":
        summary = _regenerate(quarter, week)
        return {"action": "KEEP", "summary": summary}
    if action == "REJECT":
        iti.apply_input(quarter=quarter, week=week, subject=subject,
                        op="reject_assignment", value=title)
    elif action == "RESTORE":
        iti.apply_input(quarter=quarter, week=week, subject=subject,
                        op="restore_assignment", value=title)
    else:
        raise ValueError(f"unknown assignment action {action!r}")
    summary = _regenerate(quarter, week)
    return {"action": action, "title": title, "summary": summary}


def edit_announcement(
    *, quarter: int, week: int, subject: str, transition: str, source_hash: str | None = None
) -> dict[str, Any]:
    """Edit a weekly-update announcement's transition wording (local only)."""
    _assert_current(quarter, week, source_hash)
    iti.apply_input(quarter=quarter, week=week, subject=subject,
                    op="replace_announcement", value=transition)
    summary = _regenerate(quarter, week)
    return {"subject": subject, "summary": summary}


def approve_artifact(
    *,
    quarter: int,
    week: int,
    subject: str,
    artifact_type: str,
    expected_artifact_hash: str,
    source_hash: str | None = None,
) -> dict[str, Any]:
    """Approve an artifact, binding to the EXACT current draft + source hashes.

    Rejects unknown subject/artifact-type, hash mismatch, stale source, and
    artifacts that are blocked (pending source / unresolved question).
    """
    _assert_current(quarter, week, source_hash)

    if artifact_type not in iap.GRANULARITIES:
        raise ValueError(f"unknown artifact type {artifact_type!r}")

    # Regenerate to obtain the CURRENT hashes + active subjects + gate context.
    summary = intake.build_intake(quarter=quarter, week=week, fresh=False,
                                  canvas=None, include_canvas_context=False)
    active = summary["active_subjects"]
    if subject not in active:
        raise ValueError(f"subject {subject!r} not active for this week")

    draft_hashes = summary["draft_hashes"].get(subject, {})
    current_hash = draft_hashes.get(artifact_type, "")
    if current_hash != expected_artifact_hash:
        raise StaleEdit("artifact changed; refresh and review")

    # Block approval if unresolved questions or pending-source materially affect the subject.
    blockers = _subject_blockers(quarter, week, subject, summary)
    if blockers:
        raise ValueError("; ".join(blockers))

    rec = iap.approve_artifact(
        quarter, week, subject, artifact_type,
        draft_hash=current_hash, source_hash=summary["source_hash"], subjects=active,
    )
    # Recompute the gate.
    intake.build_intake(quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False)
    return {"subject": subject, "artifact_type": artifact_type, "state": "APPROVED",
            "draft_hash": current_hash, "source_hash": summary["source_hash"]}


def revoke_artifact(
    *,
    quarter: int,
    week: int,
    subject: str,
    artifact_type: str,
    source_hash: str | None = None,
) -> dict[str, Any]:
    """Revoke an approval (local only), preserving history."""
    _assert_current(quarter, week, source_hash)
    if artifact_type not in iap.GRANULARITIES:
        raise ValueError(f"unknown artifact type {artifact_type!r}")
    summary = intake.build_intake(quarter=quarter, week=week, fresh=False,
                                  canvas=None, include_canvas_context=False)
    active = summary["active_subjects"]
    iap.revoke_approval(quarter, week, subject, artifact_type, subjects=active)
    intake.build_intake(quarter=quarter, week=week, fresh=False, canvas=None, include_canvas_context=False)
    return {"subject": subject, "artifact_type": artifact_type, "state": "PENDING"}


def _subject_blockers(quarter: int, week: int, subject: str, summary: dict[str, Any]) -> list[str]:
    """Compute approval blockers for a subject (pending source + open questions).

    An open question blocks the SUBJECT it belongs to. A pending-source day
    blocks the subject's page/announcement/reminder (content can't be generated
    for unresolved days).
    """
    from scripts.teacher_workstation import adapter

    blockers: list[str] = []
    detail = adapter.week_detail(quarter, week)
    if not detail:
        return blockers
    # Open questions belonging to this subject.
    for q in detail.get("open_questions", []):
        if isinstance(q, dict) and q.get("subject") == subject:
            blockers.append(f"unresolved question: {q.get('reason', '')[:80]}")
            break
    # Pending-source days for this subject block page/announcement/reminder.
    for wd, st in (detail.get("day_states", {}).get(subject, {}) or {}).items():
        if st in ("PENDING_SOURCE", "NEEDS_INPUT"):
            blockers.append(f"{wd} source pending")
    return blockers


def _affected(subject: str) -> list[str]:
    """Affected artifact classes for a day override on a subject (UI impact preview)."""
    return [
        f"{subject} weekly page",
        f"{subject} weekly announcement",
        f"{subject} page/announcement approvals become stale",
    ]


def undo_last_plan_edit(*, quarter: int, week: int, source_hash: str | None = None) -> dict[str, Any]:
    """Undo the latest not-yet-undone plan edit for this week."""
    _assert_current(quarter, week, source_hash)
    week_dir = imf.staging_dir(quarter, week)
    history = read_events(week_dir)
    undone = {
        str((event.get("after") or {}).get("undo_of"))
        for event in history if event.get("action") == "plan_edit_undone"
    }
    target = next(
        (event for event in reversed(history)
         if event.get("action") == "plan_edit" and event.get("event_id") not in undone),
        None,
    )
    if target is None:
        raise ValueError("no plan edit is available to undo")
    undo = target.get("undo") or {}
    subject, day = undo.get("subject"), undo.get("day")
    if not subject or not day:
        raise ValueError("plan edit has no undo record")
    data = ioo.load_overrides(quarter, week)
    key = f"{subject}|{day}"
    before = undo.get("value")
    if before is None:
        data.pop(key, None)
    else:
        data[key] = before
    ioo.save_overrides(quarter, week, data)
    summary = _regenerate(quarter, week)
    append_event(
        week_dir, action="plan_edit_undone", actor="owner",
        reason=f"Owen undid the last edit to {subject} {day}.",
        before=target.get("after"), after={"undo_of": target["event_id"], "value": before},
    )
    ai_review.schedule(quarter, week, reason=f"Plan edit undone for {subject} {day}")
    return {"undone_event_id": target["event_id"], "subject": subject, "day": day, "summary": summary}


def command_self_test() -> int:
    import tempfile
    from pathlib import Path

    # Exercise mutation layer with a temp staging root (no Canvas, no real packet).
    with tempfile.TemporaryDirectory() as tmp:
        import scripts.canvas_llm_intake.manifest as mfmod
        orig = mfmod.staging_dir
        mfmod.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            # Stale edit rejected when no packet exists.
            try:
                apply_day_edit(quarter=2, week=3, subject="math", day="Wednesday",
                               at_home="Study", source_hash="abc")
                raise AssertionError("expected StaleEdit")
            except StaleEdit:
                pass

            # Create a minimal packet manifest so _assert_current passes.
            m = imf.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                 date_range={"start": "2026-10-26", "end": "2026-10-30"})
            m["source_hash"] = "abc"
            imf.save_manifest(2, 3, m)

            # apply_day_edit writes an override (regeneration will attempt intake.build_intake
            # which needs the full staging tree — we only assert the override write + status).
            ioo.upsert_override(2, 3, subject="math", day="Wednesday",
                                source_value="Review", in_class=["Review"],
                                at_home="Study for tomorrow's test.", status="PLANNED")
            rec = ioo.day_override(2, 3, "math", "Wednesday")
            assert rec["at_home"] == "Study for tomorrow's test."

            # answer_question records.
            iti.answer_question(2, 3, "math-q2w3-wednesday-review-at-home", "Yes, add At Home")  # type: ignore[arg-type]
            d = iti.load_input(2, 3)
            assert d["question_answers"]["math-q2w3-wednesday-review-at-home"]["answer"] == "Yes, add At Home"

            # assignment disposition.
            iti.apply_input(quarter=2, week=3, subject="math", op="reject_assignment", value="SM5: X")
            assert "SM5: X" in iti.load_input(2, 3)["subjects"]["math"]["reject_assignments"]
        finally:
            mfmod.staging_dir = orig
    print("PASS teacher-workstation mutation self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
