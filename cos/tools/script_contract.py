"""Static network-free / read-only contract for wrapped bin/chief-of-staff commands.

egress.py governs cos's own HTTP. It cannot see subprocesses, so each wrapped
status command is checked here before it is registered. The check covers the
code that actually runs for the flag:
  - bin/chief-of-staff top-level statements before the argument loop (other
    flags' `if [ "${1:-}" = "--x" ]` blocks and function bodies are skipped),
  - the flag's dispatch block (case arm or if-block),
  - every shell function those call, transitively,
  - every script they launch (bash/sh/source/python), followed recursively.

In that code it rejects: known network-capable commands, /dev/tcp|udp,
mutating commands (rm, mv, tee, ...), non-read git subcommands, file
redirections other than /dev/null, eval, inline interpreter code (bash -c,
python -c, ...), awk system()/pipes/redirects, dynamic command names, and
launched scripts it cannot resolve. Python scripts are checked with ast for
network, subprocess, and file-mutation use. It is a conservative denylist
check, not a sandbox: anything it cannot analyze is a violation.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

NETWORK_COMMANDS = frozenset({
    "curl", "wget", "nc", "ncat", "netcat", "socat", "telnet", "ssh", "scp", "sftp", "rsync",
    "ftp", "tftp", "http", "https", "httpie", "aria2c", "openssl", "dig", "nslookup", "host",
    "ping", "traceroute", "mtr", "gh", "npm", "npx", "pnpm", "yarn", "pip", "pip3", "brew",
    "ollama", "open", "osascript", "networksetup", "scutil", "launchctl", "softwareupdate",
    "mas", "docker", "kubectl", "aws", "gcloud", "az",
})
MUTATING_COMMANDS = frozenset({
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "tee", "dd", "chmod", "chown", "chgrp", "ln",
    "install", "truncate", "mktemp", "shred", "unlink", "defaults", "killall", "kill", "pkill",
    "crontab", "ditto", "tar", "zip", "unzip", "plutil", "xattr", "sudo", "doas",
})
DYNAMIC_EXEC = frozenset({"eval", "trap"})
SHELLS = frozenset({"bash", "sh", "zsh", "source", "."})
PYTHONS = frozenset({"python", "python3", "python3.12", "python3.11", "python3.13", "python3.14"})
OTHER_INTERPRETERS = frozenset({"node", "ruby", "perl", "php", "swift", "lua", "tclsh", "deno", "bun"})
PREFIX_COMMANDS = frozenset({"exec", "command", "builtin", "env", "nohup", "nice", "time", "xargs"})
KEYWORDS = frozenset({"if", "then", "elif", "else", "fi", "do", "done", "while", "until", "!", "{",
                      "}", "]]", "function", "esac", "in", "local", "declare", "readonly",
                      "export", "return", "shift", "set", "unset", "break", "continue", "typeset"})
GIT_READ = frozenset({"rev-parse", "diff", "status", "log", "show", "ls-files", "symbolic-ref",
                      "describe", "cat-file", "show-ref", "merge-base", "rev-list", "grep", "blame",
                      "for-each-ref", "name-rev", "check-ignore"})
SAFE_REDIRECT_TARGETS = frozenset({"/dev/null", "/dev/stderr", "/dev/stdout"})
COMMAND_SEPARATORS = frozenset({"|", "||", "&&", ";", "&", "(", ")", "|&", ";;", ";&", "\n"})
PY_NETWORK = frozenset({"socket", "ssl", "http", "urllib.request", "urllib3", "requests", "httpx",
                        "aiohttp", "ftplib", "smtplib", "telnetlib", "xmlrpc", "websocket",
                        "websockets", "subprocess", "multiprocessing", "shutil", "pty"})
PY_BAD_CALLS = frozenset({"os.system", "os.popen", "os.remove", "os.unlink", "os.rename",
                          "os.replace", "os.rmdir", "os.removedirs", "os.makedirs", "os.mkdir",
                          "os.execv", "os.execvp", "os.spawnv", "os.kill", "os.chmod"})
PY_BAD_METHODS = frozenset({"write_text", "write_bytes", "unlink", "mkdir", "rmdir", "rename",
                            "replace", "touch", "chmod", "symlink_to", "hardlink_to"})

HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^\]]*\])?\+?=")
FUNC_DEF_RE = re.compile(r"^(?:function\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*\(\)\s*\{?\s*$")
FLAG_IF_RE = re.compile(r'^if \[ "\$\{1:-\}" = "(--[A-Za-z0-9-]+)" \]; then\s*$')
MAIN_LOOP_RE = re.compile(r"^while \[\[ \$# -gt 0 \]\]; do\s*$")
PATH_VALUE_RE = re.compile(r"""^\s*(?:local\s+)?([A-Za-z_][A-Za-z0-9_]*)=["']?([^"'\s]+\.(?:sh|py))["']?\s*$""")


class ContractViolation(Exception):
    pass


# ----------------------------------------------------------------------------- lexing

def _read_paren(line: str, i: int) -> tuple[str, int]:
    """line[i:] follows a '$(' ; return (body, index after the matching ')')."""
    depth, j, quote = 1, i, None
    while j < len(line):
        c = line[j]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"':
                j += 1
        elif c in "'\"":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return line[i:j], j + 1
        j += 1
    return line[i:], len(line)


def lex(line: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Tokens [(kind, text)] with kind in {word, op}, plus command-substitution bodies."""
    tokens: list[tuple[str, str]] = []
    subs: list[str] = []
    cur, has_word, i, n = "", False, 0, len(line)

    def flush():
        nonlocal cur, has_word
        if has_word:
            tokens.append(("word", cur))
        cur, has_word = "", False

    while i < n:
        c = line[i]
        if c in " \t":
            flush()
            i += 1
        elif c == "\n":
            flush()
            tokens.append(("op", "\n"))
            i += 1
        elif c == "#" and not has_word:
            break
        elif c == "\\":
            cur += line[i + 1:i + 2]
            has_word = True
            i += 2
        elif c == "'":
            j = line.find("'", i + 1)
            j = n if j < 0 else j
            cur += line[i + 1:j]
            has_word = True
            i = j + 1
        elif c == '"':
            i += 1
            has_word = True
            while i < n and line[i] != '"':
                if line[i] == "\\":
                    cur += line[i + 1:i + 2]
                    i += 2
                elif line.startswith("$((", i):
                    end = line.find("))", i)
                    i = n if end < 0 else end + 2
                    cur += "0"
                elif line.startswith("$(", i):
                    body, i = _read_paren(line, i + 2)
                    subs.append(body)
                    cur += "$SUB"
                elif line[i] == "`":
                    end = line.find("`", i + 1)
                    end = n if end < 0 else end
                    subs.append(line[i + 1:end])
                    cur += "$SUB"
                    i = end + 1
                else:
                    cur += line[i]
                    i += 1
            i += 1
        elif line.startswith("$((", i):
            end = line.find("))", i)
            i = n if end < 0 else end + 2
            cur += "0"
            has_word = True
        elif line.startswith("$(", i):
            body, i = _read_paren(line, i + 2)
            subs.append(body)
            cur += "$SUB"
            has_word = True
        elif c == "`":
            end = line.find("`", i + 1)
            end = n if end < 0 else end
            subs.append(line[i + 1:end])
            cur += "$SUB"
            has_word = True
            i = end + 1
        elif c in "|;&()<>":
            flush()
            for op in (">>", "&>>", "&>", ">&", "<&", "<<<", "<<", "&&", "||", ";;", ";&", "|&", ">|"):
                if line.startswith(op, i):
                    tokens.append(("op", op))
                    i += len(op)
                    break
            else:
                tokens.append(("op", c))
                i += 1
        else:
            cur += c
            has_word = True
            i += 1
    flush()
    return tokens, subs


