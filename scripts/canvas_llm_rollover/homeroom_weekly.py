"""Weekly Homeroom newsletter page architecture.

Homeroom now uses one existing weekly page per instructional week, matching the
four academic courses. The old rolling newsletter page is retired and must not
be updated or deleted by this module.

The module is deterministic and local-first except for explicit GET-only page
resolution. It never creates pages and never publishes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import week_resolution as wr

from . import birthdays as bday
from . import homeroom_newsletter

COURSE_ID = 26429
KIND = "homeroom_weekly_newsletter_html"
RESOLUTION_FILE = "homeroom-page-resolution.json"
APPROVAL_FILE = "homeroom-weekly-approval.json"
HTML_FILE = "drafts/homeroom-page.html"


class HomeroomWeeklyError(RuntimeError):
    pass


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def week_slug(quarter: int, week: int) -> str:
    from scripts.canvas_llm_intake import intake as intake_mod

    return intake_mod._slug_for(wr.week_code_for(quarter, week))


def week_code(quarter: int, week: int) -> str:
    return wr.week_code_for(quarter, week)


def week_dates(quarter: int, week: int) -> tuple[str, str]:
    from scripts.instructional_weeks import week_range

    bounds = week_range(wr.find_week(quarter, week) or {})
    if bounds is None:
        raise HomeroomWeeklyError("instructional week dates unavailable")
    return bounds[0].isoformat(), bounds[1].isoformat()


def resolution_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / "planner" / RESOLUTION_FILE


def approval_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / "planner" / APPROVAL_FILE


def html_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / HTML_FILE


def load_page_resolution(quarter: int, week: int) -> dict[str, Any] | None:
    try:
        return json.loads(resolution_path(quarter, week).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_approval(quarter: int, week: int) -> dict[str, Any] | None:
    try:
        return json.loads(approval_path(quarter, week).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_page(quarter: int, week: int, client: Any) -> dict[str, Any]:
    """GET-only resolution of the existing weekly Homeroom page.

    Fails closed on missing or ambiguous pages. Never creates a page.
    """
    slug = week_slug(quarter, week)
    found = client.find_page(COURSE_ID, slug)
    if found is None:
        record = {
            "schemaVersion": 1,
            "week": week_code(quarter, week),
            "course_id": COURSE_ID,
            "slug": slug,
            "page_id": None,
            "status": "MISSING",
            "method": "LIVE_GET",
            "resolved_at": _now(),
        }
        write_page_resolution(quarter, week, record)
        raise HomeroomWeeklyError(f"Homeroom weekly page missing for {slug}")
    try:
        pages = client.list_pages(COURSE_ID)
    except Exception:  # noqa: BLE001
        pages = [found]
    matches = [
        page for page in pages
        if page.get("url") == slug or page.get("title") == found.get("title")
    ]
    if len(matches) > 1:
        record = {
            "schemaVersion": 1,
            "week": week_code(quarter, week),
            "course_id": COURSE_ID,
            "slug": slug,
            "page_id": None,
            "status": "DUPLICATE",
            "candidate_count": len(matches),
            "method": "LIVE_GET",
            "resolved_at": _now(),
        }
        write_page_resolution(quarter, week, record)
        raise HomeroomWeeklyError(f"duplicate Homeroom weekly pages for {slug}")
    record = {
        "schemaVersion": 1,
        "week": week_code(quarter, week),
        "course_id": COURSE_ID,
        "slug": slug,
        "page_id": found.get("page_id") or found.get("id"),
        "title": found.get("title"),
        "front_page": bool(found.get("front_page")),
        "published": found.get("published"),
        "status": "FOUND",
        "method": "LIVE_GET",
        "resolved_at": _now(),
        "note": "Existing weekly page; the retired rolling page is not a target.",
    }
    write_page_resolution(quarter, week, record)
    return record


def write_page_resolution(quarter: int, week: int, record: dict[str, Any]) -> Path:
    path = resolution_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def build_weekly_html(
    quarter: int,
    week: int,
    *,
    source_html: str,
    plan: dict[str, Any],
    roster: list[bday.Birthday] | None = None,
) -> str:
    start, end = week_dates(quarter, week)
    return homeroom_newsletter.build_from_plan(
        source_html, plan, roster=roster,
        week_start=date.fromisoformat(start),
        week_end=date.fromisoformat(end),
    )


def record_preview(
    quarter: int,
    week: int,
    *,
    page: dict[str, Any],
    body: str,
    source_body_hash: str,
    roster_version: str = "",
) -> dict[str, Any]:
    """Write the staged weekly HTML and a PENDING hash-bound approval record."""
    if page.get("status") != "FOUND" or page.get("page_id") is None:
        raise HomeroomWeeklyError("cannot record a preview without a resolved weekly page")
    html_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    html_path(quarter, week).write_text(body, encoding="utf-8")
    record = {
        "kind": KIND,
        "course_id": COURSE_ID,
        "week": week_code(quarter, week),
        "page_id": int(page["page_id"]),
        "page_slug": page["slug"],
        "page_title": page.get("title", ""),
        "source_body_hash": source_body_hash,
        "approved_body_hash": _sha(body),
        "roster_version": roster_version,
        "approved": False,
        "status": "PENDING_OWNER_APPROVAL",
        "created_at": _now(),
        "approved_at": None,
        "approved_by": None,
        "html_file": HTML_FILE,
        "preview_only": True,
    }
    approval_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    approval_path(quarter, week).write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def record_approval(
    quarter: int,
    week: int,
    *,
    page_id: int,
    page_slug: str,
    week_code_value: str,
    source_body_hash: str,
    approved_body_hash: str,
    body: str,
) -> dict[str, Any]:
    """Owner-UI-only approval record (not used by this mission)."""
    if _sha(body) != approved_body_hash:
        raise ValueError("approved_body_hash does not match the supplied body")
    html_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    html_path(quarter, week).write_text(body, encoding="utf-8")
    record = {
        "kind": KIND,
        "course_id": COURSE_ID,
        "week": week_code_value,
        "page_id": int(page_id),
        "page_slug": page_slug,
        "source_body_hash": source_body_hash,
        "approved_body_hash": approved_body_hash,
        "approved": True,
        "status": "APPROVED",
        "approved_at": _now(),
        "approved_by": "OWNER_UI",
        "html_file": HTML_FILE,
    }
    approval_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    approval_path(quarter, week).write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def verify_at(
    week_dir: Path, *, course_id: int, week_code_value: str,
) -> tuple[bool, list[str]]:
    week_dir = Path(week_dir)
    problems: list[str] = []
    try:
        rec = json.loads((week_dir / "planner" / APPROVAL_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, ["homeroom weekly approval record missing"]
    if rec.get("kind") != KIND:
        return False, ["homeroom approval is not a weekly_newsletter_html record"]
    if not rec.get("approved"):
        return False, ["homeroom weekly approval not approved"]
    if int(rec.get("course_id") or 0) != int(course_id):
        problems.append("homeroom course id changed")
    if (rec.get("week") or "") != week_code_value:
        problems.append("homeroom week changed")
    try:
        body = (week_dir / HTML_FILE).read_text(encoding="utf-8")
    except OSError:
        body = None
    if body is None:
        problems.append("homeroom weekly HTML body missing")
    elif _sha(body) != rec.get("approved_body_hash"):
        problems.append("homeroom weekly HTML body changed")
    return (len(problems) == 0), problems


def verify(quarter: int, week: int, *, course_id: int = COURSE_ID) -> tuple[bool, list[str]]:
    return verify_at(
        imf.staging_dir(quarter, week),
        course_id=course_id,
        week_code_value=week_code(quarter, week),
    )


def build_rollover_block(quarter: int, week: int) -> dict[str, Any]:
    """Build the rollover manifest block from local weekly resolution/approval."""
    resolution = load_page_resolution(quarter, week) or {}
    approval = load_approval(quarter, week) or {}
    slug = resolution.get("slug") or week_slug(quarter, week)
    page_id = approval.get("page_id") or resolution.get("page_id")
    body = ""
    try:
        body = html_path(quarter, week).read_text(encoding="utf-8")
    except OSError:
        body = ""
    approved = bool(
        approval.get("approved")
        and approval.get("approved_body_hash") == _sha(body)
        and str(approval.get("page_id")) == str(page_id)
        and approval.get("week") == week_code(quarter, week)
    )
    return {
        "course_id": COURSE_ID,
        "to_page_id": page_id,
        "to_page_slug": slug,
        "source_content_hash": approval.get("source_body_hash", ""),
        "proposed_content_hash": _sha(body) if body else "",
        "body": body,
        "mode": KIND,
        "approved": approved,
        "page_resolution": resolution,
        "front_page_action": "SET_FRONT_PAGE",
    }


def command_self_test() -> int:
    import tempfile

    orig = imf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        imf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            page = {
                "status": "FOUND", "page_id": 123456, "slug": "q2w4-november-2-6-2026",
                "title": "Q2W4 - November 2–6, 2026", "front_page": False,
            }
            write_page_resolution(2, 4, {
                "schemaVersion": 1, "week": week_code(2, 4), "course_id": COURSE_ID,
                "slug": page["slug"], "page_id": page["page_id"], "status": "FOUND",
                "method": "LIVE_GET",
            })
            body = "<div>Weekly newsletter</div>"
            rec = record_preview(
                2, 4, page=page, body=body, source_body_hash="src", roster_version="v",
            )
            assert rec["approved"] is False and rec["page_id"] == 123456
            assert html_path(2, 4).read_text(encoding="utf-8") == body
            ok, problems = verify(2, 4)
            assert not ok and "not approved" in problems[0]
            record_approval(
                2, 4, page_id=123456, page_slug=page["slug"], week_code_value=week_code(2, 4),
                source_body_hash="src", approved_body_hash=_sha(body), body=body,
            )
            ok2, problems2 = verify(2, 4)
            assert ok2, problems2
            html_path(2, 4).write_text(body + "x", encoding="utf-8")
            ok3, _ = verify(2, 4)
            assert not ok3
        finally:
            imf.staging_dir = orig
    print("PASS weekly Homeroom page self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
