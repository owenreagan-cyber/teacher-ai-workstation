"""Answer guards: deterministic checks on model-written text before Owen sees it.

The model proposes words; code decides what reaches Owen (D-003). Two guards:

  scrub_cleanup(answer, question)
      Chief never suggests deleting files, emptying the Trash, or running a destructive command
      (rm, ollama rm, tmutil deletelocalsnapshots, ...) as a fix, unless Owen asked to delete or
      remove something. Each sentence (or list line) that suggests one is dropped; a sentence
      that only warns against one ("don't use ollama rm: it deletes the model") is kept. If
      anything was dropped, a fixed note says so. If nothing is left, a fixed answer replaces it.
      When Owen asked to clear or empty something ("how do I clear the cache?"), "clear <thing>"
      steps (Clear browsing data) are kept; deleting files and destructive commands are not.

  scrub_unload(answer, loaded)
      `ollama stop <name>` may only name a model that is loaded right now (ollama ps, via
      mac.status). Any other name, or every name when the loaded list is unknown, becomes the
      placeholder `ollama stop <model>`.

These patterns are written independently of the harness checks (evals/harness/checks.py), so
the harness tests cos against the rule rather than against itself.
"""
from __future__ import annotations

import re

CLEANUP_NOTE = "I left out steps that delete files or empty the Trash; Chief doesn't suggest deleting things as a fix."
CLEANUP_EMPTY = ("I don't suggest deleting files or emptying the Trash as a fix. Ask \"how's my Mac\" "
                 "for free disk space; macOS's own Storage settings show what is using it.")

# Owen asked to delete something: destructive suggestions about it are allowed.
DELETE_REQUEST = re.compile(r"\b(?:delete|deleting|remove|removing|uninstall|erase|wipe|purge|get rid of|rm)\b",
                            re.IGNORECASE)
# Owen asked to clear or empty something: plain-language steps for it are allowed (not commands).
CLEAR_REQUEST = re.compile(r"\b(?:clear|clearing|empty|emptying|clean out)\b", re.IGNORECASE)

COMMANDS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"(?<![\w-])(?:sudo\s+)?rm\s+(?:-\w+\s+)*[~/.\w<$*\"'`]",
    r"\bollama\s+rm\b",
    r"\btmutil\s+delete",
    r"\bfind\b[^\n]*\s-delete\b",
    r"\bgit\s+(?:reset\s+--hard|clean)\b",
    r"\brmdir\b",
    r"\bshred\b",
    r"\bsrm\b",
    r"\bdiskutil\s+(?:erase|zerodisk|reformat|secureerase|partitiondisk)",
    r"\bbrew\s+(?:uninstall|remove|rm|cleanup|autoremove)\b",
    r"\bdocker\s+(?:system\s+prune|image\s+prune|volume\s+(?:rm|prune)|rmi?\b)",
    r"\b(?:npm|yarn|pnpm)\s+cache\s+clean\b",
    r"\bpip3?\s+cache\s+(?:purge|remove)\b",
    r"\bdefaults\s+delete\b",
    r"\bsecurity\s+delete-",
))
_THINGS = (r"\b(?:files?|folders?|caches?|downloads|snapshots?|models?|apps?|applications|installers?|"
           r"attachments|backups?|logs?|photos|videos|items|data|dmgs?|disk images?)\b")
# Deleting files or emptying the Trash: never suggested as a fix.
PLAIN = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\bempty(?:ing)?\s+(?:the\s+|your\s+)?(?:trash|bin)\b",
    r"\bempty\s+trash\b",
    r"\b(?:delete|deleting|remove|removing|erase|wipe|purge|trash|clear(?:ing)?\s+out|clean(?:ing)?\s+out|"
    r"uninstall)\b[^.\n]{0,60}?" + _THINGS,
    r"\b(?:can|could|may|might)\s+(?:often\s+|usually\s+|safely\s+)?be\s+(?:deleted|removed|trashed)\b",
))
# "Clear <something>": allowed only when Owen asked to clear or empty something.
CLEAR = (re.compile(r"\bclear(?:ing)?\b[^.\n]{0,60}?" + _THINGS, re.IGNORECASE),)
# A sentence that only warns against a destructive step, or says Chief can't do it, is kept.
WARNING = re.compile(r"\b(?:don'?t|do not|never|avoid|instead of|rather than|warning|careful|caution|"
                     r"not recommended|shouldn'?t|should not|doesn'?t|does not|isn'?t|is not|deletes|erases|"
                     r"wipes|permanently|i can'?t|i cannot|i can not|i'?m unable|i am unable|i'?m not able|"
                     r"i am not able|i won'?t)\b", re.IGNORECASE)
