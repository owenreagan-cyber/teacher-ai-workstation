"""Canvas Weekly Intake orchestrator.

Reuses the Phase 3 pacing engine to produce a teacher-reviewable staging packet:

    fetch pacing -> normalize week -> translate subjects -> draft pages /
    assignments / reminders / announcements -> questions -> REVIEW.md

Writes only local staging artifacts under .local/canvas-llm/intake/. Canvas
reads are GET-only (page lookup + duplicate assignment check). No Canvas writes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase3 import constants as P3
from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_phase3 import pacing_announcement as pa
from scripts.canvas_llm_phase3 import canvas_preview as cp
from scripts.canvas_llm_phase3 import week_workflow as wf

from . import constants as C
from . import manifest as mf
from . import questions as qs
from . import week_resolution as wr
from . import teacher_input as ti
from . import approval as ap
from . import reminders as rem
from . import owner_overrides as oo
from .canvas_readonly import CanvasReadOnly


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug_for(week_code: str) -> str:
    """Derive the canonical weekly page slug from the instructional-weeks export."""
    weeks = json.loads(P3.WEEKS_PATH.read_text(encoding="utf-8")).get("weeks", [])
    entry = next((w for w in weeks if w.get("code") == week_code), None)
    if not entry:
        return ""
    # sourcePath ends with e.g. "q2w2-october-19-23-2026.html" -> strip .html
    return entry.get("sourcePath", "").split("/")[-1].removesuffix(".html")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _content_hash(week_norm: dict[str, Any]) -> str:
    """Stable hash of pacing CONTENT only (week code, dates, days, unit context).

    Excludes the ``source`` metadata (which carries a fetch timestamp), so the
    hash is identical across regenerations of unchanged pacing.
    """
    content = {
        "week": week_norm.get("week", {}),
        "unitContext": week_norm.get("unitContext", {}),
        "days": week_norm.get("days", {}),
    }
    return _hash(json.dumps(content, sort_keys=True, ensure_ascii=False))


def _coerce_days(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Coerce a subject report's days into canvas_preview's {in_class, at_home}."""
    days: dict[str, dict[str, Any]] = {}
    for wd in C.WEEKDAYS:
        day = (report.get("days") or {}).get(wd, {})
        in_class = day.get("in_class") or day.get("lines") or []
        at_home = day.get("at_home")
        days[wd] = {
            "in_class": in_class if in_class else ["(no source)"],
            "at_home": [at_home] if at_home else None,
        }
    return days


