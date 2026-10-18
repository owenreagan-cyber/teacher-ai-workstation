#!/usr/bin/env python3
"""Developer safety guard: a Claude Code PreToolUse hook (stdlib only).

Source of truth: tools/dev_safety/dev_guard.py in the teacher-ai-workstation repo.
Running copy: ~/.claude/hooks/cos/dev_guard.py, installed read-only by
install_dev_guard.py. Never edit the installed copy directly.

This hook is the second layer. It checks the command text, so it cannot see what
a program it allows (python3 x.py, npm test, make) goes on to do; the Claude Code
Bash sandbox (tools/dev_safety/README.md) is what contains those.

Reads one PreToolUse JSON payload on stdin. Allowed calls exit 0 with no
output; denied calls print a hookSpecificOutput deny decision. Anything the
guard cannot parse is denied (fail closed).

Bash policy
  - git (after normalizing `git -C ..`, `git -c k=v ..`, `env X=1 git ..`,
    `/usr/bin/git ..`, `$(..)`): deny push, config, clean, gc, update-ref,
    reset --hard, any force flag, `-c alias.*`, and worktree add/remove/move/prune
    unless the target is exactly $COS_FEATURE_WORKTREE (prune is always denied).
  - sudo / doas / su: always denied.
  - inline code: shells (sh, bash, zsh, ...) with or without arguments,
    `python -c`, `node -e/-p`, `perl -e/-E`, `ruby -e`, `php -r`, `osascript`,
    awk programs that call system() or pipe, and interpreters reading their
    program from stdin. Wrappers (env, xargs, nice, timeout, exec, find -exec)
    are peeled recursively. Running a file or module stays allowed.
  - destructive: rm -r / rmdir outside the project or system temp, find -delete,
    shred, dd, mkfs/newfs, diskutil erase/zero/reformat/partition, tmutil delete,
    brew uninstall/autoremove/cleanup, docker rm/rmi/prune.
  - ps: allowed only with an explicit -o format made of safe keywords
    (e.g. `ps -o pid,ppid,comm`); full-command-line forms are denied.
  - pgrep: deny -a, and -f combined with -l.
  - any path-like word or redirection target (absolute, relative, ~, $HOME,
    following `cd` within the command and symlinks) that resolves into a denied
    root, or a glob / variable whose literal prefix contains one.

File-tool policy (Read, Edit, Write, MultiEdit, NotebookEdit, Glob, Grep, and any
other tool whose input carries a path)
  - every path-bearing key (file_path, notebook_path, path, edits[].file_path, ...)
    is checked; a write-like tool with no recognizable path is denied;
  - deny any path that resolves (after symlinks) into a denied root. Denied roots are
    the credential stores, Claude Code state, and the ChiefOfStaff state folder in
    DENIED_ROOT_RELS, plus any roots in student_data_roots.txt (beside this file; empty
    under the D-022 light profile); if that file is missing, unreadable, or invalid,
    ~/Documents and ~/Desktop are denied too;
  - deny Glob/Grep whose search base contains a denied root;
  - deny Edit/Write-family calls into <project>/.claude or the installed
    hook directory.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import sys
import tempfile

TAG = "[dev_guard]"

PATH_KEYS = ("file_path", "notebook_path", "path", "filePath", "notebookPath")
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
WRITE_LIKE_RE = re.compile(r"(Edit|Write)", re.I)
NON_FILE_TOOLS = {"TodoWrite"}  # name looks write-like, but it never touches a file
SEARCH_TOOLS = {"Glob", "Grep"}

# Light profile (D-022): ~/.teacher-ai-workstation and ~/Downloads are not denied; school
# files on Owen's Mac are non-sensitive. Credential stores, Claude Code state, and the
# ChiefOfStaff state folder stay denied.
DENIED_ROOT_RELS = (
    ".ssh",
    ".aws",
    ".gnupg",
    ".config/gh",
    ".netrc",
    ".docker/config.json",
    ".kube/config",
    ".npmrc",
    ".pgpass",
    ".config/op",
    ".config/gcloud",
    "Library/Application Support/ChiefOfStaff",
    # Claude Code's own state: settings, account file, and every session transcript.
    ".claude.json",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/projects",
)
HOOK_DIR_REL = ".claude/hooks/cos"
# Student-data roots, one per line (~ and globs allowed). Read from beside this file, so the
# installed hook reads its installed, read-only copy.
ROOTS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "student_data_roots.txt")
# Denied when ROOTS_FILE is missing, unreadable, or has an invalid line (fail closed).
FALLBACK_ROOT_RELS = ("Documents", "Desktop")
GLOB_RE = re.compile(r"[*?\[]")

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

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "csh", "tcsh"}
PASSTHROUGH = {"command", "builtin", "exec", "nohup", "time", "caffeinate", "arch", "stdbuf"}
PRIV = {"sudo", "doas", "su", "run0", "pkexec"}
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
PYTHON_RE = re.compile(r"^(python|pypy)(\d+(\.\d+)?)?$")
AWKS = {"awk", "gawk", "nawk", "mawk"}
# Tools that walk a directory tree: a base that contains a denied root reaches it.
TREE_WALKERS = {"find", "rg", "ag", "tar", "zip", "rsync", "ditto", "du", "tree"}
# Characters after which a word's value is unknown to the guard (globs, variables, expansions).
OPAQUE_RE = re.compile(r"[*?\[{$`]")
MAX_DEPTH = 6


class Deny(Exception):
    pass


# ---------------------------------------------------------------- paths

def _home(ctx):
    return ctx["home"]


def _roots(ctx):
    h = _home(ctx)
    return [os.path.join(h, r) for r in DENIED_ROOT_RELS] + list(ctx.get("extra_roots", ()))


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


def _strictly_under(path, root):
    for p in _variants(path):
        for q in _variants(root):
            if p.startswith(q.rstrip("/") + "/"):
                return True
    return False


def _expand(raw, ctx, base=None):
    s = raw.replace("${HOME}", _home(ctx)).replace("$HOME", _home(ctx))
    if s == "~" or s.startswith("~/"):
        s = _home(ctx) + s[1:]
    if not os.path.isabs(s):
        s = os.path.join(base or ctx["cwd"], s)
    return os.path.normpath(s)


def _resolve_all(raw, ctx):
    """raw resolved against every working directory the command may be in."""
    return sorted({_expand(raw, ctx, c) for c in ctx.get("cwds") or [ctx["cwd"]]})


def load_student_roots(path, home):
    """(literal roots, glob patterns) from the roots file; fails closed to ~/Documents, ~/Desktop."""
    roots, globs, ok = [], [], True
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        lines, ok = [], False
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = s.replace("${HOME}", home).replace("$HOME", home)
        if s == "~" or s.startswith("~/"):
            s = home + s[1:]
        if not os.path.isabs(s):
            ok = False  # a relative root has no meaning for the hook: fail closed
            continue
        s = os.path.normpath(s)
        (globs if GLOB_RE.search(s) else roots).append(s)
    if not ok:
        roots += [os.path.join(home, r) for r in FALLBACK_ROOT_RELS]
    return roots, globs


def _glob_hit(path, pattern):
    """True when path, or a folder above it, matches the glob pattern."""
    for p in _variants(path):
        while True:
            if fnmatch.fnmatchcase(p, pattern):
                return True
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
    return False


def denied_root_for(path, ctx):
    for root in _roots(ctx):
        if _under(path, root):
            return root
    for pattern in ctx.get("root_globs", ()):
        if _glob_hit(path, pattern):
            return pattern
    return None


def _contains_denied_root(base, ctx):
    """The denied root a recursive walk from base would reach, if any."""
    for t in _roots(ctx):
        if _under(t, base):
            return t
    for pattern in ctx.get("root_globs", ()):
        prefix = _glob_prefix(pattern) or "/"
        if _under(prefix, base) or _under(base, prefix):
            return pattern
    return None


def _glob_prefix(pattern):
    """Literal directory prefix of a glob pattern ('' when it starts with a wildcard)."""
    m = OPAQUE_RE.search(pattern)
    if m is None:
        return pattern
    head = pattern[:m.start()]
    return head.rsplit("/", 1)[0] if "/" in head else ""


def _protected_write(p, ctx):
    proj_claude = os.path.join(ctx["project_dir"], ".claude")
    if _under(p, proj_claude):
        return f"{proj_claude} is denied (profile is immutable to the agent)"
    hook_dir = os.path.join(_home(ctx), HOOK_DIR_REL)
    if _under(p, hook_dir):
        return f"installed hook directory {hook_dir} is denied"
    return None


# ---------------------------------------------------------------- file tools

def _collect_paths(obj, tool, where=""):
    """Every value under a path-bearing key, at any depth (MultiEdit edits[], ...)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PATH_KEYS:
                if v is None:
                    continue
                if not isinstance(v, str):
                    raise Deny(f"{tool}.{where}{k} is not a string")
                if v:
                    out.append(v)
            elif isinstance(v, (dict, list)):
                out += _collect_paths(v, tool, f"{where}{k}.")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _collect_paths(v, tool, f"{where}[{i}].")
    return out