EMPTY_REQUEST = re.compile(r"\bempty(?:ing)?\b", re.IGNORECASE)
EMPTY_FENCE = re.compile(r"^[ \t]*```[\w-]*[ \t]*\n(?:[ \t]*\n)*[ \t]*```[ \t]*$", re.MULTILINE)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=\S)")
LIST_MARKER = re.compile(r"^(\s*)(?:(\d+)([.)])|[-*•])\s+")
EMPTY_LINE = re.compile(r"^\s*(?:(?:\d+[.)])|[-*•])?\s*(?:\*\*[^*]*\*\*\s*:?)?\s*$")


def _normalize(text: str) -> str:
    return text.replace("’", "'").replace("‘", "'")


def _suggests(sentence: str, patterns) -> bool:
    s = _normalize(sentence)
    return any(p.search(s) for p in patterns) and not WARNING.search(s)


def _renumber(lines: list[str]) -> list[str]:
    """Number each run of numbered list lines 1, 2, 3 ... per indentation level."""
    counters: dict[int, int] = {}
    out = []
    for line in lines:
        m = LIST_MARKER.match(line)
        if m and m.group(2):
            indent = len(m.group(1))
            counters = {k: v for k, v in counters.items() if k <= indent}
            counters[indent] = counters.get(indent, 0) + 1
            line = f"{m.group(1)}{counters[indent]}{m.group(3)} " + line[m.end():]
        elif line.strip() and not line.startswith((" ", "\t")) and not m:
            counters = {}
        out.append(line)
    return out


def scrub_cleanup(answer: str, question: str) -> tuple[str, bool]:
    """(answer, removed) with destructive or delete-as-a-fix suggestions dropped."""
    if DELETE_REQUEST.search(question or ""):
        return answer, False
    plain = PLAIN[2:] if EMPTY_REQUEST.search(question or "") else PLAIN  # asked to empty the Trash
    patterns = COMMANDS + plain + (() if CLEAR_REQUEST.search(question or "") else CLEAR)
    kept_lines, removed = [], False
    dropped_indent: int | None = None
    for line in answer.split("\n"):
        indent = len(line) - len(line.lstrip())
        if dropped_indent is not None and line.strip() and indent > dropped_indent:
            removed = True  # a sub-item of a dropped list item goes with it
            continue
        dropped_indent = None
        marker = LIST_MARKER.match(line)
        prefix = line[:marker.end()] if marker else ""
        sentences = SENTENCE_END.split(line[len(prefix):])
        kept = [s for s in sentences if not _suggests(s, patterns)]
        if len(kept) == len(sentences):
            kept_lines.append(line)
            continue
        removed = True
        if marker and _suggests(sentences[0], patterns):
            dropped_indent = indent  # the item's lead step was dropped: drop the whole item
            continue
        rest = prefix + " ".join(kept)
        if not EMPTY_LINE.match(rest):
            kept_lines.append(rest)
    if not removed:
        return answer, False
    text = "\n".join(_renumber(kept_lines))
    text = EMPTY_FENCE.sub("", text)  # a code block whose command was dropped
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not re.search(r"[A-Za-z]{3}", text):
        return CLEANUP_EMPTY, True
    return text, True


OLLAMA_STOP = re.compile(r"(\bollama\s+stop\s+)(`?)([A-Za-z0-9][\w.:/-]*)(`?)")


def scrub_unload(answer: str, loaded: list[str] | None) -> tuple[str, bool]:
    """(answer, changed): `ollama stop <name>` names only a loaded model, else the placeholder."""
    names = set(loaded or [])
    names |= {n.removesuffix(":latest") for n in names}
    changed = False

    def fix(m):
        nonlocal changed
        name = m.group(3).rstrip(".,;:")
        if name in names:
            return m.group(0)
        changed = True
        return f"{m.group(1)}{m.group(2)}<model>{m.group(4)}{m.group(3)[len(name):]}"

    return OLLAMA_STOP.sub(fix, answer), changed


def mentions_unload(answer: str) -> bool:
    """The answer names a specific model in an ollama stop command (so the loaded list is needed)."""
    return OLLAMA_STOP.search(answer) is not None
