#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/programs/canvas-llm/current-handoff.md"
SCRIPTS = ROOT / "scripts"
SECTION_TITLE = "## Machine-Maintained Handoff Breadcrumb Guardrail"


@dataclass(frozen=True)
class Breadcrumb:
    script: str
    label: str
    pattern: str


def extract_patterns() -> list[Breadcrumb]:
    items: list[Breadcrumb] = []

    for path in sorted(SCRIPTS.glob("canvas-llm-phase-*.sh")):
        src = path.read_text(errors="ignore")
        for line in src.splitlines():
            if "check_contains" not in line:
                continue
            if "HANDOFF" not in line and "handoff" not in line.lower():
                continue

            match = re.search(
                r'check_contains\s+"([^"]*(?:HANDOFF|handoff)[^"]*)"\s+"([^"]+)"\s+"([^"]+)"',
                line,
            )
            if not match:
                continue

            _target, pattern, label = match.groups()
            items.append(
                Breadcrumb(
                    script=str(path.relative_to(ROOT)),
                    label=label,
                    pattern=pattern,
                )
            )

    manual = [
        Breadcrumb("manual", "handoff references PR #300 baseline", "PR #300 baseline: 5af1ecd"),
        Breadcrumb("manual", "handoff references PR #300 baseline exact phrase", "Current handoff references PR #300 baseline: 5af1ecd"),
        Breadcrumb("manual", "handoff records PR #301 baseline", "PR #301 baseline: f61dae2"),
        Breadcrumb("manual", "handoff records PR #301 baseline exact phrase", "Current handoff records PR #301 baseline: f61dae2"),
    ]

    seen = set()
    deduped: list[Breadcrumb] = []

    for item in items + manual:
        if item.pattern in seen:
            continue
        seen.add(item.pattern)
        deduped.append(item)

    return deduped


def render_missing_section(missing: list[Breadcrumb]) -> str:
    lines = [
        "",
        "---",
        "",
        SECTION_TITLE,
        "",
        "This section is maintained by `scripts/canvas-llm-handoff-breadcrumb-repair.py`.",
        "",
        "Do not manually delete this section during phase handoff edits.",
        "",
    ]

    for item in missing:
        lines += [
            f"### {item.label}",
            "",
            f"Source: `{item.script}`",
            "",
            "```text",
            item.pattern,
            "```",
            "",
            item.pattern,
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()

    if not args.check and not args.repair:
        parser.error("use --check or --repair")

    handoff_text = HANDOFF.read_text()
    patterns = extract_patterns()
    missing = [item for item in patterns if item.pattern not in handoff_text]

    print("Canvas LLM Handoff Breadcrumb Guardrail")
    print("--------------------------------------")
    print(f"checked_patterns: {len(patterns)}")
    print(f"missing_patterns: {len(missing)}")

    for item in missing:
        print(f"MISSING: {item.label} :: {item.pattern}")

    if args.check:
        if missing:
            print("FAIL: missing handoff breadcrumbs")
            return 1
        print("PASS: all handoff breadcrumbs are present")
        return 0

    if args.repair:
        if missing:
            HANDOFF.write_text(handoff_text.rstrip() + "\n" + render_missing_section(missing))
            print(f"PASS: appended {len(missing)} missing breadcrumbs")
        else:
            print("PASS: no repair needed")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
