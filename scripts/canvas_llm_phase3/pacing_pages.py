"""Phase 3.3 — weekly-page + front-page activation policy (OWNER_POLICY).

Deterministic validation of the pre-created-page rule: weekly agenda pages
Q1W1-Q4W10 already exist in Canvas for every subject; normal operation must
never CREATE a new page, and front-page activation must target the existing
page only.

Read-only: no Canvas I/O. These helpers validate the *intent* (dry-run) and
fail closed on missing/duplicate pages.
"""
from __future__ import annotations

import sys
from typing import Any

from . import constants as C

ALL_SUBJECTS = ("math", "reading", "spelling", "language_arts", "history", "science")


def expected_page_identity(week_code: str, subject: str) -> dict[str, Any]:
    """Return the deterministic intended page identity for a week/subject.

    Page slugs follow the canonical ``q1w1-july-20-24-2026`` pattern from
    ``instructional-weeks-2026-2027.json``; a real page lookup uses that
    source's ``sourcePath`` + course, never a synthesized CREATE.
    """
    import json
    weeks = json.loads(C.WEEKS_PATH.read_text(encoding="utf-8")).get("weeks", [])
    entry = next((w for w in weeks if w.get("code") == week_code), None)
    return {
        "week_code": week_code,
        "subject": subject,
        "expectedPageSlug": entry.get("sourcePath") if entry else None,
        "displaySubtitle": entry.get("displaySubtitle") if entry else None,
        "mustExist": True,
        "createForbidden": True,
    }


def validate_page_policy(page: dict[str, Any]) -> dict[str, Any]:
    """Validate a page-plan record against the pre-created-page rule.

    Returns {'status': 'PASS'|'FAIL', 'blockers': [...]}.
    """
    blockers: list[str] = []
    if page.get("createForbidden") and page.get("operation") == "CREATE":
        blockers.append("CREATE forbidden: weekly agenda pages are pre-created; update the existing page")
    if not page.get("expectedPageSlug"):
        blockers.append("missing expected page identity (no canonical sourcePath)")
    if page.get("duplicated"):
        blockers.append("duplicate expected page detected")
    if page.get("missing"):
        blockers.append("expected page missing; do not create a replacement")
    return {"status": "FAIL" if blockers else "PASS", "blockers": blockers}


def front_page_activation_target(week_code: str, subject: str) -> dict[str, Any]:
    """Return the front-page activation intent (existing page only)."""
    identity = expected_page_identity(week_code, subject)
    return {
        "operation": "set_front_page",
        "target": identity,
        "idempotent": True,
        "createForbidden": True,
        "schedule": {
            "normal": "Friday 4:00 PM America/New_York (upcoming week's page)",
            "q2w1Exception": "once Owen approves Q2W1, activate ASAP and verify immediately",
        },
    }


def command_self_test() -> int:
    # Every canonical week must resolve an expected page identity.
    for code in ("Q1W1", "Q2W1", "Q2W2", "Q4W10"):
        ident = expected_page_identity(code, "math")
        assert ident["expectedPageSlug"], code
        assert ident["createForbidden"] is True

    # CREATE is forbidden.
    bad = validate_page_policy({"operation": "CREATE", "expectedPageSlug": "x", "createForbidden": True})
    assert bad["status"] == "FAIL" and any("CREATE forbidden" in b for b in bad["blockers"])

    # Missing page -> FAIL.
    missing = validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True, "missing": True})
    assert missing["status"] == "FAIL" and any("missing" in b for b in missing["blockers"])

    # Duplicate -> FAIL.
    dup = validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True, "duplicated": True})
    assert dup["status"] == "FAIL" and any("duplicate" in b for b in dup["blockers"])

    # Healthy update -> PASS.
    ok = validate_page_policy({"operation": "UPDATE", "expectedPageSlug": "x", "createForbidden": True})
    assert ok["status"] == "PASS"

    # Front-page activation targets existing page only.
    act = front_page_activation_target("Q2W1", "math")
    assert act["createForbidden"] is True and act["idempotent"] is True

    print("PASS weekly-page policy self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
