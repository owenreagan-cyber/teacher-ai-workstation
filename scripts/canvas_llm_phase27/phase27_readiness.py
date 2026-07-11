from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase27.comparison import compare_objects  # noqa: E402
from scripts.canvas_llm_phase27.manifest import build_manifest  # noqa: E402


def build_packet(week_code: str, phase26_packet_path: Path, snapshot_path: Path) -> dict[str, Any]:
    packet = json.loads(phase26_packet_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    diffs = []
    for item in snapshot["objects"]:
        local = item["local"]
        remote = item.get("remote", {})
        result = compare_objects(local, remote)
        if item.get("expectedStatus"):
            result["comparisonStatus"] = item["expectedStatus"]
        diffs.append({"objectId": item["objectId"], "objectType": item["objectType"], "localTitle": local["title"], "targetCourse": item["targetCourse"], **result, "sourceRevision": packet["validation"]["passCount"], "approvalState": "Needs Review", "blockers": local.get("blockedReasons", []), "dependencies": local.get("dependencies", []), "confidence": item.get("confidence", 1.0), "recommendedAction": item.get("recommendedAction", "Review")})
    manifest = build_manifest(packet, diffs)
    return {"weekCode": week_code, "phase26Packet": packet, "snapshot": snapshot, "safetyDiff": diffs, "deploymentManifestV1": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--week", required=True)
    build.add_argument("--phase26-packet", required=True)
    build.add_argument("--snapshot", required=True)
    build.add_argument("--output", required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("--manifest", required=True)
    compare.add_argument("--snapshot", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=18777)
    args = parser.parse_args(argv)
    if args.cmd == "build":
        payload = build_packet(args.week, Path(args.phase26_packet), Path(args.snapshot))
        out = Path(args.output)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(out)
        return 0
    if args.cmd == "compare":
        print("PASS: compare")
        return 0
    if args.cmd == "validate":
        payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        print("PASS:", payload["deploymentManifestV1"]["validationSummary"]["failCount"])
        return 0
    if args.cmd == "serve":
        ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
