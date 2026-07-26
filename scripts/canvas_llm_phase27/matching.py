from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MatchResult:
    status: str  # "matched" | "unresolved" | "conflict"
    matchedCanvasId: str | None
    matchReason: str | None
    confidence: float
    candidateIds: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matchedCanvasId": self.matchedCanvasId,
            "matchReason": self.matchReason,
            "confidence": self.confidence,
            "candidateIds": self.candidateIds,
        }


def _normalize_title(title: str) -> str:
    return " ".join((title or "").strip().lower().split())


def _ids(candidates: list[dict[str, Any]]) -> list[str]:
    return [c["canvasId"] for c in candidates]


def match_object(
    local: dict[str, Any],
    remote_candidates: list[dict[str, Any]],
    alias_registry: dict[str, str] | None = None,
) -> MatchResult:
    """Deterministic matching precedence: saved Canvas ID -> exact slug ->
    exact canonical title within course -> approved alias -> unique
    high-confidence fuzzy title match -> unresolved.

    Never matches across courses: `remote_candidates` must already be
    filtered to `local["courseRef"]` by the caller, and this function
    re-filters defensively so a caller mistake cannot cause a cross-course
    match.
    """
    alias_registry = alias_registry or {}
    course_ref = local.get("courseRef")
    object_type = local.get("objectType")
    same_course = [
        r
        for r in remote_candidates
        if r.get("courseRef") == course_ref and r.get("objectType") == object_type
    ]

    saved_id = local.get("targetCanvasId")
    if saved_id:
        hits = [r for r in same_course if r.get("canvasId") == saved_id]
        if len(hits) == 1:
            return MatchResult("matched", hits[0]["canvasId"], "canvas-id", 1.0, _ids(hits))
        if len(hits) > 1:
            return MatchResult("conflict", None, "canvas-id-ambiguous", 0.0, _ids(hits))

    slug = local.get("slug")
    if slug:
        hits = [r for r in same_course if r.get("slug") == slug]
        if len(hits) == 1:
            return MatchResult("matched", hits[0]["canvasId"], "exact-slug", 0.95, _ids(hits))
        if len(hits) > 1:
            return MatchResult("conflict", None, "slug-ambiguous", 0.0, _ids(hits))

    title = _normalize_title(local.get("title") or local.get("canonicalTitle", ""))
    if title:
        title_hits = [r for r in same_course if _normalize_title(r.get("title", "")) == title]
        if len(title_hits) == 1:
            return MatchResult(
                "matched", title_hits[0]["canvasId"], "exact-title", 0.85, _ids(title_hits)
            )
        if len(title_hits) > 1:
            return MatchResult("conflict", None, "title-ambiguous", 0.0, _ids(title_hits))

    alias_target = alias_registry.get(local.get("localObjectId", ""))
    if alias_target:
        hits = [r for r in same_course if r.get("canvasId") == alias_target]
        if len(hits) == 1:
            return MatchResult(
                "matched", hits[0]["canvasId"], "approved-alias", 0.8, _ids(hits)
            )

    if title:
        fuzzy_hits = [
            r
            for r in same_course
            if title in _normalize_title(r.get("title", ""))
            or _normalize_title(r.get("title", "")) in title
        ]
        if len(fuzzy_hits) == 1:
            return MatchResult(
                "matched", fuzzy_hits[0]["canvasId"], "fuzzy-title", 0.6, _ids(fuzzy_hits)
            )
        if len(fuzzy_hits) > 1:
            return MatchResult("conflict", None, "fuzzy-title-ambiguous", 0.0, _ids(fuzzy_hits))

    return MatchResult("unresolved", None, None, 0.0, [])
