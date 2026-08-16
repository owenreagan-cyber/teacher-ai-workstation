#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

echo "Canvas LLM Phase 18D — Write-Readiness Dry-Run & Safety Diff Test Suite"
echo "-----------------------------------------------------------------------"

python3 - <<'PY'
import copy
import json
import sys
sys.path.insert(0, ".")

from scripts.canvas_llm_phase18a.examples import build_example_plan
from scripts.canvas_llm_phase18c.preview import assemble_teacher_preview
from scripts.canvas_llm_phase18c.contracts import RuntimeContext
from scripts.canvas_llm_phase18d.deployment import (
    CONTENT_FIELDS, assemble_dry_run_packet, build_safety_diff, validate_packet,
)
from scripts.canvas_llm_phase18d.diff import semantic_hash
from scripts.canvas_llm_phase18d.readiness import approval_is_valid, packet_is_stale
from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord, CanvasSnapshot, DeploymentIntent, DryRunContext, SnapshotObject,
)

CFG = {
    "math": {"course_id": "COURSE_MATH", "module_id": "MODULE_MATH", "assignment_group_id": "AG_MATH"},
    "reading-spelling": {"course_id": "COURSE_READING", "module_id": "MODULE_READING", "assignment_group_id": "AG_READING"},
    "language-arts": {"course_id": "COURSE_LA", "module_id": "MODULE_LA", "assignment_group_id": "AG_LA"},
    "history": {"course_id": "COURSE_HISTORY", "module_id": "MODULE_HISTORY", "assignment_group_id": "AG_HISTORY"},
}

def resolved_ctx(**kw):
    base = dict(canvas_config=CFG, due_time_policy="resolved", resolved_due_time="15:00",
                publish_policy="resolved", resolved_publish_state="published")
    base.update(kw)
    return DryRunContext(**base)

def clean_plan():
    plan = build_example_plan()
    plan = copy.deepcopy(plan)
    for day in plan.courses["History"].days:
        if day.weekday == "Wednesday":
            day.ambiguity = ""
            day.in_class = "Unit 1 Lesson 2 (resolved)"
            day.raw = "Unit 1 Lesson 2"
    return plan

def preview_of(plan=None, due_time_policy="resolved"):
    plan = plan or clean_plan()
    return assemble_teacher_preview(plan, RuntimeContext(canvas_config=CFG, due_time_policy=due_time_policy))

def empty_snap():
    return CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-empty", objects=[])

def matching_snap(pkt, snap_id="snap-matching"):
    objs = []
    for i in pkt.intents:
        if i.operation in ("CREATE", "UPDATE", "NO_CHANGE"):
            fields = CONTENT_FIELDS.get(i.object_type, ["title", "body", "course_id"])
            h = semantic_hash(i.desired_state, fields)
            objs.append(SnapshotObject(
                object_id=f"live-{i.id}", object_type=i.object_type, course=i.course,
                locator=i.target_locator, title=str(i.desired_state.get("title", "")),
                current_state=dict(i.desired_state), content_hash=h, managed=True, baseline_hash=h,
            ))
    return CanvasSnapshot(week_code=pkt.week_code, snapshot_id=snap_id, objects=objs)

N = 0
def scenario(name, fn):
    global N
    fn()
    N += 1
    print(f"PASS: {name}")

# 1. Canonical blank -> no fabricated operation
def t1():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    # No intent may invent "No homework"/"None"/"TBD" as a write target.
    blob = json.dumps(pkt.to_dict())
    for forbidden in ("No homework", "No Homework", "None", "TBD"):
        # The only "No Homework" allowed is teacher-authored canonical homework text, never a title/locator.
        assert not any(i.target_locator.lower().endswith(forbidden.lower().replace(" ", "")) for i in pkt.intents)
    # Science (blank, protected) is SKIP, not a write.
    sci = [i for i in pkt.intents if i.course == "science"]
    assert sci and all(i.operation == "SKIP" for i in sci)
