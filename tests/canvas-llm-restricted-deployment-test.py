#!/usr/bin/env python3
"""Restricted Q2W6 release safety tests.

Deterministic, local-only. Every Canvas interaction uses ``FakeDeployClient``;
no network request and no real Canvas write is performed.

Covers:
* missing / malformed / stale / mismatched reconciliation fails closed;
* duplicate and semantic matches never silently become CREATE;
* scoped preflight and full-week readiness stay distinct;
* the explicit scope rejects out-of-scope subjects and artifact types;
* preserved assignments and a protected (untouched) assignment are read back;
* production confirmation, preflight expiry, and stale-source gates stay intact;
* the local Q2W6 packet (when staged) keeps its verified Friday baseline.
"""
from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import coordinator, ledger, plan as plan_mod  # noqa: E402
from scripts.canvas_llm_deploy import preflight as preflight_mod  # noqa: E402
from scripts.canvas_llm_deploy import restricted_release  # noqa: E402
from scripts.canvas_llm_deploy import scope as scope_mod  # noqa: E402
from scripts.canvas_llm_deploy.client import FakeDeployClient  # noqa: E402
from scripts.canvas_llm_intake import approval as ap  # noqa: E402
from scripts.canvas_llm_intake import assignment_reconciliation as ar  # noqa: E402
from scripts.canvas_llm_intake import manifest as imf  # noqa: E402
from scripts.canvas_llm_intake import questions as qs  # noqa: E402
from scripts.canvas_planner.approval_bundle import current_bundle  # noqa: E402
from scripts.canvas_llm_storage import isolated_storage  # noqa: E402

MATH = 26404
READING = 26442
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
SUBJECTS = ["math", "reading_spelling", "language_arts", "science"]

PROPOSALS = [
    {
        "course": "math", "course_id": MATH, "title": "SM5: Lesson 49 Homework",
        "assignment_group": "Homework/Class Work", "due_date": "2026-11-16",
        "points_possible": 100, "grading_type": "percent",
        "submission_types": "on_paper", "omit_from_final_grade": False,
    },
    {
        "course": "math", "course_id": MATH, "title": "SM5: Written Assessment 9",
        "assignment_group": "Written Assessments", "due_date": "2026-11-19",
        "points_possible": 100, "grading_type": "percent",
        "submission_types": "on_paper", "omit_from_final_grade": False,
    },
]

CREATE_LIVE = None
MATCH_LIVE = {
    "assignment_id": 1062904, "course_id": MATH,
    "title": "SM5: Written Assessment 9", "assignment_group": "Written Assessments",
    "assignment_group_id": 60319, "due_at": "2026-11-20T04:59:00Z",
    "points_possible": 100.0, "grading_type": "percent",
    "submission_types": ["on_paper"], "omit_from_final_grade": False, "published": True,
}


def _base_report(results=None, *, source_hash="src-1", checked_at=None):
    results = results or [
        {"course": "math", "course_id": MATH, "title": PROPOSALS[0]["title"],
         "classification": "CREATE_REQUIRED", "live": CREATE_LIVE},
        {"course": "math", "course_id": MATH, "title": PROPOSALS[1]["title"],
         "classification": "MATCH", "live": MATCH_LIVE},
    ]
    counts = {name: 0 for name in ar.CLASSIFICATIONS}
    for item in results:
        counts[item["classification"]] += 1
    return {
        "schemaVersion": ar.REPORT_SCHEMA_VERSION,
        "quarter": 2, "week": 6, "week_code": "Q2W6",
        "source_hash": source_hash,
        "checked_at": (checked_at or NOW).isoformat(),
        "proposal_count": len(PROPOSALS),
        "proposal_digest": ar.proposal_digest(PROPOSALS),
        "results": results,
        "counts": counts,
        "blockers": [],
        "pending_actions": [],
        "bundle_status": "READY_FOR_APPROVAL",
        "execution_ready": False,
        "canvas_writes": 0,
    }


