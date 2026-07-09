#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"\b(?:Bearer\s+)?[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-\.]{8,}\b")
LONG_SECRET_RE = re.compile(r"\b[A-Za-z0-9_\-]{48,}\b")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def sanitize_text(value: str, canvas_base_url: str | None = None) -> str:
    sanitized = value
    if canvas_base_url:
        sanitized = sanitized.replace(canvas_base_url.rstrip("/"), "[CANVAS_BASE_URL]")
    sanitized = URL_RE.sub("[URL_REMOVED]", sanitized)
    sanitized = EMAIL_RE.sub("[EMAIL_REMOVED]", sanitized)
    sanitized = TOKEN_RE.sub("[TOKEN_REMOVED]", sanitized)
    sanitized = LONG_SECRET_RE.sub("[TOKEN_LIKE_REMOVED]", sanitized)
    return sanitized


def sanitize_value(value: Any, canvas_base_url: str | None = None) -> Any:
    if isinstance(value, str):
        return sanitize_text(value, canvas_base_url)
    if isinstance(value, list):
        return [sanitize_value(item, canvas_base_url) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in {"url", "html_url", "avatar_url", "preview_url", "api_url"}:
                sanitized[key] = "[URL_REMOVED]" if item else item
            elif lowered in {"name", "display_name", "short_name", "sortable_name", "email", "login_id"}:
                sanitized[key] = "[PERSON_OR_EMAIL_REMOVED]" if item else item
            elif lowered in {"body", "description", "message"}:
                sanitized[key] = sanitize_text(str(item), canvas_base_url)[:2000] if item else item
            else:
                sanitized[key] = sanitize_value(item, canvas_base_url)
        return sanitized
    return value
