#!/usr/bin/env bash
set -u

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

echo "Running Phase 27 tests..."

P=apps/unified-weekly-production/data/phase26-demo.json
S=fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json
S_STALE=fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot-stale.json
S_EXPIRED=fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot-expired.json
T=$(mktemp -d "${TMPDIR:-/tmp}/phase27.XXXXXX")
trap 'rm -rf "$T"' EXIT
O="$T/phase27.json"
LEDGER="$T/ledger.db"

# --- fixture hygiene: the expectedStatus/conflict forcing pattern must be gone ---
if grep -q "expectedStatus" "$S"; then
  fail "fixture still contains expectedStatus (forces production classification)"
else
  pass "fixture contains no expectedStatus field"
fi
if grep -q '"conflict"[[:space:]]*:[[:space:]]*true' "$S"; then
  fail "fixture still contains a conflict:true forcing field"
else
  pass "fixture contains no conflict:true forcing field"
fi

# --- build: real production behavior ---
python3 scripts/canvas_llm_phase27/phase27_readiness.py build --week Q1W5 \
  --phase26-packet "$P" --snapshot "$S" --output "$O" --ledger "$LEDGER" \
  >"$T/build.txt" 2>&1 && pass "build produces a manifest" || { cat "$T/build.txt"; fail "build failed"; }

python3 scripts/canvas_llm_phase27/validate_phase27.py "$O" >"$T/validate.txt" 2>&1
if [[ $? -eq 0 ]]; then pass "validate passes on a real build"; else cat "$T/validate.txt"; fail "validate failed on a real build"; fi
grep -q '^PASS: manifest.preview' "$T/validate.txt" && pass "validate reports manifest preview PASS" || fail "validate preview PASS line missing"

python3 scripts/canvas_llm_phase27/phase27_readiness.py compare --manifest "$O" --snapshot "$S" \
  >"$T/compare.txt" 2>&1
if [[ $? -eq 0 ]]; then pass "compare recomputes and matches a real build"; else cat "$T/compare.txt"; fail "compare failed on a real build"; fi

# --- negative: compare/validate/build must not be no-ops ---
python3 scripts/canvas_llm_phase27/phase27_readiness.py compare \
  --manifest "$T/does-not-exist.json" --snapshot "$T/does-not-exist2.json" >/dev/null 2>&1
if [[ $? -ne 0 ]]; then pass "compare fails nonzero on nonexistent inputs"; else fail "compare is a no-op: nonexistent inputs returned 0"; fi

python3 scripts/canvas_llm_phase27/phase27_readiness.py validate --manifest "$T/does-not-exist.json" >/dev/null 2>&1
if [[ $? -ne 0 ]]; then pass "validate fails nonzero on nonexistent manifest"; else fail "validate is a no-op: nonexistent manifest returned 0"; fi

python3 - "$O" "$T/tampered.json" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
payload = json.loads(open(src, encoding="utf-8").read())
for item in payload["safetyDiff"]:
    if item["objectId"] == "language-arts":
        item["comparisonStatus"] = "UNCHANGED"
json.dump(payload, open(dst, "w", encoding="utf-8"))
PY
python3 scripts/canvas_llm_phase27/validate_phase27.py "$T/tampered.json" >/dev/null 2>&1
if [[ $? -ne 0 ]]; then pass "validate fails when safetyDiff is tampered (does not trust stored counters)"; else fail "validate trusted a tampered manifest"; fi

python3 scripts/canvas_llm_phase27/phase27_readiness.py compare --manifest "$T/tampered.json" --snapshot "$S" >/dev/null 2>&1
if [[ $? -ne 0 ]]; then pass "compare fails when safetyDiff is tampered"; else fail "compare did not detect tampering"; fi

# --- all seven Safety Diff states are genuinely computed ---
python3 - "$O" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
statuses = {item["comparisonStatus"] for item in payload["safetyDiff"]}
required = {"CREATE", "UPDATE", "UNCHANGED", "BLOCKED", "CONFLICT", "OMIT", "DELETE_CANDIDATE"}
missing = required - statuses
assert not missing, f"missing statuses: {missing}"
assert payload["deploymentManifestV1"]["executable"] is False
assert payload["deploymentManifestV1"]["mode"] == "preview-only"
assert all(op["executable"] is False for op in payload["deploymentManifestV1"]["operations"])
print("PASS all seven Safety Diff states present with executable=false throughout")
PY
[[ $? -eq 0 ]] && pass "all seven Safety Diff states present (CREATE/UPDATE/UNCHANGED/BLOCKED/CONFLICT/OMIT/DELETE_CANDIDATE)" || fail "not all Safety Diff states present"

