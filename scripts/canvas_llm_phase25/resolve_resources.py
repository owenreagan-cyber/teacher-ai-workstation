#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase25.correction_memory import load_correction_state, save_resource_correction  # noqa: E402
from scripts.canvas_llm_phase25.integration import build_phase25_packet  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def command_build_demo(args: argparse.Namespace) -> int:
    packet = build_phase25_packet(args.week, Path(args.predictions), Path(args.registry), Path(args.corrections))
    out = Path(args.out)
    write_json(out, packet.to_dict())
    print(f"Phase 25 resource-resolution packet rebuilt: {out}")
    return 0


def command_self_test(args: argparse.Namespace) -> int:
    packet = build_phase25_packet(args.week, Path(args.predictions), Path(args.registry), Path(args.corrections))
    payload = packet.to_dict()
    assert payload["validation"]["failCount"] == 0
    assert payload["validation"]["warnCount"] == 2
    assert any(item["resolutionMethod"] == "exact-verified-match" for item in payload["resolvedResources"])
    assert any(item["resolutionMethod"] == "owner-approved-correction" for item in payload["resolvedResources"])
    assert any(item["resolutionMethod"] == "approved-parity-or-family-match" for item in payload["resolvedResources"])
    assert any(item["resolutionMethod"] == "unresolved" for item in payload["resolvedResources"])
    assert any(item["status"] == "Needs Review" for item in payload["reviewQueue"])
    assert any(item["status"] == "Blocked" for item in payload["reviewQueue"])
    assert any(item["status"] == "Teacher-Only" for item in payload["reviewQueue"])
    assert any(item["status"] == "Conflicting" for item in payload["reviewQueue"])
    assert payload["phase23Preview"]["deploymentState"] == "preview-only"
    assert payload["phase23Preview"]["approvalState"] == "draft"
    assert all("Checkout 14" not in json.dumps(item, ensure_ascii=False) for item in payload["phase23Preview"]["assessmentReminders"])
    state = load_correction_state(Path(args.state))
    assert state["status"] == "saved"
    save = save_resource_correction(
        {
            "subject": "math",
            "weekCode": "Q1W5",
            "day": "Monday",
            "requiredResourceClass": "worksheet",
            "predictedResourceId": "SM5-L18-WORKSHEET-LEGACY",
            "approvedResourceId": "SM5-LESSON-1-20-WORKSHEET",
            "correctionScope": "this lesson",
            "timestamp": "2026-07-11T00:00:00Z",
            "reason": "Legacy alias maps to the approved lesson-range worksheet",
            "sourceRule": "teacher.resource.override",
            "revision": 1,
        },
        0,
        Path(args.state),
    )
    assert save["status"] == "saved"
    conflict = save_resource_correction(
        {
            "subject": "math",
            "weekCode": "Q1W5",
            "day": "Monday",
            "requiredResourceClass": "worksheet",
            "predictedResourceId": "SM5-L18-WORKSHEET-LEGACY",
            "approvedResourceId": "SM5-LESSON-1-20-WORKSHEET",
            "correctionScope": "this lesson",
            "timestamp": "2026-07-11T00:00:00Z",
            "reason": "Legacy alias maps to the approved lesson-range worksheet",
            "sourceRule": "teacher.resource.override",
            "revision": 2,
        },
        0,
        Path(args.state),
    )
    assert conflict["status"] == "conflict"
    print("PASS Phase 25 self-test complete")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    from scripts.canvas_llm_phase25.validate_resolution import main as validate_main  # noqa: E402

    original_argv = sys.argv
    try:
        sys.argv = ["validate_resolution.py", *args.paths]
        return validate_main()
    finally:
        sys.argv = original_argv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 25 curriculum source intelligence and resource resolver")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_demo = sub.add_parser("build-demo", help="Build the committed demo resolution packet")
    build_demo.add_argument("--out", default=".local/canvas-llm/phase-25-curriculum-source-intelligence/phase25-demo.json")
    build_demo.add_argument("--week", default="Q1W5")
    build_demo.add_argument("--predictions", default="fixtures/canvas-llm/phase-25/phase24-predicted-week.json")
    build_demo.add_argument("--registry", default="fixtures/canvas-llm/phase-25/resource-registry.json")
    build_demo.add_argument("--corrections", default="fixtures/canvas-llm/phase-25/resource-corrections.json")
    build_demo.set_defaults(func=command_build_demo)

    validate = sub.add_parser("validate", help="Validate packet JSON files")
    validate.add_argument("paths", nargs="+")
    validate.add_argument("--week", default="Q1W5")
    validate.add_argument("--predictions", default="fixtures/canvas-llm/phase-25/phase24-predicted-week.json")
    validate.add_argument("--registry", default="fixtures/canvas-llm/phase-25/resource-registry.json")
    validate.add_argument("--corrections", default="fixtures/canvas-llm/phase-25/resource-corrections.json")
    validate.set_defaults(func=command_validate)

    self_test = sub.add_parser("self-test", help="Run deterministic packet assertions")
    self_test.add_argument("--week", default="Q1W5")
    self_test.add_argument("--predictions", default="fixtures/canvas-llm/phase-25/phase24-predicted-week.json")
    self_test.add_argument("--registry", default="fixtures/canvas-llm/phase-25/resource-registry.json")
    self_test.add_argument("--corrections", default="fixtures/canvas-llm/phase-25/resource-corrections.json")
    self_test.add_argument("--state", default=".local/canvas-llm/phase-25-curriculum-source-intelligence/resource-corrections.json")
    self_test.set_defaults(func=command_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
