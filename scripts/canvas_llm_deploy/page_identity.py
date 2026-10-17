"""Canonical Canvas page-identity model (pure; no Canvas I/O).

Encodes the rule discovered during the Homeroom newsletter cleanup:

    PAGE ID   = canonical, stable object identity
    SLUG/URL  = mutable navigation/compatibility identity
    TITLE     = mutable content metadata

A title update can make Canvas auto-derive a new canonical slug. Canvas MAY
retain the former slug as a redirect alias (this was observed; it is not
guaranteed for every historical slug). A slug change — or an old slug that
still resolves to the same ``page_id`` — is NOT evidence of page replacement,
duplication, or broken identity.

This module provides the single classification function the deployment layer
uses to (a) never fail a readback solely because the slug changed, and (b)
never create a replacement page solely because a canonical slug changed.
"""
from __future__ import annotations

from typing import Any

# ---- classification states -------------------------------------------------
UNCHANGED_SLUG = "UNCHANGED_SLUG"
CANONICAL_SLUG_CHANGED_SAME_PAGE = "CANONICAL_SLUG_CHANGED_SAME_PAGE"
LEGACY_SLUG_REDIRECTS_SAME_PAGE = "LEGACY_SLUG_REDIRECTS_SAME_PAGE"
SLUG_IDENTITY_CONFLICT = "SLUG_IDENTITY_CONFLICT"
PAGE_ID_NOT_RESOLVED = "PAGE_ID_NOT_RESOLVED"

# Which states block deployment (hard failure).
FATAL_STATES = frozenset({SLUG_IDENTITY_CONFLICT, PAGE_ID_NOT_RESOLVED})
# Which states are compatible-but-worth-noting (WARN, never FAIL).
WARN_STATES = frozenset({CANONICAL_SLUG_CHANGED_SAME_PAGE})
# Which states are clean (PASS).
PASS_STATES = frozenset({UNCHANGED_SLUG, LEGACY_SLUG_REDIRECTS_SAME_PAGE})


def _nid(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def classify_page_identity(
    *,
    known_page_id: Any,
    current_slug: str,
    current_page_id: Any,
    old_slug: str | None = None,
    old_slug_resolves_to: Any | None = None,
) -> str:
    """Classify a page's identity given observed slug/page resolutions.

    Parameters (all optional observations; ``current_*`` describe the live page
    reached via the current canonical route):

    - ``known_page_id``: the page_id we already consider canonical for the object.
    - ``current_slug``: the page's current canonical slug (its ``url``).
    - ``current_page_id``: the page_id the current route resolves to.
    - ``old_slug``: a previously-known slug (None if we have no prior slug).
    - ``old_slug_resolves_to``: what the old slug now resolves to (None if it
      no longer resolves).

    Returns one of the classification constants above.
    """
    known = _nid(known_page_id)
    current = _nid(current_page_id)
    old_resolves = _nid(old_slug_resolves_to)

    # The canonical page must resolve to the known page_id.
    if current is None:
        return PAGE_ID_NOT_RESOLVED
    if known is not None and current != known:
        return SLUG_IDENTITY_CONFLICT

    if old_slug is None or old_slug == current_slug:
        return UNCHANGED_SLUG

    # Slug changed (or a distinct legacy slug was provided).
    if old_resolves is None:
        return CANONICAL_SLUG_CHANGED_SAME_PAGE
    if old_resolves == current:
        # Legacy slug still redirects to the SAME page — compatible alias.
        return LEGACY_SLUG_REDIRECTS_SAME_PAGE
    return SLUG_IDENTITY_CONFLICT


def slug_change_is_fatal(classification: str) -> bool:
    """True only for hard identity failures (different/missing page)."""
    return classification in FATAL_STATES


def slug_change_is_warning(classification: str) -> bool:
    """True for compatible-but-noteworthy slug changes."""
    return classification in WARN_STATES


def classify_resolved_page(lookup_slug: str, page: dict[str, Any],
                           known_page_id: Any | None = None) -> str:
    """Classify a page dict resolved via ``lookup_slug`` (preflight convenience).

    Uses the resolved page's ``url`` as current canonical slug and its
    ``page_id``/``id`` as current_page_id. ``known_page_id`` defaults to the
    resolved page_id (fresh lookups have no prior identity).
    """
    pid = page.get("page_id") or page.get("id")
    url = page.get("url") or lookup_slug
    known = pid if known_page_id is None else known_page_id
    return classify_page_identity(
        known_page_id=known,
        current_slug=url,
        current_page_id=pid,
        old_slug=lookup_slug,
        old_slug_resolves_to=pid,
    )


def command_self_test() -> int:
    # Case A: same page_id + changed slug (old slug no longer resolves).
    assert classify_page_identity(
        known_page_id=798072, current_slug="new-slug", current_page_id=798072,
        old_slug="old-slug", old_slug_resolves_to=None,
    ) == CANONICAL_SLUG_CHANGED_SAME_PAGE

    # Case B: old slug + new slug both resolve same page_id -> alias (PASS).
    assert classify_page_identity(
        known_page_id=798072, current_slug="class-4a-newsletter-october-19-23-2026",
        current_page_id=798072, old_slug="q1w2-july-27-31-2026",
        old_slug_resolves_to=798072,
    ) == LEGACY_SLUG_REDIRECTS_SAME_PAGE

    # Case C: same-looking title but different page_ids -> conflict (FAIL).
    assert classify_page_identity(
        known_page_id=798072, current_slug="new-slug", current_page_id=999999,
        old_slug=None, old_slug_resolves_to=None,
    ) == SLUG_IDENTITY_CONFLICT

    # Case D: legacy slug resolves to a different page_id -> conflict (FAIL).
    assert classify_page_identity(
        known_page_id=798072, current_slug="new-slug", current_page_id=798072,
        old_slug="old-slug", old_slug_resolves_to=888888,
    ) == SLUG_IDENTITY_CONFLICT

    # Case E: known page_id no longer resolves -> missing (FAIL).
    assert classify_page_identity(
        known_page_id=798072, current_slug="whatever", current_page_id=None,
        old_slug=None, old_slug_resolves_to=None,
    ) == PAGE_ID_NOT_RESOLVED

    # Case F: slug missing but known page_id resolves correctly -> PASS.
    assert classify_page_identity(
        known_page_id=798072, current_slug="whatever", current_page_id=798072,
        old_slug=None, old_slug_resolves_to=None,
    ) == UNCHANGED_SLUG

    # No prior slug and unchanged -> UNCHANGED.
    assert classify_page_identity(
        known_page_id=798072, current_slug="s", current_page_id=798072,
    ) == UNCHANGED_SLUG

    # Fatality / warning semantics.
    assert slug_change_is_fatal(SLUG_IDENTITY_CONFLICT) is True
    assert slug_change_is_fatal(PAGE_ID_NOT_RESOLVED) is True
    assert slug_change_is_fatal(CANONICAL_SLUG_CHANGED_SAME_PAGE) is False
    assert slug_change_is_fatal(LEGACY_SLUG_REDIRECTS_SAME_PAGE) is False
    assert slug_change_is_warning(CANONICAL_SLUG_CHANGED_SAME_PAGE) is True
    assert slug_change_is_warning(LEGACY_SLUG_REDIRECTS_SAME_PAGE) is False

    # classify_resolved_page convenience (legacy slug redirects to same page).
    assert classify_resolved_page(
        "q1w2-july-27-31-2026",
        {"page_id": 798072, "url": "class-4a-newsletter-october-19-23-2026"},
    ) == LEGACY_SLUG_REDIRECTS_SAME_PAGE

    print("PASS canvas page identity self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