# --- fix: prohibited statuses are never approvable via the CLI/manifest path ---
python3 - "$O" <<'PY'
import json, sys, tempfile, os
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.ledger import DeploymentLedger
from scripts.canvas_llm_phase27.approval_gate import approve_operation, is_approved, ApprovalRejectedError

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
manifest = payload["deploymentManifestV1"]
by_status = {}
for item in payload["safetyDiff"]:
    by_status.setdefault(item["comparisonStatus"], item)
required = {"CONFLICT", "BLOCKED", "OMIT", "DELETE_CANDIDATE"}
assert required <= set(by_status), f"fixture missing prohibited-status coverage: {required - set(by_status)}"

tmp = tempfile.mkdtemp()
ledger = DeploymentLedger(os.path.join(tmp, "prohibited.db"))
for status, item in by_status.items():
    if status not in required:
        continue
    try:
        approve_operation(ledger, item, manifest["packetRevision"], manifest["targetSnapshotId"], manifest["targetSnapshotFreshness"], "owen")
        raise AssertionError(f"{item['objectId']} ({status}) was approvable")
    except ApprovalRejectedError:
        pass
    assert not is_approved(ledger, item["objectId"], manifest["packetRevision"], manifest["targetSnapshotId"])
ledger.close()
print("PASS prohibited statuses (CONFLICT/BLOCKED/OMIT/DELETE_CANDIDATE) are never approvable, no record created")
PY
[[ $? -eq 0 ]] && pass "CONFLICT, BLOCKED (incl. archived-course/due-time), OMIT, and DELETE_CANDIDATE are never approvable" || fail "a prohibited status was approvable"

# --- fix: system validation vs demo manifest readiness are distinct signals ---
python3 - "$O" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
manifest = payload["deploymentManifestV1"]
assert "systemValidationStatus" in manifest, "systemValidationStatus missing from manifest"
assert manifest["systemValidationStatus"] == "PASS", f"expected PASS, got {manifest['systemValidationStatus']}"
assert manifest["overallReadiness"] == "blocked", "expected demo manifest readiness to be blocked (real conflict/blocked content present)"
assert manifest["systemValidationStatus"] != manifest["overallReadiness"].upper(), (
    "systemValidationStatus and overallReadiness must be able to differ -- "
    "they answer different questions (software correctness vs this week's content readiness)"
)
print("PASS system validation (software correctness) and demo manifest readiness (this week's content) are distinct and both correct")
PY
[[ $? -eq 0 ]] && pass "system validation and demo manifest readiness are distinct, independently-correct signals" || fail "system validation / demo readiness distinction failed"

# --- fix: resource verification reuses real Phase 25/26 resolvedResources data ---
python3 - "$O" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
check = next(h for h in payload["healthChecks"] if h["check"] == "resource-link-verification")
assert check["status"] != "NOT_APPLICABLE", "resource-link-verification is still a stub (NOT_APPLICABLE)"
assert "verified" in check["detail"] or "missing" in check["detail"], f"detail does not reflect real classification: {check['detail']}"
resolved = payload["phase26Packet"]["resourceResolution"]["resolvedResources"]
assert len(resolved) > 0, "phase26 demo packet has no resolvedResources to classify"
print(f"PASS resource-link-verification classifies {len(resolved)} real Phase 25/26 resolved resources: {check['detail']}")
PY
[[ $? -eq 0 ]] && pass "resource verification reuses real Phase 25/26 resolvedResources state (not NOT_APPLICABLE)" || fail "resource verification is still a stub"

