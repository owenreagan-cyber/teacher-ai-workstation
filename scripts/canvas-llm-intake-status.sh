#!/usr/bin/env bash
# Canvas Weekly Intake status (PASS/WARN/FAIL proof only — no approve, no publish).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

exec python3 -m scripts.canvas_llm_intake.cli status
