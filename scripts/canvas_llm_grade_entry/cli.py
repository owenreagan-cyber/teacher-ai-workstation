#!/usr/bin/env python3
"""CLI for the bounded grade-entry capability (default: read-only preview).

Commands:
    packet   --request request.json [--out packet.json] [--live] [--fake]
             Build and print the approval packet. Never writes grades.
    apply    --packet packet.json --approve --approved-by "Name" [--live] [--fake]
             Apply an explicitly approved packet, then read back and verify.
    self-test
             Deterministic guard tests (offline, no credentials, no network).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_entry import fake_canvas  # noqa: E402
from scripts.canvas_llm_grade_entry import grade_entry as ge  # noqa: E402

DEFAULT_PACKET_DIR = REPO_ROOT / ".local" / "canvas-llm" / "grade-entry"


def _client(*, live: bool, fake: bool):
    if fake:
        return fake_canvas.ela4_course().client(), "fake"
    if not live:
        raise ge.GradeEntryError(
            "BLOCKED: choose --live or --fake; no implicit Canvas source is used"
        )
    from scripts.canvas_llm_phase22 import canvas_credentials as credentials

    credentials.load_credentials()
    return ge.CanvasGradeClient.from_env(), "live"


def command_packet(args: argparse.Namespace) -> int:
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    client, source = _client(live=bool(args.live), fake=bool(args.fake))
    packet = ge.build_packet(request=request, client=client)
    out = Path(args.out) if args.out else DEFAULT_PACKET_DIR / f"{packet.packet_hash[:12]}-packet.json"
    packet.write(out)
    print(f"source: {source} (no grades written)")
    print(packet.render())
    print(f"\npacket file: {out}")
    return 0


def command_apply(args: argparse.Namespace) -> int:
    packet = ge.ApprovalPacket.load(Path(args.packet))
    client, source = _client(live=bool(args.live), fake=bool(args.fake))
    if not args.approve:
        print("BLOCKED: --approve is required to apply a packet; nothing written")
        return 1
    ge.enable(owner=args.approved_by)
    report = ge.apply_packet(packet=packet, client=client, approved=True,
                             approved_by=args.approved_by)
    out = Path(args.out) if args.out else DEFAULT_PACKET_DIR / f"{packet.packet_hash[:12]}-result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": source, **report}, indent=2), encoding="utf-8")
    print(f"source: {source}")
    for row in report["results"]:
        print(
            f"  {row['action']:15s} {row['student_name']} (id {row['student_id']}): "
            f"{ge.format_grade(row['previous_grade'])} -> "
            f"{ge.format_grade(row['readback_grade'])} "
            f"{'OK' if row['verified'] else 'MISMATCH'}"
        )
    print(f"\nwrites performed: {report['writes_performed']}")
    print(f"already correct:  {report['already_correct']}")
    print(f"other assignments touched: {report['other_assignments_touched']}")
    print(f"other courses touched: {report['other_courses_touched']}")
    print(f"readback verified: {'PASS' if report['readback_verified'] else 'FAIL'}")
    for mismatch in report["readback_mismatches"]:
        print(f"  MISMATCH: {mismatch}")
    print(f"result file: {out}")
    return 0 if report["readback_verified"] else 1


def command_self_test(_args: argparse.Namespace) -> int:
    from scripts.canvas_llm_grade_entry import tests as grade_entry_tests

    grade_entry_tests.run_all()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded Canvas grade entry (disabled by default)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_packet = sub.add_parser("packet", help="build an approval packet (no writes)")
    p_packet.add_argument("--request", required=True)
    p_packet.add_argument("--out")
    p_packet.add_argument("--live", action="store_true")
    p_packet.add_argument("--fake", action="store_true")
    p_packet.set_defaults(func=command_packet)

    p_apply = sub.add_parser("apply", help="apply an approved packet")
    p_apply.add_argument("--packet", required=True)
    p_apply.add_argument("--approve", action="store_true")
    p_apply.add_argument("--approved-by", required=True)
    p_apply.add_argument("--out")
    p_apply.add_argument("--live", action="store_true")
    p_apply.add_argument("--fake", action="store_true")
    p_apply.set_defaults(func=command_apply)

    sub.add_parser("self-test").set_defaults(func=command_self_test)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ge.GradeEntryError as exc:
        print(ge.redact(str(exc)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