def _open_construct(text: str) -> bool:
    """True if text ends inside a quote or an unclosed $( ... )."""
    quote, depth, i = None, 0, 0
    while i < len(text):
        c = text[i]
        if quote == "'":
            if c == "'":
                quote = None
        elif quote == '"':
            if c == "\\":
                i += 1
            elif c == '"':
                quote = None
            elif text.startswith("$(", i):
                depth += 1
                i += 1
        else:
            if c == "\\":
                i += 1
            elif c == "#" and (i == 0 or text[i - 1] in " \t\n;"):
                nl = text.find("\n", i)
                if nl < 0:
                    break
                i = nl
            elif c in "'\"":
                quote = c
            elif text.startswith("$(", i):
                depth += 1
                i += 1
            elif c == ")" and depth:
                depth -= 1
        i += 1
    return quote is not None or depth > 0


def logical_lines(text: str) -> list[str]:
    """Join continuations and multi-line quotes; drop heredoc bodies (keeping unquoted
    bodies' substitutions)."""
    raw = text.replace("\\\n", " ").splitlines()
    out, i = [], 0
    while i < len(raw):
        line = raw[i]
        i += 1
        while _open_construct(line) and i < len(raw) and not HEREDOC_RE.search(line):
            line += "\n" + raw[i]
            i += 1
        out.append(line)
        m = HEREDOC_RE.search(line) if "<<<" not in line else None
        if m:
            quoted, delim = bool(m.group(1)), m.group(2)
            while i < len(raw) and raw[i].strip() != delim:
                if not quoted:
                    for sub in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", raw[i]):
                        out.append(sub[0] or sub[1])
                i += 1
            i += 1
    return out


