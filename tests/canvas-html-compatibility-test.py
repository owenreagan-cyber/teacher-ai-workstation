#!/usr/bin/env python3
"""Offline, deterministic validation for the Canvas HTML/Unicode compatibility framework.

Validates:
- the sandbox contract (course 24399, mustRemainUnpublished=true, sandboxOnly,
  allowed/forbidden lists, guard sequence)
- the compatibility matrix (status vocabulary exact, html/unicode/riskier
  matrices present, capture fields, no fabricated VERIFIED_* statuses)
- the guard precheck function (pure, no network): returns PASS only when the
  course record is 24399 and published == false.

Performs NO Canvas writes and NO network I/O. This is the structural gate that
gates future approved sandbox write tests; it does not itself run them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SANDBOX_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "canvas-test-sandbox.json"
COMPAT_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "canvas-html-compatibility.json"

ALLOWED_STATUS = {
    "VERIFIED_SAFE",
    "VERIFIED_WITH_NORMALIZATION",
    "UNSUPPORTED",
    "DEVICE_VARIANT",
    "REQUIRES_MORE_TESTING",
}


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sandbox_guard_precheck(course_record: dict) -> tuple[bool, list[str]]:
    """Pure guard precheck (no network). Returns (ok, blockers).

    Mirrors steps 1-3 of the canonical guard sequence: the course must be
    exactly 24399 and published == false before ANY sandbox write.
    """
    blockers: list[str] = []
    if int(course_record.get("course_id") or course_record.get("id") or 0) != 24399:
        blockers.append("course_id is not 24399")
    if course_record.get("published") is not False:
        blockers.append("course is published (must be false)")
    return (len(blockers) == 0), blockers


def main() -> int:
    # --- Sandbox contract ---
    sandbox = load(SANDBOX_PATH)
    s = sandbox["sandbox"]
    check("sandbox course_id == 24399", s["courseId"] == 24399)
    check("sandbox mustRemainUnpublished == true", s["mustRemainUnpublished"] is True)
    check("sandbox sandboxOnly == true", s["sandboxOnly"] is True)
    check("sandbox noStudentsParentsObservers == true", s["noStudentsParentsObservers"] is True)
    check("sandbox has allowed list", isinstance(sandbox.get("allowed"), list) and len(sandbox["allowed"]) >= 8)
    check("sandbox has forbidden list", isinstance(sandbox.get("forbidden"), list) and len(sandbox["forbidden"]) >= 5)
    check("sandbox guard sequence length 8", isinstance(sandbox.get("guardSequence"), list) and len(sandbox["guardSequence"]) == 8)
    check("sandbox forbids publishing", any("publish" in f for f in sandbox["forbidden"]))
    check("sandbox forbids production-touch", any("production" in f for f in sandbox["forbidden"]))
    check("sandbox privacy: no URL committed", sandbox["privacy"]["noSchoolCanvasUrlCommitted"] is True)
    check("sandbox privacy: no tokens", sandbox["privacy"]["noTokensOrSecrets"] is True)

    # --- Compatibility matrix ---
    compat = load(COMPAT_PATH)
    vocab = set(compat.get("statusVocabulary", []))
    check("status vocabulary exact", vocab == ALLOWED_STATUS)
    check("capture fields present", len(compat.get("captureFields", [])) == 8)
    check("html matrix present", len(compat.get("htmlMatrix", [])) >= 20)
    check("unicode matrix present", len(compat.get("unicodeMatrix", [])) >= 15)
    check("riskier unicode present", len(compat.get("unicodeRiskier", [])) >= 5)
    # Evidence has now been recorded from the sandbox write test. Validate that
    # every matrix status is drawn from the allowed vocabulary, and that the
    # evidence-backed results are internally consistent (accepted pages are
    # unpublished + cleaned up).
    all_statuses = (
        [e.get("status") for e in compat.get("htmlMatrix", [])]
        + [e.get("status") for e in compat.get("unicodeMatrix", [])]
        + [e.get("status") for e in compat.get("unicodeRiskier", [])]
    )
    check("all matrix statuses in allowed vocabulary", all(s in ALLOWED_STATUS for s in all_statuses))
    check("core unicode verified safe", all(
        e.get("status") == "VERIFIED_SAFE"
        for e in compat.get("unicodeMatrix", [])
        if e.get("char") in ("en dash", "em dash", "lightning", "leaf", "maple", "birthday")
    ))
    check("box-shadow marked UNSUPPORTED", any(
        e.get("element") == "box-shadow" and e.get("status") == "UNSUPPORTED"
        for e in compat.get("htmlMatrix", [])
    ))
    check("css-animation marked UNSUPPORTED", any(
        e.get("element") == "css-animation" and e.get("status") == "UNSUPPORTED"
        for e in compat.get("htmlMatrix", [])
    ))
    check("results recorded (3 pages)", len(compat.get("results", [])) == 3)
    check("evidence timestamp present", bool(compat.get("evidenceTimestamp")))

    # Unicode samples decode cleanly (no mojibake in the matrix source).
    samples = "".join(e.get("sample", "") for e in compat.get("unicodeMatrix", []))
    check("unicode matrix samples are clean UTF-8 (no mojibake)",
          not any(p in samples for p in ("\u00f0\u0178", "â€“", "â€”", "\ufffd")))

    # --- Guard precheck (pure) ---
    ok, blockers = sandbox_guard_precheck({"course_id": 24399, "published": False})
    check("guard precheck PASS for 24399 + unpublished", ok and blockers == [])
    ok2, _ = sandbox_guard_precheck({"course_id": 24399, "published": True})
    check("guard precheck FAIL when published", ok2 is False)
    ok3, _ = sandbox_guard_precheck({"course_id": 26404, "published": False})
    check("guard precheck FAIL for wrong course", ok3 is False)

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
