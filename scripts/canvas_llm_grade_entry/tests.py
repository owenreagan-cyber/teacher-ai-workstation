#!/usr/bin/env python3
"""Deterministic guard tests for the bounded grade-entry capability.

Every test is offline: no network, no credentials, no live Canvas.
Run with:  python3 -m scripts.canvas_llm_grade_entry.cli self-test
"""
from __future__ import annotations

import os
from typing import Any

from scripts.canvas_llm_grade_entry import fake_canvas
from scripts.canvas_llm_grade_entry import grade_entry as ge

TITLE = "ELA4A: Personal Narrative Final Draft"
ASSIGNMENT_ID = 1042769
OTHER_ASSIGNMENT_ID = 1042770


def _request() -> dict[str, Any]:
    return {
        "schema": ge.REQUEST_SCHEMA,
        "course": {"course_id": 28171, "course_code": "15-ELA4"},
        "assignment_title": TITLE,
        "grades": [
            {"student": "Hannah Bradshaw", "grade": 94},
            {"student": "Jasmin Brar", "grade": 89},
            {"student": "Ava Venne", "grade": 97},
        ],
        "skip": ["Nathan Snapp"],
    }


def _enabled() -> None:
    os.environ[ge.ENABLE_ENV] = ge.ENABLE_VALUE
    ge.enable(owner="test-owner")


def _reset() -> None:
    ge.disable()
    os.environ.pop(ge.ENABLE_ENV, None)


# 1. grade writes are blocked without approval -----------------------------
def test_blocked_without_approval() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    try:
        client.write_grade(course_id=28171, assignment_id=ASSIGNMENT_ID, student_id=9001,
                           grade=94, approved=False, approval_packet_hash="x",
                           expected_packet_hash="x")
        raise AssertionError("write must require approval")
    except ge.GradeEntryError as exc:
        assert "missing human approval" in str(exc), exc
    assert canvas.write_log == [], "no write may occur without approval"

    # without the env gate
    _reset()
    try:
        client.write_grade(course_id=28171, assignment_id=ASSIGNMENT_ID, student_id=9001,
                           grade=94, approved=True, approval_packet_hash="x",
                           expected_packet_hash="x")
        raise AssertionError("write must be blocked when disabled")
    except ge.GradeEntryError as exc:
        assert "disabled" in str(exc), exc
    assert canvas.write_log == []

    # env gate present but no explicit human enablement
    os.environ[ge.ENABLE_ENV] = ge.ENABLE_VALUE
    try:
        client.write_grade(course_id=28171, assignment_id=ASSIGNMENT_ID, student_id=9001,
                           grade=94, approved=True, approval_packet_hash="x",
                           expected_packet_hash="x")
        raise AssertionError("write must be blocked before explicit enablement")
    except ge.GradeEntryError as exc:
        assert "not enabled" in str(exc), exc
    _reset()
    print("PASS grade writes are blocked without approval")


# 2. wrong course fails closed --------------------------------------------
def test_wrong_course_fails_closed() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    request = _request()
    request["course"] = {"course_id": 999999}
    try:
        ge.build_packet(request=request, client=client)
        raise AssertionError("non-allowlisted course must fail closed")
    except ge.GradeEntryError as exc:
        assert "not allowlisted" in str(exc), exc

    try:
        client.write_grade(course_id=999999, assignment_id=ASSIGNMENT_ID, student_id=9001,
                           grade=94, approved=True, approval_packet_hash="h",
                           expected_packet_hash="h")
        raise AssertionError("write to another course must fail closed")
    except ge.GradeEntryError as exc:
        assert "not allowlisted" in str(exc), exc
    _reset()
    print("PASS wrong course fails closed")


# 3. wrong assignment fails closed ---------------------------------------
def test_wrong_assignment_fails_closed() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    request = _request()
    request["assignment_title"] = "ELA4A: Personal Narrative FINAL Draft"  # near miss
    try:
        ge.build_packet(request=request, client=client)
        raise AssertionError("fuzzy assignment title must fail closed")
    except ge.GradeEntryError as exc:
        assert "exactly 1 assignment" in str(exc), exc

    request["assignment_title"] = "ELA4A: Personal Narrative"
    try:
        ge.build_packet(request=request, client=client)
        raise AssertionError("partial assignment title must fail closed")
    except ge.GradeEntryError:
        pass
    _reset()
    print("PASS wrong assignment fails closed")