def _stage(report=None, *, write_report=True):
    """Create a minimal Q2W6 staging packet in the active isolated storage."""
    d = imf.staging_dir(2, 6)
    (d / "drafts").mkdir(parents=True, exist_ok=True)
    m = imf.new_manifest(
        quarter=2, week=6, week_code="Q2W6",
        date_range={"start": "2026-11-16", "end": "2026-11-20"},
    )
    m["source_hash"] = "src-1"
    m["status"] = "READY_FOR_REVIEW"
    m["ready_to_publish"] = False
    m["publish_blockers"] = [
        "math:announcement not approved", "language_arts:page not approved",
    ]
    imf.save_manifest(2, 6, m)
    (d / "drafts" / "assignments.json").write_text(
        json.dumps(PROPOSALS), encoding="utf-8"
    )
    (d / "drafts" / "math-page.html").write_text(
        "<div id='kl_wrapper_3'>agenda</div><p>Reminders</p><p>Mr. Reagan</p>",
        encoding="utf-8",
    )
    if write_report:
        ar.write_report(report or _base_report(), quarter=2, week=6)


def _approve_math(*, now=NOW):
    """Two-step approval: actions first, then bind to the stable fingerprint."""
    bundle = current_bundle(2, 6, "math")
    for g in ("page", "assignments"):
        ap.set_state(
            2, 6, "math", g, "APPROVED",
            draft_hash=bundle["hashes"][g], source_hash="src-1", subjects=SUBJECTS,
        )
    plan = plan_mod.build_plan(2, 6, now=now)
    fingerprint = plan["plan_fingerprint"]
    for g in ("page", "assignments"):
        ap.set_state(
            2, 6, "math", g, "APPROVED",
            draft_hash=bundle["hashes"][g], source_hash="src-1", subjects=SUBJECTS,
            plan_fingerprint=fingerprint,
        )
    return plan_mod.build_plan(2, 6, now=now)


def _scope(plan, *, protected=None, artifacts=None, now=NOW):
    return scope_mod.authorize_scope(
        2, 6, plan=plan, subjects=["math"],
        artifacts=artifacts or ["page", "assignments"],
        confirmation="SCOPE Q2W6", reason="test fixture", now=now,
        protected_assignments=protected or [],
    )


def _client(plan):
    client = FakeDeployClient(
        courses={MATH: {"id": MATH, "name": "Math", "workflow_state": "available"}},
        now=lambda: NOW,
    )
    client.assignment_groups[MATH] = [
        {"id": 60321, "name": "Homework/Class Work"},
        {"id": 60319, "name": "Written Assessments"},
    ]
    client.seed_page(MATH, plan["slug"], title="Q2W6",
                     body="<div id='kl_wrapper_3'>old</div><p>Reminders</p>")
    seeded = client.seed_assignment(
        MATH, "SM5: Written Assessment 9", assignment_group="Written Assessments",
    )
    client.assignments.pop(seeded["id"])
    seeded.update({"id": "1062904", "due_at": "2026-11-20T04:59:00Z", "published": True})
    client.assignments["1062904"] = seeded
    protected = client.seed_assignment(
        MATH, "Protected Lesson", assignment_group="Homework/Class Work",
    )
    client.assignments.pop(protected["id"])
    protected.update({"id": "999"})
    client.assignments["999"] = protected
    return client


def _assert_no_create(plan):
    assert plan["counts"]["assignments_create"] == 0, plan["counts"]
    assert plan["counts"]["assignments_blocked"] == len(PROPOSALS), plan["counts"]
    assert all(a["action"] == "BLOCKED" for a in plan["assignments"]), plan["assignments"]
    assert plan["assignment_reconciliation"]["status"] != "VALID"


def test_reconciliation_fail_closed():
    with isolated_storage():
        # Missing report.
        _stage(write_report=False)
        _approve_math()
        plan = plan_mod.build_plan(2, 6, now=NOW)
        _assert_no_create(plan)
        assert any("missing" in e for e in plan["assignment_reconciliation"]["errors"])

        # Malformed JSON.
        _stage()
        (imf.staging_dir(2, 6) / "planner" / "assignment-reconciliation.json").write_text("{")
        _assert_no_create(plan_mod.build_plan(2, 6, now=NOW))

        # Stale report.
        _stage(_base_report(checked_at=NOW - timedelta(hours=ar.MAX_REPORT_AGE_HOURS + 1)))
        stale = plan_mod.build_plan(2, 6, now=NOW)
        _assert_no_create(stale)
        assert any("stale" in e for e in stale["assignment_reconciliation"]["errors"])

        # Mismatched proposal digest (draft changed after reconciliation).
        report = _base_report()
        report["proposal_digest"] = "0" * 64
        _stage(report)
        digested = plan_mod.build_plan(2, 6, now=NOW)
        _assert_no_create(digested)
        assert any("proposal_digest" in e for e in digested["assignment_reconciliation"]["errors"])

        # Wrong week.
        report = _base_report()
        report["week_code"] = "Q2W5"
        _stage(report)
        _assert_no_create(plan_mod.build_plan(2, 6, now=NOW))

        # Scope authorization cannot be minted while reconciliation is missing.
        _stage(write_report=False)
        blocked_plan = plan_mod.build_plan(2, 6, now=NOW)
        try:
            _scope(blocked_plan)
            raise AssertionError("expected ScopeError")
        except scope_mod.ScopeError:
            pass
    print("PASS reconciliation failures fail closed (no CREATE fallback)")


