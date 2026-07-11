from __future__ import annotations

import html
import json
import re
import unicodedata
from hashlib import sha256
from typing import Any


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", value).strip()


def canonicalize_html(value: str) -> str:
    value = _normalize_text(value)
    value = re.sub(r">\s+<", "><", value)
    value = re.sub(r"\s+", " ", value)
    return value


def canonicalize_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonicalize_content(value: Any) -> str:
    if isinstance(value, str):
        if "<" in value and ">" in value:
            return canonicalize_html(value)
        return _normalize_text(value)
    return canonicalize_json(value)


def canonical_hash(value: Any) -> str:
    return sha256(canonicalize_content(value).encode("utf-8")).hexdigest()


def body_hash(value: Any) -> str:
    return canonical_hash(value)


def metadata_hash(value: Any) -> str:
    return canonical_hash(value)


def placement_hash(value: Any) -> str:
    return canonical_hash(value)


def full_operation_hash(value: Any) -> str:
    return canonical_hash(value)

