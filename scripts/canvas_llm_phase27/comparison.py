from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .canonicalize import body_hash, canonicalize_content, metadata_hash, placement_hash


def compare_objects(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    diffs = []
    fields = ["title", "body", "publication", "dueDate", "modulePosition", "linkTarget"]
    for field in fields:
        if local.get(field) != remote.get(field):
            diffs.append({"field": field, "before": remote.get(field), "after": local.get(field)})
    if not remote:
        status = "CREATE"
    elif not local:
        status = "DELETE_CANDIDATE"
    elif diffs:
        status = "UPDATE"
    else:
        status = "UNCHANGED"
    if local.get("blockedReasons"):
        status = "BLOCKED"
    if local.get("conflict"):
        status = "CONFLICT"
    return {
        "comparisonStatus": status,
        "fieldDiffs": diffs,
        "contentHashBefore": body_hash(remote.get("body", "")),
        "contentHashAfter": body_hash(local.get("body", "")),
        "metadataHash": metadata_hash({"title": local.get("title"), "publication": local.get("publication")}),
        "placementHash": placement_hash({"module": local.get("moduleRef"), "position": local.get("modulePosition")}),
    }

