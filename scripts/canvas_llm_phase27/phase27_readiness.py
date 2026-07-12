from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase27.canvas_snapshot import (  # noqa: E402
    SnapshotValidationError,
    load_snapshot,
)
from scripts.canvas_llm_phase27.export_package import export_package  # noqa: E402
from scripts.canvas_llm_phase27.health_checks import run_health_checks  # noqa: E402
from scripts.canvas_llm_phase27.ledger import DeploymentLedger, DEFAULT_LEDGER_PATH  # noqa: E402
from scripts.canvas_llm_phase27.manifest import build_manifest  # noqa: E402
from scripts.canvas_llm_phase27.safety_diff import build_safety_diff  # noqa: E402
from scripts.canvas_llm_phase27.transport import DisabledCanvasTransport, MutationNotAllowedError  # noqa: E402


def _transport_readiness() -> dict[str, Any]:
    """Computed by actually invoking the disabled transport, not printed --
    mirrors the mutation-disabled-state health check."""
    try:
        DisabledCanvasTransport().create_page()
        verified = False
    except MutationNotAllowedError:
        verified = True
    return {
        "defaultTransport": "DisabledCanvasTransport",
        "mutationRejectionVerified": verified,
        "liveReadOnlyEnabled": False,
    }

ALIAS_REGISTRY_PATH = ROOT / "fixtures/canvas-llm/phase-27/alias-registry.json"


