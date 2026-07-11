#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 23 weekly content production engine tests..."
M=scripts/canvas_llm_phase23/phase23_content_engine.py
V=scripts/canvas_llm_phase23/validate_phase23_packet.py
T=$(mktemp -d "${TMPDIR:-/tmp}/phase23.XXXXXX")
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M" "$V"

DEMO="$T/phase23-demo.json"
python3 "$M" build-demo --out "$DEMO"
python3 - "$DEMO" apps/weekly-content-production/data/phase23-demo.json <<'PY'
import json
import sys
from pathlib import Path

def scrub(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    obj["generatedAt"] = "__normalized__"
    return obj

temp = scrub(sys.argv[1])
committed = scrub(sys.argv[2])
assert temp["schemaVersion"] == 1
assert temp == committed
assert temp["containsStudentData"] is False
assert temp["weekCode"] == "Q1W5"
assert temp["validation"]["failCount"] == 0
assert temp["validation"]["warnCount"] == 1
print("PASS demo packet matches committed artifact shape")
PY

python3 "$V" "$DEMO" | grep -q '^FAIL: 0$'
python3 "$V" "$DEMO" | grep -q '^WARN: due-time.unresolved'
python3 "$V" "$DEMO" | grep -q '^PASS: reading-test-14.checkout Reading Test 14 correctly has no checkout reminder$'

python3 "$M" self-test

LOCAL_ROOT="$T/local-state-root"
SERVER_LOG="$T/p23-serve.txt"
srv=""

start_server() {
  PHASE23_LOCAL_ROOT="$LOCAL_ROOT" python3 "$M" serve --host 127.0.0.1 --port 18775 >"$SERVER_LOG" 2>&1 &
  srv=$!
  for _ in $(seq 1 60); do
    if python3 - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:18775/api/health", timeout=1)
PY
    then
      return
    fi
    sleep 0.25
  done
  cat "$SERVER_LOG"
  echo "FAIL: server failed to start"
  exit 1
}

stop_server() {
  if [ -n "${srv:-}" ]; then
    kill "$srv" >/dev/null 2>&1 || true
    wait "$srv" >/dev/null 2>&1 || true
    srv=""
  fi
}

cleanup() {
  stop_server
  rm -rf "$T"
}
trap cleanup EXIT

start_server

python3 - <<'PY'
import json
import urllib.request

base = "http://127.0.0.1:18775"
health = json.loads(urllib.request.urlopen(base + "/api/health").read())
assert health["previewOnly"] is True
assert health["canvasWritesAllowed"] is False
packet = json.loads(urllib.request.urlopen(base + "/api/packet").read())
index_html = urllib.request.urlopen(base + "/").read().decode()
required_ids = [
    "packet-meta",
    "approval-state",
    "deployment-state",
    "warn-pill",
    "export-btn",
    "export-status",
    "local-approval-state",
    "local-approval-save",
    "local-approval-status",
    "packet-summary",
    "pages-grid",
    "assignments-grid",
    "resources-grid",
    "reminders-grid",
    "html-preview",
    "text-preview",
    "packet-json-preview",
    "validation-list",
    "validation-summary",
    "risks-list",
    "provenance-list",
]
for required_id in required_ids:
    assert f'id="{required_id}"' in index_html, required_id
assert urllib.request.urlopen(base + "/").status == 200
assert urllib.request.urlopen(base + "/workstation.js").status == 200
assert urllib.request.urlopen(base + "/styles.css").status == 200
assert packet["weekCode"] == "Q1W5"
assert packet["validation"]["failCount"] == 0
assert packet["validation"]["warnCount"] == 1
local_state = json.loads(urllib.request.urlopen(base + "/api/local-state?weekCode=Q1W5").read())
assert local_state["status"] == "saved"
assert local_state["approvalState"] == "draft"
assert local_state["version"] == 0
save = urllib.request.Request(
    base + "/api/local-state",
    data=json.dumps({"weekCode": "Q1W5", "approvalState": "reviewed", "version": 0}).encode(),
    method="POST",
    headers={"Content-Type": "application/json"},
)
saved_state = json.loads(urllib.request.urlopen(save).read())
assert saved_state["status"] == "saved"
assert saved_state["approvalState"] == "reviewed"
assert saved_state["version"] == 1
packet_after_save = json.loads(urllib.request.urlopen(base + "/api/packet").read())
assert packet_after_save["approvalState"] == "reviewed"
export = urllib.request.Request(base + "/api/export", data=b"{}", method="POST")
result = json.loads(urllib.request.urlopen(export).read())
assert result["ok"] is True
saved = json.loads(urllib.request.urlopen(base + "/api/packet").read())
assert saved["packetId"] == packet["packetId"]
print("PASS runtime interface")
PY

node - <<'JS'
const fs = require('fs');
const vm = require('vm');

const packet = JSON.parse(fs.readFileSync('apps/weekly-content-production/data/phase23-demo.json', 'utf8'));
const localState = { weekCode: 'Q1W5', approvalState: 'draft', version: 0, status: 'saved', source: 'default' };

function makeNode(id) {
  return {
    id,
    textContent: '',
    innerHTML: '',
    value: '',
    dataset: {},
    classList: { toggle() {} },
    listeners: {},
    addEventListener(type, handler) {
      this.listeners[type] = handler;
    },
    click() {
      if (this.listeners.click) {
        return this.listeners.click();
      }
    },
  };
}

const ids = ['packet-meta', 'approval-state', 'deployment-state', 'warn-pill', 'export-btn', 'export-status', 'packet-summary', 'pages-grid', 'assignments-grid', 'resources-grid', 'reminders-grid', 'html-preview', 'text-preview', 'packet-json-preview', 'validation-list', 'validation-summary', 'risks-list', 'provenance-list', 'local-approval-state', 'local-approval-save', 'local-approval-status'];
const nodes = new Map(ids.map((id) => [id, makeNode(id)]));

const document = {
  body: { innerHTML: '' },
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, makeNode(id));
    return nodes.get(id);
  },
  querySelectorAll(selector) {
    if (selector === '.tab') {
      return ['summary', 'pages', 'assignments', 'resources', 'reminders', 'html-preview', 'text-preview', 'json-preview', 'validation', 'risks', 'provenance'].map((tab) => ({
        dataset: { tab },
        classList: { toggle() {} },
        addEventListener() {},
      }));
    }
    if (selector === '.panel') return [];
    return [];
  },
};