scenario("canonical blank generates no fabricated operation", t1)

# 2. Unresolved field -> blocked
def t2():
    p = preview_of(build_example_plan())  # History Wednesday unresolved
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    hist = [i for i in pkt.intents if i.course == "history"]
    assert hist and all(i.operation == "BLOCKED" and "unresolved_content" in i.blockers for i in hist)
    assert pkt.readiness == "BLOCKED_UNRESOLVED", pkt.readiness
scenario("unresolved canonical field blocks mutation", t2)

# 3. Protected course -> zero writable intents
def t3():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    sci = [i for i in pkt.intents if i.course == "science"]
    assert sci and all(i.operation == "SKIP" for i in sci)
    assert not [i for i in pkt.intents if i.course == "science" and i.operation in ("CREATE", "UPDATE")]
scenario("protected course produces zero writable intents", t3)

# 4. Missing config -> blocked, no guessed ID
def t4():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), DryRunContext(canvas_config={}))
    assert pkt.readiness == "BLOCKED_MISSING_CONFIG", pkt.readiness
    # No intent may guess a course/module/assignment-group ID.
    for i in pkt.intents:
        if i.operation in ("CREATE", "UPDATE"):
            assert not (i.desired_state.get("course_id") or "").strip()
scenario("missing config blocks without guessed IDs", t4)

# 5. Duplicate targets -> collision detection
def t5():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    from scripts.canvas_llm_phase18d.deployment import _detect_intent_collisions
    # A second intent targeting a different locator is fine.
    distinct = DeploymentIntent(
        id="dup-1", operation="CREATE", object_type="agenda_page", course="math",
        canonical_source="canonical_rule", target_locator="math-agenda-OTHER",
        desired_state={}, current_state={}, provenance=[{"x": 1}], reason="x",
    )
    assert _detect_intent_collisions(pkt.intents + [distinct]) == []
    # A second intent targeting the SAME locator collides.
    dup = DeploymentIntent(
        id="dup-2", operation="CREATE", object_type="agenda_page", course="math",
        canonical_source="canonical_rule", target_locator="math-agenda-q1w3",
        desired_state={}, current_state={}, provenance=[{"x": 1}], reason="x",
    )
    collisions = _detect_intent_collisions(pkt.intents + [dup])
    assert any("math-agenda-q1w3" in c for c in collisions)
scenario("duplicate targets are collision-detected", t5)

# 6. Title collision -> no overwrite
def t6():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    # Teacher-created page with same title but unmanaged, different locator.
    objs = [SnapshotObject(
        object_id="teacher-page-9", object_type="agenda_page", course="math",
        locator="someone-elses-page", title=math_page.desired_state["title"],
        current_state={"title": math_page.desired_state["title"], "body": "teacher wrote this"},
        content_hash="abc", managed=False, baseline_hash="",
    )]
    pkt2 = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-coll", objects=objs), resolved_ctx())
    m2 = next(i for i in pkt2.intents if i.object_type == "agenda_page" and i.course == "math")
    assert m2.operation == "BLOCKED" and "title_collision" in m2.blockers, m2.blockers
scenario("title collision with teacher-created page never overwrites", t6)

# 7. Remote teacher edit -> remote drift blocker
def t7():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    fields = CONTENT_FIELDS["agenda_page"]
    base = semantic_hash(math_page.desired_state, fields)
    objs = [SnapshotObject(
        object_id="live-math", object_type="agenda_page", course="math",
        locator=math_page.target_locator, title=math_page.desired_state["title"],
        current_state={"title": math_page.desired_state["title"], "body": "teacher edited this body", "course_id": "COURSE_MATH"},
        content_hash="drifted-hash", managed=True, baseline_hash=base,
    )]
    pkt2 = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-drift", objects=objs), resolved_ctx())
    m2 = next(i for i in pkt2.intents if i.object_type == "agenda_page" and i.course == "math")
    assert m2.operation == "BLOCKED" and "remote_drift" in m2.blockers, m2.blockers