def test_duplicate_and_semantic_never_create():
    with isolated_storage():
        for classification in ("DUPLICATE", "SEMANTIC_MATCH_REVIEW", "UNVERIFIED"):
            results = [
                {"course": "math", "course_id": MATH, "title": PROPOSALS[0]["title"],
                 "classification": classification, "live": [MATCH_LIVE]},
                {"course": "math", "course_id": MATH, "title": PROPOSALS[1]["title"],
                 "classification": "MATCH", "live": MATCH_LIVE},
            ]
            _stage(_base_report(results))
            _approve_math()
            plan = plan_mod.build_plan(2, 6, now=NOW)
            assert plan["counts"]["assignments_create"] == 0, (classification, plan["counts"])
            first = next(a for a in plan["assignments"] if a["title"] == PROPOSALS[0]["title"])
            assert first["action"] == "BLOCKED", first
            assert plan["reconciliation_blockers"], plan["reconciliation_blockers"]
    print("PASS duplicate/semantic/unverified matches never become CREATE")


def test_valid_plan_and_approval_hashes():
    with isolated_storage():
        _stage()
        plan = _approve_math()
        assert plan["counts"] == {
            "pages_update": 1, "assignments_create": 1, "assignments_skip": 1,
            "assignments_update": 0, "assignments_blocked": 0,
            "announcements_create": 0, "announcements_update": 0, "deletes": 0,
        }, plan["counts"]
        assert plan["assignment_reconciliation"]["status"] == "VALID"
        assert all(a["approved"] is True for a in plan["assignments"]), plan["assignments"]
        assert plan["pages"][0]["approved"] is True
        assert plan["weekly_announcements"] == [] and plan["assessment_reminders"] == []
    print("PASS valid reconciliation produces CREATE/SKIP with hash-bound approvals")


def test_scope_rejects_out_of_scope_and_global_stays_false():
    with isolated_storage():
        _stage()
        plan = _approve_math()
        record = _scope(plan)
        assert record["excluded_subjects"] == [
            "language_arts", "reading_spelling", "science",
        ]
        assert plan["ready_to_publish"] is False
        assert record["global_ready_to_publish"] is False

        loaded, errors = scope_mod.load_scope(2, 6)
        assert not errors, errors
        assert scope_mod.validate_scope(loaded, plan, quarter=2, week=6, now=NOW) == []

        # A page for a protected subject is rejected.
        bad = copy.deepcopy(plan)
        bad["pages"].append({"subject": "language_arts", "action": "UPDATE",
                             "approved": True, "title": "x"})
        assert any("outside scope" in e for e in
                   scope_mod.validate_scope(loaded, bad, quarter=2, week=6, now=NOW))

        # An announcement is rejected in a restricted release.
        bad = copy.deepcopy(plan)
        bad["weekly_announcements"] = [{"title": "Math Canvas Weekly Update"}]
        assert any("announcements" in e for e in
                   scope_mod.validate_scope(loaded, bad, quarter=2, week=6, now=NOW))

        # An assessment reminder is rejected.
        bad = copy.deepcopy(plan)
        bad["assessment_reminders"] = [{"title": "Math reminder"}]
        assert any("reminders" in e for e in
                   scope_mod.validate_scope(loaded, bad, quarter=2, week=6, now=NOW))

        # Automatic update of an existing assignment is rejected.
        bad = copy.deepcopy(plan)
        bad["assignments"][0]["action"] = "UPDATE"
        assert any("not CREATE/SKIP" in e for e in
                   scope_mod.validate_scope(loaded, bad, quarter=2, week=6, now=NOW))

        # Stale fingerprint / expiry are rejected.
        bad = copy.deepcopy(plan); bad["plan_fingerprint"] = "other"
        assert any("fingerprint" in e for e in
                   scope_mod.validate_scope(loaded, bad, quarter=2, week=6, now=NOW))
        assert any("expired" in e for e in scope_mod.validate_scope(
            loaded, plan, quarter=2, week=6, now=NOW + timedelta(days=30),
        ))
    print("PASS scope rejects out-of-scope subjects/artifacts; global readiness stays false")