def _apply_day_overrides(
    quarter: int,
    week: int,
    subject: str,
    days: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Apply active owner overrides to a subject's coerced day map.

    Overrides may set in_class, set/clear at_home, or mark a day blank/pending.
    Source snapshots are never touched; only the regenerated draft is affected.
    """
    overrides = oo.load_overrides(quarter, week)
    for wd in C.WEEKDAYS:
        rec = overrides.get(f"{subject}|{wd}")
        if not rec or not rec.get("active", True):
            continue
        status = rec.get("status")
        if status == oo.STATUS_OWNER_CONFIRMED_BLANK:
            days[wd] = {"in_class": [], "at_home": None}
            continue
        if status == oo.STATUS_PENDING_SOURCE:
            days[wd] = {"in_class": ["(pending)"], "at_home": None}
            continue
        in_class = rec.get("in_class")
        if in_class is not None:
            days[wd]["in_class"] = list(in_class) if in_class else ["(no source)"]
        at_home = rec.get("at_home")
        if at_home is not None:
            days[wd]["at_home"] = [at_home] if at_home else None
    return days


def build_intake(
    *,
    quarter: int,
    week: int,
    fresh: bool = True,
    canvas: CanvasReadOnly | None = None,
    include_canvas_context: bool = True,
    normalized_override: dict[str, Any] | None = None,
    source_meta_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full intake for one week and persist the staging packet.

    Returns a summary dict. No Canvas writes occur.
    """
    week_code = wr.week_code_for(quarter, week)
    m = mf.new_manifest(
        quarter=quarter,
        week=week,
        week_code=week_code,
        date_range={},
    )

    # ---- 1. Source fetch + normalize (reuse Phase 3) ---------------------
    if normalized_override is None:
        rows, meta = pe.fetch_pacing(fresh=fresh)
        week_norm = pe.extract_week(rows, week_code, meta)
    else:
        week_norm = normalized_override
        meta = source_meta_override or (week_norm.get("source") or {})
    m["source_retrieved_at"] = meta.get("readTimestampUtc") or _now()
    # Content-only hash (excludes the timestamp-bearing ``source`` metadata) so
    # the source hash is STABLE across regenerations of identical pacing. This
    # is what makes stale-edit detection and UNCHANGED-delta detection reliable.
    m["source_hash"] = _content_hash(week_norm)
    m["date_range"] = {
        "start": week_norm.get("week", {}).get("startDate", ""),
        "end": week_norm.get("week", {}).get("endDate", ""),
    }
    mf.advance_status(m, "NORMALIZED")

    d = mf.staging_dir(quarter, week)
    src_dir = d / "source"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "pacing-snapshot.json").write_text(
        json.dumps({
            "retrieved_at": m["source_retrieved_at"],
            "spreadsheet_id": P3.SPREADSHEET_ID,
            "tab": "4A - Reagan",
            "normalized": week_norm,
            "hash": m["source_hash"],
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (d / "normalized").mkdir(parents=True, exist_ok=True)
    (d / "normalized" / "week.json").write_text(
        json.dumps(week_norm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---- 2. Active subjects ---------------------------------------------
    # Phase 3 reports reading + spelling separately; the intake models them as
    # one combined Reading/Spelling course (26442). Normalize + de-duplicate.
    phase3_active = wf.active_subjects(week_code, week_norm)
    _merge = {"reading": "reading_spelling", "spelling": "reading_spelling"}
    active: list[str] = []
    for s in phase3_active:
        key = _merge.get(s, s)
        if key not in active:
            active.append(key)
    m["subjects"] = {s: {"state": "PENDING"} for s in active}

    # ---- 3. Translate + draft per subject --------------------------------
    subject_reports: dict[str, dict[str, Any]] = {}
    assignments: list[dict[str, Any]] = []
    drafts_dir = d / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    pages: dict[str, Any] = {}

    for subject in active:
        report = _translate_subject(subject, week_norm)
        subject_reports[subject] = report
        m["subjects"][subject]["deterministic"] = report.get("deterministic", False)
        m["subjects"][subject]["unresolved"] = len(report.get("unresolved") or [])
        # Reading/Spelling carries its assignments under reading.* / spelling.*.
        sub_assignments = list(report.get("assignments") or [])
        if subject == "reading_spelling":
            sub_assignments = list((report.get("reading") or {}).get("assignments") or [])
            sub_assignments += list((report.get("spelling") or {}).get("assignments") or [])
        for a in sub_assignments:
            assignments.append(_normalize_assignment(subject, a))

    # Page HTML + assignments files. Capture the agenda HTML per subject so the
    # announcement's agenda_hash binds to the exact page HTML (§26 invariant).
    # Owner overrides (day-level in_class/at_home/status) are applied here so
    # page + announcement + reminder drafts reflect Owen's edits.
    page_html: dict[str, str] = {}
    for subject in active:
        report = subject_reports[subject]
        days = _coerce_days(report)
        days = _apply_day_overrides(quarter, week, subject, days)
        reminders = _reminders_for(week_norm, subject)
        if subject == "reading_spelling":
            html = cp.build_combined_reading_spelling_html(
                week_code,
                _apply_day_overrides(quarter, week, "reading_spelling", _coerce_days(report.get("reading", {}))),
                _coerce_days(report.get("spelling", {})),
                reminders=reminders,
            )
            fname = "reading-page.html"
        else:
            html = cp.build_agenda_html(week_code, days, reminders=reminders)
            fname = f"{subject}-page.html"
        (drafts_dir / fname).write_text(html, encoding="utf-8")
        page_html[subject] = html
        pages[subject] = {
            "file": f"drafts/{fname}",
            "body_chars": len(html),
            "reminders": reminders,
            "agenda_hash": _hash(html),
        }

    (drafts_dir / "assignments.json").write_text(
        json.dumps(assignments, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---- 4. Announcements (weekly-update drafts; no POST) -----------------
    announcements = _draft_weekly_announcements(week_norm, subject_reports, pages, page_html)
    (drafts_dir / "announcements.json").write_text(
        json.dumps(announcements, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---- 4b. Assessment reminders (drafts only; no POST) ------------------
    assessment_reminders: list[dict[str, Any]] = []
    assessment_reminders += rem.draft_math_assessment_reminders(week_norm)
    assessment_reminders += rem.draft_spelling_reminders(week_norm)
    (drafts_dir / "assessment-reminders.json").write_text(
        json.dumps(assessment_reminders, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---- 5. Canvas GET-only context (page lookup + duplicate prevention) --
    page_lookup: dict[str, Any] = {}
    dup_check: dict[str, Any] = {}
    if canvas is not None and include_canvas_context:
        slug = _slug_for(week_code)
        for subject in active:
            cid = _course_id(subject)
            if cid is None:
                page_lookup[subject] = {"status": "NO_COURSE_MAPPING"}
                continue
            found = canvas.find_page(cid, slug)
            if found is not None:
                page_lookup[subject] = {
                    "status": "FOUND",
                    "course_id": cid,
                    "page_id": found.get("page_id"),
                    "url": found.get("url"),
                    "front_page": found.get("front_page"),
                }
            else:
                page_lookup[subject] = {"status": "MISSING_OR_AMBIGUOUS", "course_id": cid, "slug": slug}
            existing = canvas.list_assignments(cid)
            existing_names = {a.get("name") for a in existing if a.get("name")}
            for a in [x for x in assignments if x["course_id"] == cid]:
                key = a["title"]
                a["duplicate_classification"] = (
                    "EXISTS_EXACT" if key in existing_names else "NEW_PROPOSAL"
                )
            dup_check[subject] = {
                "existing_assignment_count": len(existing),
                "proposed": sum(1 for a in assignments if a["course_id"] == cid),
            }
        pages["page_lookup"] = page_lookup

    # ---- 6. Questions + teacher input ------------------------------------
    questions = qs.generate_questions(
        week=week_norm,
        subject_reports=subject_reports,
        assessment_events=[],
        reminder_events=[],
    )

    # Apply teacher input: answer questions, reject/restore assignments, add
    # reminders, replace announcement wording. Source + normalized source are
    # never modified.
    teacher_input = ti.load_input(quarter, week)
    questions = qs.apply_question_answers(questions, teacher_input.get("question_answers", {}))
    rejections = {
        a for _sub, block in teacher_input.get("subjects", {}).items()
        for a in block.get("reject_assignments", [])
    }
    assignments = [a for a in assignments if a["title"] not in rejections]
    for subject in active:
        block = teacher_input.get("subjects", {}).get(subject, {})
        for r in block.get("add_reminder", []):
            pages[subject]["reminders"].append(r)
        if block.get("replace_announcement"):
            for ann in announcements:
                if ann["course"] == _subject_label(subject):
                    ann["transition"] = block["replace_announcement"]

    qs.write_questions(quarter, week, questions)
    m["questions"] = [q["question_id"] for q in questions]
    open_questions = qs.unresolved_questions(questions)

    # ---- 7. Approvals + READY_TO_PUBLISH gate -----------------------------
    approvals = ap.load_approvals(quarter, week, active)
    # Invalidate any approval whose artifact OR source changed (hash binding).
    draft_hashes = _draft_hashes(active, subject_reports, assignments, announcements, pages, assessment_reminders)
    for subject in active:
        ap.invalidate_if_stale(approvals, subject=subject,
                               draft_hashes=draft_hashes.get(subject, {}),
                               source_hash=m.get("source_hash"))
    ap.save_approvals(quarter, week, approvals)

    # Blocking question: any OPEN question that blocks publish (marker semantics
    # or ambiguous token). For Q2W2 the FA6* marker is the blocking one.
    has_blocking = len(open_questions) > 0
    artifacts = {s: {"page", "announcement"} for s in active}
    for s in active:
        if any(a["course"] == s for a in assignments):
            artifacts[s].add("assignments")
    # Assessment reminders require approval when drafted for a subject.
    reminder_courses = {r["course"] for r in assessment_reminders}
    for s in active:
        if _subject_label(s) in reminder_courses:
            artifacts[s].add("assessment_reminder")
    ready, blockers = ap.ready_to_publish(
        approvals, subjects=active, has_blocking_questions=has_blocking, artifacts=artifacts,
    )

    # ---- 8. Finalize manifest + review ------------------------------------
    mf.advance_status(m, "DRAFTED")
    if open_questions:
        mf.advance_status(m, "NEEDS_INPUT")
    elif ready:
        mf.advance_status(m, "READY_TO_PUBLISH")
    else:
        mf.advance_status(m, "READY_FOR_REVIEW")
    m["page_lookup"] = page_lookup
    m["assignment_count"] = len(assignments)
    m["announcement_count"] = len(announcements)
    m["assessment_reminder_count"] = len(assessment_reminders)
    m["approval_summary"] = _approval_summary(approvals)
    m["ready_to_publish"] = ready
    m["publish_blockers"] = blockers
    mf.save_manifest(quarter, week, m)

    _write_review(
        quarter, week, m, subject_reports, assignments, announcements, questions,
        pages, approvals, ready, blockers, page_lookup, assessment_reminders,
    )

    return {
        "week_code": week_code,
        "quarter": quarter,
        "week": week,
        "date_range": m["date_range"],
        "status": m["status"],
        "source_hash": m["source_hash"],
        "active_subjects": active,
        "pages": pages,
        "assignment_count": len(assignments),
        "announcement_count": len(announcements),
        "assessment_reminder_count": len(assessment_reminders),
        "open_questions": len(open_questions),
        "answered_questions": len(questions) - len(open_questions),
        "ready_to_publish": ready,
        "publish_blockers": blockers,
        "draft_hashes": draft_hashes,
        "canvas_writes": 0,
    }


_SUBJECT_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
}


def _subject_label(subject: str) -> str:
    return _SUBJECT_LABELS.get(subject, subject)


def _draft_hashes(
    active: list[str],
    subject_reports: dict[str, dict[str, Any]],
    assignments: list[dict[str, Any]],
    announcements: list[dict[str, Any]],
    pages: dict[str, Any],
    assessment_reminders: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, str]]:
    """Compute a draft hash per subject granularity for approval binding."""
    reminders = assessment_reminders or []
    hashes: dict[str, dict[str, str]] = {}
    for subject in active:
        # Page hash binds to the FULL rendered page HTML (reminders are a proxy;
        # the page_html dict already holds agenda_hash). Prefer the full body hash
        # when available so an edit to In Class/At Home actually invalidates page approval.
        page_hash = pages.get(subject, {}).get("agenda_hash") or _hash(
            json.dumps(pages.get(subject, {}).get("reminders", []), sort_keys=True))
        sub_assignments = [a for a in assignments if a["course"] == subject]
        assign_hash = _hash(json.dumps(sub_assignments, sort_keys=True, ensure_ascii=False))
        ann = next((a for a in announcements if a["course"] == _subject_label(subject)), None)
        ann_hash = _hash(json.dumps(ann or {}, sort_keys=True, ensure_ascii=False))
        # Assessment reminder hash: bind to all reminders drafted for this subject.
        sub_rems = [r for r in reminders if r.get("course") == _subject_label(subject)]
        rem_hash = _hash(json.dumps(sub_rems, sort_keys=True, ensure_ascii=False)) if sub_rems else ""
        hashes[subject] = {
            "page": page_hash,
            "assignments": assign_hash,
            "announcement": ann_hash,
            "assessment_reminder": rem_hash,
        }
    return hashes


def _approval_summary(approvals: dict[str, Any]) -> dict[str, Any]:
    """Compact per-subject approval state for the manifest."""
    out: dict[str, Any] = {}
    for s, entry in (approvals.get("subjects") or {}).items():
        out[s] = {g: entry.get(g, {}).get("state", "PENDING") for g in ap.GRANULARITIES}
    return out


def _course_id(subject: str) -> int | None:
    mapping = {
        "math": "math",
        "reading_spelling": "reading",
        "language_arts": "language-arts",
        "science": "science",
        "history": "history",
    }
    return C.course_id_for_subject(mapping.get(subject, subject))


def _translate_subject(subject: str, week_norm: dict[str, Any]) -> dict[str, Any]:
    if subject == "math":
        return pm.translate_math_week(week_norm)
    if subject == "reading_spelling":
        return prd.translate_reading_spelling_week(week_norm)
    if subject == "language_arts":
        return pt.translate_subject_week(week_norm, "language_arts")
    if subject == "science":
        return pt.translate_subject_week(week_norm, "science")
    if subject == "history":
        return pt.translate_subject_week(week_norm, "history")
    return {"subject": subject, "deterministic": False, "days": {}, "assignments": [], "unresolved": []}


def _normalize_assignment(subject: str, a: dict[str, Any]) -> dict[str, Any]:
    """Normalize a proposed assignment to the canonical intake schema."""
    cid = _course_id(subject)
    due = a.get("due_date", "")
    return {
        "course": subject,
        "course_id": cid,
        "title": a.get("title", ""),
        "assignment_group": a.get("assignment_group", ""),
        "due_date": due,
        "points_possible": a.get("points_possible", C.ASSIGNMENT_DEFAULTS["points_possible"]),
        "grading_type": a.get("grading_type", C.ASSIGNMENT_DEFAULTS["grading_type"]),
        "submission_types": a.get("submission_types", list(C.ASSIGNMENT_DEFAULTS["submission_types"])),
        "omit_from_final_grade": C.ASSIGNMENT_DEFAULTS["omit_from_final_grade"],
        "due_time": C.ASSIGNMENT_DEFAULTS["due_time"],
        "timezone": C.ASSIGNMENT_DEFAULTS["timezone"],
        "source_reason": a.get("authority", "OWNER_POLICY"),
        "confidence": "high" if a.get("authority") == "OWNER_POLICY" else "medium",
        "requires_teacher_approval": True,
    }


def _reminders_for(week_norm: dict[str, Any], subject: str) -> list[str]:
    """Propose reminders from canonical assessment facts (deterministic only)."""
    try:
        facts = pa.resolve_assessment_facts(week_norm)
    except Exception:  # noqa: BLE001 - reminders are best-effort
        facts = []
    subject_map = {
        "math": "Math",
        "reading_spelling": "Reading/Spelling",
        "language_arts": "Language Arts",
        "science": "Science",
        "history": "History",
    }
    label = subject_map.get(subject)
    reminders: list[str] = []
    for ev in facts:
        if ev.get("course") != label:
            continue
        date_display = pe.format_weekday_date_iso(ev.get("assessmentDate", ""))
        for a in (ev.get("assessments") or []):
            if a:
                reminders.append(f"{a} — {date_display}")
    # Active course with instructional content but no explicit assessment still
    # needs a meaningful, source-derived reminder (never an empty Reminders box).
    if not reminders and subject in ("science", "language_arts"):
        fallback = _fallback_subject_reminder(week_norm, subject)
        if fallback:
            reminders.append(fallback)
    return reminders


def _fallback_subject_reminder(week_norm: dict[str, Any], subject: str) -> str:
    """Deterministic, source-derived reminder for an active course with content
    but no explicit assessment (e.g. Science "Check (MC)" weeks).

    Derived strictly from the normalized raw cells; never invents homework or
    grading language, never labels a Check as Test/Quiz/Assessment. Per the
    Science/History agenda-display rule, the visible reminder must not expose
    detailed pacing activity names (Reading / Slides / Notes / Finish / Quiz /
    Labs / Checks), so only the unit name and chapter numbers are surfaced.
    """
    if subject != "science":
        return ""
    import re as _re
    cells: list[str] = []
    for wd in C.WEEKDAYS:
        day = (week_norm.get("days") or {}).get(wd, {})
        raw = (day.get("subjects", {}).get("science", {}).get("raw") or "").strip()
        if raw:
            cells.append(raw)
    if not cells:
        return ""

    unit = ""
    chapters: list[int] = []
    for raw in cells:
        for seg in _re.split(r"/", raw):
            seg = seg.strip()
            m = _re.match(r"^U\s*(\d+)", seg, _re.IGNORECASE)
            if m and not unit:
                unit = f"Unit {int(m.group(1))}"
            for cm in _re.finditer(r"Ch\.?\s*(\d+)", seg, _re.IGNORECASE):
                n = int(cm.group(1))
                if n not in chapters:
                    chapters.append(n)

    chapters.sort()
    unit_part = f"we will continue {unit}" if unit else "we will continue our current unit"
    chapter_part = ""
    if len(chapters) == 1:
        chapter_part = f" as we work through Chapter {chapters[0]}"
    elif len(chapters) >= 2:
        listed = ", ".join(str(n) for n in chapters[:-1])
        chapter_part = f" as we work through Chapters {listed}, and {chapters[-1]}"

    return f"This week {unit_part}{chapter_part}."



def _draft_weekly_announcements(
    week_norm: dict[str, Any],
    subject_reports: dict[str, dict[str, Any]],
    pages: dict[str, Any],
    page_html: dict[str, str],
) -> list[dict[str, Any]]:
    """Draft one weekly-update announcement per active course (no POST).

    ``agenda_hash`` binds to the exact staged page HTML, so
    ``weekly_update_agenda_hash == page_agenda_hash`` (§26 invariant).
    """
    week_code = week_norm.get("week", {}).get("code", "")
    labels = {
        "math": "Math",
        "reading_spelling": "Reading/Spelling",
        "language_arts": "Language Arts",
        "science": "Science",
        "history": "History",
    }
    # Subject-isolated narrative (lazy import avoids an intake <-> rollover cycle).
    from scripts.canvas_llm_rollover import narrative as _narrative
    prior_norm = _prior_week_norm(week_norm)
    out: list[dict[str, Any]] = []
    for subject in subject_reports:
        label = labels.get(subject, subject)
        agenda_hash = _hash(page_html.get(subject, ""))
        out.append({
            "course": label,
            "title": f"{label} Canvas Weekly Update",
            "greeting": "Good afternoon,",
            "week_in_review": _narrative.week_in_review(subject, prior_norm),
            "next_week_overview": _narrative.next_week_overview(subject, week_norm),
            "transition": f"The Canvas {label} page has been updated. Please see the upcoming week ahead.",
            "closing": "Have a great weekend!\n\nMr. Reagan",
            "agenda_hash": agenda_hash,
            "page_agenda_hash": pages.get(subject, {}).get("agenda_hash", ""),
            "hash_consistent": agenda_hash == pages.get(subject, {}).get("agenda_hash", ""),
            "preview_only": True,
        })
    return out


def _prior_week_norm(week_norm: dict[str, Any]) -> dict[str, Any] | None:
    """Load the immediately-preceding instructional week's normalized data."""
    code = (week_norm or {}).get("week", {}).get("code", "")
    if not code:
        return None
    from . import week_resolution as _wr
    weeks = sorted(
        (w for w in _wr.load_weeks() if _wr._week_start(w) is not None),
        key=lambda w: _wr._week_start(w),
    )
    idx = next((i for i, w in enumerate(weeks) if w.get("code") == code), None)
    if idx is None or idx == 0:
        return None
    prev = weeks[idx - 1]
    p = mf.staging_dir(int(prev["quarter"]), int(prev["week"])) / "normalized" / "week.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_review(
    quarter: int,
    week: int,
    m: dict[str, Any],
    subject_reports: dict[str, dict[str, Any]],
    assignments: list[dict[str, Any]],
    announcements: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    pages: dict[str, Any],
    approvals: dict[str, Any],
    ready: bool,
    blockers: list[str],
    page_lookup: dict[str, Any],
    assessment_reminders: list[dict[str, Any]] | None = None,
) -> None:
    labels = {
        "math": "MATH",
        "reading_spelling": "READING / SPELLING",
        "language_arts": "LANGUAGE ARTS",
        "science": "SCIENCE",
        "history": "HISTORY",
    }
    lines = [
        f"# {m['week_code']} — Canvas Weekly Intake Review",
        "",
        f"Dates: {m['date_range'].get('start')} → {m['date_range'].get('end')}",
        f"Status: {m['status']}",
        f"Source hash: {m['source_hash'][:12]}…",
        f"Ready to publish: {'YES' if ready else 'NO'}",
        "",
    ]
    for subject, report in subject_reports.items():
        lines.append(f"## {labels.get(subject, subject.upper())}")
        unresolved = report.get("unresolved") or []
        if unresolved:
            lines.append(f"- Ambiguities: {len(unresolved)}")
        else:
            lines.append("- No unresolved tokens")
        sub_assignments = [a for a in assignments if a["course"] == subject]
        if sub_assignments:
            lines.append(f"- Assignments proposed: {len(sub_assignments)}")
            for a in sub_assignments:
                dup = a.get("duplicate_classification", "")
                dup_txt = f" [{dup}]" if dup else ""
                lines.append(f"  - {a['title']} ({a['assignment_group']}, due {a['due_date']}){dup_txt}")
        else:
            lines.append("- Assignments proposed: 0")
        rem = pages.get(subject, {}).get("reminders", [])
        if rem:
            lines.append(f"- Reminders: {', '.join(rem)}")
        # Page lookup state
        pl = page_lookup.get(subject, {})
        if pl:
            lines.append(f"- Page: {pl.get('status')}" + (f" (id {pl.get('page_id')})" if pl.get('page_id') else ""))
        # Approval states
        appr = (approvals.get("subjects") or {}).get(subject, {})
        states = ", ".join(f"{g}:{appr.get(g, {}).get('state', 'PENDING')}" for g in ap.GRANULARITIES)
        lines.append(f"- Approvals: {states}")
        lines.append("")

    lines.append("## GLOBAL QUESTIONS")
    open_qs = [q for q in questions if q.get("status", "OPEN") == "OPEN"]
    answered_qs = [q for q in questions if q.get("status") == "ANSWERED"]
    if open_qs:
        for q in open_qs:
            lines.append(f"- Q{q['question_id']} [OPEN]: {q['reason']} (recommended: {q['recommended_default']})")
    else:
        lines.append("- None open.")
    if answered_qs:
        lines.append("")
        lines.append("## ANSWERED QUESTIONS")
        for q in answered_qs:
            lines.append(f"- Q{q['question_id']}: {q.get('answer')}")

    lines.append("")
    lines.append("## APPROVAL SUMMARY")
    for s in subject_reports:
        appr = (approvals.get("subjects") or {}).get(s, {})
        parts = []
        for g in ap.GRANULARITIES:
            st = appr.get(g, {}).get("state", "PENDING")
            parts.append(f"{g}:{st}")
        lines.append(f"- {labels.get(s, s.upper())}: " + ", ".join(parts))

    if assessment_reminders:
        lines.append("")
        lines.append("## ASSESSMENT REMINDERS")
        for r in assessment_reminders:
            lines.append(f"- {r['title']} ({r['course']}, due {r.get('assessment_date', '')})")
            if r.get("power_up"):
                lines.append(f"  - Power Up {r['power_up']}")

    lines.append("")
    lines.append("## READY_TO_PUBLISH GATE")
    if ready:
        lines.append("- PASS — all required artifacts approved, no blockers.")
    else:
        lines.append("- NOT READY")
        for b in blockers:
            lines.append(f"  - {b}")

    lines.append("")
    lines.append("> No Canvas writes occurred. Approval is required before publishing.")

    d = mf.staging_dir(quarter, week)
    (d / "REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_self_test() -> int:
    from . import week_resolution, canvas_readonly, questions, constants
    from . import teacher_input, approval, reminders, scheduling

    week_resolution.command_self_test()
    canvas_readonly.command_self_test()
    questions.command_self_test()
    teacher_input.command_self_test()
    approval.command_self_test()
    reminders.command_self_test()
    scheduling.command_self_test()
    constants.course_id_for_subject  # import smoke
    # Synthetic end-to-end via fixture (exercised in tests/).
    print("PASS intake orchestrator self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
