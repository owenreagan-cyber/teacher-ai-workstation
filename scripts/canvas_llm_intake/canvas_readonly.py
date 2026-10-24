"""GET-only Canvas context for intake (page lookup + duplicate prevention).

This module issues GET requests only. It is used to locate the pre-created
weekly pages and to check for existing assignments before proposing anything.
It never performs POST/PUT/PATCH/DELETE and never constructs a write path.

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


class CanvasReadOnly:
    """Minimal GET-only Canvas client for intake lookups."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    @classmethod
    def from_env(cls) -> "CanvasReadOnly":
        creds = credentials.load_credentials()
        return cls(creds["CANVAS_BASE_URL"], creds["CANVAS_TOKEN"])

    def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError:
            return None
        except urllib.error.URLError:
            return None

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        """Return the page object if a single page with this slug exists, else None."""
        return self._get(f"/api/v1/courses/{course_id}/pages/{urllib.parse.quote(slug)}")

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        """GET all pages for a course (unique-target / duplicate detection)."""
        data = self._get(f"/api/v1/courses/{course_id}/pages?per_page=100")
        return data if isinstance(data, list) else []

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/api/v1/courses/{course_id}/assignments?per_page=100")
        return data if isinstance(data, list) else []

    def get_course(self, course_id: int) -> dict[str, Any] | None:
        """GET the course object (id, name, workflow_state)."""
        return self._get(f"/api/v1/courses/{course_id}")

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/api/v1/courses/{course_id}/assignment_groups")
        return data if isinstance(data, list) else []

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/api/v1/courses/{course_id}/discussion_topics?only_announcements=true&per_page=100")
        return data if isinstance(data, list) else []

    def list_active_announcements(self, context_codes: list[str] | None = None) -> list[dict[str, Any]]:
        """Account-wide active-only announcement feed, scoped to context codes.

        The Canvas Announcements API requires ``context_codes[]`` (e.g.
        ``course_<id>``); requesting ``/api/v1/announcements`` without it returns
        HTTP 400. This is the canonical student-visibility signal.
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
