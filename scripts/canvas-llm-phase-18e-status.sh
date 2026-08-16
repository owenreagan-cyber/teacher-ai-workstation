#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); echo "PASS: $1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); echo "WARN: $1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); echo "FAIL: $1"; }

require_file() {
  if [[ -f "$1" ]]; then pass "file exists: $1"; else fail "missing file: $1"; fi
}

PKG="scripts/canvas_llm_phase18e"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-phase-18e-owner-policy-execution-preconditions.md"
TEST="tests/canvas-llm-phase-18e-owner-policy-execution-preconditions-test.sh"

echo "Canvas LLM Phase 18E: Owner Policy, Approval-Bound Preconditions & Write Prep"
echo "-----------------------------------------------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/contracts.py"
require_file "$PKG/policy.py"
require_file "$PKG/preconditions.py"
require_file "$PKG/validation.py"
require_file "$PKG/adapter.py"
require_file "$PKG/snapshot_adapter.py"
require_file "$CLI"
require_file "$DOC"
require_file "$TEST"
require_file "scripts/canvas_llm_phase18d/deployment.py"
require_file "scripts/canvas_llm_phase18d/contracts.py"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "Phase 18E modules compile"
else
  fail "Phase 18E modules failed to compile"
fi

echo
echo "Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck 2>&1)"; then
  echo "$selfcheck_output"
  pass "Phase 18E self-check passed"
else
  echo "$selfcheck_output"
  fail "Phase 18E self-check failed"
fi

echo
echo "Import-Safe Contract Boundaries"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18e.contracts import ExecutionPreconditionReport, WriterRequest, ReadinessState
from scripts.canvas_llm_phase18e.policy import OwnerCanvasPolicy, default_policy, due_timestamp, policy_hash
from scripts.canvas_llm_phase18e.preconditions import evaluate_preconditions
from scripts.canvas_llm_phase18e.adapter import build_writer_requests
for mod in ("canvas_writer", "canvas_connector",
            "scripts.canvas_llm_phase22.phase22_workstation",
            "scripts.canvas_llm_phase22.weekly_agenda_publisher",
            "scripts.canvas_llm_phase26.pipeline"):
    assert mod not in sys.modules, mod
print("OK")
PY
then
  pass "pure Phase 18E modules import without execution modules"
else
  fail "Phase 18E pulled execution modules"
fi

echo
echo "Owner Policy + Precondition Behavior"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord, CanvasSnapshot, DeploymentIntent, DryRunPacket, SnapshotObject,
)
from scripts.canvas_llm_phase18e.policy import OwnerCanvasPolicy, default_policy, due_timestamp, policy_hash
from scripts.canvas_llm_phase18e.preconditions import evaluate_preconditions, record_approval_bindings
from scripts.canvas_llm_phase18e.adapter import build_writer_requests
from scripts.canvas_llm_phase27.canonicalize import canonical_hash

POLICY = OwnerCanvasPolicy(publish_state="resolved", publish_decision="published")
CFG = {"math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"}}

# --- policy determinism + DST ---
assert policy_hash(default_policy()) == policy_hash(default_policy())
assert due_timestamp("2026-08-24", "America/New_York") == "2026-08-24T23:59:00-04:00"
assert due_timestamp("2026-01-15", "America/New_York") == "2026-01-15T23:59:00-05:00"
assert due_timestamp("2026-08-21", "America/New_York") == "2026-08-21T23:59:00-04:00"  # Friday stays Friday
try:
    due_timestamp("", "America/New_York"); raise AssertionError("blank date did not block")
except ValueError:
    pass

def intent(op, oid="", assigned="2026-08-24", blockers=None, desired=None):
    ds = {
        "title": "Math Homework — Monday",
        "course_id": "M",
        "assignment_group_id": "MA",
        "assigned_date": assigned,
        "due_at": assigned,
        "timezone": "America/New_York",
    }
    if desired: ds.update(desired)
    return DeploymentIntent(
        id=oid or f"i-{op}-1",
        operation=op,
        object_type="assignment",
        course="math",
        canonical_source="canonical_rule",
        target_locator="math-homework-q1w3-monday",
        desired_state=ds,
        provenance=[{"sourceType": "canonical-weekly-plan", "sourceRef": "wp-Q1W3", "details": "x"}],
        preconditions={"week_code": "Q1W3", "expected_object_id": "a1", "expected_current_hash": "h1",
                       "expected_last_updated": "t1"},
        blockers=blockers or [],
    )

