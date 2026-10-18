#!/usr/bin/env bash
set -euo pipefail
# Pin "today" to 2026-08-19 (Q1W5, the week the synthetic fixtures plan) so the result does not depend on the
# date the test runs. Read only by the test-clock hooks; unset in real use.
export TAW_TODAY=2026-08-19

echo "Running Canvas launcher manifest-approval tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LAUNCH="scripts/canvas_llm_phase22/canvas_launcher.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-approval.XXXXXX")"
trap 'rm -rf "$T"' EXIT

python3 -m py_compile "$LAUNCH"

python3 - "$T" <<'PY'
import contextlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_phase22 import canvas_launcher as launcher

tmp = Path(sys.argv[1])
man_dir = tmp / "manifest"
man_dir.mkdir()
backup_dir = tmp / "backups"

# Seed a temp copy of the real Q1W5 manifest (which is currently unapproved) so
# the real repo manifest is never touched by these tests.
src = launcher.load_manifest("Q1W5")
man_path = man_dir / "q1w5-corrective-manifest.json"
man_path.write_text(json.dumps(src, indent=2))
original_text = man_path.read_text()


def run(cmd):
    """Run an approval command with stdout captured, and assert zero Canvas calls."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), \
         mock.patch.object(launcher.credentials, "load_credentials",
                           side_effect=AssertionError("network call made")), \
         mock.patch.object(launcher, "_fetch_live_inventory",
                           side_effect=AssertionError("network call made")):
        rc = cmd()
    return rc, out.getvalue()


with mock.patch.object(launcher, "MANIFESTS", {"Q1W5": man_path}), \
     mock.patch.object(launcher, "BACKUP_DIR", backup_dir):

    # approve works
    rc, out = run(lambda: launcher.command_approve("Q1W5"))
    assert rc == 0, out
    assert '"teacherApproved": true' in out, out
    assert "CANVAS_TOKEN" not in out and "token" not in out.lower(), out
    approved = json.loads(man_path.read_text())
    ap = approved["approval"]
    assert ap["teacherApproved"] is True
    assert ap["approvedBy"] == "Owen Reagan"
    assert ap["approvedAt"], "approvedAt must be non-empty"
    ts = datetime.fromisoformat(ap["approvedAt"])
    assert ts.tzinfo is not None and ts.utcoffset() is not None, "approvedAt must be timezone-aware"
    # all other content preserved
    assert approved["weekCode"] == src["weekCode"]
    assert approved["title"] == src["title"]
    assert approved["mode"] == src["mode"]
    assert approved["actions"] == src["actions"]
    print("PASS approve works")

    # original manifest backup is created (byte-identical to pre-approval state)
    backups = list(backup_dir.glob("approval-q1w5-corrective-manifest-*.json"))
    assert len(backups) == 1, backups
    assert backups[0].read_text() == original_text
    print("PASS original manifest backup is created")

    # unapprove works
    rc, out = run(lambda: launcher.command_unapprove("Q1W5"))
    assert rc == 0, out
    assert '"teacherApproved": false' in out, out
    unapproved = json.loads(man_path.read_text())
    ap = unapproved["approval"]
    assert ap["teacherApproved"] is False
    assert ap["approvedBy"] is None
    assert ap["approvedAt"] is None
    assert unapproved["actions"] == src["actions"]
    print("PASS unapprove works")

# malformed JSON blocks without modifying the original
bad_path = man_dir / "bad-manifest.json"
bad_content = "{ this is not json "
bad_path.write_text(bad_content)
with mock.patch.object(launcher, "MANIFESTS", {"Q1W5": bad_path}), \
     mock.patch.object(launcher, "BACKUP_DIR", backup_dir):
    rc, out = run(lambda: launcher.command_approve("Q1W5"))
    assert rc == 1, out
    assert "BLOCKED" in out, out
    assert bad_path.read_text() == bad_content, "malformed manifest must be left unmodified"
print("PASS malformed JSON blocks without modifying the original")

# approval performs zero Canvas calls (proven by the side_effect guards above
# never tripping across approve/unapprove). Confirm no live client was built.
print("PASS approval performs zero Canvas calls")
PY

echo "PASS Canvas launcher manifest-approval tests complete"