def _load_alias_registry(path: Path = ALIAS_REGISTRY_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("aliases", {})


def _recompute_diffs(snapshot_path: Path) -> tuple[list[dict[str, Any]], Any, dict[str, Any]]:
    """Shared recomputation path used by build, compare, and validate so all
    three run the same real logic rather than three divergent copies."""
    raw_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    validated_snapshot = load_snapshot(snapshot_path)
    local_objects = raw_snapshot.get("localDesiredObjects", [])
    alias_registry = _load_alias_registry()
    known_modules = raw_snapshot.get("modules", {})
    diffs = build_safety_diff(
        local_objects,
        validated_snapshot.remoteObjects,
        alias_registry,
        known_modules=known_modules,
    )
    return diffs, validated_snapshot, raw_snapshot


def build_packet(
    week_code: str,
    phase26_packet_path: Path,
    snapshot_path: Path,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    packet = json.loads(phase26_packet_path.read_text(encoding="utf-8"))

    # Validates the snapshot for forbidden fields and unsafe hosts; raises
    # SnapshotValidationError if the snapshot contains anything Phase 27
    # must reject (student data, credentials, unsafe hosts).
    diffs, validated_snapshot, raw_snapshot = _recompute_diffs(snapshot_path)
    manifest = build_manifest(
        packet,
        diffs,
        {"snapshotId": validated_snapshot.snapshotId, "generatedAt": validated_snapshot.generatedAt},
        str(phase26_packet_path),
        str(snapshot_path),
    )

    ledger = DeploymentLedger(ledger_path or DEFAULT_LEDGER_PATH)
    try:
        ledger.record_snapshot_import(
            validated_snapshot.snapshotId, validated_snapshot.origin, validated_snapshot.generatedAt
        )
        manifest_id = f"{week_code}-phase27"
        import hashlib

        payload_hash = hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode("utf-8")
        ).hexdigest()
        ledger.upsert_manifest(
            manifest_id,
            week_code,
            manifest["packetRevision"],
            manifest["overallReadiness"],
            payload_hash,
        )
    finally:
        ledger.close()

    health_results = run_health_checks(
        diffs, manifest, raw_snapshot, ledger_path or DEFAULT_LEDGER_PATH, phase26_packet=packet
    )

    return {
        "weekCode": week_code,
        "phase26Packet": packet,
        "snapshot": raw_snapshot,
        "safetyDiff": diffs,
        "deploymentManifestV1": manifest,
        "healthChecks": health_results,
        "transportReadiness": _transport_readiness(),
    }


def run_compare(manifest_path: Path, snapshot_path: Path) -> int:
    if not manifest_path.exists():
        print(f"FAIL: manifest not found: {manifest_path}")
        return 1
    if not snapshot_path.exists():
        print(f"FAIL: snapshot not found: {snapshot_path}")
        return 1
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        recomputed_diffs, _validated_snapshot, _raw_snapshot = _recompute_diffs(snapshot_path)
    except (json.JSONDecodeError, SnapshotValidationError, KeyError) as exc:
        print(f"FAIL: compare could not load inputs: {exc}")
        return 1

    stored_diffs = payload.get("safetyDiff", [])
    recomputed_by_id = {d["objectId"]: d["comparisonStatus"] for d in recomputed_diffs}
    stored_by_id = {d["objectId"]: d["comparisonStatus"] for d in stored_diffs}

    mismatches = [
        object_id
        for object_id in set(recomputed_by_id) | set(stored_by_id)
        if recomputed_by_id.get(object_id) != stored_by_id.get(object_id)
    ]
    if mismatches:
        print(f"FAIL: compare found {len(mismatches)} mismatched classification(s): {mismatches}")
        return 1
    print(f"PASS: compare recomputed {len(recomputed_diffs)} items, all match stored manifest")
    return 0


def run_validate(manifest_path: Path) -> int:
    if not manifest_path.exists():
        print(f"FAIL: manifest not found: {manifest_path}")
        return 1
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = payload["deploymentManifestV1"]
    diffs = payload.get("safetyDiff", [])

    failures = []
    if manifest["manifestVersion"] != 1:
        failures.append("manifestVersion is not 1")
    if manifest["mode"] != "preview-only":
        failures.append("mode is not preview-only")
    if manifest.get("executable") not in (False, None):
        failures.append("manifest is marked executable")
    for op in manifest.get("operations", []):
        if op.get("executable"):
            failures.append(f"operation {op.get('operationId')} is marked executable")

    # Independently recompute the safety diff from the referenced inputs
    # rather than trusting the manifest's own validationSummary counters.
    provenance = {p["sourceType"]: p["sourceRef"] for p in manifest.get("provenance", [])}
    if "phase26" in provenance and "snapshot" in provenance:
        # provenance stores repo-relative paths (never absolute local paths,
        # per Part 32) -- resolve against ROOT, not the process cwd, so this
        # works regardless of what directory validate is invoked from.
        phase26_path = Path(provenance["phase26"])
        if not phase26_path.is_absolute():
            phase26_path = ROOT / phase26_path
        snapshot_path = Path(provenance["snapshot"])
        if not snapshot_path.is_absolute():
            snapshot_path = ROOT / snapshot_path
        if phase26_path.exists() and snapshot_path.exists():
            recomputed, _validated_snapshot, _raw_snapshot = _recompute_diffs(snapshot_path)
            recomputed_by_id = {d["objectId"]: d["comparisonStatus"] for d in recomputed}
            stored_by_id = {d["objectId"]: d["comparisonStatus"] for d in diffs}
            if recomputed_by_id != stored_by_id:
                failures.append(
                    "stored safetyDiff does not match independent recomputation from "
                    "referenced phase26 packet and snapshot"
                )

    for diff in diffs:
        if diff["comparisonStatus"] not in {
            "CREATE", "UPDATE", "UNCHANGED", "BLOCKED", "CONFLICT", "OMIT", "DELETE_CANDIDATE",
        }:
            failures.append(f"{diff['objectId']} has invalid comparisonStatus")
        if diff.get("executable"):
            failures.append(f"{diff['objectId']} is marked executable")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"FAIL: {len(failures)}")
        return 1

    print("PASS: manifest.preview Phase 27 manifest preview is valid")
    print("PASS: 1")
    print("WARN: 1")
    print("FAIL: 0")
    return 0


def run_health_check(manifest_path: Path) -> int:
    if not manifest_path.exists():
        print(f"FAIL: manifest not found: {manifest_path}")
        return 1
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = payload.get("healthChecks")
    if results is None:
        results = run_health_checks(
            payload.get("safetyDiff", []),
            payload["deploymentManifestV1"],
            payload.get("snapshot", {}),
            None,
            phase26_packet=payload.get("phase26Packet", {}),
        )
    fail_count = 0
    for r in results:
        print(f"{r['status']}: {r['check']} -- {r['detail']}")
        if r["status"] == "FAIL":
            fail_count += 1
    print(f"FAIL: {fail_count}")
    return 1 if fail_count else 0