def packet(*intents):
    p = DryRunPacket(
        week_code="Q1W3", canonical_plan_identity="wp-Q1W3", canonical_revision="wp-Q1W3",
        preview_identity="preview-abc", preview_hash="abc123", snapshot_identity="snap-1",
        snapshot_hash="snap123", target_environment="sandbox", intents=list(intents),
    )
    p.packet_hash = canonical_hash({
        "week_code": p.week_code, "canonical_revision": p.canonical_revision,
        "preview_hash": p.preview_hash, "snapshot_hash": p.snapshot_hash,
        "target_environment": p.target_environment, "intents": [i.to_dict() for i in p.intents],
    })
    return p

def approval(p, policy, ids):
    b = record_approval_bindings(packet=p, policy=policy, canvas_config=CFG)
    return ApprovalRecord(packet_hash=p.packet_hash, reviewer="Owner", approved_at="2026-07-25T00:00:00Z",
                          scope="full-week", approved_intent_ids=ids, preconditions=b)

# safe CREATE
c = intent("CREATE")
p = packet(c)
a = approval(p, POLICY, ["i-CREATE-1"])
snap = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[])
rep = evaluate_preconditions(p, c, a, POLICY, canvas_config=CFG, snapshot=snap)
assert rep.readiness == "READY_FOR_EXECUTION_REVIEW", rep.readiness
assert build_writer_requests(p, a, POLICY, canvas_config=CFG, snapshot=snap)

# safe UPDATE
obj = SnapshotObject(object_id="a1", object_type="assignment", course="math",
                     locator="math-homework-q1w3-monday", title="Math Homework — Monday",
                     current_state={"course_id": "M", "title": "Math Homework — Monday", "updated_at": "t1"},
                     content_hash="h1", managed=True, baseline_hash="h1")
u = intent("UPDATE")
pu = packet(u)
au = approval(pu, POLICY, ["i-UPDATE-1"])
snapu = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[obj])
repu = evaluate_preconditions(pu, u, au, POLICY, canvas_config=CFG, snapshot=snapu)
assert repu.readiness == "READY_FOR_EXECUTION_REVIEW", (repu.readiness, repu.blockers)
assert build_writer_requests(pu, au, POLICY, canvas_config=CFG, snapshot=snapu)

# publish policy unresolved blocks
upol = OwnerCanvasPolicy(publish_state="unresolved")
au_pub = approval(pu, upol, ["i-UPDATE-1"])
rep_pub = evaluate_preconditions(pu, u, au_pub, upol, canvas_config=CFG, snapshot=snapu)
assert rep_pub.readiness == "BLOCKED_PUBLISH_POLICY", (rep_pub.readiness, rep_pub.blockers)

# stale live state blocks
obj_stale = SnapshotObject(object_id="a1", object_type="assignment", course="math",
                           locator="math-homework-q1w3-monday", title="Math Homework — Monday",
                           current_state={"course_id": "M", "title": "Math Homework — Monday", "updated_at": "t1"},
                           content_hash="DIFFERENT", managed=True, baseline_hash="h1")
snap_stale = CanvasSnapshot(week_code="Q1W3", snapshot_id="snap-1", objects=[obj_stale])
rep_stale = evaluate_preconditions(pu, u, au, POLICY, canvas_config=CFG, snapshot=snap_stale)
assert rep_stale.readiness == "BLOCKED_STALE_CANVAS", rep_stale.readiness

# config drift blocks
rep_cfg = evaluate_preconditions(pu, u, au, POLICY, canvas_config={"math": {"course_id": "X"}}, snapshot=snapu)
assert rep_cfg.readiness == "BLOCKED_CONFIG", rep_cfg.readiness