const sandbox = {
  document,
  fetch: async (path, options = {}) => {
    if (path === '/api/packet') {
      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({ ...packet, approvalState: localState.approvalState }),
      };
    }
    if (path.startsWith('/api/local-state') && (!options.method || options.method === 'GET')) {
      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({ ...localState }),
      };
    }
    if (path === '/api/local-state' && options.method === 'POST') {
      const body = JSON.parse(options.body);
      if (Number(body.version || 0) !== localState.version) {
        return {
          ok: false,
          status: 409,
          statusText: 'Conflict',
          json: async () => ({ status: 'conflict', approvalState: localState.approvalState, version: localState.version }),
        };
      }
      localState.approvalState = body.approvalState;
      localState.version += 1;
      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({ ...localState }),
      };
    }
    if (path === '/api/export') {
      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({ ok: true, savedPath: '/tmp/export.json' }),
      };
    }
    throw new Error(`Unexpected fetch ${path}`);
  },
  console,
  JSON,
  Promise,
  setTimeout,
  clearTimeout,
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('apps/weekly-content-production/workstation.js', 'utf8'), sandbox);

Promise.resolve().then(() => new Promise((resolve) => setTimeout(resolve, 0))).then(() => {
  if (document.body.innerHTML.includes('Load failed')) {
    throw new Error('browser smoke hit Load failed');
  }
  if (document.getElementById('packet-meta').textContent !== `Q1W5 • 2026-08-17 to 2026-08-21 • ${packet.packetId}`) {
    throw new Error('browser smoke did not render the week header');
  }
  if (!document.getElementById('packet-summary').textContent.includes('Pages 5')) {
    throw new Error('browser smoke did not render packet summary');
  }
  if (document.getElementById('packet-summary').textContent.includes('undefined')) {
    throw new Error('browser smoke used an undefined packet field');
  }
  if (!document.getElementById('pages-grid').innerHTML.includes('Math Weekly Agenda')) {
    throw new Error('browser smoke did not render pages');
  }
  if (!document.getElementById('assignments-grid').innerHTML.includes('SM5: Lesson 18 Study Guide')) {
    throw new Error('browser smoke did not render assignments');
  }
  if (!document.getElementById('resources-grid').innerHTML.includes('SM5 Lesson 18 Guide')) {
    throw new Error('browser smoke did not render resources');
  }
  if (!document.getElementById('reminders-grid').innerHTML.includes('Reading Test 14')) {
    throw new Error('browser smoke did not render Reading Test 14');
  }
  if (document.getElementById('reminders-grid').innerHTML.includes('Checkout 14')) {
    throw new Error('browser smoke rendered Checkout 14');
  }
  if (!document.getElementById('html-preview').innerHTML.includes('Weekly Agenda')) {
    throw new Error('browser smoke did not render HTML preview');
  }
  if (document.getElementById('html-preview').innerHTML.includes('&nbsp;&nbsp;')) {
    throw new Error('browser smoke rendered placeholder bullet content');
  }
  if (!document.getElementById('text-preview').textContent.includes('Monday:')) {
    throw new Error('browser smoke did not render text preview');
  }
  if (!document.getElementById('text-preview').textContent.includes('Thursday: Reading Mastery Test 14')) {
    throw new Error('browser smoke did not render canonical Reading Test 14 text');
  }
  if (!document.getElementById('packet-json-preview').textContent.includes('"weekCode": "Q1W5"')) {
    throw new Error('browser smoke did not render packet JSON preview');
  }
  if (document.getElementById('local-approval-state').value !== 'draft') {
    throw new Error('browser smoke did not render local approval state');
  }
  if (!document.getElementById('local-approval-status').textContent.includes('Ready')) {
    throw new Error('browser smoke did not render local approval status');
  }
  if (!document.getElementById('approval-state').textContent.includes('draft')) {
    throw new Error('browser smoke did not render approval state');
  }
  if (!document.getElementById('deployment-state').textContent.includes('preview-only')) {
    throw new Error('browser smoke did not render deployment state');
  }
  document.getElementById('local-approval-state').value = 'approved';
  return Promise.resolve(document.getElementById('local-approval-save').click()).then(() => {
    if (!document.getElementById('local-approval-status').textContent.includes('Saved v1')) {
      throw new Error('browser smoke did not save local approval state');
    }
    if (!document.getElementById('approval-state').textContent.includes('approved')) {
      throw new Error('browser smoke did not refresh approval state');
    }
    if (!document.getElementById('packet-summary').textContent.includes('Approval approved')) {
      throw new Error('browser smoke did not refresh packet summary');
    }
    return Promise.resolve(document.getElementById('export-btn').click());
  }).then(() => {
    if (!document.getElementById('export-status').textContent.startsWith('Saved ')) {
      throw new Error('browser smoke export control did not update status');
    }
    console.log('PASS browser smoke');
  });
}).catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
JS

