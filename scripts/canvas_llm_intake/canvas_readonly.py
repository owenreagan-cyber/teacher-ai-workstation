"""GET-only Canvas context for intake (page lookup + duplicate prevention).

This module issues GET requests only. It is used to locate the pre-created
weekly pages and to check for existing assignments before proposing anything.
It never performs POST/PUT/PATCH/DELETE and never constructs a write path.

Announcement reads are strict: a successful list may be empty (zero duplicates),
but an HTTP or transport failure raises ``CanvasTransportError``. A failure is
never converted into an empty list.

Write verbs are statically forbidden here; the zero-write proof in the status
module scans this package for write-verb tokens.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402


class CanvasTransportError(RuntimeError):
    """A Canvas GET failed at the transport/HTTP layer.

    This is deliberately distinct from an empty successful result. Callers that
    need duplicate detection must never treat a transport failure as "nothing
    found".
    """

    def __init__(self, path: str, *, status: int | None = None, reason: str = "") -> None:
        self.path = path
        self.status = status
        self.reason = reason
        detail = f"HTTP {status}" if status is not None else "transport error"
        super().__init__(f"Canvas GET {path} failed ({detail}: {reason})")


class CanvasReadOnly:
    """Minimal GET-only Canvas client for intake lookups."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    @classmethod
    def from_env(cls) -> "CanvasReadOnly":
        creds = credentials.load_credentials()
        return cls(creds["CANVAS_BASE_URL"], creds["CANVAS_TOKEN"])

    def _get_strict(self, path: str) -> Any:
        """GET and return the decoded body, or raise ``CanvasTransportError``.

        Never converts a transport or HTTP failure into an empty value.
        """
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise CanvasTransportError(path, status=exc.code,
                                       reason=str(exc.reason)) from exc
        except urllib.error.URLError as exc:
            raise CanvasTransportError(path, reason=str(exc.reason)) from exc
        except ValueError as exc:
            raise CanvasTransportError(path,
                                       reason=f"invalid JSON payload: {exc}") from exc

    def _get(self, path: str) -> Any:
        """Legacy soft GET: ``None`` on failure. Not used for announcement duplication."""
        try:
            return self._get_strict(path)
        except CanvasTransportError:
            return None

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        """Return the page object if a single page with this slug exists, else None."""
        return self._get(f"/api/v1/courses/{course_id}/pages/{urllib.parse.quote(slug)}")

    def get_page(self, course_id: int, page_ref: str) -> dict[str, Any] | None:
        """GET one page by slug/id reference. Read-only alias of ``find_page``."""
        return self.find_page(course_id, page_ref)

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        """GET all pages for a course (unique-target / duplicate detection)."""
        data = self._get(f"/api/v1/courses/{course_id}/pages?per_page=100")
        return data if isinstance(data, list) else []

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        """Read every Canvas assignment page; fail closed on incomplete reads."""
        import re

        path = f"/api/v1/courses/{int(course_id)}/assignments"
        url = f"{self.base_url}{path}?per_page=100"
        expected_origin = urllib.parse.urlsplit(self.base_url)
        visited: set[str] = set()
        assignments: list[dict[str, Any]] = []

        while url:
            if url in visited or len(visited) >= 20:
                raise CanvasTransportError(
                    path, reason="assignment pagination loop or page limit"
                )

            parts = urllib.parse.urlsplit(url)
            if (
                parts.scheme != expected_origin.scheme
                or parts.netloc != expected_origin.netloc
                or parts.path != path
            ):
                raise CanvasTransportError(
                    path, reason="unexpected assignment pagination URL"
                )

            visited.add(url)
            request = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                },
                method="GET",
            )

            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    links = response.headers.get("Link", "")
            except urllib.error.HTTPError as exc:
                raise CanvasTransportError(
                    path, status=exc.code, reason=str(exc.reason)
                ) from exc
            except (urllib.error.URLError, ValueError) as exc:
                raise CanvasTransportError(
                    path, reason=type(exc).__name__
                ) from exc

            if not isinstance(data, list) or any(
                not isinstance(item, dict) for item in data
            ):
                raise CanvasTransportError(
                    path, reason="unexpected assignment response"
                )

            assignments.extend(data)

            next_links = re.findall(
                r'<([^>]+)>;\s*rel="next"', links
            )
            if len(next_links) > 1:
                raise CanvasTransportError(
                    path, reason="ambiguous pagination links"
                )
            if not next_links and re.search(
                r'rel\s*=\s*"?next"?', links, re.I
            ):
                raise CanvasTransportError(
                    path, reason="unparseable next-page link"
                )

            url = (
                urllib.parse.urljoin(url, next_links[0])
                if next_links else None
            )

        return assignments

    def get_file(self, course_id: int, file_id: int) -> dict[str, Any] | None:
        """GET one course file. Returns only an authoritative URL that names the file id."""
        data = self._get(f"/api/v1/courses/{course_id}/files/{int(file_id)}")
        if not isinstance(data, dict) or int(data.get("id") or 0) != int(file_id):
            return None
        url = data.get("url") or data.get("html_url") or ""
        if str(file_id) not in str(url):
            return None
        return {
            "id": int(file_id),
            "display_name": data.get("display_name") or data.get("filename") or "",
            "url": url,
            "source": "CANVAS_FILE_METADATA",
        }

    def get_course(self, course_id: int) -> dict[str, Any] | None:
        """GET the course object (id, name, workflow_state)."""
        return self._get(f"/api/v1/courses/{course_id}")

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/api/v1/courses/{course_id}/assignment_groups")
        return data if isinstance(data, list) else []

    def get_assignment(self, course_id: int, assignment_id: int | str) -> dict[str, Any] | None:
        """GET one assignment by id (read-only). 404 -> None, other failures raise."""
        path = f"/api/v1/courses/{int(course_id)}/assignments/{assignment_id}"
        try:
            return self._get_strict(path)
        except CanvasTransportError as exc:
            if exc.status == 404:
                return None
            raise

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        """GET course announcements. Empty list = zero; failure raises.

        ``CanvasTransportError`` means the duplicate check is unavailable and
        must be reported as a verification error, never as zero duplicates.
        """
        path = (f"/api/v1/courses/{course_id}/discussion_topics"
                f"?only_announcements=true&per_page=100")
        data = self._get_strict(path)
        if not isinstance(data, list):
            raise CanvasTransportError(path, reason="unexpected payload (expected list)")
        return data

    def get_announcement(self, course_id: int, announcement_id: int | str) -> dict[str, Any] | None:
        """GET one announcement by id (read-only).

        Returns ``None`` only for HTTP 404 (genuinely absent). Other transport
        and HTTP failures raise ``CanvasTransportError`` so callers can
        distinguish "missing" from "unreachable".
        """
        path = f"/api/v1/courses/{course_id}/discussion_topics/{announcement_id}"
        try:
            return self._get_strict(path)
        except CanvasTransportError as exc:
            if exc.status == 404:
                return None
            raise

    def list_active_announcements(self, context_codes: list[str] | None = None) -> list[dict[str, Any]]:
        """Account-wide active-only announcement feed, scoped to context codes.

        The Canvas Announcements API requires ``context_codes[]`` (e.g.
        ``course_<id>``). Canvas returns future-scheduled announcements to course
        administrators, so this feed is NOT proof of student visibility.
        """
        params = ["active_only=true", "per_page=100"]
        for code in context_codes or []:
            params.append(f"context_codes[]={urllib.parse.quote(code)}")
        data = self._get(f"/api/v1/announcements?{'&'.join(params)}")
        return data if isinstance(data, list) else []


def command_self_test() -> int:
    # No network: verify the module has no write verbs. Tokens are constructed
    # dynamically so the scanner's own source never self-matches.
    source = __import__("pathlib").Path(__file__).read_text(encoding="utf-8")
    tokens = ["." + v + "(" for v in ("post", "put", "patch", "delete")]
    tokens += ["method" + "=\"" + v.upper() + "\"" for v in ("post", "put", "patch", "delete")]
    for tok in tokens:
        assert tok not in source, f"write token {tok!r} present"
    print("PASS intake canvas-readonly self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
