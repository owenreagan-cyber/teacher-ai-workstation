from __future__ import annotations

from typing import Any

from .canonicalize import body_hash, canonicalize_content, metadata_hash, placement_hash

# Field -> change-kind classification, per Part 13 of the Phase 27 spec.
_FIELD_KIND = {
    "title": "metadata-only change",
    "body": "material content change",
    "publication": "publication-only change",
    "dueDate": "date-only change",
    "unlockDate": "date-only change",
    "lockDate": "date-only change",
    "assignmentGroup": "metadata-only change",
    "submissionType": "metadata-only change",
    "pointsPossible": "metadata-only change",
    "modulePosition": "placement-only change",
    "moduleRef": "placement-only change",
    "linkTarget": "metadata-only change",
    "visibility": "publication-only change",
}

_COMPARED_FIELDS = tuple(_FIELD_KIND.keys())


def field_level_diff(local: dict[str, Any], remote: dict[str, Any]) -> list[dict[str, Any]]:
    diffs = []
    for name in _COMPARED_FIELDS:
        before = remote.get(name)
        after = local.get(name)
        if name == "body":
            # Canonicalized comparison: whitespace-equivalent HTML is not a
            # change, matching body_hash's own equivalence rule.
            changed = canonicalize_content(before or "") != canonicalize_content(after or "")
        else:
            changed = before != after
        if changed:
            diffs.append(
                {
                    "field": name,
                    "before": before,
                    "after": after,
                    "changeKind": _FIELD_KIND[name],
                }
            )
    return diffs


def compare_content(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    """Real field-level comparison between a local desired object and its
    matched remote Canvas object (empty dict if unmatched). Produces field
    diffs and the three narrower hash domains for both sides. Does not
    itself assign a comparisonStatus -- that is derived in safety_diff.py
    from real match/dependency/policy state, never from a fixture field."""
    diffs = field_level_diff(local, remote)
    return {
        "fieldDiffs": diffs,
        "hasMaterialChange": any(d["changeKind"] == "material content change" for d in diffs),
        "contentHashBefore": body_hash(remote),
        "contentHashAfter": body_hash(local),
        "metadataHashBefore": metadata_hash(remote),
        "metadataHashAfter": metadata_hash(local),
        "placementHashBefore": placement_hash(remote),
        "placementHashAfter": placement_hash(local),
    }
