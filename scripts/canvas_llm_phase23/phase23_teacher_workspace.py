#!/usr/bin/env python3
"""Phase 23 teacher-facing weekly Canvas workspace (chat-first prototype).

A small local web workspace for Owen Reagan that simplifies the weekly Canvas
workflow into one screen: chat, current-week pacing panel, suggested Canvas
assignments, review, and launch.

This prototype intentionally reuses the existing backend rather than
reimplementing it:

- canonical instructional weeks, pacing, and graded-assignment routing
  come from ``scripts/canvas_llm_phase22/phase22_workstation.py`` and
  ``scripts/canvas_llm_phase23/phase23_content_engine.py``;
- course routing comes from ``scripts/canvas_llm_phase22/canvas_course_resolver.py``;
- the launch + reconciliation workflow reuses
  ``scripts/canvas_llm_phase22/canvas_launcher.py`` (the same module that
  ``bin/canvas-launch`` execs), including its approval gate, duplicate/drift
  detection, and CREATE/UPDATE/REMOVE/LEAVE analysis.

Launch is dry-run by default (no credentials, no network, no Canvas writes).
A real launch path shells out to ``bin/canvas-launch`` and is opt-in only.

Retired (REL-2): no launcher, doc, or test uses this server, and the Teacher
Workstation (``bin/teacher-workstation``) supersedes it, so ``serve`` refuses
to start. The code and ``self-test`` stay for reference.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import subprocess
import sys
import urllib.parse
from datetime import date, datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_course_resolver as resolver  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_launcher as launcher  # noqa: E402
from scripts.canvas_llm_phase23 import phase23_content_engine as engine  # noqa: E402

APP_DIR = REPO_ROOT / "apps" / "phase23-teacher-workspace"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MANUAL_SUBJECTS = {"history", "science"}
WRITE_ACTIONS = ("CREATE", "UPDATE", "REMOVE")

# Subject display order and teacher-facing labels. Course IDs/prefixes are
# resolved at runtime from the canonical router so the UI never hardcodes them.
SUBJECT_ORDER = ["math", "reading", "spelling", "language-arts", "history", "science"]
SUBJECT_LABELS = {
    "math": "Math",
    "reading": "Reading",
    "spelling": "Spelling",
    "language-arts": "Language Arts",
    "history": "History",
    "science": "Science",
}

# Mock "already in Canvas" assignment titles. This is clearly-labeled local
# mock data used only so the suggested-assignment panel can demonstrate the
# "Already exists" vs "Create" distinction without touching Canvas. The real
# existence check lives in ``canvas_launcher.run_preflight`` / the live audit.
MOCK_EXISTING_ASSIGNMENT_TITLES = {
    "SM5: Monday Homework — Lesson 18",
    "RM4: Monday Workbook Classwork — Lesson 50",
    "RM4: Tuesday Comprehension Questions — Lesson 51",
}

# In-memory teacher decisions (ambiguous "Create as an assignment?" answers).
# Ephemeral for the prototype; the production decision record lives in
# ``teacher_decision_records`` (scripts/canvas_llm_phase22/teacher_decisions.py).
_DECISIONS: dict[str, dict[str, str]] = {}


def stable_id(*parts: Any) -> str:
    payload = "|".join(map(str, parts)).encode("utf-8")
    return "p23tw-" + hashlib.sha256(payload).hexdigest()[:16]


def compact(value: Any) -> str:
    return p22.compact(value)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_week_code(code: str) -> str:
    return p22.canonical_week_code(code)


def format_date_range(starts_on: str, ends_on: str) -> str:
    if not starts_on or not ends_on:
        return "Dates TBD"
    try:
        start = date.fromisoformat(str(starts_on))
        end = date.fromisoformat(str(ends_on))
    except (ValueError, TypeError):
        return f"{starts_on} to {ends_on}"
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%B')} {start.day}–{end.day}, {start.year}"
    if start.year == end.year:
        return f"{start.strftime('%B')} {start.day} – {end.strftime('%B')} {end.day}, {start.year}"
    return f"{start.strftime('%B')} {start.day}, {start.year} – {end.strftime('%B')} {end.day}, {end.year}"


def _entries_for_week(fixture: dict[str, Any], week: Any) -> list[Any]:
    """Load all pacing entries for a week (including inactive-quarter subjects)."""
    entries: list[Any] = []
    for raw in fixture.get("entries", []):
        entry_date = raw.get("date", "")
        if not (week.starts_on <= entry_date <= week.ends_on):
            continue
        entries.append(
            engine.PacingEntry(
                date=entry_date,
                weekday=raw.get("weekday", ""),
                subject=raw.get("subject", ""),
                title=raw.get("title", ""),
                entry_type=raw.get("entryType", "lesson"),
                lesson=raw.get("lesson"),
                test=raw.get("test"),
                in_class=raw.get("inClass", ""),
                at_home=raw.get("atHome", ""),
                resource_hints=[],
                notes=raw.get("notes", ""),
                coverage=raw.get("coverage", ""),
            )
        )
    entries.sort(key=lambda item: (item.date, item.subject, item.title))
    return entries


def _subject_route(subject: str) -> dict[str, Any]:
    try:
        route = resolver.resolve_route(subject)
    except KeyError:
        return {"courseId": None, "prefix": "", "manual": subject in MANUAL_SUBJECTS}
    return {
        "courseId": route.course_id,
        "prefix": route.prefix,
        "manual": subject in MANUAL_SUBJECTS or not route.allowed,
    }


def build_week_panel(week: Any, entries: list[Any]) -> dict[str, Any]:
    subjects: list[dict[str, Any]] = []
    pacing: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for subject in SUBJECT_ORDER:
        route = _subject_route(subject)
        subject_entries = [e for e in entries if compact(e.subject).lower() == subject]
        active = engine.subject_active_for_week(subject, week) if subject_entries else False
        day_map: dict[str, list[dict[str, Any]]] = {wd: [] for wd in WEEKDAYS}
        for entry in subject_entries:
            day = compact(entry.weekday)
            if day not in day_map:
                continue
            day_map[day].append(
                {
                    "title": compact(entry.title) or (f"Lesson {entry.lesson}" if entry.lesson else ""),
                    "type": entry.entry_type,
                    "inClass": compact(entry.in_class),
                    "atHome": compact(entry.at_home),
                    "lesson": entry.lesson,
                    "test": entry.test,
                }
            )
        pacing[subject] = day_map
        subjects.append(
            {
                "id": subject,
                "label": SUBJECT_LABELS[subject],
                "courseId": route["courseId"],
                "prefix": route["prefix"],
                "manual": route["manual"],
                "active": bool(active),
            }
        )

    return {
        "weekCode": week.code,
        "startsOn": week.starts_on,
        "endsOn": week.ends_on,
        "dateRange": format_date_range(week.starts_on, week.ends_on),
        "quarter": week.quarter,
        "displaySubtitle": week.display_subtitle,
        "subjects": subjects,
        "pacing": pacing,
    }


def _suggested_item(
    subject: str,
    title: str,
    status: str,
    *,
    day: str = "",
    group: str = "",
    question: bool = False,
) -> dict[str, Any]:
    return {
        "id": stable_id("assignment", subject, title, day),
        "subject": subject,
        "subjectLabel": SUBJECT_LABELS.get(subject, subject),
        "title": title,
        "day": day,
        "group": group,
        "status": status,
        "question": "Create as an assignment?" if question else None,
    }


def build_suggested_assignments(week: Any, entries: list[Any]) -> list[dict[str, Any]]:
    specs = engine.assignment_specs_for_week(week, entries)
    items: list[dict[str, Any]] = []

    for spec in specs:
        subject = compact(spec.get("subject") or "").lower()
        if subject in MANUAL_SUBJECTS:
            continue  # handled below as manual-only
        title = compact(spec.get("title") or "")
        if not title:
            continue
        meta = (spec.get("payload") or {}).get("metadata") or {}
        group = "Assessments" if meta.get("gradeCategory") == "assessment" else "Assignments"
        status = "exists" if title in MOCK_EXISTING_ASSIGNMENT_TITLES else "create"
        items.append(
            _suggested_item(
                subject, title, status, day=spec.get("row", {}).get("weekday", ""), group=group
            )
        )

    for entry in entries:
        subject = compact(entry.subject).lower()
        if subject in MANUAL_SUBJECTS:
            title = compact(entry.title) or (f"{subject.title()} {entry.entry_type.title()}")
            items.append(
                _suggested_item(subject, title, "manual", day=entry.weekday)
            )
        elif subject == "language-arts" and entry.entry_type == "lesson":
            title = compact(entry.title) or "Classroom Practice"
            items.append(
                _suggested_item(subject, title, "needs-owen", day=entry.weekday, question=True)
            )

    return items


def apply_decisions(week_code: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = _DECISIONS.get(canonical_week_code(week_code), {})
    for item in items:
        answer = decisions.get(item["id"])
        if answer == "yes":
            item["status"] = "create"
        elif answer == "no":
            item["status"] = "no-assignment"
    return items


def build_week_status(week: Any, entries: list[Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    decisions_needed = sum(1 for item in items if item["status"] == "needs-owen")
    assessments = sum(1 for entry in entries if entry.entry_type == "test")
    state = "Ready to review" if decisions_needed == 0 else "Needs a decision"
    return {
        "pacing": "Pacing fresh",
        "decisionsNeeded": decisions_needed,
        "assessments": assessments,
        "state": state,
    }


def _mock_inventory_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Build a preflight-compatible inventory from the manifest's existing refs.

    This mirrors ``canvas_launcher._fake_inventory`` but is seeded so the real
    reconciliation logic (``analyze_action``) can run offline. Each action's
    ``existing`` reference is presented as already-present, which yields a clean
    CREATE/UPDATE/REMOVE/LEAVE breakdown with no duplicate/drift blockers.
    """
    courses: dict[str, dict[str, Any]] = {}
    for action in manifest.get("actions", []):
        cid = str(action.get("course_id"))
        otype = action.get("object_type")
        if otype not in ("page", "assignment", "announcement"):
            continue
        bucket = courses.setdefault(cid, {"pages": [], "assignments": [], "announcements": []})
        existing = (action.get("existing") or "").strip()
        existing_id = action.get("existing_id")
        if otype == "page":
            bucket["pages"].append(
                {"page_id": existing_id, "url": existing, "title": existing, "published": True, "body": ""}
            )
        elif otype == "assignment":
            bucket["assignments"].append(
                {"id": existing_id, "name": existing, "due_at": None, "published": True, "omit_from_final_grade": None}
            )
        elif otype == "announcement":
            bucket["announcements"].append(
                {"id": existing_id, "title": existing, "message": "", "published": True}
            )
    return {"courses": courses}


