#!/usr/bin/env bash
# Canvas Planner macOS launcher status (PASS/WARN/FAIL, bounded, no network).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

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

echo "Canvas Planner macOS Launcher"

# Launcher source + build script + installer helpers.
[ -f "scripts/canvas_planner_app/launcher.sh" ]; check "launcher source present" $?
[ -f "scripts/canvas_planner_app/build_app.sh" ]; check "build script present" $?
[ -f "scripts/canvas_planner_app/generate_icon.py" ]; check "icon generator present" $?
[ -x "bin/install-canvas-planner-app" ]; check "install helper present" $?
[ -x "bin/open-canvas-planner" ]; check "open helper present" $?

# Launcher binds localhost only + has no secrets.
python3 - <<'PY'
import sys
from pathlib import Path
src = Path("scripts/canvas_planner_app/launcher.sh").read_text()
ok = ("127.0.0.1" in src and "0.0.0.0" not in src
      and "TEACHER_WORKSTATION_REPO" in src)
for tok in ("CANVAS_TOKEN", "Authorization", "client_secret", "thalesacademy.instructure"):
    if tok in src:
        ok = False
sys.exit(0 if ok else 1)
PY
check "localhost-only + no secrets in launcher source" $?

# Tests pass (bounded, isolated).
bash tests/canvas-planner-launcher-test.sh >/dev/null 2>&1
check "launcher tests pass" $?

# App installed (WARN if not — installation is optional for the repo itself).
APP="${HOME}/Applications/Teacher Workstation - Canvas Planner.app"
if [ -d "${APP}" ] && [ -x "${APP}/Contents/MacOS/CanvasPlannerLauncher" ] && [ -f "${APP}/Contents/Resources/CanvasPlanner.icns" ]; then
  echo "  PASS  app installed at ~/Applications"
  PASS=$((PASS+1))
else
  echo "  WARN  app not installed (run bin/install-canvas-planner-app)"
  WARN=$((WARN+1))
fi

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
