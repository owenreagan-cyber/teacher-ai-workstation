#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 26 unified weekly production workstation tests..."
M=scripts/canvas_llm_phase26/phase26_workstation.py
V=scripts/canvas_llm_phase26/validate_phase26_state.py
T=$(mktemp -d "${TMPDIR:-/tmp}/phase26.XXXXXX")
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" \
  "$V" \
  scripts/canvas_llm_phase26/models.py \
  scripts/canvas_llm_phase26/storage.py \
  scripts/canvas_llm_phase26/pipeline.py \
  scripts/canvas_llm_phase26/approval.py \
  scripts/canvas_llm_phase26/revisions.py \
  scripts/canvas_llm_phase26/readiness.py \
  scripts/canvas_llm_phase26/export_package.py \
  scripts/canvas_llm_phase26/deployment_manifest.py

DEMO="$T/phase26-demo.json"
PHASE26_LOCAL_ROOT="$T/local-root" python3 "$M" build-demo --week Q1W5 --output "$DEMO"

python3 - "$DEMO" <<'PY'
import json
import sys
from pathlib import Path

def scrub(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    obj["generatedAt"] = "__normalized__"
    obj["packetId"] = "__normalized__"
    obj["localState"]["weekState"]["updated_at"] = "__normalized__"
    return obj

temp = scrub(sys.argv[1])
assert temp["schemaVersion"] == 1
assert temp["weekCode"] == "Q1W5"
assert temp["validation"]["failCount"] == 0
assert temp["validation"]["warnCount"] == 1
assert temp["weekSelection"]["quarterWeekCounts"] == {"Q1": 9, "Q2": 9, "Q3": 9, "Q4": 10}
assert temp["weekSelection"]["weeks"][0]["code"] == "Q1W1"
assert temp["weekSelection"]["weeks"][-1]["code"] == "Q4W10"
assert temp["productionPacket"]["weekCode"] == "Q1W5"
assert any(item["title"] == "Reading Test 14" for item in temp["productionPacket"]["assessmentReminders"])
assert any(item["event"] == "Reading Test 14" for item in temp["exceptionInbox"])
assert temp["deploymentManifestPreview"]["mode"] == "preview-only"
assert temp["deploymentManifestPreview"]["operations"]
print("PASS demo packet shape")
PY

python3 "$V" "$DEMO" | grep -q '^WARN: due-time.unresolved Canvas assignment due-time convention remains owner-unresolved$'
if python3 "$V" "$DEMO" | grep -q '^FAIL: reading-test-14.checkout '; then
  echo "FAIL: Reading Test 14 produced a Checkout failure"
  exit 1
fi
python3 "$V" "$DEMO" | grep -q '^PASS: manifest.preview Deployment manifest preview is available$'
python3 "$V" "$DEMO" | grep -q '^FAIL: 0$'

LOCAL_ROOT="$T/local-root"
cleanup() {
  rm -rf "$T"
}
trap cleanup EXIT

python3 - "$LOCAL_ROOT" <<'PY'
import sqlite3
import sys
from pathlib import Path

from scripts.canvas_llm_phase26 import storage

root = Path(sys.argv[1])
conn = storage.connect(root / "workstation.db")
try:
    storage.set_selected_week_code(conn, "Q1W1")
    storage.ensure_week_state(conn, "Q1W1")
    storage.save_correction(conn, {
        "kind": "instructional",
        "weekCode": "Q1W1",
        "subject": "math",
        "day": "Monday",
        "field": "at home",
        "originalValue": "SM5: Lesson 18 Evens",
        "editedValue": "SM5: Lesson 18 Odds",
        "scope": "this occurrence only",
        "reason": "Teacher correction",
        "sourceRule": "teacher.override",
        "timestamp": "2026-07-11T00:00:00Z",
        "revision": 1,
        "invalidatesApproval": True,
    })
    snapshot = storage.state_summary(conn, "Q1W1")
    assert snapshot["weekState"]["week_code"] == "Q1W1"
    assert snapshot["correctionCount"] >= 1
    assert snapshot["revisionCount"] >= 0
finally:
    conn.close()

try:
    root.joinpath("workstation.db").write_text("not-a-sqlite-db", encoding="utf-8")
    conn = storage.connect(root / "workstation.db")
    conn.close()
finally:
    pass

quarantine_root = storage.LOCAL_ROOT / "quarantine"
assert quarantine_root.exists()
assert any(quarantine_root.rglob("*corrupt-db*.sqlite3")) or any(quarantine_root.rglob("*readonly-db*.sqlite3"))
print("PASS local-state and quarantine recovery")
PY

node - <<'JS'
const fs = require('fs');
const vm = require('vm');

const packet = JSON.parse(fs.readFileSync('apps/unified-weekly-production/data/phase26-demo.json', 'utf8'));

function node(id) {
  return {
    id,
    textContent: '',
    innerHTML: '',
    value: '',
    dataset: {},
    listeners: {},
    classList: { toggle() {} },
    addEventListener(type, handler) { this.listeners[type] = handler; },
  };
}

const ids = ['week-select','generate-btn','regenerate-btn','approve-week-btn','export-btn','readiness-pill','approval-pill','manifest-pill','state-pill','readiness-score','readiness-explainer','exception-count','revision-count','subject-grid','exception-inbox','revision-history','approval-panel','trace-grid','correction-form','correction-subject','correction-day','correction-field','correction-original','correction-edited','correction-scope','correction-reason','correction-source-rule','correction-status','local-state','agenda-html','text-preview','json-preview','assignments-preview','reminders-preview','resources-preview','manifest-preview'];
const nodes = new Map(ids.map((id) => [id, node(id)]));

const document = {
  body: { innerHTML: '' },
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, node(id));
    return nodes.get(id);
  },
  querySelector(selector) {
    if (selector === '.tab.active') {
      return { dataset: { tab: 'agenda-html' } };
    }
    return null;
  },
  querySelectorAll(selector) {
    if (selector === '.tab') {
      return ['agenda-html','text','json','assignments','reminders','resources','manifest'].map((tab) => ({
        dataset: { tab },
        classList: { toggle() {} },
        addEventListener() {},
      }));
    }
    if (selector === '.preview') {
      return ['agenda-html','text','json','assignments','reminders','resources','manifest'].map((panel) => ({
        dataset: { panel },
        classList: { toggle() {} },
      }));
    }
    return [];
  },
};

