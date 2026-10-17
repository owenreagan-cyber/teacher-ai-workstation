#!/usr/bin/env bash
# Guarded Canvas deployment tests (synthetic fixtures + in-memory fake client).
# ZERO real Canvas writes. Production write path is exercised only via the
# in-memory FakeDeployClient, so Canvas POST/PUT/PATCH/DELETE = 0.
set -euo pipefail

echo "Running Canvas guarded deployment tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULES=(
  "scripts/canvas_llm_deploy/__init__.py"
  "scripts/canvas_llm_deploy/plan.py"
  "scripts/canvas_llm_deploy/client.py"
  "scripts/canvas_llm_deploy/ledger.py"
  "scripts/canvas_llm_deploy/preflight.py"
  "scripts/canvas_llm_deploy/coordinator.py"
  "scripts/canvas_llm_deploy/cli.py"
  "scripts/canvas_llm_intake/canvas_readonly.py"
)
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "${MODULES[@]}"
echo "PASS deploy modules compile"

# Module self-tests (pure, no network).
python3 -m scripts.canvas_llm_deploy.plan self-test
python3 -m scripts.canvas_llm_deploy.client self-test
python3 -m scripts.canvas_llm_deploy.ledger self-test
python3 -m scripts.canvas_llm_deploy.preflight self-test
python3 -m scripts.canvas_llm_deploy.coordinator self-test
python3 -m scripts.canvas_llm_deploy.cli self-test
echo "PASS deploy module self-tests"

python3 - <<'PY'
import json
import sys
import tempfile
from pathlib import Path

root = Path('.').resolve()
sys.path.insert(0, str(root))

from scripts.canvas_llm_deploy import coordinator
from scripts.canvas_llm_deploy import ledger
from scripts.canvas_llm_deploy import plan as planmod
from scripts.canvas_llm_deploy import preflight as preflightmod
from scripts.canvas_llm_deploy.client import FakeDeployClient, DeployClientError
from scripts.canvas_llm_intake import manifest as imf

PAGE_BODY = "<div id='kl_wrapper_3'>agenda</div><p>Reminders</p><p>Mr. Reagan</p>"
SLUG = "q2w9-test"

def synthetic_plan(**overrides):
    plan = {
        "quarter": 2, "week": 9, "week_code": "Q2W9", "slug": SLUG,
        "date_range": {"start": "2026-12-07", "end": "2026-12-11"},
        "status": "READY_TO_PUBLISH", "ready_to_publish": True,
        "publish_blockers": [],
        "source_hash": "src-hash-1", "approval_snapshot_hash": "appr-hash-1",
        "pages": [{"subject": "math", "course_id": 26404, "slug": SLUG, "title": "Q2W9",
                   "action": "UPDATE", "live_page_id": "page-26404-q2w9-test"}],
        "assignments": [
            {"course": "math", "course_id": 26404, "title": "SM5: Lesson 50 Homework",
             "assignment_group": "Homework/Class Work", "due_date": "2026-12-07",
             "due_utc": "2026-12-08T03:59:00Z", "points_possible": 100, "grading_type": "percent",
             "submission_types": ["on_paper"], "omit_from_final_grade": False,
             "action": "CREATE", "duplicate_classification": "NEW"},
        ],
        "weekly_announcements": [
            {"course": "Math", "course_id": 26404, "subject": "math", "title": "Math Canvas Weekly Update",
             "message": "<p>Good afternoon,</p><div id='kl_wrapper_3'>agenda</div><p>Reminders</p><p>Mr. Reagan</p>",
             "scheduled": True, "delayed_post_at": "2026-12-04T21:00:00Z",
             "action": "CREATE", "duplicate_classification": "NEW"},
        ],
        "assessment_reminders": [],
        "deletes": [],
        "untouched": {},
        "counts": {"pages_update": 1, "assignments_create": 1, "announcements_create": 1,
                   "assignments_update": 0, "announcements_update": 0, "deletes": 0},
    }
    plan.update(overrides)
    return plan

