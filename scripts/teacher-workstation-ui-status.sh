#!/usr/bin/env bash
# Teacher Workstation UI status (PASS/WARN/FAIL proof — read-only).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
WARN=0
FAIL=0

check() {
  local label="$1"; local ok="$2"
  if [ "$ok" = "0" ]; then
    echo "  PASS  $label"
    PASS=$((PASS+1))
  else
    echo "  FAIL  $label"
    FAIL=$((FAIL+1))
  fi
}

echo "Teacher Workstation UI"

# Launcher + server module exist.
[ -x "bin/teacher-workstation" ]; check "launcher exists" $?
[ -f "scripts/teacher_workstation/server.py" ]; check "server module exists" $?
[ -f "scripts/teacher_workstation/adapter.py" ]; check "adapter module exists" $?
[ -f "scripts/teacher_workstation/mutate.py" ]; check "mutation layer exists" $?
[ -f "scripts/canvas_llm_intake/owner_overrides.py" ]; check "owner-override ledger exists" $?

# Local-mutation routes terminate at local state; local-only bind; no secrets.
python3 - <<'PY'
import sys
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
ok = True
for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
    if verb not in src:
        ok = False
if 'HOST = "127.0.0.1"' not in src or "0.0.0.0" in src:
    ok = False
if "from . import mutate" not in src:
    ok = False
for tok in ("CANVAS_TOKEN", "Bearer", "verifier=", "client_secret"):
    if tok in src:
        ok = False
for tok in ("canvas_connection_" + "manager", "canvas_" + "writer", "Phase22Live" + "CanvasClient",
            "create_" + "assignment", "update_" + "page"):
    if tok in src:
        ok = False
sys.exit(0 if ok else 1)
PY
check "local-mutation-only routes + local-only bind + no Canvas write path + no secrets" $?

# Frontend assets.
for f in index.html styles.css app.js; do
  [ -f "apps/teacher-workstation/$f" ]; check "asset $f present" $?
done

# UI tests pass (start a server, hit routes).
bash tests/teacher-workstation-ui-test.sh >/dev/null 2>&1
check "UI tests pass" $?

echo ""
if [ "$FAIL" -gt 0 ]; then
  echo "Summary: FAIL"
  exit 2
elif [ "$WARN" -gt 0 ]; then
  echo "Summary: WARN"
  exit 1
else
  echo "Summary: PASS"
  exit 0
fi
