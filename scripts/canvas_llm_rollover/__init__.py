"""Friday 4 PM Canvas weekly rollover workflow (pure/deterministic core).

This package adds the canonical Friday rollover on top of the existing intake
+ guarded-deployment architecture. It never performs Canvas writes on its own:
production writes require an explicit ``--production`` flag plus owner
confirmation, and are gated behind the same client + ledger primitives used by
``scripts/canvas_llm_deploy``.

Modules:

- ``schedule``   : Friday 4:00 PM America/New_York scheduling + lifecycle.
- ``narrative``  : subject-isolated Week-in-Review / Next-Week-Overview.
- ``homeroom``   : legacy newsletter copy-forward (retained, not published).
- ``homeroom_weekly`` : weekly Homeroom page architecture (current).
- ``birthdays``  : private Class 4-A birthday service.
- ``manifest``   : deterministic rollover plan builder.
- ``ledger``     : untracked rollover deployment ledger.
- ``rollover``   : readiness gate, GET-only preflight, guarded execution.
- ``cli``        : manual fallback command.
"""
from __future__ import annotations

from . import birthdays, homeroom, homeroom_weekly, ledger, manifest, narrative, rollover, schedule

__all__ = [
    "birthdays", "homeroom", "homeroom_weekly", "ledger", "manifest",
    "narrative", "rollover", "schedule",
]


def command_self_test() -> int:
    birthdays.command_self_test()
    schedule.command_self_test()
    narrative.command_self_test()
    homeroom.command_self_test()
    homeroom_weekly.command_self_test()
    manifest.command_self_test()
    ledger.command_self_test()
    rollover.command_self_test()
    print("PASS canvas-rollover package self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