# 4. ambiguous student fails closed --------------------------------------
def test_ambiguous_student_fails_closed() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    canvas.roster.append({"student_id": 9005, "name": "Hannah Bradshaw"})  # duplicate label
    client = canvas.client()
    try:
        ge.build_packet(request=_request(), client=client)
        raise AssertionError("duplicate student match must fail closed")
    except ge.GradeEntryError as exc:
        assert "ambiguous" in str(exc), exc

    try:
        ge.build_packet(
            request={"course": {"course_id": 28171}, "assignment_title": TITLE,
                     "grades": [{"student": "Nobody Here", "grade": 90}]},
            client=client,
        )
        raise AssertionError("unknown student must fail closed")
    except ge.GradeEntryError as exc:
        assert "no roster match" in str(exc), exc
    _reset()
    print("PASS ambiguous student fails closed")


# 5. skipped student remains untouched ----------------------------------
def test_skipped_student_untouched() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    packet = ge.build_packet(request=_request(), client=client)
    before = canvas.snapshot()

    # the skipped student must never appear in proposed changes or writes
    ids = {row["student_id"] for row in packet.proposed_changes}
    assert 9004 not in ids, "Nathan Snapp must not be in the write set"
    assert any(row["student_id"] == 9004 for row in packet.skipped), "skip must be recorded"

    ge.apply_packet(packet=packet, client=client, approved=True, approved_by="test-owner")
    after = canvas.snapshot()
    assert after[(9004, ASSIGNMENT_ID)] is None, "skipped student's cell must stay blank"
    assert before[(9004, ASSIGNMENT_ID)] == after[(9004, ASSIGNMENT_ID)]
    assert all(w["user_id"] != 9004 for w in canvas.write_log), "no write may target the skipped student"
    _reset()
    print("PASS skipped student remains untouched")


# 6. unapproved student cannot be written -------------------------------
def test_unapproved_student_cannot_be_written() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    packet = ge.build_packet(request=_request(), client=client)
    before = canvas.snapshot()

    # attempt out-of-scope write (student present on roster but not in the packet)
    try:
        client.write_grade(course_id=28171, assignment_id=ASSIGNMENT_ID, student_id=9004,
                           grade=100, approved=True,
                           approval_packet_hash=packet.packet_hash,
                           expected_packet_hash=packet.packet_hash)
    except ge.GradeEntryError:
        pass
    assert canvas.grade_of(9004, ASSIGNMENT_ID) is None, "unapproved student must stay blank"

    # hash mismatch blocks the write entirely
    try:
        client.write_grade(course_id=28171, assignment_id=ASSIGNMENT_ID, student_id=9001,
                           grade=94, approved=True, approval_packet_hash="tampered",
                           expected_packet_hash=packet.packet_hash)
        raise AssertionError("hash mismatch must fail closed")
    except ge.GradeEntryError as exc:
        assert "hash mismatch" in str(exc), exc

    after = canvas.snapshot()
    assert before[(9001, ASSIGNMENT_ID)] == after[(9001, ASSIGNMENT_ID)], "no write on mismatch"

    # tampered packet is rejected before any write
    tampered = ge.ApprovalPacket(**packet.to_dict())
    tampered.total_writes = 999
    tampered.packet_hash = packet.packet_hash
    try:
        ge.apply_packet(packet=tampered, client=client, approved=True, approved_by="test-owner")
        raise AssertionError("tampered packet must fail closed")
    except ge.GradeEntryError as exc:
        assert "hash mismatch" in str(exc), exc
    _reset()
    print("PASS unapproved student cannot be written")


# 7. no other assignments are modified ----------------------------------
def test_no_other_assignments_modified() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    packet = ge.build_packet(request=_request(), client=client)
    before = canvas.snapshot()
    report = ge.apply_packet(packet=packet, client=client, approved=True, approved_by="test-owner")
    after = canvas.snapshot()

    touched_assignments = {w["assignment_id"] for w in canvas.write_log}
    assert touched_assignments <= {ASSIGNMENT_ID}, touched_assignments
    assert OTHER_ASSIGNMENT_ID not in touched_assignments
    assert before[(9001, OTHER_ASSIGNMENT_ID)] == after[(9001, OTHER_ASSIGNMENT_ID)]
    assert before[(9003, OTHER_ASSIGNMENT_ID)] == after[(9003, OTHER_ASSIGNMENT_ID)]
    assert report["other_assignments_touched"] == 0
    assert report["other_courses_touched"] == 0
    print("PASS no other assignments are modified")
    _reset()


