from __future__ import annotations

from typing import Any


def build_local_diff(revisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(revisions) < 2:
        return []
    previous, current = revisions[-2], revisions[-1]
    categories: list[str] = []
    kind = current.get("kind")
    payload = current.get("payload", {})
    if kind == "correction":
        field = str(payload.get("field") or "").lower()
        mapping = {
            "title": "title changed",
            "lesson title": "title changed",
            "in class": "lesson changed",
            "at home": "homework changed",
            "assessment date": "assessment moved",
            "resource selection": "resource replaced",
            "resource": "resource replaced",
            "reminder text": "reminder changed",
            "visibility": "visibility changed",
        }
        categories.append(mapping.get(field, "lesson changed"))
        categories.append("approval changed")
    elif kind == "approval":
        categories.append("approval changed")
    elif kind == "regenerate":
        categories.append("lesson changed")
        categories.append("resource added")
    elif kind == "export":
        categories.append("approval changed")
    else:
        categories.append("lesson changed")
    return [
        {
            "category": category,
            "fromRevision": previous.get("revision"),
            "toRevision": current.get("revision"),
            "summary": current.get("summary"),
        }
        for category in dict.fromkeys(categories)
    ]


def build_revision_history(revisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "revision": row["revision"],
            "kind": row["kind"],
            "summary": row["summary"],
            "createdAt": row["createdAt"],
            "payload": row["payload"],
        }
        for row in revisions
    ]