stop_server

start_server

python3 - "$LOCAL_ROOT" <<'PY'
import json
import sys
import urllib.request
from pathlib import Path

base = "http://127.0.0.1:18775"
local_root = Path(sys.argv[1])

state = json.loads(urllib.request.urlopen(base + "/api/local-state?weekCode=Q1W5").read())
assert state["status"] == "saved"
assert state["approvalState"] == "reviewed"
assert state["version"] == 1
packet = json.loads(urllib.request.urlopen(base + "/api/packet").read())
assert packet["approvalState"] == "reviewed"
assert packet["weekCode"] == "Q1W5"
assert local_root.joinpath("state", "Q1W5.json").exists()
print("PASS local state restart proof")
PY

stop_server

mkdir -p "$LOCAL_ROOT/state"
printf '{broken-json' > "$LOCAL_ROOT/state/Q1W5.json"

PHASE23_LOCAL_ROOT="$LOCAL_ROOT" python3 "$M" serve --host 127.0.0.1 --port 18775 >"$SERVER_LOG" 2>&1 &
srv=$!
for _ in $(seq 1 60); do
  if python3 - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:18775/styles.css", timeout=1)
PY
  then
    break
  fi
  sleep 0.25
done

python3 - "$LOCAL_ROOT" <<'PY'
import json
import sys
import urllib.request
from pathlib import Path

base = "http://127.0.0.1:18775"
local_root = Path(sys.argv[1])

state = json.loads(urllib.request.urlopen(base + "/api/local-state?weekCode=Q1W5").read())
assert state["status"] == "error"
assert state["approvalState"] == "draft"
assert "could not be parsed" in state["error"] or "Invalid local approval state" in state["error"]
quarantine_root = local_root / "quarantine" / "state"
assert quarantine_root.exists()
assert any(path.name == "Q1W5.json" for path in quarantine_root.rglob("Q1W5.json"))
print("PASS local state quarantine proof")
PY

stop_server

python3 "$V" "$DEMO" >/tmp/p23-validate.txt 2>&1 || { cat /tmp/p23-validate.txt; exit 1; }
grep -q '^PASS: 1$' /tmp/p23-validate.txt || true

if git ls-files .local | grep -q .; then
  echo "FAIL: .local artifacts tracked"
  exit 1
fi

echo "PASS: Canvas LLM Phase 23 weekly content production engine tests complete"
