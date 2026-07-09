#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from canvas_safety import require_reference_read_only, require_safe_endpoint


@dataclass
class CanvasApiClient:
    base_url: str
    token: str
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "CanvasApiClient":
        base_url = os.environ.get("CANVAS_BASE_URL", "").strip().rstrip("/")
        token = os.environ.get("CANVAS_TOKEN", "").strip()
        if not base_url or not token:
            raise SystemExit("FAIL: CANVAS_BASE_URL and CANVAS_TOKEN are required")
        return cls(base_url=base_url, token=token)

    def request(
        self,
        method: str,
        kind: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        course_id: str | None = None,
    ) -> Any:
        require_safe_endpoint(kind, path)
        if course_id:
            require_reference_read_only(course_id, method)
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            text = response.read().decode("utf-8")
            if not text:
                return {}
            return json.loads(text)

    def get_paginated(
        self,
        kind: str,
        path: str,
        params: dict[str, Any] | None = None,
        course_id: str | None = None,
        limit_pages: int = 10,
    ) -> list[Any]:
        require_safe_endpoint(kind, path)
        url = f"{self.base_url}{path}"
        merged = {"per_page": 100}
        if params:
            merged.update(params)
        url = f"{url}?{urllib.parse.urlencode(merged, doseq=True)}"
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        items: list[Any] = []
        for _ in range(limit_pages):
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8") or "[]")
                if isinstance(payload, list):
                    items.extend(payload)
                else:
                    items.append(payload)
                link = response.headers.get("Link", "")
            next_url = _next_link(link)
            if not next_url:
                break
            url = next_url
        if course_id:
            require_reference_read_only(course_id, "GET")
        return items


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">")
        if start >= 0 and end > start:
            return part[start + 1 : end]
    return None