# --- fix: blocked-dependency propagation is visible in the dependency summary ---
python3 - "$O" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
manifest = payload["deploymentManifestV1"]
la_worksheet = next(item for item in payload["safetyDiff"] if item["objectId"] == "la-worksheet-page")
assert la_worksheet["comparisonStatus"] == "BLOCKED", "la-worksheet-page should be BLOCKED via dependency propagation"
assert "la-worksheet-page" in manifest["dependencies"]["blocked"], (
    "la-worksheet-page is BLOCKED but missing from manifest.dependencies.blocked -- "
    "the dependency summary must reflect propagated blocks, not just cycles/missing edges"
)
print("PASS propagated blocked dependency (la-worksheet-page) is visible in manifest.dependencies.blocked")
PY
[[ $? -eq 0 ]] && pass "blocked-dependency propagation is visible in manifest.dependencies.blocked" || fail "propagated block missing from dependency summary"

# --- canonicalization and distinct hash domains ---
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.canonicalize import (
    body_hash, metadata_hash, placement_hash, full_operation_hash, canonical_hash,
)

base = {"title": "T", "body": "<p>Body</p>", "publication": "published", "module": "M", "position": 1}
assert metadata_hash(dict(base, title="T2")) != metadata_hash(base)
assert body_hash(dict(base, title="T2")) == body_hash(base)
assert body_hash(dict(base, body="<p>Different</p>")) != body_hash(base)
assert metadata_hash(dict(base, body="<p>Different</p>")) == metadata_hash(base)
assert placement_hash(dict(base, position=2)) != placement_hash(base)
assert body_hash(dict(base, position=2)) == body_hash(base)
assert full_operation_hash(base, dependencies=["a", "b"]) != full_operation_hash(base, dependencies=["a"])
assert canonical_hash(dict(base, updatedAt="2026-01-01T00:00:00Z")) == canonical_hash(base)
assert canonical_hash(dict(base, localPath="/Users/owen/x")) == canonical_hash(base)
assert canonical_hash("<div>\n  <p>Practice</p>\n</div>") == canonical_hash("<div><p>Practice</p></div>")
assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
print("PASS canonicalization hash independence")
PY
[[ $? -eq 0 ]] && pass "body/metadata/placement/full-operation hashes are independently provable" || fail "hash independence assertions failed"

# --- canvas snapshot validation rejects unsafe content ---
python3 - <<'PY'
import sys, json, tempfile, os
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.canvas_snapshot import load_snapshot, SnapshotValidationError

def expect_reject(raw, label):
    fd, path = tempfile.mkstemp(suffix=".json", dir="fixtures/canvas-llm/phase-27")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh)
    try:
        load_snapshot(path)
        raise AssertionError(f"{label} was not rejected")
    except SnapshotValidationError:
        pass
    finally:
        os.unlink(path)

expect_reject(
    {"snapshotId": "s", "generatedAt": "2026-01-01T00:00:00Z",
     "source": "https://canvas.example.invalid/", "remoteObjects": [{"canvasId": "1", "studentId": "x"}]},
    "student data",
)
expect_reject(
    {"snapshotId": "s", "generatedAt": "2026-01-01T00:00:00Z",
     "source": "http://localhost/", "remoteObjects": []},
    "unsafe host",
)
print("PASS snapshot validation rejects forbidden fields and unsafe hosts")
PY
[[ $? -eq 0 ]] && pass "Canvas snapshot validation rejects student data and unsafe hosts" || fail "snapshot validation did not reject unsafe content"

# --- canonical object model rejects malformed/dangerous input ---
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.models import DeployableObject, SafetyDiffItem, ModelValidationError

def expect_reject(factory, label):
    try:
        factory()
        raise AssertionError(f"{label} was not rejected")
    except ModelValidationError:
        pass

expect_reject(
    lambda: DeployableObject(localObjectId="x", objectType="not-a-real-type", weekCode="Q1W5",
                              subject="math", courseRef="26404", canonicalTitle="T",
                              canonicalBody="B", contentHash="h"),
    "invalid objectType",
)
expect_reject(
    lambda: DeployableObject(localObjectId="x", objectType="page", weekCode="Q1W5", subject="math",
                              courseRef="26404", canonicalTitle="T",
                              canonicalBody="token=Bearer abc123", contentHash="h"),
    "credential-like content",
)
expect_reject(
    lambda: SafetyDiffItem(objectId="x", objectType="page", localTitle="T", targetCourse="26404",
                            matchedCanvasId=None, matchReason=None, matchConfidence=1.0,
                            comparisonStatus="UPDATE", fieldDiffs=[], contentHashBefore="a",
                            contentHashAfter="b", metadataHashBefore="a", metadataHashAfter="b",
                            placementHashBefore="a", placementHashAfter="b", sourceRevision=1,
                            approvalState="Needs Review", blockers=[], dependencies=[],
                            driftCategory="no drift", recommendedAction="Review", executable=True),
    "executable=True",
)
print("PASS canonical object model rejects malformed and unsafe input")
PY
[[ $? -eq 0 ]] && pass "canonical object model rejects invalid objectType, credentials, and executable=True" || fail "model validation did not reject unsafe input"