scenario("remote teacher edit triggers remote-drift blocker", t7)

# 8. Stale snapshot invalidates approval
def t8():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    rec = ApprovalRecord(packet_hash=pkt.packet_hash, reviewer="Teacher", approved_at="now",
                         scope="week", approved_intent_ids=[i.id for i in pkt.intents],
                         preconditions={"canonical_revision": pkt.canonical_revision,
                                        "preview_hash": pkt.preview_hash,
                                        "snapshot_hash": pkt.snapshot_hash})
    ok, _ = approval_is_valid(rec, pkt)
    assert ok
    stale, reasons = packet_is_stale(pkt, snapshot_hash="different-snapshot-hash")
    assert stale and "snapshot" in " ".join(reasons)
scenario("stale snapshot invalidates approval", t8)

# 9. Stale canonical plan invalidates packet
def t9():
    pA = preview_of(clean_plan())
    pktA = assemble_dry_run_packet(pA, empty_snap(), resolved_ctx())
    planB = clean_plan()
    planB.courses["Math"].days[0].in_class = "Lesson 999"
    pB = assemble_teacher_preview(planB, RuntimeContext(canvas_config=CFG, due_time_policy="resolved"))
    pktB = assemble_dry_run_packet(pB, empty_snap(), resolved_ctx())
    assert pktA.canonical_revision != pktB.canonical_revision
    stale, reasons = packet_is_stale(pktA, canonical_revision=pktB.canonical_revision)
    assert stale and "canonical" in " ".join(reasons)
scenario("stale canonical plan invalidates packet", t9)

# 10. Stale preview invalidates packet
def t10():
    pA = preview_of(due_time_policy="resolved")
    pktA = assemble_dry_run_packet(pA, empty_snap(), resolved_ctx())
    pB = assemble_teacher_preview(clean_plan(), RuntimeContext(canvas_config=CFG, due_time_policy="unresolved"))
    pktB = assemble_dry_run_packet(pB, empty_snap(), resolved_ctx())
    assert pktA.preview_hash != pktB.preview_hash
    stale, reasons = packet_is_stale(pktA, preview_hash=pktB.preview_hash)
    assert stale and "preview" in " ".join(reasons)
scenario("stale teacher preview invalidates packet", t10)

# 11. Due date is canonical assigned date; no time-of-day fabricated at 18D.
def t11():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), DryRunContext(canvas_config=CFG, publish_policy="resolved", resolved_publish_state="published"))
    assigns = [i for i in pkt.intents if i.object_type == "assignment"]
    assert assigns, "expected assignment intents"
    assert all(i.operation == "CREATE" for i in assigns), [(i.operation, i.blockers) for i in assigns]
    for i in assigns:
        ad = i.desired_state.get("assigned_date")
        assert ad and ad == i.desired_state.get("due_at"), i.desired_state
        assert "T" not in ad, f"fabricated time-of-day in {ad!r}"
        assert i.desired_state.get("timezone") == "America/New_York"
scenario("assignment due date is canonical assigned date (no fabricated time)", t11)

# 12. No implicit publication
def t12():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), DryRunContext(canvas_config=CFG, due_time_policy="resolved", resolved_due_time="15:00"))
    pages = [i for i in pkt.intents if i.object_type == "agenda_page" and i.course != "science"]
    assert all(i.operation == "BLOCKED" and any(b == "policy:publish_state_unresolved" for b in i.blockers) for i in pages)
scenario("no implicit publication intent", t12)

# 13. Idempotence
def t13():
    p = preview_of()
    snap = empty_snap()
    a = json.dumps(assemble_dry_run_packet(p, snap, resolved_ctx()).to_dict(), sort_keys=True)
    b = json.dumps(assemble_dry_run_packet(p, snap, resolved_ctx()).to_dict(), sort_keys=True)
    assert a == b
scenario("idempotent packet and hash", t13)

