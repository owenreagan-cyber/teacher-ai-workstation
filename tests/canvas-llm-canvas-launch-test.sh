#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas launch wrapper and credential loader tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CRED="scripts/canvas_llm_phase22/canvas_credentials.py"
LAUNCH="scripts/canvas_llm_phase22/canvas_launcher.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-launch.XXXXXX")"
trap 'rm -rf "$T"' EXIT

python3 -m py_compile "$CRED" "$LAUNCH"
python3 "$CRED" self-test
python3 "$LAUNCH" self-test

# Proofs 1-4: credential precedence, fallback, missing/bad-permissions blocking.
python3 - "$T" <<'PY'
import sys
from pathlib import Path
from scripts.canvas_llm_phase22 import canvas_credentials as creds

tmp = Path(sys.argv[1])
env_file = tmp / "canvas.env"
env_file.write_text(
    "CANVAS_BASE_URL=https://file.example.com\nCANVAS_TOKEN=file-token\n"
)
env_file.chmod(0o600)

# 1. env credentials take precedence.
resolved = creds.resolve_credentials(
    env_file=env_file,
    environ={"CANVAS_BASE_URL": "https://env.example.com", "CANVAS_TOKEN": "env-token"},
)
assert resolved["CANVAS_TOKEN"] == "env-token", resolved
assert resolved["CANVAS_BASE_URL"] == "https://env.example.com", resolved
print("PASS env credentials take precedence")

# 2. private config loads when env is absent.
resolved = creds.resolve_credentials(env_file=env_file, environ={})
assert resolved["CANVAS_TOKEN"] == "file-token", resolved
assert resolved["CANVAS_BASE_URL"] == "https://file.example.com", resolved
print("PASS private config loads when env absent")

# 3. missing credentials block.
missing = tmp / "missing.env"
missing.write_text("CANVAS_BASE_URL=https://missing.example.com\n")
missing.chmod(0o600)
try:
    creds.resolve_credentials(env_file=missing, environ={})
except creds.CredentialError:
    print("PASS missing credentials block")
else:
    raise AssertionError("missing credentials did not block")

# 4. bad file permissions block.
bad = tmp / "bad.env"
bad.write_text("CANVAS_BASE_URL=https://bad.example.com\nCANVAS_TOKEN=bad-token\n")
bad.chmod(0o644)
assert creds.file_mode_is_secure(bad) is False
try:
    creds.resolve_credentials(env_file=bad, environ={})
except creds.CredentialError as exc:
    assert "bad-token" not in str(exc)
    print("PASS bad file permissions block")
else:
    raise AssertionError("unsafe permissions did not block")
PY

# Proof 5: token never appears in stdout/stderr.
SENTINEL="SUPERSECRETCANVASTOKEN_7f3a9b2c"
ENV_FILE="$T/leak.env"
printf 'CANVAS_BASE_URL=https://thalesacademy.instructure.com\nCANVAS_TOKEN=%s\n' "$SENTINEL" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
LEAK_OUT="$(python3 - "$ENV_FILE" <<'PY' 2>&1
import sys
from pathlib import Path
from scripts.canvas_llm_phase22 import canvas_credentials as creds
creds_val = creds.resolve_credentials(env_file=Path(sys.argv[1]), environ={})
print(creds.redacted_status(creds_val))
print("base url:", creds_val["CANVAS_BASE_URL"])
PY
)"
if printf '%s' "$LEAK_OUT" | grep -q "$SENTINEL"; then
    echo "FAIL: CANVAS_TOKEN leaked to stdout/stderr" >&2
    exit 1
fi
echo "PASS token never appears in stdout/stderr"

# Proof 6: launch cannot write without approval (blocks before any network).
# Hermetic: patches load_manifest to an unapproved manifest so this never runs
# the real launch path (which could otherwise reach live Canvas if a teacher
# has already approved the manifest).
python3 - <<'PY'
from unittest import mock
from scripts.canvas_llm_phase22 import canvas_launcher as launcher

unapproved = {
    "weekCode": "Q1W5",
    "approval": {"teacherApproved": False, "approvedBy": None},
    "actions": [],
}
with mock.patch.object(launcher, "load_manifest", return_value=unapproved), \
     mock.patch.object(launcher.credentials, "load_credentials",
                       side_effect=AssertionError("creds must not load when unapproved")), \
     mock.patch.object(launcher, "_fetch_live_inventory",
                       side_effect=AssertionError("no live GET when unapproved")):
    rc = launcher.command_launch("Q1W5", test_mode=False)
assert rc == 1, rc
print("PASS launch cannot write without approval")
PY

echo "PASS Canvas launch wrapper tests complete"