def make_client():
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
    client.assignment_groups[26404] = [
        {"id": "60321", "name": "Homework/Class Work"},
        {"id": "60319", "name": "Written Assessments"},
        {"id": "60320", "name": "Fact Assessments"},
    ]
    client.seed_page(26404, SLUG, title="Q2W9", body="<div id='kl_wrapper_3'>old</div><p>Reminders</p>")
    return client

def write_preflight(ledger_root, *, expires_past=False, source="src-hash-1", approval="appr-hash-1",
                    ready=True, plan=None):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    exp = (now - timedelta(minutes=1) if expires_past else now + timedelta(minutes=15)).isoformat()
    rec = {
        "preflight_id": "pf-test", "created_at": now.isoformat(), "expires_at": exp,
        "quarter": 2, "week": 9, "week_code": "Q2W9",
        "source_hash": source, "approval_snapshot_hash": approval,
        "plan": plan or synthetic_plan(), "live": {}, "warnings": [], "blockers": [],
        "ready": ready, "canvas_writes": 0,
    }
    ledger.write_preflight(2, 9, rec)
    return rec


def reset_state():
    """Reset ledger + manifest to a fresh READY_TO_PUBLISH week."""
    for name in ("deployment-ledger.json", "published-verified-ledger.json"):
        p = ledger.deploy_dir(2, 9) / name
        if p.exists():
            p.unlink()
    m = imf.new_manifest(quarter=2, week=9, week_code="Q2W9",
                         date_range={"start": "2026-12-07", "end": "2026-12-11"})
    m["status"] = "READY_TO_PUBLISH"
    m["source_hash"] = "src-hash-1"
    imf.save_manifest(2, 9, m)