# 8. readback mismatch fails verification -------------------------------
def test_readback_mismatch_fails_verification() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    packet = ge.build_packet(request=_request(), client=client)

    # simulate Canvas not persisting the requested grade
    original_transport = canvas.transport

    def lying_transport(method: str, path: str, data: dict[str, Any] | None):
        if method.upper() == "PUT":
            parts = path.rstrip("/").split("/")
            student_id, assignment_id = int(parts[8]), int(parts[6])
            previous = canvas.grades.get((student_id, assignment_id))
            result = original_transport(method, path, data)
            canvas.grades[(student_id, assignment_id)] = previous  # Canvas did not persist
            return {**result, "score": 12.0}
        return original_transport(method, path, data)

    client._injected = lying_transport
    report = ge.apply_packet(packet=packet, client=client, approved=True, approved_by="test-owner")
    assert report["readback_verified"] is False, "readback mismatch must fail verification"
    assert report["readback_mismatches"], "mismatch must be reported"
    _reset()
    print("PASS readback mismatch fails verification")


# 9. write payload is bounded -------------------------------------------
def test_write_payload_is_bounded() -> None:
    for forbidden in ("comment", "excuse", "late", "missing", "rubric_assessment"):
        try:
            ge.assert_write_payload_is_bounded({"submission[posted_grade]": "94",
                                                f"submission[{forbidden}]": "true"})
            raise AssertionError(f"payload must reject submission[{forbidden}]")
        except ge.GradeEntryError as exc:
            assert "may not set" in str(exc) or "unexpected write field" in str(exc), exc
    ge.assert_write_payload_is_bounded({"submission[posted_grade]": "94"})
    assert "comment" in ge.FORBIDDEN_SUBMISSION_FIELDS
    print("PASS write payload is bounded to posted_grade")


# 10. exact grade entry, no rounding/conversion ---------------------------
def test_exact_grades_and_already_correct() -> None:
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    packet = ge.build_packet(request=_request(), client=client)
    report = ge.apply_packet(packet=packet, client=client, approved=True, approved_by="test-owner")
    assert canvas.grade_of(9001, ASSIGNMENT_ID) == 94.0
    assert canvas.grade_of(9002, ASSIGNMENT_ID) == 89.0
    assert canvas.grade_of(9003, ASSIGNMENT_ID) == 97.0
    actions = {r["student_name"]: r["action"] for r in report["results"]}
    assert actions["Jasmin Brar"] == "ALREADY_CORRECT", actions
    assert actions["Hannah Bradshaw"] == "WRITTEN"
    assert report["writes_performed"] == 2
    assert report["already_correct"] == 1
    assert all(r["verified"] for r in report["results"])

    # parseInt rejects non-numeric and non-explicit values
    for bad in ("A", "94%", "ninety-four", "", "9 4"):
        try:
            ge.parse_grade(bad)
            raise AssertionError(f"parse_grade must reject {bad!r}")
        except ge.GradeEntryError:
            pass
    assert ge.parse_grade(94) == 94.0
    assert ge.parse_grade("89") == 89.0
    assert ge.parse_grade(94.5) == 94.5
    _reset()
    print("PASS exact grades entered and already-correct grades reported")


def test_injected_transport_cannot_truncate_readback() -> None:
    """A transport-injected readback must refuse to silently collapse to one page."""
    _enabled()
    canvas = fake_canvas.ela4_course()
    client = canvas.client()
    big = [{"student_id": 8000 + i, "assignment_id": ASSIGNMENT_ID, "score": 50.0} for i in range(150)]
    canvas.grades.update({(row["student_id"], ASSIGNMENT_ID): 50.0 for row in big})
    for row in big:
        canvas.roster.append({"student_id": row["student_id"], "name": f"Student {row['student_id']}"})
    original = canvas.transport

    def injected(method: str, path: str, data: Any):
        result = original(method, path, data)
        if isinstance(result, list) and len(result) > 100:
            return result[:100]  # emulate a single-page injected response
        return result

    client._injected = injected
    try:
        client.list_submissions(28171)
        raise AssertionError("a full injected page must not be accepted silently")
    except ge.GradeEntryError as exc:
        assert "pagination" in str(exc), exc
    _reset()
    print("PASS injected transport cannot silently truncate readback")


def run_all() -> None:
    tests = (
        test_blocked_without_approval,
        test_wrong_course_fails_closed,
        test_wrong_assignment_fails_closed,
        test_ambiguous_student_fails_closed,
        test_skipped_student_untouched,
        test_unapproved_student_cannot_be_written,
        test_no_other_assignments_modified,
        test_readback_mismatch_fails_verification,
        test_write_payload_is_bounded,
        test_exact_grades_and_already_correct,
        test_injected_transport_cannot_truncate_readback,
    )
    for test in tests:
        test()
    print(f"PASS grade-entry guard tests complete ({len(tests)} tests)")


if __name__ == "__main__":
    run_all()
