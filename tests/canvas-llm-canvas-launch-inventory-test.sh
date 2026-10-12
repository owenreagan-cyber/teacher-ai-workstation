#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas launcher live-inventory self-containment tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LAUNCH="scripts/canvas_llm_phase22/canvas_launcher.py"
INVENTORY="scripts/canvas_llm_phase22/canvas_live_inventory.py"

python3 -m py_compile "$LAUNCH" "$INVENTORY"
python3 "$INVENTORY" self-test

python3 - <<'PY'
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_phase22 import canvas_launcher as launcher
from scripts.canvas_llm_phase22 import canvas_live_inventory as inventory
from scripts.canvas_llm_phase22 import canvas_connection as connection

# 1. The launcher must not reference any q1w5_* module (the one-off audit).
launcher_src = Path(launcher.__file__).read_text()
assert "q1w5_live_audit" not in launcher_src, "launcher still imports q1w5_live_audit"
assert "importlib" not in launcher_src, "launcher still uses importlib (was only for q1w5)"
assert "scripts/canvas-llm/q1w5_" not in launcher_src, "launcher still points at the q1w5 scripts dir"
print("PASS launcher has no q1w5_* import")

# 2. The live inventory module is self-contained and week-agnostic.
assert inventory.has_no_week_specific_hardcoding()
assert inventory.live_course_ids() == dict(connection.COURSE_MAP)
print("PASS live inventory is week-agnostic and sources course ids from COURSE_MAP")

# 3. Non-test fetch dispatches through the permanent module (not any q1w5 file).
sentinel = {"courses": {"26404": {"pages": [], "assignments": [], "announcements": []}}}
with mock.patch.object(inventory, "fetch_live_inventory", return_value=sentinel):
    result = launcher._fetch_live_inventory(test_mode=False)
assert result is sentinel, result
print("PASS launcher fetch_live_inventory uses the permanent module")

# 4. test_mode still uses the fake transport store (no network, no q1w5).
fake = launcher._fetch_live_inventory(test_mode=True)
assert isinstance(fake, dict) and "courses" in fake
print("PASS test-mode inventory still uses the fake transport store")
PY

echo "PASS Canvas launcher live-inventory self-containment tests complete"