# --- deterministic matching: cross-course rejection, ambiguity -> CONFLICT ---
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.matching import match_object

local = {"localObjectId": "x", "courseRef": "999", "objectType": "page", "title": "Same Title"}
cross_course = [{"canvasId": "1", "courseRef": "111", "objectType": "page", "title": "Same Title"}]
result = match_object(local, cross_course)
assert result.status == "unresolved", "cross-course candidate must never match"

ambiguous = [
    {"canvasId": "1", "courseRef": "999", "objectType": "page", "title": "Same Title"},
    {"canvasId": "2", "courseRef": "999", "objectType": "page", "title": "Same Title"},
]
result2 = match_object(local, ambiguous)
assert result2.status == "conflict", "ambiguous candidates must never be auto-selected"
print("PASS matching: cross-course rejected, ambiguity becomes conflict")
PY
[[ $? -eq 0 ]] && pass "matching rejects cross-course candidates and never auto-selects ambiguous matches" || fail "matching safety properties failed"

# --- dependency graph: cycle detection, blocked propagation ---
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.dependency_graph import build_dependency_graph

cyclic = build_dependency_graph(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])
assert cyclic.cycles, "cycle must be detected"
assert {"a", "b", "c"} <= cyclic.blocked, "cycle members must be blocked"

propagated = build_dependency_graph(["a", "b"], [("a", "b")], initially_blocked={"b"})
assert "a" in propagated.blocked, "blocked dependency must propagate to dependents"

clean = build_dependency_graph(["a", "b"], [("a", "b")])
assert clean.order == ["b", "a"], f"topological order must place dependency before dependent, got {clean.order}"
print("PASS dependency graph: cycles rejected, blocking propagates, order is deterministic")
PY
[[ $? -eq 0 ]] && pass "dependency graph detects cycles, propagates blocking, and orders deterministically" || fail "dependency graph assertions failed"

# --- SQLite ledger: restart persistence, quarantine, approval invalidation ---
python3 - "$T" <<'PY'
import sys, os
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.ledger import DeploymentLedger, DEFAULT_LEDGER_PATH
from scripts.canvas_llm_phase27.approval_gate import approve_operation, is_approved, revoke_operation, ApprovalRejectedError

assert DEFAULT_LEDGER_PATH.is_absolute(), "DEFAULT_LEDGER_PATH must be absolute (cwd-independent)"

db_path = os.path.join(sys.argv[1], "ledger-unit.db")

l1 = DeploymentLedger(db_path)
l1.record_snapshot_import("snap-1", "fixture", "2026-07-11T00:00:00Z")
l1.upsert_manifest("m1", "Q1W5", 3, "preview-only", "hash-a")
count_before = l1.event_count()
l1.close()

l2 = DeploymentLedger(db_path)
assert l2.event_count() == count_before, "events did not persist across restart"
assert l2.integrity_check()

approve_operation(l2, {"objectId": "obj-1", "comparisonStatus": "UPDATE", "blockers": []}, 3, "snap-1", "fresh", "owen")
assert is_approved(l2, "obj-1", 3, "snap-1")
assert not is_approved(l2, "obj-1", 4, "snap-1"), "approval survived a manifest revision change"
assert not is_approved(l2, "obj-1", 3, "snap-2"), "approval survived a snapshot change"

