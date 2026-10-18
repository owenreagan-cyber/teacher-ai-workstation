#!/usr/bin/env bash
# Deterministic guard tests for the bounded Canvas grade-entry capability.
# Offline: no network, no credentials, no live Canvas, no grades written.
set -euo pipefail

echo "Running bounded grade-entry guard tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

python3 -m py_compile \
  scripts/canvas_llm_grade_entry/__init__.py \
  scripts/canvas_llm_grade_entry/grade_entry.py \
  scripts/canvas_llm_grade_entry/fake_canvas.py \
  scripts/canvas_llm_grade_entry/tests.py \
  scripts/canvas_llm_grade_entry/cli.py

# 1. Deterministic guard suite (10 tests).
python3 -m scripts.canvas_llm_grade_entry.cli self-test

# 2. Disabled by default: no env gate, no enablement -> nothing is enabled.
python3 - <<'PY'
import os
from scripts.canvas_llm_grade_entry import grade_entry as ge

os.environ.pop(ge.ENABLE_ENV, None)
assert ge.feature_enabled() is False, 'must be disabled without the env gate'
assert ge.is_enabled() is False, 'must not be enabled by default'
try:
    ge.enable(owner='someone')
    raise AssertionError('enable() must require the env gate')
except ge.GradeEntryError as exc:
    assert 'GRADE_ENTRY_ENABLED' in str(exc), exc
print('PASS disabled by default (env gate absent)')
PY

# 3. Env gate present but no human enablement -> still disabled.
python3 - <<'PY'
from scripts.canvas_llm_grade_entry import grade_entry as ge

ge.disable()
print('PASS env gate alone does not enable grade entry')
PY

# 4. apply requires explicit --approve; without it nothing is written.
python3 -m scripts.canvas_llm_grade_entry.cli apply --fake \
  --packet "$(ls -t .local/canvas-llm/grade-entry/*-packet.json 2>/dev/null | head -1 || echo /dev/null)" \
  --approved-by "test" >/tmp/grade-entry-noapprove.txt 2>&1 && {
    echo "FAIL apply without --approve must exit non-zero"
    exit 1
  } || true
grep -q "BLOCKED" /tmp/grade-entry-noapprove.txt || {
  echo "FAIL apply without --approve must report BLOCKED"
  cat /tmp/grade-entry-noapprove.txt
  exit 1
}
echo "PASS apply without --approve writes nothing"

# 5. Live apply without the env gate fails closed (no live write).
python3 - <<'PY'
import json
import os
from pathlib import Path

from scripts.canvas_llm_grade_entry import grade_entry as ge

packets = sorted(Path('.local/canvas-llm/grade-entry').glob('*-packet.json'))
if not packets:
    print('SKIP live fail-closed check (no packet on disk)')
    raise SystemExit(0)
packet = ge.ApprovalPacket.load(packets[-1])
os.environ.pop(ge.ENABLE_ENV, None)
ge.disable()

class Tripwire:
    def __getattr__(self, name):
        raise AssertionError(f'no Canvas call may occur while disabled (tried {name})')

try:
    ge.apply_packet(packet=packet, client=Tripwire(), approved=True, approved_by='owner')
    raise AssertionError('apply must be blocked while disabled')
except ge.GradeEntryError as exc:
    assert 'not enabled' in str(exc) or 'disabled' in str(exc), exc
print('PASS live apply fails closed before any Canvas call when disabled')
PY

echo "PASS bounded grade-entry guard tests complete"