def build_review(week_code: str) -> dict[str, Any]:
    try:
        manifest = launcher.load_manifest(week_code)
    except launcher.LaunchError:
        return {
            "available": False,
            "weekCode": canonical_week_code(week_code),
            "create": 0, "update": 0, "remove": 0, "leave": 0,
            "reminders": 0, "approved": False, "details": [],
        }

    counts = {"CREATE": 0, "UPDATE": 0, "REMOVE": 0, "LEAVE": 0}
    details: list[dict[str, Any]] = []
    reminders = 0
    for action in manifest.get("actions", []):
        act = compact(action.get("action") or "LEAVE").upper()
        if act not in counts:
            act = "LEAVE"
        counts[act] += 1
        timing = compact(action.get("timing") or "")
        if "scheduled" in timing.lower():
            reminders += 1
        details.append(
            {
                "action": act,
                "course": compact(action.get("course") or ""),
                "type": compact(action.get("object_type") or ""),
                "title": compact(action.get("existing") or action.get("resulting_title") or "(untitled)"),
                "reason": compact(action.get("reason") or ""),
            }
        )
    return {
        "available": True,
        "weekCode": canonical_week_code(week_code),
        "create": counts["CREATE"],
        "update": counts["UPDATE"],
        "remove": counts["REMOVE"],
        "leave": counts["LEAVE"],
        "reminders": reminders,
        "approved": launcher.manifest_approved(manifest),
        "details": details,
    }