def check_file_tool(tool, tin, ctx):
    is_write = tool in WRITE_TOOLS or (tool not in NON_FILE_TOOLS and bool(WRITE_LIKE_RE.search(tool)))
    if tool == "MultiEdit" and "edits" in tin and not isinstance(tin["edits"], list):
        raise Deny("MultiEdit.edits is not a list")
    raw = _collect_paths(tin, tool)
    if is_write and not raw:
        raise Deny(f"{tool} payload has no recognizable path (unknown write-tool shape)")
    paths = [_expand(v, ctx) for v in raw]
    if tool in SEARCH_TOOLS:
        top = tin.get("path")
        base = _expand(top, ctx) if isinstance(top, str) and top else ctx["cwd"]
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
        if is_write:
            why = _protected_write(p, ctx)
            if why:
                raise Deny(f"{tool} into {why}")


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


# ---------------------------------------------------------------- inline code

def _inline(prog, how):
    raise Deny(f"inline code execution ({prog} {how}) is denied; write a file and run it instead")


def _check_short_flag_interp(prog, args, code_letters, value_letters="", stop_letters=""):
    """Generic scan for perl/ruby/php/lua-style interpreters.

    Denies when a short-option cluster before the script contains a code letter, or when
    no script is named (program read from stdin). Returns normally when a file runs.
    """
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-":
            _inline(prog, "- (program on stdin)")
        if a == "--":
            if i + 1 < len(args):
                return
            break
        if a.startswith("--"):
            if a in ("--version", "--help"):
                return
            i += 1
            continue
        if a.startswith("-") and len(a) > 1:
            for k, ch in enumerate(a[1:], start=1):
                if ch in code_letters:
                    _inline(prog, f"-{ch}")
                if ch in stop_letters:
                    return
                if ch in value_letters:
                    if k == len(a) - 1:
                        i += 1
                    break
            i += 1
            continue
        return  # a script file
    _inline(prog, "with no script (program on stdin)")