# ----------------------------------------------------------------------------- shell scan

class Scan:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.violations: list[str] = []
        self.commands: list[str] = []
        self.launched: list[Path] = []

    def bad(self, where: str, why: str):
        self.violations.append(f"{where}: {why}")

    def resolve(self, arg: str, here: Path, assigns: dict) -> Path | None:
        value = arg
        m = re.fullmatch(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", arg)
        if m:
            value = assigns.get(m.group(1), "")
        if not value.endswith((".sh", ".py")):
            return None
        if "scripts/" in value:
            return self.repo_root / ("scripts/" + value.rsplit("scripts/", 1)[1])
        if re.match(r"\$\{?script_dir\}?/", value):
            return here.parent / value.split("/", 1)[1]
        if "$" not in value:
            p = Path(value)
            return p if p.is_absolute() else self.repo_root / p
        return None

    def check_command(self, words: list[str], where: str, here: Path, assigns: dict):
        while words and (ASSIGN_RE.match(words[0]) or words[0] in KEYWORDS or words[0] == "[["):
            if words[0] == "[[":  # test expression: operands are data, not commands
                words = words[words.index("]]") + 1:] if "]]" in words else []
                continue
            if words[0] in ("for", "case", "select"):
                return
            words = words[1:]
        if not words:
            return
        if words[0] in ("for", "case", "select"):
            return
        while words and words[0] in PREFIX_COMMANDS:
            words = [w for w in words[1:] if not ASSIGN_RE.match(w)] if words[0] == "env" else words[1:]
            while words and words[0].startswith("-"):
                words = words[1:]
        if not words:
            return
        cmd = words[0]
        name = cmd.rsplit("/", 1)[-1]
        self.commands.append(name)
        if "$" in cmd:
            self.bad(where, f"dynamic command name {cmd!r}")
        elif name in NETWORK_COMMANDS:
            self.bad(where, f"network-capable command {name!r}")
        elif name in MUTATING_COMMANDS:
            self.bad(where, f"mutating command {name!r}")
        elif name in DYNAMIC_EXEC:
            self.bad(where, f"dynamic execution {name!r}")
        elif name == "git":
            rest = list(words[1:])
            while rest and rest[0].startswith("-"):
                opt = rest.pop(0)
                if opt in ("-C", "-c") and rest:
                    rest.pop(0)
            sub = rest[0] if rest else ""
            if sub == "branch" and ("--show-current" in rest or "--list" in rest):
                pass
            elif sub not in GIT_READ:
                self.bad(where, f"git subcommand {sub!r} is not read-only")
        elif name == "sed" and any(w == "-i" or w.startswith("-i") for w in words[1:]):
            self.bad(where, "sed -i edits files")
        elif name == "find" and any(w in ("-exec", "-execdir", "-delete", "-ok") for w in words[1:]):
            self.bad(where, "find with -exec/-delete")
        elif name in ("awk", "gawk", "nawk"):
            prog = " ".join(words[1:])
            if re.search(r"system\s*\(|\|\s*getline|\bprintf?\b[^;]*?>\s*\S|\|\s*\"", prog):
                self.bad(where, "awk program runs commands or writes files")
        elif name in SHELLS or name in PYTHONS:
            args = words[1:]
            if any(a in ("-c", "-e") for a in args) or (name in PYTHONS and "-m" in args):
                self.bad(where, f"inline code passed to {name}")
                return
            target = next((a for a in args if not a.startswith("-")), None)
            if target is None:
                if name in SHELLS:
                    self.bad(where, f"{name} without a script reads code from stdin")
                return
            path = self.resolve(target, here, assigns)
            if path is None or not path.exists():
                self.bad(where, f"cannot resolve script launched by {name}: {target!r}")
            else:
                self.launched.append(path)
        elif name in OTHER_INTERPRETERS:
            self.bad(where, f"interpreter {name!r} is not analyzed")

    def scan_lines(self, lines: list[str], label: str, here: Path, assigns: dict, start: int = 1):
        queue = [(start + k, l) for k, l in enumerate(lines)]
        while queue:
            lineno, line = queue.pop(0)
            where = f"{label}:{lineno}"
            if "/dev/tcp" in line or "/dev/udp" in line:
                self.bad(where, "bash network redirection /dev/tcp|udp")
            tokens, subs = lex(line)
            queue.extend((lineno, s) for s in subs)
            words: list[str] = []
            expect_target = False
            for kind, text in tokens + [("op", "\n")]:
                if expect_target:
                    expect_target = False
                    if kind == "word" and text not in SAFE_REDIRECT_TARGETS and not text.isdigit() \
                            and text not in ("-",):
                        self.bad(where, f"redirection writes to {text!r}")
                    continue
                if kind == "op" and text in (">", ">>", ">|", "&>", "&>>"):
                    expect_target = True
                    continue
                if kind == "op" and text in (">&",):
                    expect_target = False
                    continue
                if kind == "op" and text in ("<<", "<<<", "<", "<&"):
                    expect_target = False
                    words.append("")  # consume the following word as data
                    continue
                if kind == "op" and text in COMMAND_SEPARATORS:
                    self.check_command([w for w in words if w != ""], where, here, assigns)
                    words = []
                    continue
                if words and words[-1] == "":
                    words.pop()  # heredoc delimiter / input file: data, not an argument
                    continue
                words.append(text)


def _assignments(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = PATH_VALUE_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _functions(lines: list[str]) -> dict[str, tuple[int, int]]:
    """name -> (first body line index, end index) for column-0 `name() {` ... `}` blocks."""
    funcs, i = {}, 0
    while i < len(lines):
        m = FUNC_DEF_RE.match(lines[i])
        if m:
            j = i + 1
            while j < len(lines) and lines[j].rstrip() != "}":
                j += 1
            funcs[m.group(1)] = (i + 1, j)
            i = j
        i += 1
    return funcs


def _dispatch_region(lines: list[str], flag: str) -> tuple[int, int]:
    found = []
    arm = re.compile(r"^\s+" + re.escape(flag) + r"\)\s*$")
    for i, line in enumerate(lines):
        if arm.match(line):
            j = i + 1
            while j < len(lines) and lines[j].strip() != ";;":
                j += 1
            found.append((i + 1, j))
        m = FLAG_IF_RE.match(line)
        if m and m.group(1) == flag:
            j = i + 1
            while j < len(lines) and lines[j].rstrip() != "fi":
                j += 1
            found.append((i + 1, j))
    if len(found) != 1:
        raise ContractViolation(f"bin/chief-of-staff: expected one dispatch block for {flag}, found {len(found)}")
    return found[0]


def _toplevel_region(lines: list[str], flag: str) -> list[int]:
    """Indexes of top-level lines that run for every flag before the argument loop."""
    funcs = _functions(lines)
    skip = set()
    for start, end in funcs.values():
        skip.update(range(start - 1, end + 1))
    keep, i = [], 0
    while i < len(lines):
        line = lines[i]
        if MAIN_LOOP_RE.match(line):
            break
        m = FLAG_IF_RE.match(line)
        if m:
            j = i
            while j < len(lines) and lines[j].rstrip() != "fi":
                j += 1
            i = j + 1
            continue
        if i not in skip:
            keep.append(i)
        i += 1
    return keep


def _scan_python(path: Path, scan: Scan, label: str):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        scan.bad(label, f"python not analyzable ({type(e).__name__})")
        return
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        for name in names:
            if name in PY_NETWORK or name.split(".")[0] in PY_NETWORK:
                scan.bad(f"{label}:{node.lineno}", f"python imports {name!r}")
        if isinstance(node, ast.Call):
            fn = node.func
            dotted = ast.unparse(fn) if isinstance(fn, (ast.Attribute, ast.Name)) else ""
            if dotted in PY_BAD_CALLS:
                scan.bad(f"{label}:{node.lineno}", f"python calls {dotted}")
            elif isinstance(fn, ast.Attribute) and fn.attr in PY_BAD_METHODS:
                scan.bad(f"{label}:{node.lineno}", f"python calls .{fn.attr}()")
            elif dotted in ("open", "io.open") and len(node.args) > 1:
                mode = node.args[1]
                if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)
                        and set(mode.value) <= set("rbt")):
                    scan.bad(f"{label}:{node.lineno}", "python opens a file for writing")
            elif dotted in ("eval", "exec", "__import__", "compile"):
                scan.bad(f"{label}:{node.lineno}", f"python dynamic {dotted}()")


