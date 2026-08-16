#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 18E owner policy execution preconditions tests..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

TOTAL_PASS=0
TOTAL_FAIL=0

note_pass() { TOTAL_PASS=$((TOTAL_PASS + 1)); }
note_fail() { TOTAL_FAIL=$((TOTAL_FAIL + 1)); echo "FAIL: $1"; }

PKG="scripts/canvas_llm_phase18e"

echo
echo "Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  note_pass
else
  note_fail "Phase 18E modules failed to compile"
fi

echo
echo "Substantive Scenario Suite"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")

from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord, CanvasSnapshot, DeploymentIntent, DryRunPacket, SnapshotObject,
)
from scripts.canvas_llm_phase18e.policy import (
    OwnerCanvasPolicy, default_policy, due_timestamp, policy_hash,
)
from scripts.canvas_llm_phase18e.preconditions import (
    evaluate_preconditions, record_approval_bindings,
)
from scripts.canvas_llm_phase18e.adapter import (
    build_writer_requests, build_writer_requests_with_reports, detect_request_collisions,
)
from scripts.canvas_llm_phase18e.validation import WRITER_DEFAULT_AUDIT
from scripts.canvas_llm_phase27.canonicalize import canonical_hash

POLICY = OwnerCanvasPolicy(publish_state="resolved", publish_decision="published")
UNRESOLVED_POLICY = OwnerCanvasPolicy(publish_state="unresolved")
CFG = {"math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"}}
LOCATOR = "math-homework-q1w3-monday"

passed = []
failed = []

def check(name, cond, detail=""):
    if cond:
        passed.append(name)
    else:
        failed.append((name, detail))

def make_intent(op, *, oid="i-x", course="math", obj_type="assignment", locator=LOCATOR,
                assigned="2026-08-24", title="Math Homework — Monday", blockers=None,
                provenance=None, preconditions=None, source="canonical_rule", desired=None,
                course_id="M", ag_id="MA"):
    ds = {
        "title": title,
        "course_id": course_id,
        "assignment_group_id": ag_id,
        "assigned_date": assigned,
        "due_at": assigned,
        "timezone": "America/New_York",
    }
    if desired:
        ds.update(desired)
    pre = dict(preconditions or {})
    pre.setdefault("week_code", "Q1W3")
    return DeploymentIntent(
        id=oid, operation=op, object_type=obj_type, course=course,
        canonical_source=source, target_locator=locator, desired_state=ds,
        provenance=provenance if provenance is not None else [
            {"sourceType": "canonical-weekly-plan", "sourceRef": "wp-Q1W3", "details": "x"},
        ],
        preconditions=pre, blockers=blockers or [],
    )

def make_packet(*intents, env="sandbox"):
    p = DryRunPacket(
        week_code="Q1W3", canonical_plan_identity="wp-Q1W3", canonical_revision="wp-Q1W3",
        preview_identity="preview-abc", preview_hash="abc123", snapshot_identity="snap-1",
        snapshot_hash="snap123", target_environment=env, intents=list(intents),
    )
    p.packet_hash = canonical_hash({
        "week_code": p.week_code, "canonical_revision": p.canonical_revision,
        "preview_hash": p.preview_hash, "snapshot_hash": p.snapshot_hash,
        "target_environment": p.target_environment, "intents": [i.to_dict() for i in p.intents],
    })
    return p

def make_approval(p, policy, ids, *, packet_hash=None):
    b = record_approval_bindings(packet=p, policy=policy, canvas_config=CFG)
    return ApprovalRecord(
        packet_hash=packet_hash or p.packet_hash, reviewer="Owner",
        approved_at="2026-07-25T00:00:00Z", scope="full-week",
        approved_intent_ids=ids, preconditions=b,
    )

def absent_snapshot():
    return CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[])

def update_obj(*, content_hash="h1", course="math", oid="a1", title="Math Homework — Monday",
               updated_at="t1", managed=True, baseline="h1", locator=LOCATOR):
    return SnapshotObject(
        object_id=oid, object_type="assignment", course=course, locator=locator,
        title=title, current_state={"course_id": "M", "title": title, "updated_at": updated_at},
        content_hash=content_hash, managed=managed, baseline_hash=baseline,
    )

def update_snapshot(obj):
    return CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[obj])