# Every prohibited category must reject AND leave no approval record behind.
# DELETE_CANDIDATE previously had empty blockers and was NOT in
# NON_APPROVABLE_STATUSES, so it was silently approvable -- a real bug fixed
# in this recovery.
prohibited_cases = [
    ("obj-conflict", "CONFLICT", []),
    ("obj-blocked-generic", "BLOCKED", []),
    ("obj-blocked-archived", "BLOCKED", ["target course 21957 is archived"]),
    ("obj-blocked-due-time", "BLOCKED", ["Canvas assignment due-time convention remains owner-unresolved"]),
    ("obj-omit", "OMIT", ["history assignment generation is disabled by canonical policy"]),
    ("obj-delete-candidate", "DELETE_CANDIDATE", []),
]
for object_id, bad_status, blockers in prohibited_cases:
    try:
        approve_operation(l2, {"objectId": object_id, "comparisonStatus": bad_status, "blockers": blockers}, 3, "snap-1", "fresh", "owen")
        raise AssertionError(f"{object_id} ({bad_status}) was approvable")
    except ApprovalRejectedError:
        pass
    assert not is_approved(l2, object_id, 3, "snap-1"), f"{object_id} ({bad_status}) left an approval record despite rejection"

try:
    approve_operation(l2, {"objectId": "obj-y", "comparisonStatus": "UPDATE", "blockers": []}, 3, "snap-1", "stale", "owen")
    raise AssertionError("stale-snapshot approval succeeded")
except ApprovalRejectedError:
    pass

# Regression: approve/revoke/approve back-to-back (same wall-clock second)
# must never collide on a primary key -- this previously raised
# sqlite3.IntegrityError because approvedAt only has second resolution.
for _ in range(3):
    approve_operation(l2, {"objectId": "obj-rapid", "comparisonStatus": "UPDATE", "blockers": []}, 3, "snap-1", "fresh", "owen")
    revoke_operation(l2, "obj-rapid", 3, "snap-1")
approve_operation(l2, {"objectId": "obj-rapid", "comparisonStatus": "UPDATE", "blockers": []}, 3, "snap-1", "fresh", "owen")
assert is_approved(l2, "obj-rapid", 3, "snap-1"), "rapid approve/revoke cycling left object unapproved"
l2.close()

with open(db_path, "wb") as fh:
    fh.write(b"not a sqlite file")
l3 = DeploymentLedger(db_path)
quarantined = l3._conn.execute("SELECT COUNT(*) FROM quarantine_events").fetchone()[0]
assert quarantined >= 1, "corrupt ledger was not quarantined"
l3.close()
print("PASS ledger: restart persistence, revision/snapshot-bound approval invalidation, quarantine")
PY
[[ $? -eq 0 ]] && pass "ledger persists across restart, invalidates approvals on revision/snapshot change, quarantines corruption" || fail "ledger assertions failed"

python3 scripts/canvas_llm_phase27/phase27_readiness.py ledger-status --ledger "$LEDGER" >"$T/ledger-status.txt" 2>&1
if [[ $? -eq 0 ]]; then pass "ledger-status inspects the real SQLite ledger"; else cat "$T/ledger-status.txt"; fail "ledger-status failed"; fi
python3 scripts/canvas_llm_phase27/phase27_readiness.py ledger-status --ledger "$T/does-not-exist.db" >/dev/null 2>&1
if [[ $? -ne 0 ]]; then pass "ledger-status fails nonzero for a missing ledger"; else fail "ledger-status is a no-op for a missing ledger"; fi

# --- health-check and export CLI, and cwd-independence regressions ---
python3 scripts/canvas_llm_phase27/phase27_readiness.py health-check --manifest "$O" >"$T/health.txt" 2>&1
if [[ $? -eq 0 ]]; then pass "health-check runs deterministic checks and exits 0"; else cat "$T/health.txt"; fail "health-check failed"; fi

python3 scripts/canvas_llm_phase27/phase27_readiness.py export --manifest "$O" --output-root "$T/exports" >"$T/export.txt" 2>&1
if [[ $? -eq 0 ]]; then pass "export writes a real package"; else cat "$T/export.txt"; fail "export failed"; fi

python3 - "$T/exports" <<'PY'
import sys
sys.path.insert(0, ".")
from pathlib import Path
from scripts.canvas_llm_phase27.export_package import REQUIRED_EXPORT_FILES, validate_export_package
export_dir = Path(sys.argv[1]) / "Q1W5"
for name in REQUIRED_EXPORT_FILES:
    assert (export_dir / name).exists(), f"missing export file: {name}"
