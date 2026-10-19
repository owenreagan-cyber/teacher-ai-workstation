"""``python3 -m scripts.canvas_llm_rollover`` runs the package self-test."""
from __future__ import annotations

from scripts.canvas_llm_rollover import command_self_test

if __name__ == "__main__":
    raise SystemExit(command_self_test())