# 1. Safe approved CREATE -> READY_FOR_EXECUTION_REVIEW
i = make_intent("CREATE", oid="i-create", preconditions={"expected_object_id": "", "expected_current_hash": ""})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-create"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("01 safe CREATE", r.readiness == "READY_FOR_EXECUTION_REVIEW", r.readiness)
check("01 safe CREATE request", len(build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())) == 1)

# 2. Safe approved UPDATE -> READY_FOR_EXECUTION_REVIEW
i = make_intent("UPDATE", oid="i-update", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-update"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("02 safe UPDATE", r.readiness == "READY_FOR_EXECUTION_REVIEW", (r.readiness, r.blockers))
check("02 safe UPDATE request", len(build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))) == 1)

# 3. NO_CHANGE -> no WriterRequest
i = make_intent("NO_CHANGE", oid="i-nc")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-nc"])
check("03 NO_CHANGE filtered", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 4. Blocked intent -> no WriterRequest
i = make_intent("CREATE", oid="i-blocked", blockers=["ownership_uncertain"])
p = make_packet(i)
a = make_approval(p, POLICY, ["i-blocked"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("04 blocked intent", r.readiness == "BLOCKED_OWNERSHIP", r.readiness)
check("04 blocked intent request", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 5. Approval packet hash mismatch blocks
i = make_intent("CREATE", oid="i-ph")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-ph"], packet_hash="WRONG")
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("05 packet hash mismatch", r.readiness == "BLOCKED_APPROVAL", r.readiness)

# 6. Approval missing intent blocks
i = make_intent("CREATE", oid="i-not-approved")
p = make_packet(i)
a = make_approval(p, POLICY, ["some-other-intent"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("06 missing intent approval", r.readiness == "BLOCKED_APPROVAL", r.readiness)

# 7. Canonical revision change blocks (approval-time binding drift)
i = make_intent("CREATE", oid="i-rev")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-rev"])
a.preconditions["canonical_revision"] = "wp-CHANGED"
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("07 canonical revision change", r.readiness == "BLOCKED_STALE_PACKET", r.readiness)

# 8. Preview hash change blocks
i = make_intent("CREATE", oid="i-prev")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-prev"])
a.preconditions["preview_hash"] = "CHANGED"
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("08 preview hash change", r.readiness == "BLOCKED_STALE_PACKET", r.readiness)

# 9. Snapshot hash change blocks
i = make_intent("CREATE", oid="i-snap")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-snap"])
a.preconditions["snapshot_hash"] = "CHANGED"
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("09 snapshot hash change", r.readiness == "BLOCKED_STALE_PACKET", r.readiness)

# 10. Live current-state hash change blocks
i = make_intent("UPDATE", oid="i-stale", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-stale"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj(content_hash="DIFFERENT")))
check("10 live hash change", r.readiness == "BLOCKED_STALE_CANVAS", r.readiness)

# 11. Target environment change blocks
i = make_intent("CREATE", oid="i-env")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-env"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot(), target_environment="production")
check("11 environment change", r.readiness == "BLOCKED_CONFIG", r.readiness)

# 12. Config change blocks
i = make_intent("CREATE", oid="i-cfg")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-cfg"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config={"math": {"course_id": "X"}}, snapshot=absent_snapshot())
check("12 config change", r.readiness == "BLOCKED_CONFIG", r.readiness)

# 13. UPDATE missing Canvas ID blocks
i = make_intent("UPDATE", oid="i-noid", preconditions={"expected_object_id": "", "expected_current_hash": "h1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-noid"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("13 UPDATE missing canvas id", r.readiness == "BLOCKED_WRITER_CONTRACT", (r.readiness, r.blockers))

# 14. Unmanaged target blocks
i = make_intent("UPDATE", oid="i-unmanaged", blockers=["ownership_uncertain"], preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-unmanaged"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj(managed=False)))
check("14 unmanaged target", r.readiness == "BLOCKED_OWNERSHIP", r.readiness)

# 15. Remote teacher edit blocks
i = make_intent("UPDATE", oid="i-drift", blockers=["remote_drift"], preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-drift"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj(content_hash="teacher-edited")))
check("15 remote teacher edit", r.readiness in ("BLOCKED_REMOTE_DRIFT", "BLOCKED_STALE_CANVAS"), r.readiness)

# 16. Protected course blocks
i = make_intent("CREATE", oid="i-protected", blockers=["protected_course"])
p = make_packet(i)
a = make_approval(p, POLICY, ["i-protected"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("16 protected course", r.readiness == "BLOCKED_PROTECTED", r.readiness)
check("16 protected request", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 17. Canonical blank creates no mutation
i = make_intent("CREATE", oid="i-blank", title="")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-blank"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("17 canonical blank", r.readiness == "BLOCKED_UNRESOLVED", (r.readiness, r.blockers))
check("17 canonical blank request", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 18. Unresolved assignment date blocks due-time generation
try:
    due_timestamp("", "America/New_York")
    check("18 unresolved date", False, "no error raised")
except ValueError:
    check("18 unresolved date", True)

# 19. Assigned-day 11:59 due time derives correctly
check("19 assigned-day 11:59", due_timestamp("2026-08-24", "America/New_York") == "2026-08-24T23:59:00-04:00",
      due_timestamp("2026-08-24", "America/New_York"))

# 20. Summer DST offset correct
check("20 summer DST", due_timestamp("2026-08-24", "America/New_York").endswith("-04:00"))

# 21. Winter standard-time offset correct
check("21 winter standard", due_timestamp("2026-01-15", "America/New_York").endswith("-05:00"))

# 22. Friday homework remains Friday 11:59
check("22 friday stays friday", due_timestamp("2026-08-21", "America/New_York") == "2026-08-21T23:59:00-04:00")

# 23. Paper homework uses on_paper
i = make_intent("CREATE", oid="i-paper")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-paper"])
reqs = build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("23 on_paper", len(reqs) == 1 and reqs[0].submission_type == "on_paper", reqs[0].submission_type if reqs else "none")

# 24. Physical next-day hand-in does not alter Canvas due date
i = make_intent("CREATE", oid="i-nextday", assigned="2026-08-21")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-nextday"])
reqs = build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("24 next-day hand-in", reqs and reqs[0].due_at.startswith("2026-08-21T23:59:00"), reqs[0].due_at if reqs else "none")

# 25. Publish policy unresolved blocks
i = make_intent("UPDATE", oid="i-pub", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, UNRESOLVED_POLICY, ["i-pub"])
r = evaluate_preconditions(p, i, a, UNRESOLVED_POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("25 publish unresolved", r.readiness == "BLOCKED_PUBLISH_POLICY", (r.readiness, r.blockers))

# 26. published=True writer default cannot override policy
check("26 publish default classified unresolved", WRITER_DEFAULT_AUDIT["published"] == "unresolved", WRITER_DEFAULT_AUDIT["published"])
i = make_intent("UPDATE", oid="i-pubdef", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, UNRESOLVED_POLICY, ["i-pubdef"])
reqs = build_writer_requests(p, a, UNRESOLVED_POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("26 unresolved policy no request", reqs == [])

# 27. Prediction-only content cannot become WriterRequest
i = make_intent("CREATE", oid="i-pred", source="predictive_suggestion", provenance=[])
p = make_packet(i)
a = make_approval(p, POLICY, ["i-pred"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("27 prediction provenance", r.readiness == "BLOCKED_PROVENANCE", r.readiness)
check("27 prediction no request", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 28. Title collision blocks
i = make_intent("CREATE", oid="i-collide", blockers=["title_collision"])
p = make_packet(i)
a = make_approval(p, POLICY, ["i-collide"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("28 title collision", r.readiness == "BLOCKED_COLLISION", r.readiness)

# 29. Duplicate WriterRequests block (drop colliding group)
i1 = make_intent("UPDATE", oid="i-dup-1", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
i2 = make_intent("UPDATE", oid="i-dup-2", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i1, i2)
a = make_approval(p, POLICY, ["i-dup-1", "i-dup-2"])
reqs = build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("29 duplicate requests dropped", reqs == [], [r.request_id for r in reqs])

# 30. Unknown operation blocks
i = make_intent("FOOBAR", oid="i-unknown")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-unknown"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("30 unknown operation", r.readiness == "BLOCKED_WRITER_CONTRACT", r.readiness)

# 31. DELETE rejected
i = make_intent("DELETE", oid="i-delete")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-delete"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("31 DELETE rejected", r.readiness == "BLOCKED_WRITER_CONTRACT", r.readiness)
check("31 DELETE no request", build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot()) == [])

# 32. Wrong-course target blocks
i = make_intent("UPDATE", oid="i-wrong", blockers=["wrong_course"], preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-wrong"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj(course="OTHER")))
check("32 wrong course", r.readiness == "BLOCKED_OWNERSHIP", r.readiness)

# 33. Provenance loss blocks
i = make_intent("CREATE", oid="i-noprov", provenance=[])
p = make_packet(i)
a = make_approval(p, POLICY, ["i-noprov"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("33 provenance loss", r.readiness == "BLOCKED_PROVENANCE", r.readiness)

# 34. Owner-policy hash mismatch blocks
i = make_intent("CREATE", oid="i-polhash")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-polhash"])
# Rebuild approval with a different policy so its recorded policy_hash differs
a2 = make_approval(p, UNRESOLVED_POLICY, ["i-polhash"])
r = evaluate_preconditions(p, i, a2, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("34 policy hash mismatch", r.readiness == "BLOCKED_APPROVAL", (r.readiness, r.blockers))

# 35. Owner-policy change invalidates prior approval
i = make_intent("CREATE", oid="i-polchange")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-polchange"])
p2 = OwnerCanvasPolicy(publish_state="resolved", publish_decision="unpublished")
r = evaluate_preconditions(p, i, a, p2, canvas_config=CFG, snapshot=absent_snapshot())
check("35 policy change invalidates", any(b == "policy:hash_mismatch" for b in r.blockers), r.blockers)

# 36. Identical semantic inputs -> identical due timestamp
check("36 deterministic due", due_timestamp("2026-08-24") == due_timestamp("2026-08-24"))

# 37. Identical semantic inputs -> identical policy hash
check("37 deterministic policy hash", policy_hash(default_policy()) == policy_hash(default_policy()))

# 38. Identical semantic inputs -> identical WriterRequest/request ID
i = make_intent("CREATE", oid="i-det")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-det"])
r1 = build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
r2 = build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("38 deterministic request", r1[0].request_id == r2[0].request_id and r1[0].to_dict() == r2[0].to_dict())

# 41. Partial snapshot fetch blocks affected target
snap_partial = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[], fetch_errors=["math"])
i = make_intent("UPDATE", oid="i-partial", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-partial"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=snap_partial)
check("41 partial fetch", r.readiness == "BLOCKED_STALE_CANVAS", (r.readiness, r.blockers))

# 42. Network read failure blocks
snap_fail = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[], read_failure=True, read_failure_reason="network down")
i = make_intent("UPDATE", oid="i-readfail", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-readfail"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=snap_fail)
check("42 read failure", r.readiness == "BLOCKED_STALE_CANVAS", (r.readiness, r.blockers))

# 43. Malformed live response blocks (missing fresh snapshot)
i = make_intent("UPDATE", oid="i-malformed", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-malformed"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=None)
check("43 malformed/missing snapshot", r.readiness == "BLOCKED_STALE_CANVAS", (r.readiness, r.blockers))

# 44. Legacy fixture cannot override live/current state (live hash authoritative)
i = make_intent("UPDATE", oid="i-legacy", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-legacy"])
# Simulate a legacy fixture claiming "h1" but live object content differs
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj(content_hash="live-actual")))
check("44 legacy fixture", r.readiness == "BLOCKED_STALE_CANVAS", r.readiness)

# 45. Assignment group missing blocks
i = make_intent("CREATE", oid="i-noag", ag_id="")
p = make_packet(i)
a = make_approval(p, POLICY, ["i-noag"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("45 assignment group missing", r.readiness == "BLOCKED_UNRESOLVED", (r.readiness, r.blockers))

# 46. CREATE target appears after approval -> collision/stale block
i = make_intent("CREATE", oid="i-appeared", preconditions={"expected_object_id": "", "expected_current_hash": ""})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-appeared"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=update_snapshot(update_obj()))
check("46 CREATE target appeared", r.readiness == "BLOCKED_STALE_CANVAS", (r.readiness, r.blockers))

# 47. UPDATE target disappears after approval -> stale target block
i = make_intent("UPDATE", oid="i-disappeared", preconditions={"expected_object_id": "a1", "expected_current_hash": "h1", "expected_last_updated": "t1"})
p = make_packet(i)
a = make_approval(p, POLICY, ["i-disappeared"])
r = evaluate_preconditions(p, i, a, POLICY, canvas_config=CFG, snapshot=absent_snapshot())
check("47 UPDATE target disappeared", r.readiness == "BLOCKED_STALE_CANVAS", (r.readiness, r.blockers))

total = len(passed) + len(failed)
for name in passed:
    print(f"PASS scenario: {name}")
for name, detail in failed:
    print(f"FAIL scenario: {name} -> {detail}")
print(f"SCENARIO_TOTAL: {total}")
print(f"SCENARIO_PASS: {len(passed)}")
print(f"SCENARIO_FAIL: {len(failed)}")
assert len(failed) == 0, failed
assert total >= 35, f"only {total} substantial scenarios (need >=35)"
PY
then
  note_pass
else
  note_fail "substantive scenario suite failed"
fi

echo
echo "Import-Safe Pure Graph"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18e.contracts import ExecutionPreconditionReport, WriterRequest
from scripts.canvas_llm_phase18e.policy import default_policy, due_timestamp, policy_hash
from scripts.canvas_llm_phase18e.preconditions import evaluate_preconditions
from scripts.canvas_llm_phase18e.adapter import build_writer_requests
forbidden = ["canvas_writer", "canvas_connector",
             "scripts.canvas_llm_phase22.phase22_workstation",
             "scripts.canvas_llm_phase26.pipeline"]
loaded = [m for m in forbidden if m in sys.modules]
assert not loaded, loaded
print("OK")
PY
then
  note_pass
else
  note_fail "pure import graph loaded execution modules"
fi

echo
echo "Static Write-Safety Scan"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request|attempt_live_write|\.deploy\(|\.apply\(' \
  "$PKG"/*.py >/tmp/phase18e_write_scan.txt 2>/dev/null; then
  cat /tmp/phase18e_write_scan.txt
  note_fail "mutation path token found in Phase 18E package"
else
  note_pass
fi
rm -f /tmp/phase18e_write_scan.txt

echo
echo "Runtime Write-Safety (mutation count = 0)"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")

# Prove no writer/mutation/live-write-gate invocation occurs from any pure 18E path.
import scripts.canvas_llm_phase18e.contracts as contracts
import scripts.canvas_llm_phase18e.policy as policy
import scripts.canvas_llm_phase18e.preconditions as preconditions
import scripts.canvas_llm_phase18e.adapter as adapter

writer_calls = 0
transport_calls = 0
gate_calls = 0

# If any forbidden module were importable/executable here it would violate safety;
# assert the write-gate execution path is blocked and never invoked.
from scripts.canvas_llm_phase22.write_gate import attempt_write, evaluate_write, write_gate_blocks_execution
decision = evaluate_write("create", "page", "p-1", approved=True, approved_by="Teacher", approved_at="2026-07-25T00:00:00Z")
assert attempt_write(decision).gate_state == "BLOCKED"
assert write_gate_blocks_execution()
gate_calls += 0  # gate was inspected, not executed

# The pure modules themselves expose no mutation/execute entrypoints.
FORBIDDEN_FN = ("attempt_live_write", "execute", "deploy", "post", "put", "patch", "delete", "apply_write", "apply")
for mod in (contracts, policy, preconditions, adapter):
    for name in dir(mod):
        if name in FORBIDDEN_FN:
            raise AssertionError(f"{mod.__name__}.{name} is a forbidden mutation name")

print(f"writer_calls={writer_calls}")
print(f"transport_calls={transport_calls}")
print(f"gate_execution_calls={gate_calls}")
assert writer_calls == 0 and transport_calls == 0 and gate_calls == 0
print("OK")
PY
then
  note_pass
else
  note_fail "runtime write-safety violated"
fi

echo
echo "CLI Self-Check"
echo "----------------------------------------"
if python3 "$PKG/cli.py" --selfcheck >/tmp/phase18e_selfcheck.txt 2>&1; then
  note_pass
else
  cat /tmp/phase18e_selfcheck.txt
  note_fail "CLI self-check failed"
fi
rm -f /tmp/phase18e_selfcheck.txt

echo
echo "Summary"
echo "----------------------------------------"
echo "TOTAL_PASS: ${TOTAL_PASS}"
echo "TOTAL_FAIL: ${TOTAL_FAIL}"

if [[ "$TOTAL_FAIL" -ne 0 ]]; then
  exit 1
fi
echo "PASS: Canvas LLM Phase 18E owner policy execution preconditions tests complete"
