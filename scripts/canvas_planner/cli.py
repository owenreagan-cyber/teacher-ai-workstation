"""CLI for the local Canvas weekly planning status contract."""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from .service import CanvasPlannerService


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="canvas-weekly-status")
    p.add_argument("--json", action="store_true", help="emit the versioned JSON contract")
    p.add_argument("--quarter", type=int)
    p.add_argument("--week", type=int)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if (args.quarter is None) != (args.week is None):
        parser().error("--quarter and --week must be supplied together")
    status = CanvasPlannerService().weekly_status(args.quarter, args.week)
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(f"{status['week']['code']} · {status['week']['label']}")
        print(f"State: {status['week']['state']}")
        print(f"Next: {status['next_action']['title']}")
        print(f"Open items: {len(status['action_items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
