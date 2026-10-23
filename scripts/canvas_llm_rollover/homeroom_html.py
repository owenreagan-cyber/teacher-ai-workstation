"""Rolling-newsletter HTML approval bridge (Q2W3 minimal production path).

The Homeroom newsletter is a Canvas-safe HTML document maintained on a single
rolling front page (course 26429, page id 798072). This module binds an explicit,
hash-bound approval to that exact HTML artifact so the Friday rollover deploys
the APPROVED body instead of routing Homeroom through the JSON proposal
renderer (``homeroom.copy_forward`` / ``render_proposed``).

This is deliberately separate from the JSON planning model, which remains in
place for preview metadata, source comparison, and future renderer work. It does
not delete or replace that model — it only separates the *planning
representation* (JSON proposal) from the *approved production representation*
(exact rolling-newsletter HTML).

Approval record shape (``kind: rolling_newsletter_html``)::

    {
      "kind": "rolling_newsletter_html",
      "course_id": 26429,
      "page_id": 798072,
      "page_slug": "class-4a-newsletter-...",
      "source_body_hash": "<sha256 of the live source body the transform was based on>",
      "approved_body_hash": "<sha256 of the approved HTML body>",
      "week": "Q2W3",
      "quarter": 2,
      "week_number": 3,
      "approved": true,
      "approved_at": "<iso timestamp>",
      "approved_by": "OWNER_UI",
      "html_file": "drafts/homeroom-page.html"
    }

The HTML body is stored next to the other staged drafts under
``.local/canvas-llm/intake/<year>/q<q>/w<w>/drafts/homeroom-page.html`` so the
rollover reads it deterministically without committing a Canvas snapshot.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import manifest as imf

HOMEROOM_COURSE_ID = 26429
HOMEROOM_ROLLING_PAGE_ID = 798072
KIND = "rolling_newsletter_html"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def html_path(quarter: int, week: int) -> Path:
    """Canonical local path of the approved rolling-newsletter HTML body."""
    return imf.staging_dir(quarter, week) / "drafts" / "homeroom-page.html"


def approval_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / "planner" / "homeroom-html-approval.json"


def load_html(quarter: int, week: int) -> str | None:
    p = html_path(quarter, week)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def load_approval(quarter: int, week: int) -> dict[str, Any] | None:
    p = approval_path(quarter, week)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def record_approval(
    quarter: int,
    week: int,
    *,
    course_id: int,
    page_id: int,
    page_slug: str,
    source_body_hash: str,
    approved_body_hash: str,
    week_code: str,
    body: str,
) -> dict[str, Any]:
    """Record an exact-hash-bound rolling-newsletter HTML approval.

    Writes the approval record AND the HTML body into the staged packet. The
    approval is invalidated by ``verify`` if the body, page, or week changes.
    """
    if _sha(body) != approved_body_hash:
        raise ValueError("approved_body_hash does not match the supplied body")
    record = {
        "kind": KIND,
        "course_id": int(course_id),
        "page_id": int(page_id),
        "page_slug": page_slug,
        "source_body_hash": source_body_hash,
        "approved_body_hash": approved_body_hash,
        "week": week_code,
        "quarter": int(quarter),
        "week_number": int(week),
        "approved": True,
        "approved_at": _now(),
        "approved_by": "OWNER_UI",
        "html_file": "drafts/homeroom-page.html",
    }
    html_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    html_path(quarter, week).write_text(body, encoding="utf-8")
    approval_path(quarter, week).parent.mkdir(parents=True, exist_ok=True)
    approval_path(quarter, week).write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def verify_at(
    week_dir: Path,
    *,
    course_id: int,
    page_id: int,
    week_code: str,
) -> tuple[bool, list[str]]:
    """Verify the rolling-newsletter HTML approval binds to the current artifact.

    Reads the record + HTML body from the given staging week directory (so
    callers can verify against a test/fixture root, not only the global staging
    root). Returns ``(valid, problems)``. Invalid if the record is
    missing/not approved, the body changed, the target page changed, the course
    changed, or the week changed.
    """
    week_dir = Path(week_dir)
    problems: list[str] = []
    try:
        rec = json.loads((week_dir / "planner" / "homeroom-html-approval.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, ["homeroom HTML approval record missing"]
    if rec.get("kind") != KIND:
        return False, ["homeroom approval is not a rolling_newsletter_html record"]
    if not rec.get("approved"):
        return False, ["homeroom HTML approval not approved"]
    if int(rec.get("course_id") or 0) != int(course_id):
        problems.append("homeroom course id changed")
    if int(rec.get("page_id") or 0) != int(page_id):
        problems.append("homeroom rolling page id changed")
    if (rec.get("week") or "") != week_code:
        problems.append("homeroom week changed")
    try:
        body = (week_dir / "drafts" / "homeroom-page.html").read_text(encoding="utf-8")
    except OSError:
        body = None
    if body is None:
        problems.append("homeroom approved HTML body missing")
    elif _sha(body) != rec.get("approved_body_hash"):
        problems.append("homeroom approved HTML body changed")
    return (len(problems) == 0), problems


def verify(
    quarter: int,
    week: int,
    *,
    course_id: int,
    page_id: int,
    week_code: str,
) -> tuple[bool, list[str]]:
    """Verify against the global staging root (see ``verify_at`` for details)."""
    return verify_at(
        imf.staging_dir(quarter, week),
        course_id=course_id, page_id=page_id, week_code=week_code,
    )


def command_self_test() -> int:
    import tempfile

    orig = imf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        imf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            body = "<div>hi</div>"
            h = _sha(body)
            record_approval(
                2, 3, course_id=26429, page_id=798072,
                page_slug="class-4a-newsletter-x", source_body_hash="s",
                approved_body_hash=h, week_code="Q2W3", body=body,
            )
            ok, problems = verify(2, 3, course_id=26429, page_id=798072, week_code="Q2W3")
            assert ok, problems

            # One-byte body change invalidates.
            html_path(2, 3).write_text("<div>changed</div>", encoding="utf-8")
            ok2, _ = verify(2, 3, course_id=26429, page_id=798072, week_code="Q2W3")
            assert not ok2
            html_path(2, 3).write_text(body, encoding="utf-8")

            # Page id change invalidates.
            ok3, _ = verify(2, 3, course_id=26429, page_id=999999, week_code="Q2W3")
            assert not ok3

            # Week change invalidates.
            ok4, _ = verify(2, 3, course_id=26429, page_id=798072, week_code="Q2W4")
            assert not ok4

            # record_approval refuses a hash that does not match the body.
            try:
                record_approval(
                    2, 3, course_id=26429, page_id=798072,
                    page_slug="class-4a-newsletter-x", source_body_hash="s",
                    approved_body_hash="0" * 64, week_code="Q2W3", body=body,
                )
                raise AssertionError("expected ValueError for hash mismatch")
            except ValueError:
                pass
        finally:
            imf.staging_dir = orig
    print("PASS homeroom HTML approval bridge self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