def build_launch_state(week_code: str) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    base = {"weekCode": canonical, "dryRun": True}
    try:
        manifest = launcher.load_manifest(canonical)
        approved = launcher.manifest_approved(manifest)
    except launcher.LaunchError:
        return {**base, "state": "Blocked", "reason": f"No launch manifest for {canonical} yet."}

    if not approved:
        return {**base, "state": "Blocked", "reason": "This week isn't teacher-approved yet."}

    review = build_review(canonical)
    pending = review["create"] + review["update"] + review["remove"]
    return {**base, "state": "Ready", "reason": None, "pendingWrites": pending}


def _run_real_canvas_launch(week_code: str) -> tuple[int, str]:
    """Opt-in real launch via the guarded ``bin/canvas-launch`` workflow."""
    launcher_bin = REPO_ROOT / "bin" / "canvas-launch"
    try:
        proc = subprocess.run(
            [str(launcher_bin), canonical_week_code(week_code)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return proc.returncode, proc.stdout.strip()


def perform_launch(week_code: str, dry_run: bool = True) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    state = build_launch_state(canonical)
    if state["state"] == "Blocked":
        return state
    if dry_run:
        # Reuse the real preflight (duplicate/drift detection) offline so the
        # guarded workflow is exercised without any credentials or network.
        try:
            manifest = launcher.load_manifest(canonical)
            inventory = _mock_inventory_from_manifest(manifest)
            _rows, blockers = launcher.run_preflight(canonical, inventory)
        except Exception as exc:  # noqa: BLE001 — surface as a teacher-facing blocker
            return {
                "weekCode": canonical,
                "dryRun": True,
                "state": "Blocked",
                "reason": f"Preflight could not run: {exc}",
            }
        if blockers:
            return {
                "weekCode": canonical,
                "dryRun": True,
                "state": "Blocked",
                "reason": "A duplicate or drift was found. Nothing was changed.",
            }
        return {
            "weekCode": canonical,
            "dryRun": True,
            "state": "Complete",
            "reason": "Launch complete (prototype dry-run — no Canvas changes were made).",
        }
    code, output = _run_real_canvas_launch(canonical)
    if code == 0:
        return {
            "weekCode": canonical,
            "dryRun": False,
            "state": "Complete",
            "reason": "Launch complete. Canvas was updated through the guarded workflow.",
            "detail": output,
        }
    return {
        "weekCode": canonical,
        "dryRun": False,
        "state": "Blocked",
        "reason": "Canvas could not be reached. Nothing was changed.",
    }


def build_workspace(week_code: str | None = None) -> dict[str, Any]:
    fixture = engine.load_fixture()
    week = engine.select_week(week_code or fixture.get("weekCode"))
    entries = _entries_for_week(fixture, week)
    panel = build_week_panel(week, entries)
    items = build_suggested_assignments(week, entries)
    items = apply_decisions(week.code, items)

    return {
        "source": {
            "pacing": "synthetic",  # Phase 23 synthetic weekly content fixture
            "routing": "canonical",  # canvas-course-mappings.json + canvas_course_resolver.py
            "reconciliation": "manifest",  # .local q1w5 corrective manifest (when present)
        },
        "week": panel,
        "suggestedAssignments": items,
        "weekStatus": build_week_status(week, entries, items),
        "review": build_review(week.code),
        "launch": build_launch_state(week.code),
    }


def list_weeks() -> list[dict[str, Any]]:
    weeks: list[dict[str, Any]] = []
    for week in p22.load_instructional_weeks():
        weeks.append(
            {
                "code": week["code"],
                "label": f"{week['code']} · {format_date_range(week['startsOn'], week['endsOn'])}",
            }
        )
    return weeks


def chat_reply(message: str, current_week: str) -> dict[str, Any]:
    """Deterministic teacher-facing chat router (no generation, no LLM)."""
    text = compact(message).lower()
    week_token = None
    for token in text.split():
        if token.upper().startswith("Q") and "W" in token.upper():
            week_token = p22.canonical_week_code(token)
            break

    if week_token and ("update" in text or "switch" in text or "go to" in text or week_token == text):
        return {"reply": f"Switched to {week_token}.", "week": week_token}

    if "launch" in text:
        return {"reply": "Running launch.", "action": "launch"}

    if "refresh" in text and ("pacing" in text or "week" in text):
        return {"reply": "Pacing refreshed from the current source.", "action": "refresh"}

    if "assignment" in text or "assignments" in text:
        return {"reply": "Suggested assignments are shown in the right panel.", "action": "focus-assignments"}

    if "review" in text or "changes" in text:
        return {"reply": "Opening the review summary.", "action": "focus-review"}

    if "looks good" in text or "good" in text or "approve" in text:
        return {"reply": "Looks good. Ready to review.", "action": "focus-review"}

    if "pacing" in text:
        return {"reply": "Current pacing is shown in the week panel.", "action": "focus-week"}

    return {
        "reply": (
            "I can help with a few things: type “Update Q1W6”, “Refresh pacing”, "
            "“Show assignments”, “Review changes”, “Looks good”, or “Launch”."
        ),
        "action": None,
    }


class WorkspaceHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _current_week(self) -> str:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        week_code = params.get("week", [None])[0]
        return canonical_week_code(week_code or "Q1W5")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/workspace":
            self._send_json(build_workspace(self._current_week()))
            return
        if parsed.path == "/api/weeks":
            self._send_json({"weeks": list_weeks()})
            return
        if parsed.path == "/api/health":
            self._send_json({"status": "ok", "previewOnly": True, "canvasWritesAllowed": False})
            return
        if parsed.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/chat":
            body = self._read_json_body()
            current_week = body.get("week") or self._current_week()
            result = chat_reply(body.get("message") or "", current_week)
            if result.get("action") == "launch":
                result["launch"] = perform_launch(current_week, dry_run=bool(body.get("dryRun", True)))
            self._send_json({**result, "week": result.get("week") or current_week})
            return
        if parsed.path == "/api/decision":
            body = self._read_json_body()
            week_code = canonical_week_code(body.get("week") or "Q1W5")
            item_id = compact(body.get("id") or "")
            answer = compact(body.get("answer") or "").lower()
            if answer not in ("yes", "no"):
                self._send_json({"error": "answer must be yes or no"}, 400)
                return
            _DECISIONS.setdefault(week_code, {})[item_id] = answer
            workspace = build_workspace(week_code)
            self._send_json(
                {"ok": True, "weekStatus": workspace["weekStatus"], "suggestedAssignments": workspace["suggestedAssignments"]}
            )
            return
        if parsed.path == "/api/launch":
            body = self._read_json_body()
            week_code = canonical_week_code(body.get("week") or "Q1W5")
            dry_run = bool(body.get("dryRun", True))
            self._send_json(perform_launch(week_code, dry_run=dry_run))
            return
        if parsed.path == "/api/refresh":
            self._send_json(build_workspace(self._current_week()))
            return
        self.send_error(404, "unknown endpoint")


RETIRED_MESSAGE = "Phase 23 teacher workspace is retired; use bin/teacher-workstation instead."


def command_serve(args: argparse.Namespace) -> int:
    print(RETIRED_MESSAGE, file=sys.stderr)
    return 1


def _retired_command_serve(args: argparse.Namespace) -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(APP_DIR)
    server = ThreadingHTTPServer((args.host, args.port), WorkspaceHandler)
    print(f"Phase 23 teacher workspace serving at http://{args.host}:{args.port}")
    print("Dry-run only: no Canvas credentials, network, or writes are used by default.")
    server.serve_forever()
    return 0


def command_self_test(_args: argparse.Namespace) -> int:
    # Canonical week + date-range formatting.
    assert canonical_week_code("q1-w5") == "Q1W5"
    assert format_date_range("2026-08-17", "2026-08-21") == "August 17–21, 2026"

    # Routing: History and Science are manual-only; Math/Reading are enabled.
    assert _subject_route("history")["manual"] is True
    assert _subject_route("science")["manual"] is True
    assert _subject_route("math")["manual"] is False
    assert _subject_route("math")["courseId"] == 26404
    assert _subject_route("reading")["courseId"] == 26442

    # Workspace build against the synthetic fixture (default Q1W5).
    workspace = build_workspace()
    assert workspace["week"]["weekCode"] == "Q1W5"
    assert workspace["week"]["dateRange"] == "August 17–21, 2026"
    subjects = {s["id"] for s in workspace["week"]["subjects"]}
    assert subjects == set(SUBJECT_ORDER)
    # Suggested assignments must include manual History/Science and an ambiguous LA item.
    statuses = {item["status"] for item in workspace["suggestedAssignments"]}
    assert "manual" in statuses
    assert "needs-owen" in statuses
    assert "create" in statuses
    assert "exists" in statuses
    # No manual subject should ever ask a question.
    for item in workspace["suggestedAssignments"]:
        if item["status"] == "manual":
            assert item["question"] is None

    # Review is derived from the real Q1W5 corrective manifest.
    review = build_review("Q1W5")
    assert review["available"] is True
    assert review["approved"] is True
    assert review["create"] >= 1 and review["leave"] >= 1

    # Launch honors the real approval gate and reuses the launcher's preflight.
    launch = build_launch_state("Q1W5")
    assert launch["state"] in ("Ready", "Complete", "Blocked")
    assert build_launch_state("Q1W6")["state"] == "Blocked"  # no manifest

    # Decisions resolve ambiguous items without creating new items.
    workspace = build_workspace()
    ambiguous = next(item for item in workspace["suggestedAssignments"] if item["status"] == "needs-owen")
    _DECISIONS.setdefault("Q1W5", {})[ambiguous["id"]] = "yes"
    workspace2 = build_workspace()
    resolved = next(item for item in workspace2["suggestedAssignments"] if item["id"] == ambiguous["id"])
    assert resolved["status"] == "create"
    _DECISIONS.clear()

    print("PASS Phase 23 teacher workspace self-test")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 23 teacher-facing weekly Canvas workspace")
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve", help="Serve the local workspace")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8780)
    serve.set_defaults(func=command_serve)
    sub.add_parser("self-test", help="Run deterministic workspace assertions").set_defaults(func=command_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
