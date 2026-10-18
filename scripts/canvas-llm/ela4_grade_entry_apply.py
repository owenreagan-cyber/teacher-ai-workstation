#!/usr/bin/env python3
"""Apply the sealed ELA4 Personal Narrative Final Draft grade packet (approved).

Approved by Owen Reagan on 2026-09-20. Packet hash:
64a927d064188e94148e481a0a3dfe1bf754728a032cb4011adf339339151b72

Writes only the 19 approved (student, assignment) grades. A tripwire rejects any
Canvas request outside the approved course/assignment before it is sent.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_entry import grade_entry as ge  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

OUT = REPO_ROOT / ".local" / "canvas-llm" / "grade-entry"
PACKET_HASH = "64a927d064188e94148e481a0a3dfe1bf754728a032cb4011adf339339151b72"
PACKET = OUT / f"{PACKET_HASH[:12]}-packet.json"
COURSE_ID = 28171
ASSIGNMENT_ID = 1042769
APPROVER = "Owen Reagan"
SKIPPED_STUDENT_ID = 44023  # Nathan Snapp


def main() -> int:
    credentials.load_credentials()
    packet = ge.ApprovalPacket.load(PACKET)
    print(f"packet hash file : {packet.packet_hash}")
    print(f"packet hash match: {packet.packet_hash == PACKET_HASH}")
    if packet.packet_hash != PACKET_HASH:
        print("BLOCKER: sealed packet hash does not match the approved hash")
        return 1
    if int(packet.course["course_id"]) != COURSE_ID:
        print("BLOCKER: packet course does not match")
        return 1
    if int(packet.assignment["assignment_id"]) != ASSIGNMENT_ID:
        print("BLOCKER: packet assignment does not match")
        return 1
    print(packet.render())

    before = json.loads((OUT / "pre-full-submissions.json").read_text())

    # --- tripwire: reject any request outside the approved course ----------
    live = ge.CanvasGradeClient.from_env()
    audit: list[dict[str, Any]] = []

    def guarded(method: str, path: str, data: dict[str, Any] | None) -> Any:
        entry = {"method": method.upper(), "path": path, "data": dict(data or {})}
        audit.append(entry)
        if f"/courses/{COURSE_ID}" not in path:
            raise ge.GradeEntryError(f"TRIPWIRE: request outside approved course: {method} {path}")
        if method.upper() == "PUT":
            if f"/assignments/{ASSIGNMENT_ID}/submissions/" not in path:
                raise ge.GradeEntryError(f"TRIPWIRE: write outside approved assignment: {path}")
            ge.assert_write_payload_is_bounded(data or {})
        return live.request(method, path, data)

    guarded_client = ge.CanvasGradeClient("https://guarded.invalid", "guarded",
                                          transport=guarded)

    ge.enable(owner=APPROVER)
    print(f"\nenabled by: {ge.enabled_by()}")
    report = ge.apply_packet(packet=packet, client=guarded_client, approved=True,
                             approved_by=APPROVER)

    (OUT / "apply-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "apply-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    # --- readback -----------------------------------------------------------
    after_rows = live.list_submissions(COURSE_ID)
    after = {f"{s['student_id']}:{s['assignment_id']}": s["score"] for s in after_rows}

    requested = {int(c["student_id"]): ge.parse_grade(c["proposed_grade"])
                 for c in packet.proposed_changes}
    matches = 0
    failures: list[str] = []
    for sid, want in requested.items():
        got = after.get(f"{sid}:{ASSIGNMENT_ID}")
        if got is not None and ge.grades_equal(float(got), want):
            matches += 1
        else:
            failures.append(f"student {sid}: wanted {want}, live {got}")

    # untouched proofs
    changed = {
        key for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    }
    expected_keys = {f"{sid}:{ASSIGNMENT_ID}" for sid in requested if before.get(f"{sid}:{ASSIGNMENT_ID}") != requested[sid]}
    unexpected = changed - expected_keys
    nathan_key = f"{SKIPPED_STUDENT_ID}:{ASSIGNMENT_ID}"
    writes = [e for e in audit if e["method"] == "PUT"]
    put_students = {int(e["path"].rstrip("/").split("/")[-1]) for e in writes}

    print("\n" + "=" * 72)
    print("RESULT")
    print(f"  approved writes attempted: 19 (packet total_writes={packet.total_writes})")
    print(f"  PUT requests issued: {len(writes)}")
    print(f"  write targets: {sorted(put_students)}")
    print(f"  readback matches: {matches}/19")
    print(f"  readback mismatches: {report['readback_mismatches'] or 'none'}")
    print(f"  changed submission keys: {len(changed)} (expected {len(expected_keys)})")
    print(f"  unexpected changes: {sorted(unexpected) or 'NONE'}")
    print(f"  Nathan Snapp key present: {nathan_key in before or nathan_key in after}")
    print(f"  Nathan Snapp before/after: {before.get(nathan_key)} / {after.get(nathan_key)}")
    print(f"  Nathan Snapp written: {SKIPPED_STUDENT_ID in put_students}")

    ok = (
        matches == 19
        and len(writes) == 19
        and not unexpected
        and SKIPPED_STUDENT_ID not in put_students
        and before.get(nathan_key) == after.get(nathan_key)
        and report["readback_verified"]
    )
    print(f"\nGRADE ENTRY APPLY: {'PASS' if ok else 'FAIL'}")
    for failure in failures:
        print(f"  FAILURE: {failure}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