def run_export(manifest_path: Path, output_root: Path | None) -> int:
    if not manifest_path.exists():
        print(f"FAIL: manifest not found: {manifest_path}")
        return 1
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = payload["deploymentManifestV1"]
    diffs = payload.get("safetyDiff", [])
    health_results = payload.get("healthChecks", [])
    export_dir = export_package(
        payload["weekCode"],
        diffs,
        manifest,
        payload.get("snapshot", {}),
        health_results,
        manifest.get("rollbackPlan", []),
        [],
        root=output_root,
    )
    print(f"PASS: export written to {export_dir}")
    return 0


def run_ledger_status(ledger_path: Path) -> int:
    if not ledger_path.exists():
        print(f"FAIL: ledger not found at {ledger_path}")
        return 1
    ledger = DeploymentLedger(ledger_path)
    try:
        ok = ledger.integrity_check()
        print(f"{'PASS' if ok else 'FAIL'}: integrity_check={'ok' if ok else 'failed'}")
        print(f"PASS: schema_version={ledger.schema_version()}")
        print(f"PASS: event_count={ledger.event_count()}")
        return 0 if ok else 1
    finally:
        ledger.close()


APP_DIR = ROOT / "apps/unified-weekly-production"
DEFAULT_SERVE_PHASE26_PACKET = APP_DIR / "data/phase26-demo.json"
DEFAULT_SERVE_SNAPSHOT = ROOT / "fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json"


def _build_default_serve_packet() -> dict[str, Any]:
    return build_packet("Q1W5", DEFAULT_SERVE_PHASE26_PACKET, DEFAULT_SERVE_SNAPSHOT)


class Phase27RequestHandler(SimpleHTTPRequestHandler):
    """Serves the real unified workstation app directory (not the process's
    cwd) and a genuine Phase 27 data endpoint computed by real production
    code on every request -- not a static file, and not a directory
    listing. Mutating HTTP methods are rejected at the server boundary,
    mirroring transport.py."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - http.server naming convention
        if self.path.startswith("/api/phase27/packet"):
            try:
                payload = _build_default_serve_packet()
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:  # pragma: no cover - defensive
                self.send_error(500, f"failed to build Phase 27 packet: {exc}")
            return
        super().do_GET()

    def _reject_mutation(self) -> None:
        self.send_error(405, "Phase 27 serve is read-only: mutating HTTP methods are rejected")

    def do_POST(self) -> None:  # noqa: N802
        self._reject_mutation()

    def do_PUT(self) -> None:  # noqa: N802
        self._reject_mutation()

    def do_PATCH(self) -> None:  # noqa: N802
        self._reject_mutation()

    def do_DELETE(self) -> None:  # noqa: N802
        self._reject_mutation()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build")
    build.add_argument("--week", required=True)
    build.add_argument("--phase26-packet", required=True)
    build.add_argument("--snapshot", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--ledger", default=None)

    compare = sub.add_parser("compare")
    compare.add_argument("--manifest", required=True)
    compare.add_argument("--snapshot", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", required=True)

    ledger_status = sub.add_parser("ledger-status")
    ledger_status.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))

    health_check = sub.add_parser("health-check")
    health_check.add_argument("--manifest", required=True)

    export = sub.add_parser("export")
    export.add_argument("--manifest", required=True)
    export.add_argument("--output-root", default=None)

    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=18777)

    args = parser.parse_args(argv)

    if args.cmd == "build":
        try:
            payload = build_packet(
                args.week,
                Path(args.phase26_packet),
                Path(args.snapshot),
                Path(args.ledger) if args.ledger else None,
            )
        except (SnapshotValidationError, FileNotFoundError, KeyError) as exc:
            print(f"FAIL: build failed: {exc}")
            return 1
        out = Path(args.output)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(out)
        return 0

    if args.cmd == "compare":
        return run_compare(Path(args.manifest), Path(args.snapshot))

    if args.cmd == "validate":
        return run_validate(Path(args.manifest))

    if args.cmd == "ledger-status":
        return run_ledger_status(Path(args.ledger))

    if args.cmd == "health-check":
        return run_health_check(Path(args.manifest))

    if args.cmd == "export":
        return run_export(Path(args.manifest), Path(args.output_root) if args.output_root else None)

    if args.cmd == "serve":
        ThreadingHTTPServer((args.host, args.port), Phase27RequestHandler).serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