# ---- Harness with temp ledger + staging roots ----------------------------
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    orig_deploy = ledger.DEPLOY_ROOT
    orig_staging = imf.staging_dir
    orig_build = planmod.build_plan
    orig_load = planmod.load_packet
    ledger.DEPLOY_ROOT = tmp / "deployments"
    imf.staging_dir = lambda q, w: tmp / "intake" / f"q{q}w{w}"
    try:
        planmod.build_plan = lambda q, w: synthetic_plan()
        planmod.load_packet = lambda q, w: {"page_bodies": {"math": PAGE_BODY}}

        # ---- 1. Happy path: preflight-ready plan deploys + verifies -------
        reset_state()
        client = make_client()
        write_preflight(tmp)
        rep = coordinator.deploy(2, 9, preflight_id="pf-test",
                                 expected_source_hash="src-hash-1",
                                 expected_approval_snapshot_hash="appr-hash-1",
                                 owner_confirmation="DEPLOY Q2W9", client=client)
        assert rep["deployment_state"] == "PUBLISHED_VERIFIED", rep["failures"]
        assert rep["verb_totals"]["PUT"] == 1 and rep["verb_totals"]["POST"] == 2, rep["verb_totals"]
        assert client._write_counts["PUT"] == 1 and client._write_counts["POST"] == 2, client._write_counts
        assert client._write_counts["DELETE"] == 0 and client._write_counts["PATCH"] == 0
        # every artifact has an explicit final disposition.
        assert rep["pages"][0]["verified"] is True
        assert rep["assignments"][0]["disposition"] == "PUBLISHED_VERIFIED"
        assert rep["weekly_announcements"][0]["disposition"] == "PUBLISHED_VERIFIED"
        # manifest advanced to PUBLISHED_VERIFIED.
        assert imf.load_manifest(2, 9)["status"] == "PUBLISHED_VERIFIED"
        print("PASS happy-path deploy -> PUBLISHED_VERIFIED + explicit dispositions")

        # ---- 2. Re-deploy after PUBLISHED_VERIFIED is blocked -------------
        try:
            coordinator.deploy(2, 9, preflight_id="pf-test",
                               expected_source_hash="src-hash-1",
                               expected_approval_snapshot_hash="appr-hash-1",
                               owner_confirmation="DEPLOY Q2W9", client=client)
            raise AssertionError("expected re-deploy block")
        except coordinator.DeploymentBlocked:
            pass
        print("PASS re-deploy blocked after PUBLISHED_VERIFIED")

        # ---- 3. Stale source blocks deploy -------------------------------
        reset_state()
        client2 = make_client()
        write_preflight(tmp, source="src-hash-1")
        planmod.build_plan = lambda q, w: synthetic_plan(source_hash="src-hash-2")
        try:
            coordinator.deploy(2, 9, preflight_id="pf-test",
                               expected_source_hash="src-hash-1",
                               expected_approval_snapshot_hash="appr-hash-1",
                               owner_confirmation="DEPLOY Q2W9", client=client2)
            raise AssertionError("expected stale-source block")
        except coordinator.DeploymentBlocked as exc:
            assert "STALE" in str(exc) or "source" in str(exc)
        assert client2._write_counts["PUT"] == 0, "no write before stale-source block"
        print("PASS stale source blocks deploy (no writes)")

        # ---- 4. Stale approval blocks deploy ------------------------------
        reset_state()
        planmod.build_plan = lambda q, w: synthetic_plan()
        client3 = make_client()
        write_preflight(tmp, approval="appr-hash-1")
        planmod.build_plan = lambda q, w: synthetic_plan(approval_snapshot_hash="appr-hash-2")
        try:
            coordinator.deploy(2, 9, preflight_id="pf-test",
                               expected_source_hash="src-hash-1",
                               expected_approval_snapshot_hash="appr-hash-1",
                               owner_confirmation="DEPLOY Q2W9", client=client3)
            raise AssertionError("expected stale-approval block")
        except coordinator.DeploymentBlocked:
            pass
        assert client3._write_counts["PUT"] == 0
        print("PASS stale approval blocks deploy (no writes)")

        # ---- 5. Expired preflight blocks deploy ---------------------------
        reset_state()
        planmod.build_plan = lambda q, w: synthetic_plan()
        client4 = make_client()
        write_preflight(tmp, expires_past=True)
        try:
            coordinator.deploy(2, 9, preflight_id="pf-test",
                               expected_source_hash="src-hash-1",
                               expected_approval_snapshot_hash="appr-hash-1",
                               owner_confirmation="DEPLOY Q2W9", client=client4)
            raise AssertionError("expected expired block")
        except coordinator.DeploymentBlocked as exc:
            assert "expired" in str(exc).lower()
        print("PASS expired preflight blocks deploy")

        # ---- 6. Missing confirmation blocks deploy ------------------------
        reset_state()
        client5 = make_client()
        write_preflight(tmp)
        try:
            coordinator.deploy(2, 9, preflight_id="pf-test",
                               expected_source_hash="src-hash-1",
                               expected_approval_snapshot_hash="appr-hash-1",
                               owner_confirmation="", client=client5)
            raise AssertionError("expected confirmation block")
        except coordinator.DeploymentBlocked:
            pass
        assert client5._write_counts["PUT"] == 0
        print("PASS missing confirmation blocks deploy")

        # ---- 7. Partial failure stops remaining writes --------------------
        # Remove the assignment group so create_assignment fails AFTER page update.
        reset_state()
        planmod.build_plan = lambda q, w: synthetic_plan()
        client6 = make_client()
        client6.assignment_groups[26404] = [{"id": "60319", "name": "Written Assessments"}]
        write_preflight(tmp)
        rep = coordinator.deploy(2, 9, preflight_id="pf-test",
                                 expected_source_hash="src-hash-1",
                                 expected_approval_snapshot_hash="appr-hash-1",
                                 owner_confirmation="DEPLOY Q2W9", client=client6)
        assert rep["deployment_state"] == "DEPLOYMENT_PARTIAL", rep["deployment_state"]
        assert rep["pages"][0]["verified"] is True, "page should have succeeded"
        assert len(rep["assignments"]) == 0 or rep["assignments"][-1].get("disposition") == "FAILED"
        assert rep["failures"], "failures must be recorded"
        assert "corrective_plan" in rep
        # announcements not attempted (only 1 POST would be the failed assignment write)
        assert client6._write_counts["POST"] == 0, f"no successful assignment POST expected: {client6._write_counts}"
        assert client6._write_counts["PUT"] == 1, "page PUT happened"
        print("PASS partial failure stops remaining writes + corrective plan")

        # ---- 8. Idempotent rerun skips EXACT_MATCH assignment -------------
        reset_state()
        client7 = make_client()
        plan_dup = synthetic_plan()
        plan_dup["assignments"][0]["duplicate_classification"] = "EXACT_MATCH"
        planmod.build_plan = lambda q, w: plan_dup
        write_preflight(tmp, plan=plan_dup)
        rep = coordinator.deploy(2, 9, preflight_id="pf-test",
                                 expected_source_hash="src-hash-1",
                                 expected_approval_snapshot_hash="appr-hash-1",
                                 owner_confirmation="DEPLOY Q2W9", client=client7)
        assert rep["deployment_state"] == "PUBLISHED_VERIFIED"
        assert rep["assignments"][0]["disposition"] == "ALREADY_EXISTS"
        assert client7._write_counts["POST"] == 1, "only the announcement POST (assignment skipped)"
        print("PASS idempotent rerun skips exact-duplicate assignment")

        # ---- 9. Duplicate classification unit (AMBIGUOUS blocks preflight) -
        from scripts.canvas_llm_deploy.preflight import classify_assignment
        assert classify_assignment("SM5: Lesson 50 Homework", ["SM5: Lesson 50 Homework"]) == "EXACT_MATCH"
        assert classify_assignment("SM5: Lesson 50 Homework", ["SM5: Lesson 50 Homework (Retake)"]) == "AMBIGUOUS"
        assert classify_assignment("SM5: Lesson 50 Homework", ["SM5: Lesson 51 Homework"]) == "NEW"
        print("PASS duplicate classification (EXACT_MATCH / AMBIGUOUS / NEW)")

        # ---- 10. Preflight blocks: missing page / wrong course / missing group
        planmod.build_plan = lambda q, w: synthetic_plan()
        # missing page
        c10a = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
        c10a.assignment_groups[26404] = [{"id": "60321", "name": "Homework/Class Work"}]
        rec = preflightmod.run_preflight(2, 9, c10a)
        assert any("weekly page missing" in b for b in rec["blockers"]), rec["blockers"]
        assert rec["ready"] is False
        # wrong course (course id not present)
        c10b = FakeDeployClient(courses={})  # no 26404
        rec = preflightmod.run_preflight(2, 9, c10b)
        assert any("course" in b for b in rec["blockers"]), rec["blockers"]
        # missing assignment group (routing fail-closed)
        c10c = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
        c10c.seed_page(26404, SLUG, title="Q2W9", body="<div id='kl_wrapper_3'>x</div>")
        c10c.assignment_groups[26404] = [{"id": "60319", "name": "Written Assessments"}]
        rec = preflightmod.run_preflight(2, 9, c10c)
        assert any("group" in b for b in rec["blockers"]), rec["blockers"]
        print("PASS preflight blocks: missing page / wrong course / missing assignment group")

        # ---- 11. Preflight is GET-only (no writes) ------------------------
        c11 = make_client()
        rec = preflightmod.run_preflight(2, 9, c11)
        assert rec["canvas_writes"] == 0
        assert c11._write_counts == {"POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "GET": 0}
        print("PASS preflight is GET-only (zero writes)")

    finally:
        ledger.DEPLOY_ROOT = orig_deploy
        imf.staging_dir = orig_staging
        planmod.build_plan = orig_build
        planmod.load_packet = orig_load

print("PASS: Canvas guarded deployment tests complete")
PY

echo "PASS Canvas guarded deployment tests complete"