# 14. No change -> NO_CHANGE not UPDATE
def t14():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    pkt2 = assemble_dry_run_packet(p, matching_snap(pkt), resolved_ctx())
    actionable = [i for i in pkt2.intents if i.operation != "SKIP"]
    assert actionable and all(i.operation == "NO_CHANGE" for i in actionable), \
        [(i.course, i.operation) for i in actionable]
    assert pkt2.readiness == "READY_FOR_OWNER_REVIEW", pkt2.readiness
scenario("already-correct Canvas state yields NO_CHANGE", t14)

# 15. Partial live fetch -> affected scope blocked
def t15():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-partial", objects=[], fetch_errors=["math"]), resolved_ctx())
    math = [i for i in pkt.intents if i.course == "math"]
    assert math and all(i.operation == "BLOCKED" and "read_failure" in i.blockers for i in math)
    assert pkt.readiness == "BLOCKED_READ_FAILURE", pkt.readiness
scenario("partial live fetch blocks affected scope", t15)

# 16. Network read failure -> blocked
def t16():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-fail", objects=[], read_failure=True, read_failure_reason="network down"), resolved_ctx())
    assert pkt.readiness == "BLOCKED_READ_FAILURE", pkt.readiness
    assert any("network down" in b for b in pkt.blocked)
scenario("network read failure blocks packet", t16)

# 17. Malformed live response -> validation failure
def t17():
    p = preview_of()
    try:
        assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="s", objects=[SnapshotObject(
            object_id="", object_type="bogus_type", course="math", locator="x", title="",
        )]), resolved_ctx())
        raise AssertionError("expected ValueError for malformed snapshot")
    except ValueError as e:
        assert "malformed" in str(e)
scenario("malformed live response fails validation", t17)

# 18. Wrong course -> block
def t18():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    wrong_state = dict(math_page.desired_state)
    wrong_state["course_id"] = "COURSE_HISTORY"  # object claims another course's ID
    objs = [SnapshotObject(
        object_id="live-math", object_type="agenda_page", course="math",
        locator=math_page.target_locator, title=math_page.desired_state["title"],
        current_state=wrong_state, content_hash="h", managed=True, baseline_hash="h",
    )]
    pkt2 = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-wrong", objects=objs), resolved_ctx())
    m2 = next(i for i in pkt2.intents if i.object_type == "agenda_page" and i.course == "math")
    assert m2.operation == "BLOCKED" and "wrong_course" in m2.blockers, m2.blockers
scenario("resolved object from wrong course is blocked", t18)

# 19. Legacy fixture conflict -> live verified state governs
def t19():
    p = preview_of()
    # A legacy fixture claims the math page already exists with different content,
    # but live snapshot is empty -> fixture must not override live state.
    ctx = resolved_ctx(legacy_fixtures={"math-agenda-q1w3": {"title": "OLD", "body": "legacy"}})
    pkt = assemble_dry_run_packet(p, empty_snap(), ctx)
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    assert math_page.operation == "CREATE", math_page.operation
scenario("legacy fixture does not override live verified state", t19)

# 20. Prediction never becomes write intent
def t20():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    assert not [i for i in pkt.intents if i.object_type == "announcement"]
    # No intent may be derived from the advisory prediction surface.
    pred = p.prediction.get("predictions", []) if hasattr(p, "prediction") else []
    for i in pkt.intents:
        assert not any(str(i.reason).startswith("prediction") for _ in [0])
scenario("prediction-only content never becomes a writable intent", t20)

# 21. Provenance loss -> fail validation
def t21():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    orphan = DeploymentIntent(id="orphan-1", operation="CREATE", object_type="agenda_page",
                              course="math", canonical_source="", target_locator="x",
                              desired_state={}, current_state={}, provenance=[], reason="")
    pkt.intents.append(orphan)
    errors = validate_packet(pkt)
    assert any("provenance" in e for e in errors)
    assert any("reason" in e for e in errors)
scenario("intent without provenance fails validation", t21)