def test_scoped_preflight_and_coordinator_refusal():
    with isolated_storage():
        _stage()
        plan = _approve_math()
        _scope(plan, protected=[{
            "course_id": MATH, "assignment_id": "999", "title": "Protected Lesson",
        }])
        client = _client(plan)
        record = preflight_mod.run_preflight(2, 6, client, scoped=True, now=NOW)
        assert record["ready"] is True, record["blockers"]
        assert record["scope_only"] is True
        assert record["global_ready_to_publish"] is False
        assert record["exclusion_evidence"]["language_arts"]["touched"] is False
        assert record["exclusion_evidence"]["science"]["touched"] is False
        assert record["live"]["protected_assignments"][0]["snapshot"]["title"] == "Protected Lesson"

        manifest = imf.load_manifest(2, 6)
        manifest["plan_fingerprint"] = plan["plan_fingerprint"]
        imf.save_manifest(2, 6, manifest)

        # D-028: the deploy coordinator may review a scoped preflight but must
        # never execute it. The rollover engine is the only publisher.
        try:
            coordinator.deploy(
                2, 6, preflight_id=record["preflight_id"],
                expected_source_hash=plan["source_hash"],
                expected_approval_snapshot_hash=plan["approval_snapshot_hash"],
                owner_confirmation="DEPLOY Q2W6", client=client, now=NOW,
            )
            raise AssertionError("expected D-028 scope refusal")
        except coordinator.DeploymentBlocked as exc:
            assert "rollover" in str(exc).lower(), exc
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0
        assert imf.load_manifest(2, 6)["status"] == "READY_FOR_REVIEW"
    print("PASS scoped preflight is auditable and the coordinator refuses to publish it")


def test_production_gates_still_enforced():
    with isolated_storage():
        _stage()
        plan = _approve_math()
        _scope(plan)
        client = _client(plan)
        record = preflight_mod.run_preflight(2, 6, client, scoped=True, now=NOW)
        manifest = imf.load_manifest(2, 6)
        manifest["plan_fingerprint"] = plan["plan_fingerprint"]
        imf.save_manifest(2, 6, manifest)

        # The exact confirmation phrase is required.
        assert coordinator._confirm_ok("DEPLOY Q2W6", "Q2W6", deletes=0) is True
        assert coordinator._confirm_ok("DEPLOY Q2W5", "Q2W6", deletes=0) is False
        assert coordinator._confirm_ok("DEPLOY", "Q2W6", deletes=0) is False

        # Expired preflight is refused before any Canvas write.
        try:
            coordinator.deploy(
                2, 6, preflight_id=record["preflight_id"],
                expected_source_hash=plan["source_hash"],
                expected_approval_snapshot_hash=plan["approval_snapshot_hash"],
                owner_confirmation="DEPLOY Q2W6", client=client,
                now=NOW + timedelta(days=1),
            )
            raise AssertionError("expected expiry block")
        except coordinator.DeploymentBlocked:
            pass
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0

        # A BLOCKED assignment plan is refused before any write.
        blocked = copy.deepcopy(plan)
        blocked["assignments"][0]["action"] = "BLOCKED"
        assert coordinator._plan_prewrite_blockers(blocked, now=NOW)
        # An UPDATE action is refused too (never silently rewrite student work).
        updated = copy.deepcopy(plan)
        updated["assignments"][0]["action"] = "UPDATE"
        assert any("automatic update" in b
                   for b in coordinator._plan_prewrite_blockers(updated, now=NOW))
        # Duplicate ambiguity is refused.
        ambiguous = copy.deepcopy(plan)
        ambiguous["assignments"][0]["duplicate_classification"] = "AMBIGUOUS"
        assert any("duplicate identity" in b
                   for b in coordinator._plan_prewrite_blockers(ambiguous, now=NOW))
    print("PASS production confirmation, expiry, and action gates enforced")