def check_python(prog, args):
    _check_short_flag_interp(prog, args, code_letters="c", value_letters="WXQ", stop_letters="mVh?")


def check_node(prog, args):
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-e", "--eval", "-p", "--print") or a.startswith(("--eval=", "--print=")):
            _inline(prog, a)
        if a in ("-v", "--version", "-h", "--help", "--test", "--run", "--check", "-c"):
            return
        if a in ("-r", "--require", "--import", "--loader", "--experimental-loader", "--input-type",
                 "--env-file", "--conditions", "-C"):
            i += 2
            continue
        if a == "-":
            _inline(prog, "- (program on stdin)")
        if re.fullmatch(r"-[a-z]+", a) and set(a[1:]) & set("ep"):
            _inline(prog, a)
        if a.startswith("-"):
            i += 1
            continue
        return  # a script file
    _inline(prog, "with no script (program on stdin)")


def check_bun_deno(prog, args):
    if prog == "bun":
        for a in args:
            if a in ("-e", "--eval", "-p", "--print") or a.startswith(("--eval=", "--print=")):
                _inline(prog, a)
        return
    sub = next((a for a in args if not a.startswith("-")), None)
    if sub in ("eval", "repl") or sub is None and "-" in args:
        _inline(prog, sub or "-")


def check_awk(prog, args):
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-f" or a.startswith("--file"):
            return  # program from a file
        if a in ("-v", "-F", "--assign", "--field-separator"):
            i += 2
            continue
        if a == "--":
            i += 1
            break
        if a.startswith("-") and len(a) > 1:
            i += 1
            continue
        break
    if i < len(args):
        program = args[i]
        if "system" in program or "|" in program:
            raise Deny(f"{prog} program that runs commands (system() or a pipe) is denied")