# 22. Unknown operation type fails closed
def t22():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    bad = DeploymentIntent(id="bad-1", operation="FLIBBLE", object_type="agenda_page",
                           course="math", canonical_source="canonical_rule", target_locator="x",
                           desired_state={}, current_state={}, provenance=[{"s": 1}], reason="bad")
    pkt.intents.append(bad)
    errors = validate_packet(pkt)
    assert any("unknown operation" in e for e in errors)
scenario("unknown operation type fails closed", t22)

# 23. Execution import isolation
def t23():
    import subprocess
    code = (
        "import sys; sys.path.insert(0, '.')\n"
        "from scripts.canvas_llm_phase18d.contracts import DeploymentIntent, DryRunPacket\n"
        "from scripts.canvas_llm_phase18d.diff import build_safety_diff_item\n"
        "from scripts.canvas_llm_phase18d.deployment import assemble_dry_run_packet\n"
        "forbidden = ['canvas_writer', 'canvas_connector', 'canvas_operations', 'weekly_agenda_publisher']\n"
        "import sys as _s\n"
        "loaded = [m for m in forbidden if m in _s.modules]\n"
        "assert not loaded, loaded\n"
        "print('OK')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
scenario("importing Phase 18D loads no execution modules", t23)

# 24. Create vs update resolution
def t24():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    # Same content but one field differs -> UPDATE (managed, no drift).
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    fields = CONTENT_FIELDS["agenda_page"]
    h = semantic_hash(math_page.desired_state, fields)
    changed = dict(math_page.desired_state)
    changed["body"] = math_page.desired_state["body"] + "<p>extra</p>"
    objs = [SnapshotObject(object_id="live-math", object_type="agenda_page", course="math",
                           locator=math_page.target_locator, title=math_page.desired_state["title"],
                           current_state=changed, content_hash=h, managed=True, baseline_hash=h)]
    pkt2 = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-upd", objects=objs), resolved_ctx())
    m2 = next(i for i in pkt2.intents if i.object_type == "agenda_page" and i.course == "math")
    assert m2.operation == "UPDATE", m2.operation
scenario("create-vs-update resolved by live state, not guess", t24)

# 25. Deterministic ordering + packet hash
def t25():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    courses = [i.course for i in pkt.intents]
    # Ordering is deterministic by course then object type then locator.
    assert courses == sorted(courses, key=lambda c: ["reading-spelling", "math", "language-arts", "history", "science"].index(c) if c in ["reading-spelling", "math", "language-arts", "history", "science"] else 99)
    assert validate_packet(pkt) == []
scenario("deterministic ordering and valid packet hash", t25)

# 26. Ownership uncertain -> blocked (never overwrite)
def t26():
    p = preview_of()
    pkt = assemble_dry_run_packet(p, empty_snap(), resolved_ctx())
    math_page = next(i for i in pkt.intents if i.object_type == "agenda_page" and i.course == "math")
    objs = [SnapshotObject(object_id="live-math", object_type="agenda_page", course="math",
                           locator=math_page.target_locator, title=math_page.desired_state["title"],
                           current_state=dict(math_page.desired_state), content_hash="h", managed=False, baseline_hash="")]
    pkt2 = assemble_dry_run_packet(p, CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-own", objects=objs), resolved_ctx())
    m2 = next(i for i in pkt2.intents if i.object_type == "agenda_page" and i.course == "math")
    assert m2.operation == "BLOCKED" and "ownership_uncertain" in m2.blockers
scenario("ownership-uncertain object is never overwritten", t26)

print(f"TOTAL_PASS: {N}")
PY

echo
echo "Static write-safety scan"
echo "-----------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request' \
  scripts/canvas_llm_phase18d/*.py >/tmp/phase18d_write_scan.txt 2>/dev/null; then
  cat /tmp/phase18d_write_scan.txt
  echo "FAIL: write/mutation-path token found"
  exit 1
else
  echo "PASS: no write/mutation-path token in Phase 18D package"
fi
rm -f /tmp/phase18d_write_scan.txt

echo
echo "PASS: no Canvas mutations"
