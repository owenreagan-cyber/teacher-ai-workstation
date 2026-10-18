"""Read-only loading of identity and the small core of assistant memory.

Files are read where they are and never written. Long files are condensed
deterministically (headings and leading bullets up to a character budget),
so the always-loaded context stays small. No model is used to summarize.
"""
from __future__ import annotations

from pathlib import Path

IDENTITY_PATH = Path(__file__).resolve().parent / "identity.md"
# Owner-editable voice and style. Loaded after identity and before the tool and safety rules,
# which take precedence over it (agent.build_system_prompt).
PERSONALITY_PATH = Path(__file__).resolve().parent / "personality.md"
PERSONALITY_BUDGET = 3000

# (repo-relative path, section heading to start at or None, char budget)
CORE_FILES = (
    ("assistant/chief-of-staff.md", None, 900),
    ("assistant/memory/teaching-context.md", "## Stable Context", 500),
    ("assistant/memory/preferences.md", "## Tool Preferences", 600),
    ("assistant/memory/projects.md", "## Active Projects", 1200),
    ("assistant/memory/active-priorities.md", "### Now", 900),
)
TOTAL_BUDGET = 4500
LINE_CAP = 180


def condense(text: str, budget: int, start_heading: str | None = None) -> str:
    lines = text.splitlines()
    if start_heading is not None:
        for i, line in enumerate(lines):
            if line.strip() == start_heading:
                lines = lines[i:]
                break
    out, used, dropped = [], 0, False
    for line in lines:
        stripped = line.strip()
        if not stripped or "TODO: ask Owen" in stripped:
            continue
        if len(stripped) > LINE_CAP:
            stripped = stripped[:LINE_CAP - 1] + "…"
        if used + len(stripped) + 1 > budget:
            dropped = True
            break
        out.append(stripped)
        used += len(stripped) + 1
    if dropped:
        out.append("[…condensed]")
    return "\n".join(out)


def load_identity(path: Path = IDENTITY_PATH) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_personality(path: Path = PERSONALITY_PATH) -> str:
    """The personality spec, or "" if the file is missing or unreadable (Chief still runs).
    Capped so an edit cannot crowd out the rules that follow it."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""
    return text if len(text) <= PERSONALITY_BUDGET else text[:PERSONALITY_BUDGET] + "\n[…truncated]"


def load_memory(repo_root: Path) -> tuple[str, list[str]]:
    """Return (context text, list of source paths used)."""
    parts, sources, used = [], [], 0
    for rel, heading, budget in CORE_FILES:
        path = Path(repo_root) / rel
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        chunk = condense(text, min(budget, TOTAL_BUDGET - used), heading)
        if not chunk:
            continue
        parts.append(f"### From {rel}\n{chunk}")
        sources.append(rel)
        used += len(chunk)
        if used >= TOTAL_BUDGET:
            break
    return "\n\n".join(parts), sources