def test_restricted_release_uses_canonical_rollover():
    """D-028: the restricted release must run through the rollover publisher."""
    with isolated_storage():
        now = datetime.now(timezone.utc)
        _stage(_base_report(checked_at=now))
        plan = _approve_math(now=now)
        _scope(plan, now=now, protected=[{
            "course_id": MATH, "assignment_id": "999", "title": "Protected Lesson",
        }])
        client = _client(plan)
        record = preflight_mod.run_preflight(2, 6, client, scoped=True, now=now)
        assert record["ready"] is True, record["blockers"]

        # Wrong phrase is refused before any Canvas call.
        try:
            restricted_release.release(
                2, 6, preflight_id=record["preflight_id"],
                confirmation="ROLLOVER Q2W5", now=now,
                read_client=client, client=client,
            )
            raise AssertionError("expected confirmation refusal")
        except restricted_release.RestrictedReleaseBlocked:
            pass

        report = restricted_release.release(
            2, 6, preflight_id=record["preflight_id"],
            confirmation="ROLLOVER Q2W6", now=now,
            read_client=client, client=client,
        )
        assert report["lifecycle"] == "EARLY_CONTENT_PUBLISHED_VERIFIED", report.get("failures")
        assert report["failures"] == []
        assert report["verb_totals"]["PUT"] == 1, report["verb_totals"]
        assert report["verb_totals"]["POST"] == 1, report["verb_totals"]
        assert report["verb_totals"]["DELETE"] == 0
        assert report["weekly_announcements"] == []
        assert report["assessment_reminders"] == []
        dispositions = {a["title"]: a["disposition"] for a in report["assignments"]}
        assert dispositions["SM5: Lesson 49 Homework"] == "PUBLISHED_VERIFIED"
        assert dispositions["SM5: Written Assessment 9"] == "ALREADY_EXISTS"
        assert report["preserved_assignments"][0]["verified"] is True
        assert report["protected_assignments"][0]["verified"] is True
        # Local before-state backups exist for every touched/preserved object.
        backups = ledger.deploy_dir(2, 6) / "backups"
        assert any(backups.glob("math-page-before.json"))
        assert any(backups.glob("assignment-sm5-written-assessment-9-before.json"))
        assert any(backups.glob("protected-assignment-999-before.json"))
        # The rollover ledger must not claim full-week publication.
        from scripts.canvas_llm_rollover import ledger as rollover_ledger
        stored = rollover_ledger.load_rollover_ledger(2, 6)
        assert stored["lifecycle"] == "EARLY_CONTENT_PUBLISHED_VERIFIED"
        assert imf.load_manifest(2, 6)["status"] == "READY_FOR_REVIEW"
    print("PASS restricted release runs through the canonical rollover publisher")


def test_local_q2w6_packet_if_staged():
    """Verify the actual staged Q2W6 baseline when it is present locally."""
    staging = imf.staging_dir(2, 6)
    if not (staging / "drafts" / "assignments.json").exists():
        print("SKIP local Q2W6 packet is not staged in this checkout")
        return
    data = qs.load_questions(2, 6)
    assert len(data) == 9, len(data)
    assert qs.unresolved_questions(data) == []
    assert all(q.get("status") == "ANSWERED" for q in data)
    assignments = json.loads((staging / "drafts" / "assignments.json").read_text())
    assert len(assignments) == 8, len(assignments)
    titles = [a["title"] for a in assignments]
    assert titles.count("SM5: Lesson 49 Homework") == 1
    assert titles.count("SM5: Lesson 50 Classwork") == 1
    assert "RM4: Thursday Comprehension Questions — Lesson 61" in titles
    assert "RM4: Tuesday Comprehension Questions — Lesson 60" not in titles
    assert len([t for t in titles if "Spelling" in t and "Craft" in t]) == 0

    math = (staging / "drafts" / "math-page.html").read_text()
    reading = (staging / "drafts" / "reading-page.html").read_text()
    for body, label in ((math, "Math Thanksgiving Activity"),
                        (reading, "Thanksgiving READING and Craft")):
        friday = body[body.index('id="kl_custom_block_1"'):]
        assert label in friday
        assert 'width: 100%' in friday
        assert "At Home" not in friday
        assert "Spelling: Craft" not in friday
        assert "Craft</li>" not in friday.replace("Thanksgiving READING and Craft", "")


def main() -> int:
    test_reconciliation_fail_closed()
    test_duplicate_and_semantic_never_create()
    test_valid_plan_and_approval_hashes()
    test_scope_rejects_out_of_scope_and_global_stays_false()
    test_scoped_preflight_and_coordinator_refusal()
    test_production_gates_still_enforced()
    test_restricted_release_uses_canonical_rollover()
    test_local_q2w6_packet_if_staged()
    print("PASS restricted Canvas deployment safety tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