def check_interpreters(prog, args):
    if prog in SHELLS:
        raise Deny(f"running a shell ({prog}{' ' + args[0] if args else ''}) is denied; "
                   "run the command directly")
    if prog == "osascript":
        _inline(prog, "(AppleScript/JXA)")
    if PYTHON_RE.match(prog):
        check_python(prog, args)
    elif prog in ("node", "nodejs"):
        check_node(prog, args)
    elif prog in ("bun", "deno"):
        check_bun_deno(prog, args)
    elif prog == "perl" or re.fullmatch(r"perl5(\.\d+)*", prog):
        _check_short_flag_interp(prog, args, code_letters="eE", value_letters="IMmdDxC")
    elif prog == "ruby":
        _check_short_flag_interp(prog, args, code_letters="e", value_letters="IrCEFKTx0")
    elif prog == "php":
        _check_short_flag_interp(prog, args, code_letters="ra", value_letters="cdz", stop_letters="vhim")
    elif prog in ("lua", "luajit"):
        _check_short_flag_interp(prog, args, code_letters="e", value_letters="l", stop_letters="v")
    elif prog in ("Rscript", "R"):
        if any(a == "-e" or a.startswith("--expr") for a in args):
            _inline(prog, "-e")
    elif prog in AWKS:
        check_awk(prog, args)


# ---------------------------------------------------------------- destructive

def _safe_areas(ctx):
    return [ctx["project_dir"]] + list(ctx.get("temp_roots", ()))


def _require_safe_targets(prog, targets, ctx):
    """Every target (all cwd readings) must be strictly inside the project or system temp."""
    if not targets:
        return
    for t in targets:
        literal = _glob_prefix(t) if OPAQUE_RE.search(t) else t
        for p in _resolve_all(literal or ".", ctx):
            if not any(_strictly_under(p, area) for area in _safe_areas(ctx)):
                raise Deny(f"{prog} {t}: target {p} is outside the project and system temp")


def _positional(args, value_opts=()):
    out, i, end = [], 0, False
    while i < len(args):
        a = args[i]
        if not end and a == "--":
            end = True
        elif not end and a in value_opts:
            i += 1
        elif end or not a.startswith("-") or a == "-":
            out.append(a)
        i += 1
    return out


def check_destructive(prog, args, ctx):
    low = [a.lower() for a in args]
    if prog == "rm":
        recursive = any(a in ("--recursive",) or (re.fullmatch(r"-[A-Za-z]+", a) and set(a[1:]) & set("rR"))
                        for a in args if a != "--")
        if recursive:
            _require_safe_targets(prog, _positional(args), ctx)
    elif prog == "rmdir":
        _require_safe_targets(prog, _positional(args), ctx)
    elif prog in ("shred", "srm"):
        raise Deny(f"{prog} is denied")
    elif prog == "dd":
        if any(a.startswith(("if=", "of=")) for a in args):
            raise Deny("dd with if=/of= is denied")
    elif prog.startswith(("mkfs", "newfs")):
        raise Deny(f"{prog} is denied")
    elif prog == "diskutil":
        if any(a.startswith(("erase", "zero", "reformat", "partition", "secureerase", "randomdisk",
                             "delete", "resize")) for a in low):
            raise Deny(f"diskutil {' '.join(args[:2])} is denied")
    elif prog == "tmutil":
        if any(a.startswith(("delete", "thinlocal")) for a in low):
            raise Deny(f"tmutil {' '.join(args[:1])} is denied")
    elif prog == "brew":
        sub = next((a for a in low if not a.startswith("-")), "")
        if sub in ("uninstall", "remove", "rm", "autoremove", "cleanup"):
            raise Deny(f"brew {sub} is denied")
    elif prog in ("docker", "podman"):
        words = [a for a in low if not a.startswith("-")]
        sub = words[0] if words else ""
        nxt = words[1] if len(words) > 1 else ""
        if sub in ("rm", "rmi") or (sub in ("system", "volume", "image", "container", "network",
                                            "builder", "buildx") and nxt in ("prune", "rm", "remove")):
            raise Deny(f"{prog} {sub} {nxt}".rstrip() + " is denied")


def check_find(args, ctx, depth):
    if "-delete" in args:
        raise Deny("find -delete is denied")
    i = 0
    while i < len(args):
        if args[i] in ("-exec", "-execdir", "-ok", "-okdir"):
            j = i + 1
            while j < len(args) and args[j] not in (";", "+"):
                j += 1
            analyze_words(args[i + 1:j], ctx, depth + 1)
            i = j
        i += 1


# ---------------------------------------------------------------- bash paths

def _pathish(piece):
    return (piece.startswith(("~", "/", "."))
            or "/" in piece or "$HOME" in piece or "${HOME}" in piece)