problems = validate_export_package(export_dir)
assert not problems, f"export package validation problems: {problems}"
print("PASS export package: all 11 files present, no forbidden content")
PY
[[ $? -eq 0 ]] && pass "export package contains all 11 required files with no credentials/paths/student data" || fail "export package validation failed"

# Regression: DEFAULT_LEDGER_PATH / DEFAULT_EXPORT_ROOT must be absolute.
# Both were previously relative, so Phase 26's `serve` (which chdirs into
# apps/unified-weekly-production before Phase 27 code runs) silently wrote
# the ledger and export package into the wrong directory.
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.ledger import DEFAULT_LEDGER_PATH
from scripts.canvas_llm_phase27.export_package import DEFAULT_EXPORT_ROOT
assert DEFAULT_LEDGER_PATH.is_absolute(), "DEFAULT_LEDGER_PATH is relative (cwd-dependent)"
assert DEFAULT_EXPORT_ROOT.is_absolute(), "DEFAULT_EXPORT_ROOT is relative (cwd-dependent)"
print("PASS default ledger/export paths are absolute and cwd-independent")
PY
[[ $? -eq 0 ]] && pass "default ledger and export paths are absolute (cwd-independent)" || fail "default paths regressed to being cwd-dependent"

python3 - "$O" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
provenance = payload["deploymentManifestV1"]["provenance"]
for entry in provenance:
    assert not entry["sourceRef"].startswith("/"), f"provenance leaks an absolute local path: {entry}"
print("PASS manifest provenance stores repo-relative paths, not absolute local paths")
PY
[[ $? -eq 0 ]] && pass "manifest provenance never contains an absolute local path" || fail "manifest provenance leaks a local path"

# --- transport boundary: every mutation method rejects, non-GET rejects ---
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.transport import (
    DisabledCanvasTransport, FakeCanvasTransport, MutationNotAllowedError,
)

mutating = [
    "create_page", "update_page", "delete_page", "create_assignment", "update_assignment",
    "delete_assignment", "create_module", "update_module", "create_module_item",
    "update_module_item", "create_announcement", "upload_file", "publish_object",
]
for transport in (DisabledCanvasTransport(), FakeCanvasTransport()):
    for method in mutating:
        try:
            getattr(transport, method)()
            raise AssertionError(f"{type(transport).__name__}.{method} did not raise")
        except MutationNotAllowedError:
            pass
    for http_method in ("POST", "PUT", "PATCH", "DELETE"):
        try:
            transport.request(http_method, "https://canvas.example.invalid/x")
            raise AssertionError(f"{type(transport).__name__} allowed {http_method}")
        except MutationNotAllowedError:
            pass
print("PASS transport boundary rejects every mutation method and non-GET HTTP verb")
PY
[[ $? -eq 0 ]] && pass "every Phase 27 transport rejects all mutation methods and non-GET HTTP verbs" || fail "a transport allowed a mutation"

# --- freshness: fresh/aging/stale/expired classification ---
python3 - "$S" "$S_STALE" "$S_EXPIRED" <<'PY'
import sys, json
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.freshness import classify_freshness, blocks_readiness

fresh_ts = json.load(open(sys.argv[1]))["generatedAt"]
stale_ts = json.load(open(sys.argv[2]))["generatedAt"]
expired_ts = json.load(open(sys.argv[3]))["generatedAt"]

assert classify_freshness(fresh_ts) in {"fresh", "aging"}
assert classify_freshness(stale_ts) in {"stale", "expired"}
assert blocks_readiness(classify_freshness(stale_ts))
assert classify_freshness(expired_ts) == "expired"
assert blocks_readiness(classify_freshness(expired_ts))
assert classify_freshness("not-a-timestamp") == "unknown"
assert blocks_readiness("unknown")
print("PASS freshness classification blocks readiness for stale/expired/unknown snapshots")
PY
[[ $? -eq 0 ]] && pass "stale/expired/unknown snapshots are classified and block readiness" || fail "freshness classification failed"

# --- .local hygiene ---
if git ls-files '.local/*' | grep -q .; then
  fail ".local output is tracked by git"
else
  pass ".local output is not tracked by git"
fi

warn "Canvas assignment due-time convention remains owner-unresolved"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -eq 0 ]]
