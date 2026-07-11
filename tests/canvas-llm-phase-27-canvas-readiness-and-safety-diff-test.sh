#!/usr/bin/env bash
set -euo pipefail
echo "Running Phase 27 tests..."
P=apps/unified-weekly-production/data/phase26-demo.json
S=fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json
T=$(mktemp -d "${TMPDIR:-/tmp}/phase27.XXXXXX")
O="$T/phase27.json"
python3 scripts/canvas_llm_phase27/phase27_readiness.py build --week Q1W5 --phase26-packet "$P" --snapshot "$S" --output "$O"
python3 scripts/canvas_llm_phase27/validate_phase27.py "$O"
python3 - <<'PY'
import json, pathlib, hashlib
from scripts.canvas_llm_phase27.canonicalize import canonical_hash, placement_hash
assert canonical_hash("<div>\n  <p>Practice</p>\n</div>") == canonical_hash("<div><p>Practice</p></div>")
assert canonical_hash({"a":1,"b":2}) == canonical_hash({"b":2,"a":1})
assert placement_hash({"module":"Weekly Agendas","position":1}) == placement_hash({"position":1,"module":"Weekly Agendas"})
print("PASS canonicalization")
PY
python3 - <<'PY'
import json
from pathlib import Path
from scripts.canvas_llm_phase27.phase27_readiness import build_packet

packet = build_packet(
    "Q1W5",
    Path("apps/unified-weekly-production/data/phase26-demo.json"),
    Path("fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json"),
)
assert packet["deploymentManifestV1"]["manifestVersion"] == 1
assert packet["deploymentManifestV1"]["mode"] == "preview-only"
assert packet["deploymentManifestV1"]["warnings"] == ["Canvas assignment due-time convention remains owner-unresolved"]
assert any(item["comparisonStatus"] == "CREATE" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "UPDATE" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "UNCHANGED" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "BLOCKED" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "CONFLICT" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "OMIT" for item in packet["safetyDiff"])
assert any(item["comparisonStatus"] == "DELETE_CANDIDATE" for item in packet["safetyDiff"])
print("PASS phase27 packet")
PY
echo "PASS: no Canvas mutations"