def check_bash_paths(items, ctx, walker=False):
    """items: [(kind, token)]. Checks words and redirection targets against denied roots."""
    hook_dir = os.path.join(_home(ctx), HOOK_DIR_REL)
    for kind, w in items:
        for piece in re.split(r"[=:]", w):
            if not piece or piece.startswith("-") or not _pathish(piece):
                continue
            opaque = bool(OPAQUE_RE.search(piece.replace("${HOME}", "").replace("$HOME", "")))
            literal = _glob_prefix(piece) if opaque else piece
            for p in _resolve_all(literal or ".", ctx):
                root = denied_root_for(p, ctx)
                if root:
                    raise Deny(f"Bash argument {w} resolves into denied root {root}")
                if (opaque or walker) and kind == "word":
                    hit = _contains_denied_root(p, ctx)
                    if hit:
                        raise Deny(f"Bash argument {w} can reach denied root {hit}")
                if _under(p, hook_dir):
                    raise Deny(f"Bash access to installed hook directory {hook_dir} is denied")
                if kind == "redir-target":
                    why = _protected_write(p, ctx)
                    if why:
                        raise Deny(f"Bash redirection into {why}")


# ---------------------------------------------------------------- bash

def analyze_words(words, ctx, depth):
    words = _strip_wrappers(words, ctx, depth)
    if not words:
        return
    prog = os.path.basename(words[0].lstrip("\\"))
    args = words[1:]
    if prog in PRIV:
        raise Deny(f"privilege escalation via {prog} is denied")
    if prog == "eval":
        analyze_command(" ".join(args), ctx, depth + 1)
        return
    check_interpreters(prog, args)
    check_destructive(prog, args, ctx)
    if prog == "find":
        check_find(args, ctx, depth)
    if prog == "git":
        check_git(args, ctx)
    elif prog == "ps":
        check_ps(args)
    elif prog == "pgrep":
        check_pgrep(args)


def _is_walker(words):
    words = [w for w in words if not ASSIGN_RE.match(w)]
    if not words:
        return False
    prog = os.path.basename(words[0])
    if prog in TREE_WALKERS:
        return True
    flags = "".join(a[1:] for a in words[1:] if re.fullmatch(r"-[A-Za-z]+", a))
    if prog in ("grep", "egrep", "fgrep") and set(flags) & set("rR"):
        return True
    if prog in ("cp", "scp", "chmod", "chown") and set(flags) & set("rRa"):
        return True
    if prog == "ls" and "R" in flags:
        return True
    return "--recursive" in words


def analyze_command(command, ctx, depth=0):
    if depth > MAX_DEPTH:
        raise Deny("shell nesting too deep to analyze")
    tokens = tokenize(command)
    ctx = dict(ctx, cwds=list(ctx.get("cwds") or [ctx["cwd"]]))
    for cmd in split_commands(tokens):
        words = [t for kind, t in cmd if kind == "word"]
        check_bash_paths(cmd, ctx, walker=_is_walker(words))
        analyze_words(words, ctx, depth)
        stripped = [w for w in words if not ASSIGN_RE.match(w)]
        if stripped and stripped[0] in ("cd", "pushd"):
            dest = next((a for a in stripped[1:] if not a.startswith("-")), "~")
            # A cd may or may not take effect (subshells, failures): keep every candidate.
            new = [_expand(dest, ctx, c) for c in ctx["cwds"]]
            ctx["cwds"] = sorted(set(ctx["cwds"]) | set(new))
    for body in substitutions(command):
        analyze_command(body, ctx, depth + 1)


# ---------------------------------------------------------------- entry

def default_temp_roots():
    roots = {tempfile.gettempdir(), "/tmp", "/private/tmp"}
    if os.environ.get("TMPDIR"):
        roots.add(os.environ["TMPDIR"])
    return sorted(os.path.realpath(r) for r in roots)


def evaluate(payload, home=None, temp_roots=None, roots_file=None):
    """Return None to allow, or a deny reason string."""
    if not isinstance(payload, dict):
        return "malformed hook payload"
    tool = payload.get("tool_name")
    tin = payload.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tin, dict):
        return "malformed hook payload (tool_name/tool_input)"
    cwd = payload.get("cwd") or os.getcwd()
    home = os.path.normpath(home or os.path.expanduser("~"))
    extra_roots, root_globs = load_student_roots(roots_file or ROOTS_FILE, home)
    ctx = {
        "home": home,
        "cwd": cwd,
        "project_dir": os.environ.get("CLAUDE_PROJECT_DIR") or cwd,
        "temp_roots": default_temp_roots() if temp_roots is None else list(temp_roots),
        "extra_roots": extra_roots,
        "root_globs": root_globs,
    }
    try:
        if tool == "Bash":
            cmd = tin.get("command")
            if not isinstance(cmd, str):
                raise Deny("Bash.command is not a string")
            analyze_command(cmd, ctx)
        else:
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
