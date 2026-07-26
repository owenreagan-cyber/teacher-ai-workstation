from __future__ import annotations

import re
import urllib.parse
from typing import Any, Callable

_LINK_RE = re.compile(r'<([^>]+)>\s*;\s*rel="?([a-zA-Z]+)"?')
_SENSITIVE_QUERY_KEYS = {"token", "access_token", "api_key", "password"}


class PaginationError(RuntimeError):
    pass


def parse_link_header(header_value: str | None) -> dict[str, str]:
    """Parses an RFC 5988 Link header. Malformed entries are simply skipped
    (no match), never raise -- an unparseable header just means no 'next'
    relation is found, which safely stops pagination."""
    if not header_value:
        return {}
    links: dict[str, str] = {}
    for part in header_value.split(","):
        match = _LINK_RE.search(part)
        if match:
            url, rel = match.group(1), match.group(2)
            links[rel.lower()] = url
    return links


def get_header(headers: dict[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def redact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = [(k, "REDACTED" if k.lower() in _SENSITIVE_QUERY_KEYS else v) for k, v in pairs]
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(redacted), parsed.fragment)
    )


def paginate(
    fetch_page: Callable[[str], tuple[list[dict[str, Any]], dict[str, str]]],
    start_url: str,
    page_cap: int = 50,
    item_cap: int = 5000,
) -> list[dict[str, Any]]:
    """Follows only the Link header's rel="next" URL, treated as fully
    opaque (never reconstructed, so query parameters are preserved exactly
    as the server sent them). Stops on: no next link, a repeated URL
    (loop), the page cap, or the item cap."""
    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    url: str | None = start_url
    pages = 0

    while url:
        if url in seen_urls:
            raise PaginationError(f"pagination loop detected at {redact_url(url)}")
        seen_urls.add(url)
        pages += 1
        if pages > page_cap:
            raise PaginationError(f"page cap ({page_cap}) exceeded")

        page_items, headers = fetch_page(url)
        items.extend(page_items)
        if len(items) > item_cap:
            raise PaginationError(f"item cap ({item_cap}) exceeded")

        links = parse_link_header(get_header(headers, "Link"))
        url = links.get("next")

    return items
