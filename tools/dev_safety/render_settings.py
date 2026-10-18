#!/usr/bin/env python3
"""Render the D1 Claude Code settings from one source (stdlib only).

Writes two files next to this script:

  settings.proposed.json  the project profile. Owen copies it to <repo>/.claude/settings.json
                          (the agent cannot: D1 and the sandbox both deny writes there).
  sandbox-lock.json       the sandbox lock. install_dev_guard.py installs it read-only to
                          ~/.claude/hooks/cos/, and Owen starts sessions with
                          `claude --settings ~/.claude/hooks/cos/sandbox-lock.json`.
                          Passing it with --settings makes the sandbox admin-required, so
                          the repo's own files cannot loosen it, and turns on strictAllowlist,
                          which Claude Code ignores in project settings.

Run `python3 tools/dev_safety/render_settings.py` after changing this file or
student_data_roots.txt; `--check` exits 1 when the committed files are stale.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "settings.proposed.json")
LOCK = os.path.join(HERE, "sandbox-lock.json")

# Home-relative paths no Claude Code tool or sandboxed command may read or write.
CREDENTIAL_PATHS = [
    "~/.ssh", "~/.aws", "~/.gnupg", "~/.config/gh", "~/.netrc", "~/.docker", "~/.kube",
    "~/.npmrc", "~/.pgpass", "~/.config/op", "~/.config/gcloud",
]
CLAUDE_PATHS = ["~/.claude.json", "~/.claude/settings.json", "~/.claude/settings.local.json",
                "~/.claude/projects"]
PRIVATE_PATHS = ["~/.teacher-ai-workstation", "~/Downloads", "~/Library/Application Support/ChiefOfStaff"]
ROOTS_FILE = os.path.join(HERE, "student_data_roots.txt")
FALLBACK_ROOTS = ["~/Documents", "~/Desktop"]  # denied when ROOTS_FILE is missing or invalid

# Sandboxed commands may reach only these hosts. github.com and api.github.com are left out on
# purpose: a domain filter cannot tell a fetch from a push, so allowing them would allow push.
ALLOWED_DOMAINS = [
    "registry.npmjs.org",
    "pypi.org", "files.pythonhosted.org",
    "codeload.github.com", "objects.githubusercontent.com", "raw.githubusercontent.com",
    "localhost:11434",
]
# Removed from the environment of sandboxed commands.
SCRUBBED_ENV = ["GITHUB_TOKEN", "GH_TOKEN", "NPM_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

BASH_DENY = ["Bash(sudo *)", "Bash(git push *)", "Bash(git config *)", "Bash(git worktree prune *)"]
HOOKS = {"PreToolUse": [{
    "matcher": "Bash|Read|Edit|Write|MultiEdit|NotebookEdit|Glob|Grep",
    "hooks": [{"type": "command", "command": "python3 \"$HOME/.claude/hooks/cos/dev_guard.py\""}],
}]}


def student_roots(path: str | None = None) -> list[str]:
    """Roots from student_data_roots.txt; fails closed to ~/Documents and ~/Desktop."""
    roots, ok = [], True
    try:
        with open(path or ROOTS_FILE, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        lines, ok = [], False
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = s.replace("${HOME}", "~").replace("$HOME", "~")
        if s == "~":
            s = "~/"
        if not (s.startswith("~/") or os.path.isabs(s)):
            ok = False
            continue
        roots.append(s.rstrip("/") if s != "~/" else s)
    if not ok:
        roots += FALLBACK_ROOTS
    return roots


def denied_paths() -> list[str]:
    seen, out = set(), []
    for p in student_roots() + PRIVATE_PATHS + CREDENTIAL_PATHS + CLAUDE_PATHS:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _rule_path(p: str) -> str:
    """Sandbox path -> permission-rule path ('//' marks absolute in rules)."""
    return p if p.startswith("~/") else "/" + p


def _is_file(p: str) -> bool:
    return p.endswith(".json") or os.path.basename(p) in (".netrc", ".npmrc", ".pgpass")


def permission_denies() -> list[str]:
    rules = []
    for p in denied_paths():
        target = _rule_path(p) if _is_file(p) else _rule_path(p) + "/**"
        rules += [f"Read({target})", f"Edit({target})"]
    rules += ["Edit(~/.claude/hooks/**)", "Edit(.claude/**)"]
    return rules + BASH_DENY


def sandbox_block(lock: bool) -> dict:
    sb = {
        "enabled": True,
        "failIfUnavailable": True,
        "allowUnsandboxedCommands": False,
        "filesystem": {"denyRead": denied_paths(), "allowWrite": ["/tmp", "/private/tmp"]},
        "network": {"allowedDomains": list(ALLOWED_DOMAINS)},
        "credentials": {"envVars": [{"name": n, "mode": "deny"} for n in SCRUBBED_ENV]},
    }
    if lock:
        sb["network"]["strictAllowlist"] = True
    else:
        sb["autoAllowBashIfSandboxed"] = False
    return sb


def proposed() -> dict:
    return {"permissions": {"deny": permission_denies()}, "env": {"GIT_OPTIONAL_LOCKS": "0"},
            "sandbox": sandbox_block(lock=False), "hooks": HOOKS}


def lock() -> dict:
    return {"sandbox": sandbox_block(lock=True)}


def render() -> dict[str, str]:
    dump = lambda d: json.dumps(d, indent=2) + "\n"
    return {PROPOSED: dump(proposed()), LOCK: dump(lock())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render D1 settings")
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed files are stale")
    args = ap.parse_args(argv)
    stale = []
    for path, text in render().items():
        try:
            with open(path) as f:
                current = f.read()
        except OSError:
            current = None
        if current != text:
            stale.append(path)
            if not args.check:
                with open(path, "w") as f:
                    f.write(text)
    for p in stale:
        print(("stale: " if args.check else "wrote: ") + os.path.relpath(p))
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
