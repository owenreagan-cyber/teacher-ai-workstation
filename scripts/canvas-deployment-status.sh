#!/usr/bin/env bash
# Guarded Canvas deployment status (PASS/WARN/FAIL proof — local, bounded, no network).
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

echo "Guarded Canvas Deployment"

# Deployment coordinator modules present.
for f in plan client ledger preflight coordinator cli; do
  [ -f "scripts/canvas_llm_deploy/$f.py" ]; check "deploy module $f.py" $?
done

# CLI commands wired into bin/canvas-intake.
python3 - <<'PY'
import sys
from pathlib import Path
src = Path("scripts/canvas_llm_intake/cli.py").read_text()
ok = ("canvas_llm_deploy" in src and "dcli.build_parser" in src)
sys.exit(0 if ok else 1)
PY
check "deploy CLI wired into bin/canvas-intake" $?

# UI server routes delegate to the guarded coordinator (no direct phase22 import,
# no generic proxy).
python3 - <<'PY'
import sys
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
dep = Path("scripts/teacher_workstation/deploy.py").read_text()
ok = True
if 'parts[4] == "preflight"' not in src: ok = False
if 'parts[4] == "deploy"' not in src: ok = False
if "production" not in dep: ok = False
for tok in ("canvas_connection_" + "manager", "canvas_" + "writer", "Phase22Live" + "CanvasClient"):
    if tok in src or tok in dep: ok = False
for tok in ("/canvas/request", "/canvas/object", "/canvas/update"):
    if tok in src or tok in dep: ok = False
sys.exit(0 if ok else 1)
PY
check "deploy routes guarded (production-gated, no proxy, no direct write import)" $?

# Deployment tests pass (synthetic + in-memory fake client; zero real writes).
bash tests/canvas-llm-deploy-test.sh >/dev/null 2>&1
check "deployment tests pass" $?

# Bounded, read-only lifecycle snapshot.
python3 - <<'PY'
import json
from pathlib import Path
from scripts.canvas_llm_deploy import ledger

weeks = []
root = Path(".local/canvas-llm/intake/2026-2027")
if root.exists():
    for mp in sorted(root.glob("q*/w*/intake-manifest.json"), reverse=True):
        data = json.loads(mp.read_text())
        weeks.append({"quarter": data.get("quarter"), "week": data.get("week"),
                      "week_code": data.get("week_code"), "status": data.get("status"),
                      "ready": bool(data.get("ready_to_publish"))})
latest = weeks[0] if weeks else None
if latest:
    q, w = latest["quarter"], latest["week"]
    print(f"Latest prepared: {latest['week_code']} ({latest['status']})")
    print(f"  READY_TO_PUBLISH: {'yes' if latest['ready'] else 'no'}")
    pre = ledger.load_ledger(q, w)
    print(f"  Deployment ledger: {pre.get('deployment_state') if pre else 'none'}")
    pub = (ledger.deploy_dir(q, w) / "published-verified-ledger.json")
    print(f"  Published-verified: {'yes' if pub.exists() else 'no'}")
else:
    print("No prepared weeks.")
PY

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