def _scan_shell_file(path: Path, scan: Scan, regions=None):
    text = path.read_text(encoding="utf-8")
    label = str(path.relative_to(scan.repo_root)) if path.is_relative_to(scan.repo_root) else str(path)
    assigns = _assignments(text)
    raw = text.splitlines()
    funcs = _functions(raw)
    if regions is None:
        scan.scan_lines(logical_lines(text), label, path, assigns)
        return
    # Dispatcher mode: only the given line indexes, then called functions transitively.
    seen_funcs: set[str] = set()
    pending = [regions]
    while pending:
        idxs = pending.pop()
        chunk = "\n".join(raw[i] for i in idxs)
        before = len(scan.commands)
        scan.scan_lines(logical_lines(chunk), label, path, assigns, start=idxs[0] + 1 if idxs else 1)
        for name in scan.commands[before:]:
            if name in funcs and name not in seen_funcs:
                seen_funcs.add(name)
                start, end = funcs[name]
                pending.append(list(range(start, end)))


def check_flag(repo_root: Path, flag: str) -> list[str]:
    """Return contract violations for `bin/chief-of-staff <flag>` (empty list = compliant)."""
    repo_root = Path(repo_root)
    bin_path = repo_root / "bin" / "chief-of-staff"
    scan = Scan(repo_root)
    try:
        lines = bin_path.read_text(encoding="utf-8").splitlines()
        start, end = _dispatch_region(lines, flag)
    except (OSError, ContractViolation) as e:
        return [str(e)]
    _scan_shell_file(bin_path, scan, regions=_toplevel_region(lines, flag))
    _scan_shell_file(bin_path, scan, regions=list(range(start, end)))
    done: set[Path] = set()
    while scan.launched:
        path = scan.launched.pop(0).resolve()
        if path in done:
            continue
        done.add(path)
        if not path.is_relative_to(repo_root.resolve()):
            scan.bad(str(path), "launched script is outside the repository")
        elif path.suffix == ".py":
            _scan_python(path, scan, str(path.relative_to(repo_root.resolve())))
        else:
            _scan_shell_file(path, scan)
    return scan.violations
