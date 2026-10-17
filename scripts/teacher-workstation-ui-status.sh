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

# Read-only routes: no write verbs except 405 stubs; local-only bind.
python3 - <<'PY'
import re, sys
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
ok = True
for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
    if verb not in src:
        ok = False
if 'HOST = "127.0.0.1"' not in src or "0.0.0.0" in src:
    ok = False
for tok in ("CANVAS_TOKEN", "Bearer", "verifier=", "client_secret"):
    if tok in src:
        ok = False
sys.exit(0 if ok else 1)
PY
check "read-only routes + local-only bind + no secrets" $?

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
