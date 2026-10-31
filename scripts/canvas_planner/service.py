"""Canonical local Canvas Planner projection service.

Both the Teacher Workstation screens and ``bin/canvas-weekly-status`` consume
this service. It reads cached JSON only and has no Canvas/network dependency.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.canvas_llm_intake import constants as intake_constants
from scripts.canvas_llm_intake import week_resolution

from .deep_links import deep_link
from .state_root import state_root
from .events import read_events

CONTRACT_VERSION = 1
SCHOOL_YEAR = "2026-2027"
EASTERN = ZoneInfo("America/New_York")

COURSE_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
    "homeroom": "Homeroom newsletter",
}
ARTIFACTS = ("page", "announcement", "assignments", "assessment_reminder")


def _read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    return value


def _iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _week_dir(root: Path, quarter: int, week: int) -> Path:
    return root / "canvas-llm" / "intake" / SCHOOL_YEAR / f"q{quarter}" / f"w{week}"


def _deploy_dir(root: Path, quarter: int, week: int) -> Path:
    return root / "canvas-llm" / "deployments" / SCHOOL_YEAR / f"q{quarter}" / f"w{week}"


def _date_label(date_range: dict[str, str]) -> str:
    try:
        start = datetime.fromisoformat(date_range["start"])
        end = datetime.fromisoformat(date_range["end"])
    except (KeyError, TypeError, ValueError):
        return "Dates unavailable"
    if start.month == end.month:
        return f"{start.strftime('%B')} {start.day}–{end.day}"
    return f"{start.strftime('%B')} {start.day}–{end.strftime('%B')} {end.day}"


def _rollover_at(date_range: dict[str, str]) -> str | None:
    try:
        start = datetime.fromisoformat(date_range["start"]).date()
    except (KeyError, TypeError, ValueError):
        return None
    prior_friday = start.fromordinal(start.toordinal() - 3)
    local = datetime.combine(prior_friday, time(16, 0), tzinfo=EASTERN)
    return _iso(local)


def _stable_id(*parts: str) -> str:
    body = "|".join(str(p) for p in parts)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:20]


def _active_courses(quarter: int) -> list[str]:
    return [*intake_constants.active_subject_keys_for_quarter(quarter), "homeroom"]


def _approval_state(record: dict[str, Any], artifact: str, required: bool) -> str:
    if not required:
        return "not_required"
    state = (record.get(artifact) or {}).get("state", "PENDING")
    if state == "APPROVED":
        return "approved"
    if (record.get(artifact) or {}).get("invalidated_at"):
        return "stale"
    if state == "BLOCKED":
        return "blocked"
    return "to_review"


def _course_projection(
    course: str,
    *,
    manifest: dict[str, Any],
    approvals: dict[str, Any],
    assignments: list[dict[str, Any]],
    reminders: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    ai_review: dict[str, Any],
) -> dict[str, Any]:
    label = COURSE_LABELS[course]
    if course == "homeroom":
        review = (ai_review.get("courses") or {}).get(course, {})
        return {
            "id": course,
            "name": label,
            "stages": {
                "source": "done" if manifest else "missing",
                "plan": "done" if manifest else "not_started",
                "ai_review": _ai_state(review),
                "assignments": "not_required",
                "preview": "approved" if (manifest.get("homeroom_approved") is True) else "to_review",
            },
        }

    record = approvals.get(course) or {}
    course_questions = [q for q in questions if q.get("subject") == course and q.get("status") != "ANSWERED"]
    manifest_subject = (manifest.get("subjects") or {}).get(course) or {}
    plan_done = manifest_subject.get("state") not in (None, "PENDING", "NEEDS_INPUT") and not course_questions
    has_assignments = any(a.get("course") == course for a in assignments)
    has_reminders = any(r.get("course") == label for r in reminders)
    assignment_state = _approval_state(record, "assignments", has_assignments)
    required_states = [
        _approval_state(record, "page", True),
        _approval_state(record, "announcement", True),
        assignment_state,
        _approval_state(record, "assessment_reminder", has_reminders),
    ]
    if "blocked" in required_states:
        preview = "blocked"
    elif "stale" in required_states:
        preview = "stale"
    elif all(value in ("approved", "not_required") for value in required_states):
        preview = "approved"
    else:
        preview = "to_review"
    return {
        "id": course,
        "name": label,
        "stages": {
            "source": "done" if manifest.get("source_hash") else "missing",
            "plan": "done" if plan_done else ("needs_you" if course_questions else "to_review"),
            "ai_review": _ai_state((ai_review.get("courses") or {}).get(course, {})),
            "assignments": assignment_state,
            "preview": preview,
        },
    }


def _ai_state(review: dict[str, Any]) -> str:
    state = str(review.get("state") or "NOT_RUN").upper()
    return {
        "PASS": "passed",
        "WARN": "passed",
        "NEEDS_OWEN": "needs_you",
        "FAIL": "needs_you",
        "UNAVAILABLE": "unavailable",
        "STALE": "stale",
    }.get(state, "not_run")


class CanvasPlannerService:
    """Read/project the authoritative JSON packet tree."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else state_root()

    def available_weeks(self) -> list[tuple[int, int]]:
        base = self.root / "canvas-llm" / "intake" / SCHOOL_YEAR
        found: list[tuple[int, int, str]] = []
        for path in base.glob("q*/w*/intake-manifest.json"):
            data = _read_json(path, {})
            try:
                found.append((int(data["quarter"]), int(data["week"]), str((data.get("date_range") or {}).get("start", ""))))
            except (KeyError, TypeError, ValueError):
                continue
        return [(q, w) for q, w, _ in sorted(found, key=lambda item: item[2])]

    def select_week(self) -> tuple[int, int]:
        weeks = self.available_weeks()
        if not weeks:
            raise FileNotFoundError(f"no Canvas intake packets under {self.root}")
        for quarter, week in weeks:
            manifest = _read_json(_week_dir(self.root, quarter, week) / "intake-manifest.json", {})
            if manifest.get("status") != "PUBLISHED_VERIFIED":
                return quarter, week
        return weeks[-1]

    def weekly_status(
        self,
        quarter: int | None = None,
        week: int | None = None,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if quarter is None or week is None:
            quarter, week = self.select_week()
        now = now or datetime.now(timezone.utc)
        week_dir = _week_dir(self.root, quarter, week)
        deploy_dir = _deploy_dir(self.root, quarter, week)
        manifest = _read_json(week_dir / "intake-manifest.json", {})
        if not manifest:
            raise FileNotFoundError(f"no packet for Q{quarter}W{week}")
        approvals_doc = _read_json(week_dir / "approvals" / "approval-manifest.json", {})
        approvals = approvals_doc.get("subjects") or {}
        questions = _read_json(week_dir / "questions" / "questions.json", [])
        assignments = _read_json(week_dir / "drafts" / "assignments.json", [])
        reminders = _read_json(week_dir / "drafts" / "assessment-reminders.json", [])
        changes = _read_json(week_dir / "changes.json", {})
        ai_review = _read_json(week_dir / "planner" / "ai-review.json", {})
        homeroom_approval = _read_json(week_dir / "planner" / "homeroom-approval.json", {})
        manifest = dict(manifest)
        manifest["homeroom_approved"] = homeroom_approval.get("state") == "APPROVED"
        week_code = str(manifest.get("week_code") or f"Q{quarter}W{week}")
        # A hash-bound weekly Homeroom newsletter approval satisfies the
        # Homeroom gate (exact body hash + weekly page id + week).
        if not manifest["homeroom_approved"]:
            try:
                from scripts.canvas_llm_rollover import homeroom_weekly as _hw
                html_ok, _html_problems = _hw.verify_at(
                    week_dir, course_id=26429, week_code_value=week_code,
                )
                manifest["homeroom_approved"] = html_ok
            except Exception:  # noqa: BLE001 - status is best-effort
                pass
        rollover_ledger = _read_json(deploy_dir / "rollover-ledger.json", {})
        verified = _read_json(deploy_dir / "published-verified-ledger.json", {})
        courses = [
            _course_projection(
                course,
                manifest=manifest,
                approvals=approvals,
                assignments=assignments,
                reminders=reminders,
                questions=questions,
                ai_review=ai_review,
            )
            for course in _active_courses(quarter)
        ]
        actions = self._actions(
            week_code=week_code,
            manifest=manifest,
            courses=courses,
            questions=questions,
            changes=changes,
            ai_review=ai_review,
            now=now,
            rollover_ledger=rollover_ledger,
            verified=verified,
        )
        rollover_at = _rollover_at(manifest.get("date_range") or {})
        rollover_state = self._rollover_state(
            courses=courses,
            verified=verified,
            ledger=rollover_ledger,
            rollover_at=rollover_at,
            now=now,
        )
        week_state = self._week_state(courses, actions, rollover_state, manifest, ai_review)
        return {
            "domain": "canvas_weekly_planning",
            "contract_version": CONTRACT_VERSION,
            "generated_at": _iso(now),
            "week": {
                "code": week_code,
                "label": _date_label(manifest.get("date_range") or {}),
                "state": week_state,
                "source_synced_at": manifest.get("source_retrieved_at"),
                "rollover_at": rollover_at,
                "rollover_state": rollover_state,
            },
            "courses": courses,
            "next_action": self._next_action(week_code, courses, actions, rollover_state),
            "action_items": actions,
            "completed": self._completed(),
        }

    def planner_week(self, quarter: int, week: int, *, now: datetime | None = None) -> dict[str, Any]:
        """Return the complete local view model for every Planner screen."""
        from scripts.canvas_llm_deploy.plan import compose_announcement_body
        from .approval_bundle import current_bundle, reapproval_diff

        week_dir = _week_dir(self.root, quarter, week)
        manifest = _read_json(week_dir / "intake-manifest.json", {})
        if not manifest:
            raise FileNotFoundError(f"no packet for Q{quarter}W{week}")
        status = self.weekly_status(quarter, week, now=now)
        normalized = _read_json(week_dir / "normalized" / "week.json", {})
        assignments = _read_json(week_dir / "drafts" / "assignments.json", [])
        announcements = _read_json(week_dir / "drafts" / "announcements.json", [])
        reminders = _read_json(week_dir / "drafts" / "assessment-reminders.json", [])
        questions = _read_json(week_dir / "questions" / "questions.json", [])
        approvals = (_read_json(week_dir / "approvals" / "approval-manifest.json", {}).get("subjects") or {})
        overrides = _read_json(week_dir / "owner-overrides.json", {})
        ai = _read_json(week_dir / "planner" / "ai-review.json", {})
        changes = _read_json(week_dir / "changes.json", {})
        source_snapshot = _read_json(week_dir / "source" / "pacing-snapshot.json", {})
        proposal = _read_json(week_dir / "planner" / "source-proposal.json", {})
        sheet_preview = _read_json(week_dir / "planner" / "source-change-preview.json", {})
        sheet_preview.pop("normalized", None)
        source_config = _read_json(self.root / "canvas-planner" / "pacing-source.json", {})
        courses: list[dict[str, Any]] = []
        projected = {course["id"]: course for course in status["courses"]}
        for course in _active_courses(quarter):
            bundle = current_bundle(quarter, week, course)
            label = COURSE_LABELS[course]
            announcement = next((a for a in announcements if a.get("course") == label), {})
            page_html = str(bundle["artifacts"]["page"] or "")
            announcement_html = compose_announcement_body(announcement, page_html) if course != "homeroom" else ""
            days = []
            for weekday in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
                source_cell = self._source_cell(normalized, course, weekday)
                override = overrides.get(f"{course}|{weekday}") or {}
                if not override.get("active", True):
                    override = {}
                date_value = ((normalized.get("days") or {}).get(weekday) or {}).get("date")
                days.append({
                    "day": weekday,
                    "date": date_value,
                    "sheet_says": source_cell,
                    "in_class": override.get("in_class") or ([source_cell] if source_cell else []),
                    "at_home": override.get("at_home"),
                    "edited": bool(override),
                    "status": override.get("status") or ("PLANNED" if source_cell else "PENDING_SOURCE"),
                    "assignments": [a for a in assignments if a.get("course") == course and a.get("due_date") == date_value],
                    "reminders": [r for r in reminders if r.get("course") == label and r.get("assessment_date") == date_value],
                })
            courses.append({
                **projected[course],
                "days": days,
                "page_html": page_html,
                "announcement": {**announcement, "exact_html": announcement_html,
                                 "posting_time": status["week"]["rollover_at"]},
                "assignments": bundle["artifacts"]["assignments"],
                "reminders": bundle["artifacts"]["assessment_reminder"],
                "hashes": bundle["hashes"],
                "approvals": approvals.get(course) or {},
                "reapproval": reapproval_diff(quarter, week, course),
                "ai_review": (ai.get("courses") or {}).get(course, {}),
            })
        week_list = self.available_weeks()
        index = week_list.index((quarter, week)) if (quarter, week) in week_list else -1
        previous = week_list[index - 1] if index > 0 else None
        following = week_list[index + 1] if 0 <= index < len(week_list) - 1 else None
        return {
            "status": status,
            "week": {
                **status["week"],
                "quarter": quarter,
                "number": week,
                "date_range": manifest.get("date_range") or {},
                "previous": self._week_ref(previous),
                "next": self._week_ref(following),
            },
            "source": {
                "name": source_config.get("name") or manifest.get("pacing_source", "2026-2027 FPK Pacing Guides"),
                "tab": source_config.get("tab") or manifest.get("pacing_tab", "4A - Reagan"),
                "synced_at": manifest.get("source_retrieved_at"),
                "connected": bool(source_snapshot),
                "spreadsheet_id": source_config.get("spreadsheet_id") or source_snapshot.get("spreadsheet_id"),
                "proposal": proposal,
                "changes": changes,
                "sheet_preview": sheet_preview,
            },
            "courses": courses,
            "questions": questions,
            "ai_review": ai,
            "history": read_events(week_dir)[-100:][::-1],
            "settings": {
                "state_root": str(self.root),
                "source_hash": manifest.get("source_hash"),
                "page_lookup": manifest.get("page_lookup") or {},
                "approval_updated_at": _read_json(week_dir / "approvals" / "approval-manifest.json", {}).get("updated_at"),
                "automatic_rollover": __import__(
                    "scripts.canvas_planner.friday", fromlist=["load_settings"]
                ).load_settings(self.root / "canvas-planner")["automatic_rollover"],
                "system_status": {
                    "domain": status["domain"],
                    "contract_version": status["contract_version"],
                    "generated_at": status["generated_at"],
                    "week_state": status["week"]["state"],
                    "rollover_state": status["week"]["rollover_state"],
                    "action_item_count": len(status["action_items"]),
                },
            },
        }

    @staticmethod
    def _week_ref(value: tuple[int, int] | None) -> dict[str, Any] | None:
        return {"quarter": value[0], "week": value[1], "code": f"Q{value[0]}W{value[1]}"} if value else None

    @staticmethod
    def _source_cell(normalized: dict[str, Any], course: str, weekday: str) -> str:
        subjects = ((normalized.get("days") or {}).get(weekday) or {}).get("subjects") or {}
        if course == "reading_spelling":
            reading = str((subjects.get("reading") or {}).get("raw") or "")
            spelling = str((subjects.get("spelling") or {}).get("raw") or "")
            return " · ".join(part for part in (f"Reading {reading}" if reading else "", f"Spelling {spelling}" if spelling else "") if part)
        if course == "homeroom":
            return "Approved Homeroom newsletter source"
        return str((subjects.get(course) or {}).get("raw") or "")

    def _actions(
        self,
        *,
        week_code: str,
        manifest: dict[str, Any],
        courses: list[dict[str, Any]],
        questions: list[dict[str, Any]],
        changes: dict[str, Any],
        ai_review: dict[str, Any],
        now: datetime,
        rollover_ledger: dict[str, Any],
        verified: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        changed = ((changes.get("delta") or {}).get("changes") or changes.get("changes") or [])
        decision = str(changes.get("decision") or "").upper()
        if changed and decision not in ("APPLIED", "KEPT"):
            for change in changed:
                course = str(change.get("subject") or "")
                before, after = str(change.get("before") or ""), str(change.get("after") or "")
                day = str(change.get("weekday") or change.get("day") or "")
                stamp = manifest.get("source_retrieved_at") or manifest.get("generated_at") or _iso(now)
                items.append(self._item(
                    id_value=f"source-{_stable_id(week_code, course, day, before, after)}",
                    kind="suggestion", priority="high", course=course or None,
                    title=f"Pacing changed for {COURSE_LABELS.get(course, course)} {day}".strip(),
                    reason=f"The sheet changed from {before or 'blank'} to {after or 'blank'}.",
                    evidence=f"sheet · {day} · {before or 'blank'} → {after or 'blank'}",
                    link=deep_link(week_code, "source"), stamp=stamp,
                ))
        for question in questions:
            if question.get("status") == "ANSWERED":
                continue
            course = str(question.get("subject") or "")
            stamp = question.get("created_at") or manifest.get("generated_at") or _iso(now)
            items.append(self._item(
                id_value=str(question.get("question_id") or f"question-{_stable_id(json.dumps(question, sort_keys=True))}"),
                kind="decision", priority="high", course=course or None,
                title=f"{COURSE_LABELS.get(course, course)} needs your decision",
                reason=str(question.get("reason") or "Review this planning question."),
                evidence=str(question.get("source_text") or "local planning packet"),
                link=deep_link(week_code, course, "plan"), stamp=stamp,
            ))
        for course, review in (ai_review.get("courses") or {}).items():
            for finding in review.get("findings") or []:
                if str(finding.get("status") or "").upper() not in ("NEEDS_OWEN", "FAIL"):
                    continue
                stamp = finding.get("created_at") or ai_review.get("created_at") or _iso(now)
                items.append(self._item(
                    id_value=str(finding.get("id") or f"ai-{_stable_id(week_code, course, str(finding.get('title')))}"),
                    kind="decision", priority="high", course=course,
                    title=f"{COURSE_LABELS.get(course, course)} review needs your attention",
                    reason="Review this AI finding and choose how to resolve it.",
                    evidence=str(finding.get("evidence") or "Evidence unavailable"),
                    link=deep_link(week_code, course, "ai"), stamp=stamp,
                ))
        for course in courses:
            if course["stages"]["preview"] in ("approved", "not_required"):
                continue
            cid = course["id"]
            stamp = manifest.get("generated_at") or _iso(now)
            items.append(self._item(
                id_value=f"approval:{week_code.lower()}:{cid}",
                kind="decision", priority="normal", course=cid,
                title=f"{course['name']} page needs your approval",
                reason=f"Review the exact {course['name']} page and related weekly materials before Friday publishing.",
                evidence="local draft hashes and approval history",
                link=deep_link(week_code, cid, "preview"), stamp=stamp,
            ))

        rollover_at = _rollover_at(manifest.get("date_range") or {})
        if rollover_at:
            rollover_local = datetime.fromisoformat(
                rollover_at.replace("Z", "+00:00")
            ).astimezone(EASTERN)
            now_local = now.astimezone(EASTERN)
            published = (
                verified.get("status") == "PUBLISHED_VERIFIED"
                or rollover_ledger.get("lifecycle") == "PUBLISHED_VERIFIED"
            )
            if now_local >= rollover_local and not published:
                items.append(self._item(
                    id_value=f"friday-readiness:{week_code.lower()}",
                    kind="decision", priority="high", course=None,
                    title="Friday rollover didn't run — Publish now when ready",
                    reason="The Friday 4:00 PM rollover did not publish this week. Review approvals, then publish when ready.",
                    evidence="Friday 4:00 PM America/New_York deadline passed without a verified rollover",
                    link=deep_link(week_code, "friday"), stamp=rollover_at,
                ))
        course_order = {course["id"]: index for index, course in enumerate(courses)}

        def action_order(item: dict[str, Any]) -> tuple[int, int, str]:
            link = item["deep_link"]
            stage = 0 if link.endswith("/source") else 1 if "/plan" in link else 2 if "/ai" in link else 3
            return stage, course_order.get(item.get("course"), 99), item["id"]

        return sorted(items, key=action_order)

    @staticmethod
    def _item(*, id_value: str, kind: str, priority: str, course: str | None,
              title: str, reason: str, evidence: str, link: str, stamp: str) -> dict[str, Any]:
        return {
            "id": id_value,
            "kind": kind,
            "priority": priority,
            "course": course,
            "title": title,
            "reason": reason,
            "evidence": evidence,
            "deep_link": link,
            "created_at": stamp,
            "updated_at": stamp,
        }

    @staticmethod
    def _rollover_state(*, courses: list[dict[str, Any]], verified: dict[str, Any],
                        ledger: dict[str, Any], rollover_at: str | None, now: datetime) -> str:
        if verified.get("status") == "PUBLISHED_VERIFIED" or ledger.get("lifecycle") == "PUBLISHED_VERIFIED":
            return "PUBLISHED_VERIFIED"
        if ledger.get("lifecycle") == "EXECUTING":
            return "EXECUTING"
        if any(c["stages"]["preview"] != "approved" for c in courses):
            return "BLOCKED"
        if rollover_at and now < datetime.fromisoformat(rollover_at.replace("Z", "+00:00")):
            return "HELD_UNTIL_4PM"
        return "READY_TO_PUBLISH"

    @staticmethod
    def _week_state(courses: list[dict[str, Any]], actions: list[dict[str, Any]],
                    rollover_state: str, manifest: dict[str, Any], ai_review: dict[str, Any]) -> str:
        if rollover_state in ("PUBLISHED_VERIFIED", "EXECUTING", "HELD_UNTIL_4PM", "READY_TO_PUBLISH"):
            return rollover_state
        if rollover_state == "BLOCKED" and any(c["stages"]["preview"] == "blocked" for c in courses):
            return "BLOCKED"
        if actions:
            return "NEEDS_OWEN"
        if ai_review and all(c["stages"]["ai_review"] == "passed" for c in courses):
            return "AI_REVIEWED"
        if all(c["stages"]["plan"] == "done" for c in courses):
            return "PLANNED"
        return "SOURCE_SYNCED" if manifest.get("source_hash") else "BLOCKED"

    @staticmethod
    def _next_action(week_code: str, courses: list[dict[str, Any]], actions: list[dict[str, Any]],
                     rollover_state: str) -> dict[str, Any]:
        source = next((a for a in actions if a["deep_link"].endswith("/source")), None)
        if source:
            return {"title": "Review pacing changes", "deep_link": source["deep_link"]}
        plan = next((a for a in actions if "/plan" in a["deep_link"]), None)
        if plan:
            return {"title": plan["title"], "deep_link": plan["deep_link"]}
        ai = next((a for a in actions if "/ai" in a["deep_link"]), None)
        if ai:
            return {"title": ai["title"], "deep_link": ai["deep_link"]}
        approval = next((a for a in actions if "/preview" in a["deep_link"]), None)
        if approval:
            return {"title": approval["title"], "deep_link": approval["deep_link"]}
        return {
            "title": "Ready for Friday 4 PM",
            "deep_link": deep_link(week_code, "friday"),
        }

    def _completed(self) -> list[dict[str, Any]]:
        base = self.root / "canvas-llm" / "deployments" / SCHOOL_YEAR
        records: list[dict[str, Any]] = []
        for path in base.glob("q*/w*/published-verified-ledger.json"):
            data = _read_json(path, {})
            if data.get("status") != "PUBLISHED_VERIFIED":
                continue
            code = data.get("week_code") or f"{path.parents[1].name.upper()}{path.parent.name.upper()}"
            records.append({
                "week": code,
                "result": "Published and verified",
                "verified_at": data.get("verified_at"),
            })
        return sorted(records, key=lambda item: str(item["week"]), reverse=True)
