from __future__ import annotations

import json
import re
import unicodedata
from hashlib import sha256
from typing import Any, Iterable, Mapping

# Fields excluded from every hash domain: volatile timestamps, local filesystem
# paths, transient UI state, and secret/authentication material.
_VOLATILE_KEYS = {
    "updatedAt",
    "createdAt",
    "generatedAt",
    "timestamp",
    "localPath",
    "path",
    "_localPath",
    "cwd",
    "token",
    "authorization",
    "apiKey",
    "api_key",
    "cookie",
    "password",
    "secret",
    "sessionToken",
}

_METADATA_FIELDS = (
    "title",
    "publication",
    "dueDate",
    "unlockDate",
    "lockDate",
    "assignmentGroup",
    "submissionType",
    "pointsPossible",
    "visibility",
)


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", value).strip()


def canonicalize_html(value: str) -> str:
    """Deterministic HTML canonicalization: collapses insignificant whitespace
    between tags while preserving semantically meaningful text whitespace."""
    value = _normalize_text(value)
    value = re.sub(r">\s+<", "><", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    return value


def _strip_volatile(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_volatile(val)
            for key, val in value.items()
            if key not in _VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value


def canonicalize_json(value: Any) -> str:
    return json.dumps(
        _strip_volatile(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def canonicalize_content(value: Any) -> str:
    if isinstance(value, str):
        if "<" in value and ">" in value:
            return canonicalize_html(value)
        return _normalize_text(value)
    return canonicalize_json(value)


def canonical_hash(value: Any) -> str:
    """Generic deterministic SHA-256 hash of any canonicalizable value."""
    return sha256(canonicalize_content(value).encode("utf-8")).hexdigest()


def body_hash(obj: Mapping[str, Any]) -> str:
    """Hash of the object's body content only. Changes only when the body
    (visible content) changes; unaffected by title, dates, or placement."""
    body = obj.get("body", obj.get("canonicalBody", ""))
    return canonical_hash(body)


def metadata_hash(obj: Mapping[str, Any]) -> str:
    """Hash of title/publication/due-unlock-lock dates/assignment metadata.
    Excludes body content and module placement."""
    payload = {name: obj.get(name) for name in _METADATA_FIELDS if name in obj}
    return canonical_hash(payload)


def placement_hash(obj: Mapping[str, Any]) -> str:
    """Hash of module assignment and position only. Excludes body and metadata."""
    payload = {
        "module": obj.get("module") or obj.get("moduleRef"),
        "position": obj.get("position") if "position" in obj else obj.get("modulePosition"),
    }
    return canonical_hash(payload)


def full_operation_hash(obj: Mapping[str, Any], dependencies: Iterable[str] | None = None) -> str:
    """Hash of the complete operation identity: body + metadata + placement +
    sorted dependency ids. Changes if any of those change, including
    dependency-only changes that leave body/metadata/placement untouched."""
    deps = list(dependencies if dependencies is not None else obj.get("dependencies", []) or [])
    payload = {
        "body": body_hash(obj),
        "metadata": metadata_hash(obj),
        "placement": placement_hash(obj),
        "dependencies": sorted(deps),
    }
    return canonical_hash(payload)