# policy change invalidates old approval
p2 = OwnerCanvasPolicy(publish_state="resolved", publish_decision="unpublished")
rep_pol = evaluate_preconditions(pu, u, au, p2, canvas_config=CFG, snapshot=snapu)
assert rep_pol.readiness in ("BLOCKED_APPROVAL", "BLOCKED_PUBLISH_POLICY"), rep_pol.readiness
assert any("policy:hash_mismatch" in b for b in rep_pol.blockers)

# provenance required
u_noprov = intent("UPDATE", oid="i-update-noprov")
u_noprov.provenance = []
pu_noprov = packet(u_noprov)
au_noprov = approval(pu_noprov, POLICY, ["i-update-noprov"])
rep_noprov = evaluate_preconditions(pu_noprov, u_noprov, au_noprov, POLICY, canvas_config=CFG, snapshot=snapu)
assert rep_noprov.readiness == "BLOCKED_PROVENANCE", rep_noprov.readiness

# DELETE rejected
d = intent("DELETE", oid="i-delete-1")
pd = packet(d)
ad = approval(pd, POLICY, ["i-delete-1"])
rep_del = evaluate_preconditions(pd, d, ad, POLICY, canvas_config=CFG, snapshot=snap)
assert rep_del.readiness == "BLOCKED_WRITER_CONTRACT", rep_del.readiness
assert not build_writer_requests(pd, ad, POLICY, canvas_config=CFG, snapshot=snap)

# NO_CHANGE -> zero writer requests
n = intent("NO_CHANGE", oid="i-nc-1")
pn = packet(n)
an = approval(pn, POLICY, ["i-nc-1"])
assert build_writer_requests(pn, an, POLICY, canvas_config=CFG, snapshot=snap) == []

# blocked intent -> zero writer requests
b = intent("CREATE", oid="i-blocked-1", blockers=["ownership_uncertain"])
pb = packet(b)
ab = approval(pb, POLICY, ["i-blocked-1"])
assert build_writer_requests(pb, ab, POLICY, canvas_config=CFG, snapshot=snap) == []

print("OK")
PY
then
  pass "owner policy / preconditions / adapter behavior verified"
else
  fail "owner policy / preconditions / adapter behavior failed"
fi

echo
echo "No Canvas Write Path / Mutation HTTP / Token Use"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request|attempt_live_write' \
  "$PKG"/*.py >/tmp/canvas_phase_18e_write_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18e_write_scan.txt
  fail "Canvas write/mutation-path token found in Phase 18E package"
else
  pass "no Canvas write/mutation-path token in Phase 18E package"
fi
rm -f /tmp/canvas_phase_18e_write_scan.txt

if grep -RInE 'CANVAS_TOKEN|CANVAS_API_TOKEN|os\.environ.*TOKEN|getenv\(.*TOKEN' "$PKG"/*.py >/tmp/canvas_phase_18e_token_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_18e_token_scan.txt
  fail "Canvas token consumption found in Phase 18E package"
else
  pass "no Canvas token consumption in Phase 18E package"
fi
rm -f /tmp/canvas_phase_18e_token_scan.txt

echo
echo "Write Gate Remains Closed"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase22.write_gate import attempt_write, evaluate_write, write_gate_blocks_execution
decision = evaluate_write("create", "page", "p-1", approved=True, approved_by="Teacher", approved_at="2026-07-25T00:00:00Z")
assert attempt_write(decision).gate_state == "BLOCKED"
assert write_gate_blocks_execution()
print("OK")
PY
then
  pass "existing write gate remains closed (execution BLOCKED)"
else
  fail "write gate execution unexpectedly open"
fi

echo
echo "CLI Wiring"
echo "----------------------------------------"
if grep -q 'canvas-llm-phase-18e-status' bin/chief-of-staff; then
  pass "chief-of-staff dispatches Phase 18E status"
else
  fail "chief-of-staff missing Phase 18E dispatch"
fi

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
