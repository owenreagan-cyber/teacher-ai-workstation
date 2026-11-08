"""One-time pairing codes, verifiers, and QR payloads.

The code has 60 bits of entropy (12 symbols from a 32-symbol alphabet), is
single-use, expires within ten minutes, and is stored only as a salted hash.
QR payloads contain only the enrollment id, the one-time code, and expiry; they
never contain the master token or a permanent device credential.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass

from ..models import DeviceError

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I/O/0/1 ambiguity
CODE_LENGTH = 12
CODE_GROUPS = 3
MAX_CODE_TTL_S = 600
DEFAULT_CODE_TTL_S = 600
MAX_CODE_ATTEMPTS = 5
_NORMALIZED = re.compile(r"^[A-Z2-9]{12}$")


@dataclass(frozen=True)
class CodeMaterial:
    display_code: str
    normalized_code: str
    salt: str
    verifier: str


def generate_pairing_code() -> str:
    chars = [secrets.choice(ALPHABET) for _ in range(CODE_LENGTH)]
    size = CODE_LENGTH // CODE_GROUPS
    return "-".join("".join(chars[i : i + size]) for i in range(0, CODE_LENGTH, size))


def normalize_pairing_code(value: str) -> str:
    if not isinstance(value, str):
        raise DeviceError("pairing code must be text")
    compact = re.sub(r"[\s-]+", "", value).upper()
    if not _NORMALIZED.fullmatch(compact):
        raise DeviceError("pairing code is malformed")
    return compact


def code_verifier(normalized_code: str, salt: str) -> str:
    return hashlib.sha256((salt + normalized_code).encode("utf-8")).hexdigest()


def generate_code_material() -> CodeMaterial:
    display = generate_pairing_code()
    normalized = normalize_pairing_code(display)
    salt = secrets.token_hex(16)
    return CodeMaterial(
        display_code=display,
        normalized_code=normalized,
        salt=salt,
        verifier=code_verifier(normalized, salt),
    )


def verify_pairing_code(supplied: str, *, salt: str, verifier: str) -> bool:
    try:
        normalized = normalize_pairing_code(supplied)
    except DeviceError:
        return False
    if not isinstance(salt, str) or not isinstance(verifier, str):
        return False
    return hmac.compare_digest(code_verifier(normalized, salt), verifier)


def qr_payload(*, enrollment_id: str, display_code: str, expires_at: str) -> str:
    return json.dumps(
        {
            "v": 1,
            "enrollment_id": enrollment_id,
            "code": display_code,
            "expires_at": expires_at,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_qr_payload(raw: str) -> dict[str, str]:
    if not isinstance(raw, str):
        raise DeviceError("QR payload must be text")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise DeviceError("QR payload is invalid") from exc
    if not isinstance(data, dict) or data.get("v") != 1:
        raise DeviceError("unsupported QR payload version")
    for key in ("enrollment_id", "code", "expires_at"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise DeviceError(f"QR payload is missing {key}")
    return {
        "enrollment_id": data["enrollment_id"],
        "code": data["code"],
        "expires_at": data["expires_at"],
    }
