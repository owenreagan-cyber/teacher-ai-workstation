#!/usr/bin/env python3
"""Developer safety guard: a Claude Code PreToolUse hook (stdlib only).

Source of truth: tools/dev_safety/dev_guard.py in the recovery repo.
Running copy: ~/.claude/hooks/cos/dev_guard.py, installed read-only by
install_dev_guard.py. Never edit the installed copy directly.

Reads one PreToolUse JSON payload on stdin. Allowed calls exit 0 with no
output; denied calls print a hookSpecificOutput deny decision. Anything the
guard cannot parse is denied (fail closed).

Bash policy
  - git (after normalizing `git -C ..`, `git -c k=v ..`, `env X=1 git ..`,
    `/usr/bin/git ..`, `bash -c '..'`, `$(..)`): deny push, config, clean,
    gc, update-ref, reset --hard, any force flag, `-c alias.*`, and
    worktree add/remove/move/prune unless the target is exactly
    $COS_FEATURE_WORKTREE (prune is always denied).
  - sudo / doas: always denied.
  - ps: allowed only with an explicit -o format made of safe keywords
    (e.g. `ps -o pid,ppid,comm`); full-command-line forms are denied.
  - pgrep: deny -a, and -f combined with -l.
  - any token that resolves into a denied root.

File-tool policy (Read, Edit, Write, MultiEdit, NotebookEdit, Glob, Grep)
  - deny any path that resolves (after symlinks) into a denied root;
  - deny Glob/Grep whose search base contains a denied root;
  - deny Edit/Write-family calls into <project>/.claude or the installed
    hook directory.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

TAG = "[dev_guard]"

FILE_PATH_KEYS = {
    "Read": ("file_path",),
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path",),
    "Glob": ("path",),
    "Grep": ("path",),
}
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SEARCH_TOOLS = {"Glob", "Grep"}

DENIED_ROOT_RELS = (
    ".teacher-ai-workstation",
    "Downloads",
    ".ssh",
    ".aws",
    ".gnupg",
    ".config/gh",
    "Library/Application Support/ChiefOfStaff",
)
HOOK_DIR_REL = ".claude/hooks/cos"
MEMORY_PARENT_REL = ".claude/projects"

GIT_DENIED_SUBCOMMANDS = {"push", "send-pack", "http-push", "config", "clean", "gc", "update-ref"}
# Global options that take a separate value. `=`-only options (--exec-path,
# --list-cmds, --super-prefix) are deliberately absent: consuming the next word
# for them would hide the real subcommand.
GIT_GLOBAL_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
# Short-option letters that mean "force" for each subcommand.
GIT_FORCE_LETTERS = {
    "add": "f", "checkout-index": "f", "clean": "f", "rm": "f", "mv": "f", "tag": "f",
    "fetch": "f", "pull": "f", "push": "f", "rebase": "f", "submodule": "f", "notes": "f",
    "replace": "f", "branch": "fDMC", "checkout": "fB", "switch": "fC", "worktree": "fB",
}
WORKTREE_VALUE_OPTS = {"-b", "-B", "--reason", "--orphan"}

PS_SAFE_KEYWORDS = {
    "pid", "ppid", "pgid", "sess", "comm", "ucomm", "stat", "state", "user", "ruser", "uid",
    "ruid", "gid", "rgid", "%cpu", "pcpu", "%mem", "pmem", "rss", "vsz", "etime", "time",
    "cputime", "start", "lstart", "tty", "tt", "pri", "nice", "ni", "flags", "f", "wchan",
    "tdev", "tpgid", "jobc", "lim", "logname", "nswap", "paddr", "rgroup", "group",
}
# macOS ps: these only select, sort, or reformat without adding argv/env columns.
PS_PLAIN_FLAGS = set("AaxrmchXS")
PS_VALUE_FLAGS = set("opUGt")

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
PASSTHROUGH = {"command", "builtin", "exec", "nohup", "time", "caffeinate"}
PRIV = {"sudo", "doas", "su", "run0", "pkexec"}
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
MAX_DEPTH = 6


class Deny(Exception):
    pass


# ---------------------------------------------------------------- paths

def _home(ctx):
    return ctx["home"]


def _roots(ctx):
    h = _home(ctx)
    return [os.path.join(h, r) for r in DENIED_ROOT_RELS]


def _variants(path):
    """The absolute path plus its symlink-resolved form."""
    a = os.path.normpath(path)
    r = os.path.realpath(a)
    return {a, r}


def _under(path, root):
    for p in _variants(path):
        for q in _variants(root):
            if p == q or p.startswith(q.rstrip("/") + "/"):
                return True
    return False


def _expand(raw, ctx, base=None):
    s = raw.replace("${HOME}", _home(ctx)).replace("$HOME", _home(ctx))
    if s == "~" or s.startswith("~/"):
        s = _home(ctx) + s[1:]
    if not os.path.isabs(s):
        s = os.path.join(base or ctx["cwd"], s)
    return os.path.normpath(s)


def _is_memory(path, ctx):
    parent = os.path.join(_home(ctx), MEMORY_PARENT_REL)
    for p in _variants(path):
        for q in _variants(parent):
            if p.startswith(q.rstrip("/") + "/"):
                parts = os.path.relpath(p, q).split(os.sep)
                if "memory" in parts[1:]:
                    return True
    return False


def denied_root_for(path, ctx):
    for root in _roots(ctx):
        if _under(path, root):
            return root
    if _is_memory(path, ctx):
        return os.path.join(_home(ctx), MEMORY_PARENT_REL, "**/memory")
    return None


def _contains_denied_root(base, ctx):
    """True when a recursive search from base would reach a denied root."""
    targets = _roots(ctx) + [os.path.join(_home(ctx), MEMORY_PARENT_REL)]
    for t in targets:
        if _under(t, base):
            return t
    return None


def _glob_prefix(pattern):
    """Literal directory prefix of a glob pattern ('' when it starts with a wildcard)."""
    m = re.search(r"[*?\[{]", pattern)
    if m is None:
        return pattern
    head = pattern[:m.start()]
    return head.rsplit("/", 1)[0] if "/" in head else ""


# ---------------------------------------------------------------- file tools

def check_file_tool(tool, tin, ctx):
    keys = FILE_PATH_KEYS[tool]
    paths = []
    for k in keys:
        v = tin.get(k)
        if v is not None and not isinstance(v, str):
            raise Deny(f"{tool}.{k} is not a string")
        if v:
            paths.append(_expand(v, ctx))
    if tool in SEARCH_TOOLS:
        base = paths[0] if paths else ctx["cwd"]
        pat = tin.get("pattern") if tool == "Glob" else tin.get("glob")
        if isinstance(pat, str) and pat:
            pre = _glob_prefix(pat)
            if pre:
                paths.append(_expand(pre, ctx, base))
        hit = _contains_denied_root(base, ctx)
        if hit:
            raise Deny(f"{tool} search base {base} contains denied root {hit}")
        if not paths:
            paths.append(base)
    for p in paths:
        root = denied_root_for(p, ctx)
        if root:
            raise Deny(f"{tool} path {p} resolves into denied root {root}")
        if tool in WRITE_TOOLS:
            proj_claude = os.path.join(ctx["project_dir"], ".claude")
            if _under(p, proj_claude):
                raise Deny(f"{tool} into {proj_claude} is denied (profile is immutable to the agent)")
            hook_dir = os.path.join(_home(ctx), HOOK_DIR_REL)
            if _under(p, hook_dir):
                raise Deny(f"{tool} into installed hook directory {hook_dir} is denied")


# ---------------------------------------------------------------- shell parsing

def tokenize(command):
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = "#"
    try:
        return list(lex)
    except ValueError as e:
        raise Deny(f"unparseable shell command ({e})")


def split_commands(tokens):
    cmds, cur = [], []
    skip_next = False
    for t in tokens:
        if skip_next:
            skip_next = False
            cur.append(("redir-target", t))
            continue
        if t and set(t) <= set(";&|()<>\n"):
            if "<" in t or ">" in t:
                skip_next = True
                continue
            if cur:
                cmds.append(cur)
            cur = []
            continue
        cur.append(("word", t))
    if cur:
        cmds.append(cur)
    return cmds


def substitutions(command):
    """Rough extraction of $(..), `..`, <(..), >(..) bodies (fail-closed: over-approximate)."""
    out = []
    for m in re.finditer(r"\$\(|<\(|>\(", command):
        out.append(command[m.end():])
    parts = command.split("`")
    out.extend(parts[1::2])
    return out


def _strip_wrappers(words, ctx, depth):
    """Peel env/command/nohup/etc. Returns remaining words (program first)."""
    i = 0
    while i < len(words):
        w = words[i]
        if ASSIGN_RE.match(w):
            i += 1
            continue
        base = os.path.basename(w.lstrip("\\"))
        if base in PRIV:
            raise Deny(f"privilege escalation via {base} is denied")
        if base == "env":
            i += 1
            while i < len(words):
                a = words[i]
                if a in ("-u", "--unset", "-C", "--chdir"):
                    i += 2
                elif a in ("-S", "--split-string"):
                    analyze_command(" ".join(words[i + 1:]), ctx, depth + 1)
                    return []
                elif a.startswith("-") or ASSIGN_RE.match(a):
                    i += 1
                else:
                    break
            continue
        if base in PASSTHROUGH:
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
            continue
        if base == "nice":
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] == "-n" else 1
            continue
        if base in ("timeout", "gtimeout"):
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in ("-s", "-k", "--signal", "--kill-after") else 1
            i += 1  # duration
            continue
        if base == "xargs":
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in ("-I", "-n", "-L", "-P", "-s", "-d", "-E", "-J", "-R", "-S") else 1
            continue
        break
    return words[i:]


# ---------------------------------------------------------------- git

def check_git(args, ctx):
    base = ctx["cwd"]
    i = 0
    while i < len(args):
        a = args[i]
        if not a.startswith("-"):
            break
        if a in GIT_GLOBAL_VALUE_OPTS:
            if i + 1 >= len(args):
                raise Deny(f"git option {a} missing its value")
            v = args[i + 1]
            if a == "-C":
                base = _expand(v, ctx, base)
            if a == "-c" and v.lower().startswith("alias."):
                raise Deny("git -c alias.* is denied (defeats subcommand checks)")
            if a == "--config-env" and v.lower().startswith("alias."):
                raise Deny("git --config-env alias.* is denied")
            i += 2
            continue
        if a.startswith("--config-env=") and a.split("=", 1)[1].lower().startswith("alias."):
            raise Deny("git --config-env alias.* is denied")
        if a.startswith("-c") and len(a) > 2 and a[2:].lower().startswith("alias."):
            raise Deny("git -c alias.* is denied")
        if a.startswith("-C") and len(a) > 2:
            base = _expand(a[2:], ctx, base)
        i += 1
    if i >= len(args):
        return
    sub, rest = args[i], args[i + 1:]
    if sub in GIT_DENIED_SUBCOMMANDS:
        raise Deny(f"git {sub} is denied")
    for a in rest:
        if a == "--":
            break
        if a == "--force" or a.startswith("--force-") or a.startswith("--force="):
            raise Deny(f"git {sub} {a}: force flags are denied")
        letters = GIT_FORCE_LETTERS.get(sub, "")
        if letters and re.fullmatch(r"-[A-Za-z]+", a) and set(a[1:]) & set(letters):
            raise Deny(f"git {sub} {a}: force flags are denied")
        if sub == "fetch" and a.startswith("+"):
            raise Deny(f"git fetch {a}: forced refspec is denied")
    if sub == "reset" and "--hard" in rest:
        raise Deny("git reset --hard is denied")
    if sub == "worktree":
        check_git_worktree(rest, base, ctx)


def check_git_worktree(rest, base, ctx):
    if not rest:
        return
    action, rest = rest[0], rest[1:]
    if action == "prune":
        raise Deny("git worktree prune is denied")
    if action == "move":
        raise Deny("git worktree move is denied")
    if action not in ("add", "remove"):
        return
    positional, i = [], 0
    while i < len(rest):
        a = rest[i]
        if a in WORKTREE_VALUE_OPTS:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        positional.append(a)
        i += 1
    feature = os.environ.get("COS_FEATURE_WORKTREE", "")
    if not feature:
        raise Deny(f"git worktree {action} denied: COS_FEATURE_WORKTREE is not set")
    if not positional:
        raise Deny(f"git worktree {action} denied: no target path")
    target = _expand(positional[0], ctx, base)
    feat = _expand(feature, ctx)
    if not (_variants(target) & _variants(feat)):
        raise Deny(f"git worktree {action} {target} is outside the feature worktree {feat}")


# ---------------------------------------------------------------- ps / pgrep

def check_ps(args):
    saw_format = False
    i = 0
    while i < len(args):
        a = args[i]
        if not a.startswith("-") or a.startswith("--"):
            raise Deny(f"ps {a}: BSD-style/long options can expose full command lines; "
                       "use `ps -o pid,ppid,comm`")
        j = 1
        while j < len(a):
            c = a[j]
            if c in PS_VALUE_FLAGS:
                val = a[j + 1:] if j + 1 < len(a) else (args[i + 1] if i + 1 < len(args) else None)
                if val is None:
                    raise Deny(f"ps -{c} missing value")
                if j + 1 >= len(a):
                    i += 1
                if c == "o":
                    saw_format = True
                    for kw in re.split(r"[,\s]+", val.lstrip("=")):
                        kw = kw.split("=", 1)[0].lower()
                        if kw and kw not in PS_SAFE_KEYWORDS:
                            raise Deny(f"ps -o {kw}: keyword can expose command lines")
                break
            if c not in PS_PLAIN_FLAGS:
                raise Deny(f"ps -{c}: flag can expose full command lines or environment")
            j += 1
        i += 1
    if not saw_format:
        raise Deny("ps without an explicit safe -o format shows full command lines; "
                   "use `ps -o pid,ppid,comm`")


def check_pgrep(args):
    flags = set()
    for a in args:
        if a.startswith("--"):
            if a in ("--list-full", "--list-name"):
                flags.add("a" if a == "--list-full" else "l")
            if a == "--full":
                flags.add("f")
            continue
        if a.startswith("-") and len(a) > 1:
            flags.update(a[1:])
    if "a" in flags:
        raise Deny("pgrep -a prints full command lines")
    if "f" in flags and "l" in flags:
        raise Deny("pgrep -f with -l prints full command lines")


# ---------------------------------------------------------------- bash

def check_bash_paths(words, ctx):
    for w in words:
        if not (w.startswith("~") or w.startswith("/") or "$HOME" in w or "${HOME}" in w):
            continue
        for piece in re.split(r"[=:]", w):
            if not piece or not (piece.startswith("~") or piece.startswith("/") or "HOME" in piece):
                continue
            p = _expand(piece, ctx)
            root = denied_root_for(p, ctx)
            if root:
                raise Deny(f"Bash argument {w} resolves into denied root {root}")
            hook_dir = os.path.join(_home(ctx), HOOK_DIR_REL)
            if _under(p, hook_dir):
                raise Deny(f"Bash access to installed hook directory {hook_dir} is denied")


def analyze_words(words, ctx, depth):
    words = _strip_wrappers(words, ctx, depth)
    if not words:
        return
    prog = os.path.basename(words[0].lstrip("\\"))
    args = words[1:]
    if prog in PRIV:
        raise Deny(f"privilege escalation via {prog} is denied")
    if prog in SHELLS or prog == "eval":
        if prog == "eval":
            analyze_command(" ".join(args), ctx, depth + 1)
            return
        for k, a in enumerate(args):
            if a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
                if k + 1 < len(args):
                    analyze_command(args[k + 1], ctx, depth + 1)
                return
    if prog == "git":
        check_git(args, ctx)
    elif prog == "ps":
        check_ps(args)
    elif prog == "pgrep":
        check_pgrep(args)


def analyze_command(command, ctx, depth=0):
    if depth > MAX_DEPTH:
        raise Deny("shell nesting too deep to analyze")
    tokens = tokenize(command)
    for cmd in split_commands(tokens):
        words = [t for kind, t in cmd if kind == "word"]
        check_bash_paths([t for _, t in cmd], ctx)
        analyze_words(words, ctx, depth)
    for body in substitutions(command):
        analyze_command(body, ctx, depth + 1)


# ---------------------------------------------------------------- entry

def evaluate(payload, home=None):
    """Return None to allow, or a deny reason string."""
    if not isinstance(payload, dict):
        return "malformed hook payload"
    tool = payload.get("tool_name")
    tin = payload.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tin, dict):
        return "malformed hook payload (tool_name/tool_input)"
    cwd = payload.get("cwd") or os.getcwd()
    ctx = {
        "home": os.path.normpath(home or os.path.expanduser("~")),
        "cwd": cwd,
        "project_dir": os.environ.get("CLAUDE_PROJECT_DIR") or cwd,
    }
    try:
        if tool == "Bash":
            cmd = tin.get("command")
            if not isinstance(cmd, str):
                raise Deny("Bash.command is not a string")
            analyze_command(cmd, ctx)
        elif tool in FILE_PATH_KEYS:
            check_file_tool(tool, tin, ctx)
    except Deny as d:
        return str(d)
    return None


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, OSError) as e:
        payload = None
        reason = f"unreadable hook payload ({e})"
    else:
        reason = evaluate(payload)
    if payload is None or reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{TAG} {reason or 'malformed hook payload'}",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
