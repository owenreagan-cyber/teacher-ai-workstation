from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase27.phase27_readiness import run_validate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    paths = argv if argv is not None else sys.argv[1:]
    worst = 0
    for raw in paths:
        result = run_validate(Path(raw))
        worst = max(worst, result)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