const sandbox = {
  document,
  console,
  JSON,
  Promise,
  setTimeout,
  clearTimeout,
  window: null,
  fetch: async (path, options = {}) => {
    if (path === '/api/workstation') {
      return { ok: true, status: 200, json: async () => packet };
    }
    if (path === '/api/select-week') {
      return { ok: true, status: 200, json: async () => ({ ok: true, weekCode: 'Q1W5' }) };
    }
    if (path === '/api/correction') {
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    }
    if (path === '/api/approve') {
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    }
    if (path === '/api/regenerate') {
      return { ok: true, status: 200, json: async () => ({ ok: true, packet }) };
    }
    if (path === '/api/export') {
      return { ok: true, status: 200, json: async () => ({ ok: true, savedPath: '/tmp/export' }) };
    }
    throw new Error(`unexpected fetch ${path}`);
  },
};
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('apps/unified-weekly-production/workstation.js', 'utf8'), sandbox);

Promise.resolve().then(() => new Promise((resolve) => setTimeout(resolve, 0))).then(() => {
  if (document.body.innerHTML.includes('Load failed')) {
    throw new Error('browser proof hit load failure');
  }
  if (!document.getElementById('subject-grid').innerHTML.includes('Math')) {
    throw new Error('browser proof did not render subject cards');
  }
  if (!document.getElementById('exception-inbox').innerHTML.includes('Due-time unresolved')) {
    throw new Error('browser proof did not render exception inbox');
  }
  if (!document.getElementById('manifest-preview').textContent.includes('"mode": "preview-only"')) {
    throw new Error('browser proof did not render manifest preview');
  }
  console.log('PASS browser proof smoke');
}).catch((error) => {
  console.error(error);
  process.exit(1);
});
JS

if git ls-files '.local/*' | grep -q .; then
  echo "FAIL: tracked .local artifact found"
  exit 1
fi

echo "PASS: no .local artifacts tracked"
echo "PASS: Phase 26 unified weekly production workstation tests complete"
